"""GlossaryRepository — async CRUD for per-novel GlossaryEntry."""

from __future__ import annotations

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.glossary_entry import GlossaryEntry


class GlossaryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entry_id: int) -> GlossaryEntry | None:
        result = await self._session.execute(
            select(GlossaryEntry).where(GlossaryEntry.id == entry_id)
        )
        return result.scalar_one_or_none()

    async def get_by_novel_id(self, novel_id: int) -> list[GlossaryEntry]:
        """Return all glossary entries for a novel ordered by category then source_term."""
        result = await self._session.execute(
            select(GlossaryEntry)
            .where(GlossaryEntry.novel_id == novel_id)
            .order_by(GlossaryEntry.category, GlossaryEntry.source_term)
        )
        return list(result.scalars().all())

    async def get_by_novel_and_term(
        self, novel_id: int, source_term: str
    ) -> GlossaryEntry | None:
        result = await self._session.execute(
            select(GlossaryEntry).where(
                and_(
                    GlossaryEntry.novel_id == novel_id,
                    GlossaryEntry.source_term == source_term,
                )
            )
        )
        return result.scalar_one_or_none()

    async def create(self, entry: GlossaryEntry) -> GlossaryEntry:
        self._session.add(entry)
        await self._session.flush()
        await self._session.refresh(entry)
        return entry

    async def update(self, entry: GlossaryEntry) -> GlossaryEntry:
        await self._session.flush()
        await self._session.refresh(entry)
        return entry

    async def delete(self, entry_id: int) -> bool:
        entry = await self.get_by_id(entry_id)
        if entry is None:
            return False
        await self._session.delete(entry)
        await self._session.flush()
        return True

    async def upsert(
        self,
        novel_id: int,
        source_term: str,
        target_term: str,
        category: str,
        notes: str | None = None,
    ) -> GlossaryEntry:
        """Insert or update a glossary entry.

        If a record with the same ``(novel_id, source_term)`` already exists,
        it is **not** overwritten — user-edited translations take precedence.
        Returns the existing or newly created entry.
        """
        existing = await self.get_by_novel_and_term(novel_id, source_term)
        if existing is not None:
            return existing  # preserve user edits

        new_entry = GlossaryEntry(
            novel_id=novel_id,
            source_term=source_term,
            target_term=target_term,
            category=category,
            notes=notes,
        )
        return await self.create(new_entry)

    async def bulk_upsert(
        self,
        novel_id: int,
        entries: list[dict],
    ) -> list[GlossaryEntry]:
        """Upsert multiple entries.  Each dict must have keys: source_term, target_term, category."""
        result = []
        for e in entries:
            entry = await self.upsert(
                novel_id=novel_id,
                source_term=e["source_term"],
                target_term=e["target_term"],
                category=e.get("category", ""),
                notes=e.get("notes"),
            )
            result.append(entry)
        return result

    async def get_source_terms(self, novel_id: int) -> set[str]:
        """Return all existing source_term values for a novel as a set."""
        result = await self._session.execute(
            select(GlossaryEntry.source_term).where(
                GlossaryEntry.novel_id == novel_id
            )
        )
        return set(result.scalars().all())

    async def bulk_insert_new(
        self,
        novel_id: int,
        entries: list[dict],
    ) -> list[GlossaryEntry]:
        """Insert only entries whose source_term does not exist yet.

        Each dict must have keys: source_term, target_term, category.
        """
        existing = await self.get_source_terms(novel_id)
        new_entries = [e for e in entries if e["source_term"] not in existing]
        if not new_entries:
            return []

        result = []
        for e in new_entries:
            entry = await self.create(
                GlossaryEntry(
                    novel_id=novel_id,
                    source_term=e["source_term"],
                    target_term=e["target_term"],
                    category=e.get("category", ""),
                    notes=e.get("notes"),
                )
            )
            result.append(entry)
        return result

    async def export_as_text(self, novel_id: int) -> str:
        """Format glossary as a plaintext string for use in LLM prompts."""
        entries = await self.get_by_novel_id(novel_id)
        if not entries:
            return "Không có tên riêng đặc biệt trong truyện này."
        lines = [f"- [{e.category}] {e.source_term} → {e.target_term}" for e in entries]
        return "\n".join(lines)
