"""Chapter router — list and edit chapters for a novel."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.database import DbDep
from app.schemas.api.chapter import ChapterListItem, ChapterResponse, ChapterUpdate
from app.services.chapter_service import ChapterService

router = APIRouter(prefix="/api/novels/{novel_id}/chapters", tags=["Chapters"])


@router.get("")
async def list_chapters(novel_id: int, db: DbDep) -> list[ChapterListItem]:
    """List all chapters (lightweight — no content) for a novel."""
    chapters = await ChapterService(db).list_chapters(novel_id)
    return chapters


@router.get("/{chapter_number}")
async def get_chapter(
    novel_id: int, chapter_number: int, db: DbDep
) -> ChapterResponse:
    """Get full chapter detail including original, translated content and summary."""
    return await ChapterService(db).get_chapter_by_number(novel_id, chapter_number)


@router.patch("/{chapter_number}")
async def update_chapter(
    novel_id: int,
    chapter_number: int,
    data: ChapterUpdate,
    db: DbDep,
) -> ChapterResponse:
    """Edit chapter title or manually set translated_content."""
    svc = ChapterService(db)
    chapter = await svc.get_chapter_by_number(novel_id, chapter_number)
    return await svc.update_chapter(chapter.id, data)
