"""ChapterService — chapter retrieval and editing."""

from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.chapter import Chapter
from app.repositories.chapter_repository import ChapterRepository
from app.schemas.api.chapter import ChapterUpdate

logger = logging.getLogger(__name__)


class ChapterService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._chapter_repo = ChapterRepository(session)

    async def get_chapter(self, chapter_id: int) -> Chapter:
        chapter = await self._chapter_repo.get_by_id(chapter_id)
        if chapter is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found"
            )
        return chapter

    async def get_chapter_by_number(
        self, novel_id: int, chapter_number: int
    ) -> Chapter:
        chapter = await self._chapter_repo.get_by_novel_and_number(
            novel_id, chapter_number
        )
        if chapter is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found"
            )
        return chapter

    async def list_chapters(self, novel_id: int) -> list[Chapter]:
        return await self._chapter_repo.get_by_novel_id(novel_id)

    async def get_chapter_range(
        self, novel_id: int, from_ch: int, to_ch: int
    ) -> list[Chapter]:
        return await self._chapter_repo.get_range(novel_id, from_ch, to_ch)

    async def update_chapter(self, chapter_id: int, data: ChapterUpdate) -> Chapter:
        chapter = await self._chapter_repo.get_by_id(chapter_id)
        if chapter is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found"
            )
        if data.title is not None:
            chapter.title = data.title
        if data.translated_content is not None:
            chapter.translated_content = data.translated_content
        return await self._chapter_repo.update(chapter)
