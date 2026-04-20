"""TranslationJob entity — audit log for each translation attempt on a chapter."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.entities.base import Base

if TYPE_CHECKING:
    from app.entities.chapter import Chapter


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TranslationJob(Base):
    """Detailed record of a single translation run for a chapter.

    A chapter may have multiple jobs when ``retranslate`` is called.
    Each retry *within* a pipeline run (i.e. LangGraph retry loop) is
    captured via ``review_feedback`` / ``review_verdict`` on the same job;
    a **new job** is created only when the user explicitly requests
    re-translation from the API.
    """

    __tablename__ = "translation_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chapter_id: Mapped[int] = mapped_column(
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(nullable=False, default=1)

    # Lifecycle
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=JobStatus.PENDING,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Pipeline outputs
    translated_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_verdict: Mapped[str | None] = mapped_column(String(10), nullable=True)
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Error info
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship
    chapter: Mapped[Chapter] = relationship(
        "Chapter", back_populates="translation_jobs"
    )

    def __repr__(self) -> str:
        return (
            f"<TranslationJob id={self.id} chapter_id={self.chapter_id} "
            f"attempt={self.attempt_number} status={self.status!r}>"
        )
