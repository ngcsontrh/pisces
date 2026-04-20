"""Novel router — CRUD + EPUB import endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, UploadFile

from app.core.database import DbDep
from app.schemas.api.novel import NovelResponse, NovelUpdate, NovelWithStats
from app.services.epub_service import EpubService
from app.services.novel_service import NovelService
from app.services.txt_service import TxtService

router = APIRouter(prefix="/api/novels", tags=["Novels"])


@router.post("/import", status_code=201)
async def import_epub(
    file: Annotated[UploadFile, File(description="EPUB file to import")],
    db: DbDep,
) -> NovelResponse:
    """Parse an EPUB file, extract metadata and chapters, persist to DB."""
    content = await file.read()
    service = EpubService(db)
    novel = await service.import_epub(content, filename=file.filename or "")
    return novel


@router.post("/import/txt", status_code=201)
async def import_txt(
    file: Annotated[UploadFile, File(description="TXT file to import")],
    db: DbDep,
    title: str | None = None,
    author: str | None = None,
) -> NovelResponse:
    """Upload a plain-text file, auto-split into ~3 000-char chapters."""
    content = await file.read()
    service = TxtService(db)
    novel = await service.import_txt(
        content, filename=file.filename or "", title=title, author=author
    )
    return novel


@router.get("")
async def list_novels(db: DbDep) -> list[NovelResponse]:
    """List all imported novels."""
    return await NovelService(db).list_novels()


@router.get("/{novel_id}")
async def get_novel(novel_id: int, db: DbDep) -> NovelWithStats:
    """Retrieve a novel with its translation statistics."""
    svc = NovelService(db)
    novel = await svc.get_novel(novel_id)
    stats = await svc.get_novel_stats(novel_id)
    return NovelWithStats(**novel.__dict__, stats=stats)


@router.patch("/{novel_id}")
async def update_novel(
    novel_id: int,
    data: NovelUpdate,
    db: DbDep,
) -> NovelResponse:
    """Update novel metadata (title, author, description)."""
    return await NovelService(db).update_novel(novel_id, data)


@router.delete("/{novel_id}", status_code=204)
async def delete_novel(novel_id: int, db: DbDep) -> None:
    """Delete a novel and all its chapters, glossary, and jobs."""
    await NovelService(db).delete_novel(novel_id)
