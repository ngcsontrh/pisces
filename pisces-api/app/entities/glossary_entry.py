"""GlossaryEntry entity — per-novel translation dictionary."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.entities.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.entities.novel import Novel


class GlossaryEntry(Base, TimestampMixin):
    """A proper noun / terminology entry in a novel-specific glossary.

    Each novel maintains its own glossary — entries are NOT shared across novels.
    The unique constraint ``(novel_id, source_term)`` ensures one canonical
    translation per term per novel.
    """

    __tablename__ = "glossary_entries"
    __table_args__ = (
        UniqueConstraint("novel_id", "source_term", name="uq_glossary_novel_term"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    novel_id: Mapped[int] = mapped_column(
        ForeignKey("novels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Core translation pair
    source_term: Mapped[str] = mapped_column(String(200), nullable=False)
    target_term: Mapped[str] = mapped_column(String(200), nullable=False)

    # Classification
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="",
        comment="E.g. Nhân vật, Địa danh, Môn phái, Công pháp, Vũ khí, ...",
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship
    novel: Mapped[Novel] = relationship("Novel", back_populates="glossary_entries")

    def __repr__(self) -> str:
        return (
            f"<GlossaryEntry id={self.id} {self.source_term!r} → {self.target_term!r}>"
        )
