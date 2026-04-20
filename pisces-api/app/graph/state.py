"""State schema for the LangGraph translation pipeline."""

from __future__ import annotations

from typing import Optional, TypedDict

from app.schemas.graph.names import NamesExtractionResult
from app.schemas.graph.review import ReviewResult
from app.schemas.graph.translate import TranslateResult


class ChapterState(TypedDict):
    """Shared state passed between all agent nodes in the pipeline.

    File paths have been removed; the TranslationService owns persistence.
    DB identifiers (chapter_id, novel_id) are passed for traceability only —
    agents do NOT interact with the database directly.
    """

    # DB context (read-only within the graph)
    chapter_id: int  # FK to Chapter.id
    novel_id: int  # FK to Novel.id

    # Content
    chinese_text: str  # Raw source text (Chinese)
    glossary_text: str  # Pre-loaded novel glossary for extract_names agent

    # Agent outputs
    names_result: Optional[NamesExtractionResult]  # Proper-name extraction
    translate_result: Optional[TranslateResult]  # Direct translation
    review_result: Optional[ReviewResult]  # Review with feedback
    final_text: str  # Final accepted translation (set by review agent)

    # Inter-chapter memory
    previous_summary: str  # Summary from the preceding chapter
    current_summary: str  # Summary for this chapter (set by summarize agent)

    # Retry control
    retry_count: int  # Current retry iteration
    max_retries: int  # Maximum allowed retries (default: 2)
