"""Novel entity — top-level metadata for an imported story."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.entities.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.entities.chapter import Chapter
    from app.entities.glossary_entry import GlossaryEntry


class Novel(Base, TimestampMixin):
    """Represents a single imported novel (EPUB source)."""

    __tablename__ = "novels"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    author: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    cover_image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_language: Mapped[str] = mapped_column(
        String(10), nullable=False, default="zh"
    )
    target_language: Mapped[str] = mapped_column(
        String(10), nullable=False, default="vi"
    )

    # Relationships
    chapters: Mapped[list[Chapter]] = relationship(
        "Chapter",
        back_populates="novel",
        cascade="all, delete-orphan",
        order_by="Chapter.chapter_number",
    )
    glossary_entries: Mapped[list[GlossaryEntry]] = relationship(
        "GlossaryEntry",
        back_populates="novel",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Novel id={self.id} title={self.title!r}>"
