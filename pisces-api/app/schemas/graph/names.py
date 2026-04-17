"""Pydantic schema for the extract_names agent output."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProperName(BaseModel):
    """A single proper noun extracted from the chapter."""

    category: str = Field(
        description=(
            "Loại tên riêng: 'Nhân vật', 'Địa danh', 'Môn phái/Tổ chức', "
            "'Công pháp/Võ học', 'Vũ khí/Bảo vật', 'Đan dược/Linh vật', "
            "'Cảnh giới/Đẳng cấp', 'Chủng tộc/Linh thú', 'Sự kiện/Thời kỳ'"
        )
    )
    chinese: str = Field(description="Tên riêng bằng tiếng Trung. Ví dụ: 萧炎")
    unified: str = Field(
        description="Bản dịch Hán Việt (Sino-Vietnamese) thống nhất. Ví dụ: Tiêu Viêm"
    )


class NamesExtractionResult(BaseModel):
    """Output of the extract_names agent."""

    names: list[ProperName] = Field(
        description="Danh sách tất cả tên riêng tìm được. Trả về list rỗng nếu không có."
    )
