"""TranslationService — orchestrates the LangGraph pipeline with the database layer."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.chapter import Chapter, ChapterStatus
from app.graph.pipeline import build_graph
from app.repositories.chapter_repository import ChapterRepository
from app.repositories.glossary_repository import GlossaryRepository
from app.repositories.novel_repository import NovelRepository
from app.repositories.translation_job_repository import TranslationJobRepository
from app.schemas.api.translation import ChapterProgress, TranslationProgress
from app.schemas.graph.names import NamesExtractionResult

logger = logging.getLogger(__name__)

# Compile once at module import
_graph = build_graph()


class TranslationService:
    """Drive the LangGraph translation pipeline for one or more chapters.

    Each call to :meth:`translate_chapters` runs sequentially through the
    requested chapter range, updating the database after every chapter.
    Previous summaries are chained automatically (chapter N summary → chapter N+1
    ``previous_summary``).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._novel_repo = NovelRepository(session)
        self._chapter_repo = ChapterRepository(session)
        self._glossary_repo = GlossaryRepository(session)
        self._job_repo = TranslationJobRepository(session)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def translate_chapters(
        self,
        novel_id: int,
        from_chapter: int,
        to_chapter: int,
        max_retries: int = 2,
    ) -> TranslationProgress:
        """Translate a contiguous range of chapters for the given novel.

        Skips chapters whose status is already TRANSLATED.
        Updates chapter status / glossary / job records after each chapter.
        """
        chapters = await self._chapter_repo.get_range(
            novel_id, from_chapter, to_chapter
        )
        if not chapters:
            logger.warning(
                "No chapters found for novel %d in range [%d, %d]",
                novel_id,
                from_chapter,
                to_chapter,
            )
            return await self.get_translation_progress(novel_id)

        # Load glossary once for the whole run
        glossary_text = await self._glossary_repo.export_as_text(novel_id)

        previous_summary = await self._get_previous_summary(
            novel_id, chapters[0].chapter_number
        )

        for chapter in chapters:
            if chapter.status == ChapterStatus.TRANSLATED:
                logger.info(
                    "Skipping already-translated chapter %d", chapter.chapter_number
                )
                previous_summary = chapter.summary or previous_summary
                continue

            previous_summary = await self._process_single_chapter(
                chapter=chapter,
                glossary_text=glossary_text,
                previous_summary=previous_summary,
                max_retries=max_retries,
            )
            # Re-load glossary after each chapter to pick up new terms
            glossary_text = await self._glossary_repo.export_as_text(novel_id)

        return await self.get_translation_progress(novel_id)

    async def retranslate_chapters(
        self,
        novel_id: int,
        from_chapter: int,
        to_chapter: int,
        max_retries: int = 2,
    ) -> TranslationProgress:
        """Reset chapters in range to PENDING and translate them again."""
        chapters = await self._chapter_repo.get_range(
            novel_id, from_chapter, to_chapter
        )
        for chapter in chapters:
            await self._chapter_repo.reset_translation(chapter.id)

        return await self.translate_chapters(
            novel_id, from_chapter, to_chapter, max_retries
        )

    async def get_translation_progress(self, novel_id: int) -> TranslationProgress:
        chapters = await self._chapter_repo.get_by_novel_id(novel_id)
        chapter_progress = []
        translated = pending = translating = failed = 0

        for ch in chapters:
            latest_job = await self._job_repo.get_latest_by_chapter(ch.id)
            verdict = latest_job.review_verdict if latest_job else None
            chapter_progress.append(
                ChapterProgress(
                    chapter_number=ch.chapter_number,
                    status=ch.status,
                    verdict=verdict,
                )
            )
            match ch.status:
                case ChapterStatus.TRANSLATED:
                    translated += 1
                case ChapterStatus.PENDING:
                    pending += 1
                case ChapterStatus.TRANSLATING:
                    translating += 1
                case ChapterStatus.FAILED:
                    failed += 1

        return TranslationProgress(
            novel_id=novel_id,
            total=len(chapters),
            translated=translated,
            pending=pending,
            translating=translating,
            failed=failed,
            chapters=chapter_progress,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_previous_summary(
        self, novel_id: int, current_chapter_number: int
    ) -> str:
        """Return summary from the chapter immediately before the translation range."""
        if current_chapter_number <= 1:
            return ""
        prev_chapter = await self._chapter_repo.get_previous_chapter(
            novel_id, current_chapter_number
        )
        if prev_chapter and prev_chapter.summary:
            return prev_chapter.summary
        return ""

    async def _process_single_chapter(
        self,
        chapter: Chapter,
        glossary_text: str,
        previous_summary: str,
        max_retries: int,
    ) -> str:
        """Run the pipeline for a single chapter and persist results.

        Returns the ``current_summary`` for use as the next chapter's
        ``previous_summary``.
        """
        logger.info(
            "=== Translating chapter %d (id=%d) ===", chapter.chapter_number, chapter.id
        )

        # Mark chapter as in-progress
        await self._chapter_repo.update_status(chapter.id, ChapterStatus.TRANSLATING)

        # Create job record
        job = await self._job_repo.create_job(chapter.id)
        await self._job_repo.mark_running(job.id)

        initial_state = {
            "chapter_id": chapter.id,
            "novel_id": chapter.novel_id,
            "chinese_text": chapter.original_content,
            "glossary_text": glossary_text,
            "names_result": None,
            "translate_result": None,
            "review_result": None,
            "final_text": "",
            "previous_summary": previous_summary,
            "current_summary": "",
            "retry_count": 0,
            "max_retries": max_retries,
        }

        try:
            final_state = await _graph.ainvoke(initial_state)
        except Exception as exc:
            error_msg = str(exc)
            logger.exception(
                "Pipeline failed for chapter %d: %s", chapter.chapter_number, error_msg
            )
            await self._chapter_repo.update_status(chapter.id, ChapterStatus.FAILED)
            await self._job_repo.mark_failed(job.id, error_msg)
            return previous_summary  # carry forward the last good summary

        # --- Persist results ---
        final_text: str = final_state.get("final_text", "")
        current_summary: str = final_state.get("current_summary", "")
        review_result = final_state.get("review_result")
        verdict = review_result.verdict if review_result else ""
        feedback = review_result.feedback_for_edit if review_result else ""

        await self._chapter_repo.update_translation(
            chapter.id, final_text, current_summary
        )
        await self._job_repo.mark_completed(
            job_id=job.id,
            translated_text=final_text,
            review_verdict=str(verdict),
            review_feedback=feedback,
            summary_text=current_summary,
        )

        # --- Insert only NEW glossary entries from names extraction ---
        names_result: NamesExtractionResult | None = final_state.get("names_result")
        if names_result and names_result.names:
            new_entries = await self._glossary_repo.bulk_insert_new(
                novel_id=chapter.novel_id,
                entries=[
                    {
                        "source_term": n.chinese,
                        "target_term": n.unified,
                        "category": n.category,
                    }
                    for n in names_result.names
                ],
            )
            logger.info(
                "Inserted %d new glossary entries from chapter %d (total extracted: %d)",
                len(new_entries),
                chapter.chapter_number,
                len(names_result.names),
            )

        logger.info(
            "Chapter %d done — verdict=%s retries=%d",
            chapter.chapter_number,
            verdict,
            final_state.get("retry_count", 0),
        )
        return current_summary
