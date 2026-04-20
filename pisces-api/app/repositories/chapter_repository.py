"""ChapterRepository — async CRUD + novel-scoped queries for Chapter."""

from __future__ import annotations

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.chapter import Chapter, ChapterStatus


class ChapterRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, chapter_id: int) -> Chapter | None:
        result = await self._session.execute(
            select(Chapter).where(Chapter.id == chapter_id)
        )
        return result.scalar_one_or_none()

    async def get_by_novel_id(self, novel_id: int) -> list[Chapter]:
        """Return all chapters for a novel ordered by chapter_number."""
        result = await self._session.execute(
            select(Chapter)
            .where(Chapter.novel_id == novel_id)
            .order_by(Chapter.chapter_number)
        )
        return list(result.scalars().all())

    async def get_by_novel_and_number(
        self, novel_id: int, chapter_number: int
    ) -> Chapter | None:
        result = await self._session.execute(
            select(Chapter).where(
                and_(
                    Chapter.novel_id == novel_id,
                    Chapter.chapter_number == chapter_number,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_range(self, novel_id: int, from_ch: int, to_ch: int) -> list[Chapter]:
        """Return chapters within [from_ch, to_ch] inclusive, ordered by number."""
        result = await self._session.execute(
            select(Chapter)
            .where(
                and_(
                    Chapter.novel_id == novel_id,
                    Chapter.chapter_number >= from_ch,
                    Chapter.chapter_number <= to_ch,
                )
            )
            .order_by(Chapter.chapter_number)
        )
        return list(result.scalars().all())

    async def get_previous_chapter(
        self, novel_id: int, chapter_number: int
    ) -> Chapter | None:
        """Fetch the chapter immediately before the given chapter_number."""
        result = await self._session.execute(
            select(Chapter).where(
                and_(
                    Chapter.novel_id == novel_id,
                    Chapter.chapter_number == chapter_number - 1,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_untranslated(self, novel_id: int) -> list[Chapter]:
        """Return chapters with status=pending ordered by chapter_number."""
        result = await self._session.execute(
            select(Chapter)
            .where(
                and_(
                    Chapter.novel_id == novel_id,
                    Chapter.status == ChapterStatus.PENDING,
                )
            )
            .order_by(Chapter.chapter_number)
        )
        return list(result.scalars().all())

    async def bulk_create(self, chapters: list[Chapter]) -> list[Chapter]:
        """Bulk-insert chapters and flush to populate ids."""
        self._session.add_all(chapters)
        await self._session.flush()
        for ch in chapters:
            await self._session.refresh(ch)
        return chapters

    async def update_translation(
        self,
        chapter_id: int,
        translated_content: str,
        summary: str,
    ) -> Chapter | None:
        """Set translated_content, summary, and flip status to TRANSLATED."""
        chapter = await self.get_by_id(chapter_id)
        if chapter is None:
            return None
        chapter.translated_content = translated_content
        chapter.summary = summary
        chapter.status = ChapterStatus.TRANSLATED
        await self._session.flush()
        await self._session.refresh(chapter)
        return chapter

    async def update_status(self, chapter_id: int, status: str) -> Chapter | None:
        """Set only the status field."""
        chapter = await self.get_by_id(chapter_id)
        if chapter is None:
            return None
        chapter.status = status
        await self._session.flush()
        await self._session.refresh(chapter)
        return chapter

    async def reset_translation(self, chapter_id: int) -> Chapter | None:
        """Clear translation data and reset status to PENDING (for re-translate)."""
        chapter = await self.get_by_id(chapter_id)
        if chapter is None:
            return None
        chapter.translated_content = None
        chapter.summary = None
        chapter.status = ChapterStatus.PENDING
        await self._session.flush()
        await self._session.refresh(chapter)
        return chapter

    async def create(self, chapter: Chapter) -> Chapter:
        self._session.add(chapter)
        await self._session.flush()
        await self._session.refresh(chapter)
        return chapter

    async def update(self, chapter: Chapter) -> Chapter:
        await self._session.flush()
        await self._session.refresh(chapter)
        return chapter

    async def delete(self, chapter_id: int) -> bool:
        chapter = await self.get_by_id(chapter_id)
        if chapter is None:
            return False
        await self._session.delete(chapter)
        await self._session.flush()
        return True
