"""Pydantic schema for the translate agent output."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TranslateResult(BaseModel):
    """Output of the translate_vietnamese agent."""

    translated_text: str = Field(
        description=(
            "Toàn bộ đoạn văn tiếng Việt đã được dịch. "
            "Chỉ chứa nội dung văn bản, không có giải thích hay ghi chú."
        )
    )
