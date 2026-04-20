"""Celery translation task — wraps the async TranslationService in a sync worker."""

from __future__ import annotations

import asyncio
import logging

from celery.exceptions import SoftTimeLimitExceeded

from app.core.celery_app import celery_app
from app.core.database import async_session_maker
from app.services.translation_service import TranslationService

logger = logging.getLogger(__name__)


async def _run_translation(
    novel_id: int,
    from_chapter: int,
    to_chapter: int,
    max_retries: int,
    retranslate: bool,
) -> dict:
    """Async implementation: opens its own DB session and calls TranslationService."""
    async with async_session_maker() as session:
        svc = TranslationService(session)
        try:
            if retranslate:
                progress = await svc.retranslate_chapters(
                    novel_id, from_chapter, to_chapter, max_retries
                )
            else:
                progress = await svc.translate_chapters(
                    novel_id, from_chapter, to_chapter, max_retries
                )
            await session.commit()
            return progress.model_dump()
        except Exception:
            await session.rollback()
            logger.exception("Translation failed for novel %d", novel_id)
            raise


@celery_app.task(
    bind=True,
    name="tasks.run_translation",
    max_retries=1,
    acks_late=True,
    reject_on_worker_lost=True,
    time_limit=2400,
    soft_time_limit=1800,
)
def run_translation(
    self,
    novel_id: int,
    from_chapter: int,
    to_chapter: int,
    max_retries: int,
    retranslate: bool,
) -> dict:
    """Sync Celery task that bridges into the async TranslationService.

    Returns a serialised :class:`~app.schemas.api.translation.TranslationProgress`
    dict stored in the result backend.
    """
    logger.info(
        "Task %s: translating novel=%d chapters %d–%d retranslate=%s",
        self.request.id,
        novel_id,
        from_chapter,
        to_chapter,
        retranslate,
    )
    try:
        return asyncio.run(
            _run_translation(novel_id, from_chapter, to_chapter, max_retries, retranslate)
        )
    except SoftTimeLimitExceeded:
        logger.error("Task %s hit soft time limit — giving up", self.request.id)
        raise
    except Exception as exc:
        logger.exception("Task %s failed: %s", self.request.id, exc)
        raise self.retry(exc=exc, countdown=60)
