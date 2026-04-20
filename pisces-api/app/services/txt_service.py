"""TxtService — import a plain-text (.txt) file, auto-split into chapters."""

from __future__ import annotations

import logging
import os

from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.chapter import Chapter
from app.entities.novel import Novel
from app.repositories.chapter_repository import ChapterRepository
from app.repositories.novel_repository import NovelRepository

logger = logging.getLogger(__name__)

TARGET_CHAPTER_SIZE = 3000  # characters per chapter


def _split_chapters(text: str, target_size: int = TARGET_CHAPTER_SIZE) -> list[str]:
    """Split *text* into chunks of approximately *target_size* characters.

    Splits only at line boundaries (``\\n``) so that no line is ever cut in
    half.  Each chunk is at least *target_size* characters long (except
    possibly the last one).
    """
    lines = text.splitlines(keepends=True)
    chunks: list[str] = []
    buffer: list[str] = []
    buffer_len = 0

    for line in lines:
        buffer.append(line)
        buffer_len += len(line)

        if buffer_len >= target_size:
            chunks.append("".join(buffer).strip())
            buffer.clear()
            buffer_len = 0

    # Remaining lines → last chapter
    if buffer:
        tail = "".join(buffer).strip()
        if tail:
            chunks.append(tail)

    return chunks


class TxtService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._novel_repo = NovelRepository(session)
        self._chapter_repo = ChapterRepository(session)

    async def import_txt(
        self,
        file_bytes: bytes,
        filename: str = "",
        title: str | None = None,
        author: str | None = None,
    ) -> Novel:
        """Decode a UTF-8 text file, split into chapters, and persist.

        Args:
            file_bytes: Raw bytes of the uploaded ``.txt`` file.
            filename:   Original filename (used to derive a fallback title).
            title:      Explicit novel title; overrides filename-derived title.
            author:     Explicit author name.

        Returns:
            The newly created :class:`Novel` ORM instance.
        """
        logger.info("Importing TXT: %s (%d bytes)", filename, len(file_bytes))

        text = file_bytes.decode("utf-8")

        # --- Metadata ---
        derived_title = title or os.path.splitext(filename)[0] or "Untitled"

        novel = Novel(
            title=derived_title,
            author=author or "",
            description="",
        )
        novel = await self._novel_repo.create(novel)
        logger.info("Created Novel id=%d title=%r", novel.id, novel.title)

        # --- Split & persist chapters ---
        raw_chapters = _split_chapters(text)
        chapters: list[Chapter] = []

        for idx, content in enumerate(raw_chapters, start=1):
            # Use first non-empty line as the chapter title (max 500 chars)
            first_line = next(
                (ln.strip() for ln in content.splitlines() if ln.strip()),
                f"Chương {idx}",
            )
            chapters.append(
                Chapter(
                    novel_id=novel.id,
                    chapter_number=idx,
                    title=first_line[:500],
                    original_content=content,
                )
            )

        if chapters:
            await self._chapter_repo.bulk_create(chapters)
            logger.info(
                "Created %d chapters for novel id=%d", len(chapters), novel.id
            )
        else:
            logger.warning("No content found in TXT file: %s", filename)

        return novel
