"""Entities package — re-exports all ORM models for convenience."""

from app.entities.base import Base, TimestampMixin
from app.entities.chapter import Chapter, ChapterStatus
from app.entities.glossary_entry import GlossaryEntry
from app.entities.novel import Novel
from app.entities.translation_job import JobStatus, TranslationJob

__all__ = [
    "Base",
    "TimestampMixin",
    "Novel",
    "Chapter",
    "ChapterStatus",
    "GlossaryEntry",
    "TranslationJob",
    "JobStatus",
]
