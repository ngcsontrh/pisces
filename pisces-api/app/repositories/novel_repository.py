"""NovelRepository — async CRUD for the Novel entity."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.entities.novel import Novel


class NovelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, novel_id: int) -> Novel | None:
        """Fetch a novel by primary key (with chapters + glossary pre-loaded)."""
        result = await self._session.execute(
            select(Novel)
            .options(selectinload(Novel.chapters), selectinload(Novel.glossary_entries))
            .where(Novel.id == novel_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_simple(self, novel_id: int) -> Novel | None:
        """Fetch a novel by primary key without eagerly loading relationships."""
        result = await self._session.execute(select(Novel).where(Novel.id == novel_id))
        return result.scalar_one_or_none()

    async def get_all(self) -> list[Novel]:
        """Return all novels ordered by creation date descending."""
        result = await self._session.execute(
            select(Novel).order_by(Novel.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, novel: Novel) -> Novel:
        """Persist a new novel and flush to get its auto-generated id."""
        self._session.add(novel)
        await self._session.flush()
        await self._session.refresh(novel)
        return novel

    async def update(self, novel: Novel) -> Novel:
        """Merge an already-tracked Novel instance."""
        await self._session.flush()
        await self._session.refresh(novel)
        return novel

    async def delete(self, novel_id: int) -> bool:
        """Delete a novel (cascades to chapters, glossary, jobs). Returns True if found."""
        novel = await self.get_by_id_simple(novel_id)
        if novel is None:
            return False
        await self._session.delete(novel)
        await self._session.flush()
        return True
