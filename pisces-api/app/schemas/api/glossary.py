"""API schemas for Glossary endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class GlossaryEntryResponse(BaseModel):
    id: int
    novel_id: int
    source_term: str
    target_term: str
    category: str
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GlossaryEntryCreate(BaseModel):
    source_term: str = Field(max_length=200)
    target_term: str = Field(max_length=200)
    category: str = Field("", max_length=100)
    notes: str | None = None


class GlossaryEntryUpdate(BaseModel):
    target_term: str | None = Field(None, max_length=200)
    category: str | None = Field(None, max_length=100)
    notes: str | None = None
