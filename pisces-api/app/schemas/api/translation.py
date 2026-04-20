"""API schemas for Translation endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TranslateRequest(BaseModel):
    """Request body to start or re-start translation for a chapter range."""

    from_chapter: int = Field(ge=1, description="First chapter number (inclusive)")
    to_chapter: int = Field(ge=1, description="Last chapter number (inclusive)")
    max_retries: int = Field(
        2, ge=0, le=5, description="Max LangGraph retry loops per chapter"
    )


class ChapterProgress(BaseModel):
    """Per-chapter status within a translation run."""

    chapter_number: int
    status: str
    verdict: str | None = None


class TranslationProgress(BaseModel):
    """Overall translation progress for a novel."""

    novel_id: int
    total: int
    translated: int
    pending: int
    translating: int
    failed: int
    chapters: list[ChapterProgress] = []


class TranslationJobQueued(BaseModel):
    """Response returned immediately after queuing a translation job."""

    task_id: str
    message: str


class TaskStatus(BaseModel):
    """Celery task status response."""

    task_id: str
    status: str
    result: dict | None = None

