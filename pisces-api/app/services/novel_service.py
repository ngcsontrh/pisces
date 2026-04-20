"""NovelService — high-level operations on novels."""

from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.chapter import ChapterStatus
from app.entities.novel import Novel
from app.repositories.chapter_repository import ChapterRepository
from app.repositories.novel_repository import NovelRepository
from app.schemas.api.novel import NovelStats, NovelUpdate

logger = logging.getLogger(__name__)


class NovelService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._novel_repo = NovelRepository(session)
        self._chapter_repo = ChapterRepository(session)

    async def get_novel(self, novel_id: int) -> Novel:
        novel = await self._novel_repo.get_by_id(novel_id)
        if novel is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Novel not found"
            )
        return novel

    async def list_novels(self) -> list[Novel]:
        return await self._novel_repo.get_all()

    async def update_novel(self, novel_id: int, data: NovelUpdate) -> Novel:
        novel = await self._novel_repo.get_by_id_simple(novel_id)
        if novel is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Novel not found"
            )
        if data.title is not None:
            novel.title = data.title
        if data.author is not None:
            novel.author = data.author
        if data.description is not None:
            novel.description = data.description
        return await self._novel_repo.update(novel)

    async def delete_novel(self, novel_id: int) -> None:
        deleted = await self._novel_repo.delete(novel_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Novel not found"
            )

    async def get_novel_stats(self, novel_id: int) -> NovelStats:
        chapters = await self._chapter_repo.get_by_novel_id(novel_id)
        total = len(chapters)
        translated = sum(1 for c in chapters if c.status == ChapterStatus.TRANSLATED)
        pending = sum(1 for c in chapters if c.status == ChapterStatus.PENDING)
        translating = sum(1 for c in chapters if c.status == ChapterStatus.TRANSLATING)
        failed = sum(1 for c in chapters if c.status == ChapterStatus.FAILED)
        return NovelStats(
            novel_id=novel_id,
            total_chapters=total,
            translated=translated,
            pending=pending,
            translating=translating,
            failed=failed,
        )
