"""Translation router — trigger and monitor translation jobs via Celery."""

from __future__ import annotations

import logging
from typing import Annotated

from celery.result import AsyncResult
from fastapi import APIRouter, Path

from app.core.database import DbDep
from app.schemas.api.translation import (
    TaskStatus,
    TranslateRequest,
    TranslationJobQueued,
    TranslationProgress,
)
from app.services.translation_service import TranslationService
from app.tasks.translation_tasks import run_translation

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/novels/{novel_id}", tags=["Translation"])


NovelIdPath = Annotated[int, Path(ge=1, description="Novel ID")]


@router.post("/translate", status_code=202)
async def translate_chapters(
    novel_id: NovelIdPath,
    body: TranslateRequest,
) -> TranslationJobQueued:
    """Queue translation for chapters [from_chapter, to_chapter].

    Returns 202 immediately; translation runs in a Celery worker.
    Already-translated chapters are skipped.
    """
    task = run_translation.delay(
        novel_id=novel_id,
        from_chapter=body.from_chapter,
        to_chapter=body.to_chapter,
        max_retries=body.max_retries,
        retranslate=False,
    )
    return TranslationJobQueued(
        task_id=task.id,
        message=f"Translation queued for chapters {body.from_chapter}–{body.to_chapter}",
    )


@router.post("/retranslate", status_code=202)
async def retranslate_chapters(
    novel_id: NovelIdPath,
    body: TranslateRequest,
) -> TranslationJobQueued:
    """Queue re-translation for chapters in range (resets existing translations first)."""
    task = run_translation.delay(
        novel_id=novel_id,
        from_chapter=body.from_chapter,
        to_chapter=body.to_chapter,
        max_retries=body.max_retries,
        retranslate=True,
    )
    return TranslationJobQueued(
        task_id=task.id,
        message=f"Re-translation queued for chapters {body.from_chapter}–{body.to_chapter}",
    )


@router.get("/translate/progress")
async def translation_progress(novel_id: NovelIdPath, db: DbDep) -> TranslationProgress:
    """Get current translation progress for a novel (reads from DB)."""
    return await TranslationService(db).get_translation_progress(novel_id)


@router.get("/translate/task/{task_id}")
async def translation_task_status(
    novel_id: NovelIdPath,
    task_id: Annotated[str, Path(description="Celery task ID returned by /translate")],
) -> TaskStatus:
    """Poll the status of a queued translation task.

    Possible statuses: ``PENDING``, ``STARTED``, ``SUCCESS``, ``FAILURE``, ``RETRY``.
    ``result`` is populated once the task succeeds (contains TranslationProgress).
    """
    async_result = AsyncResult(task_id)
    result = None
    if async_result.successful():
        result = async_result.result
    return TaskStatus(task_id=task_id, status=async_result.status, result=result)
