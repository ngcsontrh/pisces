"""EpubService — import an EPUB file and persist its chapters to the database."""

from __future__ import annotations

import io
import logging
import re
from html.parser import HTMLParser

import ebooklib
from ebooklib import epub
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.chapter import Chapter
from app.entities.novel import Novel
from app.repositories.chapter_repository import ChapterRepository
from app.repositories.novel_repository import NovelRepository

logger = logging.getLogger(__name__)


class _HTMLStripper(HTMLParser):
    """Minimal HTML → plain-text converter that preserves paragraph breaks."""

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in ("p", "br", "div", "h1", "h2", "h3", "h4", "h5", "h6"):
            self._parts.append("\n")

    def get_text(self) -> str:
        text = "".join(self._parts)
        # Collapse 3+ blank lines into 2
        return re.sub(r"\n{3,}", "\n\n", text).strip()


def _html_to_text(html_content: str) -> str:
    stripper = _HTMLStripper()
    stripper.feed(html_content)
    return stripper.get_text()


def _get_meta(book: epub.EpubBook, dc_field: str) -> str:
    values = book.get_metadata("DC", dc_field)
    if values:
        raw = values[0]
        return raw[0] if isinstance(raw, (list, tuple)) else str(raw)
    return ""


class EpubService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._novel_repo = NovelRepository(session)
        self._chapter_repo = ChapterRepository(session)

    async def import_epub(self, file_bytes: bytes, filename: str = "") -> Novel:
        """Parse an EPUB byte stream and persist novel + chapters.

        Args:
            file_bytes: Raw bytes of the EPUB file.
            filename:   Original filename (used only for logging).

        Returns:
            The newly created :class:`Novel` ORM instance.
        """
        logger.info("Importing EPUB: %s (%d bytes)", filename, len(file_bytes))

        book = epub.read_epub(io.BytesIO(file_bytes))

        # --- Metadata ---
        title = _get_meta(book, "title") or "Untitled"
        author = _get_meta(book, "creator") or ""
        description = _get_meta(book, "description") or ""

        novel = Novel(
            title=title,
            author=author,
            description=description,
        )
        novel = await self._novel_repo.create(novel)
        logger.info("Created Novel id=%d title=%r", novel.id, novel.title)

        # --- Chapters ---
        chapters: list[Chapter] = []
        chapter_number = 1

        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            content = item.get_content()
            if not content:
                continue

            try:
                html_str = content.decode("utf-8", errors="replace")
            except Exception:
                continue

            plain_text = _html_to_text(html_str)
            if not plain_text.strip():
                continue  # skip empty spine items

            # Attempt to derive a chapter title from the first non-empty line
            first_line = next(
                (ln.strip() for ln in plain_text.splitlines() if ln.strip()),
                f"Chương {chapter_number}",
            )
            title_candidate = first_line[:500]

            chapters.append(
                Chapter(
                    novel_id=novel.id,
                    chapter_number=chapter_number,
                    title=title_candidate,
                    original_content=plain_text,
                )
            )
            chapter_number += 1

        if chapters:
            await self._chapter_repo.bulk_create(chapters)
            logger.info("Created %d chapters for novel id=%d", len(chapters), novel.id)
        else:
            logger.warning("No readable chapters found in EPUB: %s", filename)

        return novel
