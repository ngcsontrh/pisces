"""TranslationJobRepository — async CRUD for TranslationJob."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.translation_job import JobStatus, TranslationJob


class TranslationJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, job_id: int) -> TranslationJob | None:
        result = await self._session.execute(
            select(TranslationJob).where(TranslationJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_by_chapter_id(self, chapter_id: int) -> list[TranslationJob]:
        """Return all jobs for a chapter ordered by attempt_number."""
        result = await self._session.execute(
            select(TranslationJob)
            .where(TranslationJob.chapter_id == chapter_id)
            .order_by(TranslationJob.attempt_number)
        )
        return list(result.scalars().all())

    async def get_latest_by_chapter(self, chapter_id: int) -> TranslationJob | None:
        """Return the most recent job for a chapter."""
        result = await self._session.execute(
            select(TranslationJob)
            .where(TranslationJob.chapter_id == chapter_id)
            .order_by(TranslationJob.attempt_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_next_attempt_number(self, chapter_id: int) -> int:
        """Compute the next attempt number for a chapter (max + 1, minimum 1)."""
        result = await self._session.execute(
            select(func.max(TranslationJob.attempt_number)).where(
                TranslationJob.chapter_id == chapter_id
            )
        )
        current_max = result.scalar_one_or_none()
        return (current_max or 0) + 1

    async def create_job(self, chapter_id: int) -> TranslationJob:
        """Create a new pending job for the given chapter."""
        attempt = await self.get_next_attempt_number(chapter_id)
        job = TranslationJob(
            chapter_id=chapter_id,
            attempt_number=attempt,
            status=JobStatus.PENDING,
        )
        self._session.add(job)
        await self._session.flush()
        await self._session.refresh(job)
        return job

    async def mark_running(self, job_id: int) -> TranslationJob | None:
        job = await self.get_by_id(job_id)
        if job is None:
            return None
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        await self._session.flush()
        await self._session.refresh(job)
        return job

    async def mark_completed(
        self,
        job_id: int,
        translated_text: str,
        review_verdict: str,
        review_feedback: str,
        summary_text: str,
    ) -> TranslationJob | None:
        job = await self.get_by_id(job_id)
        if job is None:
            return None
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now(timezone.utc)
        job.translated_text = translated_text
        job.review_verdict = review_verdict
        job.review_feedback = review_feedback
        job.summary_text = summary_text
        await self._session.flush()
        await self._session.refresh(job)
        return job

    async def mark_failed(
        self, job_id: int, error_message: str
    ) -> TranslationJob | None:
        job = await self.get_by_id(job_id)
        if job is None:
            return None
        job.status = JobStatus.FAILED
        job.completed_at = datetime.now(timezone.utc)
        job.error_message = error_message
        await self._session.flush()
        await self._session.refresh(job)
        return job
