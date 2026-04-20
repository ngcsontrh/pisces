"""Routers package — collects all APIRouter instances."""

from app.routers.chapter_router import router as chapter_router
from app.routers.glossary_router import router as glossary_router
from app.routers.novel_router import router as novel_router
from app.routers.translation_router import router as translation_router

__all__ = ["novel_router", "chapter_router", "translation_router", "glossary_router"]
