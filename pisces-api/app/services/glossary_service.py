"""GlossaryService — manage per-novel translation dictionaries."""

from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.glossary_entry import GlossaryEntry
from app.repositories.glossary_repository import GlossaryRepository
from app.schemas.api.glossary import GlossaryEntryCreate, GlossaryEntryUpdate

logger = logging.getLogger(__name__)


class GlossaryService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._glossary_repo = GlossaryRepository(session)

    async def get_glossary(self, novel_id: int) -> list[GlossaryEntry]:
        return await self._glossary_repo.get_by_novel_id(novel_id)

    async def add_entry(
        self, novel_id: int, data: GlossaryEntryCreate
    ) -> GlossaryEntry:
        # Check duplicate
        existing = await self._glossary_repo.get_by_novel_and_term(
            novel_id, data.source_term
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Term '{data.source_term}' already exists in this novel's glossary",
            )
        entry = GlossaryEntry(
            novel_id=novel_id,
            source_term=data.source_term,
            target_term=data.target_term,
            category=data.category,
            notes=data.notes,
        )
        return await self._glossary_repo.create(entry)

    async def update_entry(
        self, entry_id: int, data: GlossaryEntryUpdate
    ) -> GlossaryEntry:
        entry = await self._glossary_repo.get_by_id(entry_id)
        if entry is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Glossary entry not found"
            )
        if data.target_term is not None:
            entry.target_term = data.target_term
        if data.category is not None:
            entry.category = data.category
        if data.notes is not None:
            entry.notes = data.notes
        return await self._glossary_repo.update(entry)

    async def delete_entry(self, entry_id: int) -> None:
        deleted = await self._glossary_repo.delete(entry_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Glossary entry not found"
            )

    async def export_as_text(self, novel_id: int) -> str:
        """Return glossary as formatted text for LLM prompt injection."""
        return await self._glossary_repo.export_as_text(novel_id)
