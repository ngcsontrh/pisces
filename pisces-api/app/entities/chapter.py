"""Chapter entity — a single chapter belonging to a Novel."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.entities.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.entities.novel import Novel
    from app.entities.translation_job import TranslationJob


class ChapterStatus(str, Enum):
    PENDING = "pending"
    TRANSLATING = "translating"
    TRANSLATED = "translated"
    FAILED = "failed"


class Chapter(Base, TimestampMixin):
    """A single chapter extracted from an EPUB."""

    __tablename__ = "chapters"
    __table_args__ = (
        UniqueConstraint("novel_id", "chapter_number", name="uq_chapters_novel_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    novel_id: Mapped[int] = mapped_column(
        ForeignKey("novels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chapter_number: Mapped[int] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False, default="")

    # Content
    original_content: Mapped[str] = mapped_column(Text, nullable=False)
    translated_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # State machine
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ChapterStatus.PENDING,
    )

    # Relationships
    novel: Mapped[Novel] = relationship("Novel", back_populates="chapters")
    translation_jobs: Mapped[list[TranslationJob]] = relationship(
        "TranslationJob",
        back_populates="chapter",
        cascade="all, delete-orphan",
        order_by="TranslationJob.attempt_number",
    )

    def __repr__(self) -> str:
        return f"<Chapter id={self.id} novel_id={self.novel_id} ch={self.chapter_number} status={self.status!r}>"
