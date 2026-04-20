"""API schemas package."""

from app.schemas.api.chapter import ChapterListItem, ChapterResponse, ChapterUpdate
from app.schemas.api.glossary import (
    GlossaryEntryCreate,
    GlossaryEntryResponse,
    GlossaryEntryUpdate,
)
from app.schemas.api.novel import NovelResponse, NovelStats, NovelUpdate, NovelWithStats
from app.schemas.api.translation import (
    ChapterProgress,
    TranslateRequest,
    TranslationProgress,
)

__all__ = [
    "NovelResponse",
    "NovelUpdate",
    "NovelStats",
    "NovelWithStats",
    "ChapterResponse",
    "ChapterListItem",
    "ChapterUpdate",
    "TranslateRequest",
    "TranslationProgress",
    "ChapterProgress",
    "GlossaryEntryCreate",
    "GlossaryEntryUpdate",
    "GlossaryEntryResponse",
]
