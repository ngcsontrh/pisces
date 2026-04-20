"""Glossary router — manage per-novel translation dictionaries."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.database import DbDep
from app.schemas.api.glossary import (
    GlossaryEntryCreate,
    GlossaryEntryResponse,
    GlossaryEntryUpdate,
)
from app.services.glossary_service import GlossaryService

router = APIRouter(prefix="/api/novels/{novel_id}/glossary", tags=["Glossary"])


@router.get("")
async def get_glossary(novel_id: int, db: DbDep) -> list[GlossaryEntryResponse]:
    """List all glossary entries for a novel, ordered by category and source term."""
    return await GlossaryService(db).get_glossary(novel_id)


@router.post("", status_code=201)
async def add_glossary_entry(
    novel_id: int,
    data: GlossaryEntryCreate,
    db: DbDep,
) -> GlossaryEntryResponse:
    """Add a new glossary entry. Returns 409 if source_term already exists."""
    return await GlossaryService(db).add_entry(novel_id, data)


@router.patch("/{entry_id}")
async def update_glossary_entry(
    novel_id: int,
    entry_id: int,
    data: GlossaryEntryUpdate,
    db: DbDep,
) -> GlossaryEntryResponse:
    """Update an existing glossary entry (target_term, category, or notes)."""
    return await GlossaryService(db).update_entry(entry_id, data)


@router.delete("/{entry_id}", status_code=204)
async def delete_glossary_entry(
    novel_id: int,
    entry_id: int,
    db: DbDep,
) -> None:
    """Remove a glossary entry."""
    await GlossaryService(db).delete_entry(entry_id)
