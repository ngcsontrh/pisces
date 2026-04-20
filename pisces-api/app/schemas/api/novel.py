"""API schemas for Novel endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class NovelResponse(BaseModel):
    """Response schema for a novel resource."""

    id: int
    title: str
    author: str
    description: str
    cover_image_path: str | None
    source_language: str
    target_language: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NovelUpdate(BaseModel):
    """Request body for updating novel metadata."""

    title: str | None = Field(None, max_length=500)
    author: str | None = Field(None, max_length=300)
    description: str | None = None


class NovelStats(BaseModel):
    """Summary statistics for a novel's translation progress."""

    novel_id: int
    total_chapters: int
    translated: int
    pending: int
    translating: int
    failed: int

    @property
    def progress_pct(self) -> float:
        if self.total_chapters == 0:
            return 0.0
        return round(self.translated / self.total_chapters * 100, 1)


class NovelWithStats(NovelResponse):
    stats: NovelStats
