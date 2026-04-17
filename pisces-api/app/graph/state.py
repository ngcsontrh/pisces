"""State schema for the LangGraph translation pipeline."""

from __future__ import annotations

from typing import Optional, TypedDict

from app.schemas.graph.names import NamesExtractionResult
from app.schemas.graph.review import ReviewResult
from app.schemas.graph.translate import TranslateResult


class ChapterState(TypedDict):
    """Shared state passed between all agent nodes in the pipeline."""

    chapter_path: str  # Absolute path to the raw chapter .txt file
    output_path: str  # Absolute path to write the final translated output

    chinese_text: str  # Raw Chinese text read from file
    names_result: Optional[NamesExtractionResult]  # Structured proper-name extraction
    translate_result: Optional[TranslateResult]  # Structured direct translation
    review_result: Optional[ReviewResult]  # Structured review with feedback
    final_text: str  # Final accepted translation text (from review agent)
    previous_summary: str  # Context summary imported from the previous chapter
    current_summary: str  # Context summary generated for this chapter

    retry_count: int  # Current number of retries
    max_retries: int  # Maximum allowed retries (default: 2)
