"""API schemas for Chapter endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ChapterResponse(BaseModel):
    """Response schema for a single chapter."""

    id: int
    novel_id: int
    chapter_number: int
    title: str
    original_content: str
    translated_content: str | None
    summary: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChapterListItem(BaseModel):
    """Lightweight chapter info for list endpoints (no content)."""

    id: int
    novel_id: int
    chapter_number: int
    title: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChapterUpdate(BaseModel):
    """Request body for editing a chapter."""

    title: str | None = Field(None, max_length=500)
    translated_content: str | None = None
