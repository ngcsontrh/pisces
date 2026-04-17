"""Pydantic schema for the summarize agent output."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SummarizeResult(BaseModel):
    """Output of the summarize_agent."""

    summary: str = Field(
        description=(
            "Tóm tắt chi tiết gạch đầu dòng gạch theo các tiêu chí yêu cầu (nhân vật, bối cảnh, sự kiện, cliffhanger)."
        )
    )
