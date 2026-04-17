"""Pydantic schema for the review agent output."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Verdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class ReviewCriterion(BaseModel):
    """Result for a single review criterion."""

    criterion: str = Field(
        description=(
            "Tên tiêu chí: 'Sai nghĩa', 'Thiếu/Thừa nội dung', 'Edit quá tay', "
            "'Văn phong convert', 'Tên riêng thống nhất', 'Ngữ pháp tiếng Việt'"
        )
    )
    passed: bool = Field(description="True nếu tiêu chí ĐẠT, False nếu KHÔNG ĐẠT")
    message: str = Field(
        description=(
            "'OK' nếu đạt. Nếu không đạt: mô tả lỗi cụ thể theo format "
            "「đoạn lỗi」→ 「đề xuất sửa」(lý do). Liệt kê nhiều lỗi trên dòng riêng."
        )
    )


class ReviewResult(BaseModel):
    """Output of the review agent."""

    criteria: list[ReviewCriterion] = Field(
        description="Kết quả đánh giá 6 tiêu chí theo thứ tự."
    )
    verdict: Verdict = Field(
        description="PASS nếu tất cả 6 tiêu chí đều passed=true, ngược lại FAIL."
    )
    final_text: str = Field(
        description=(
            "Bản văn cuối cùng. Nếu tất cả ĐẠT: copy nguyên bản đã chỉnh sửa. "
            "Nếu có lỗi: bản đã sửa theo đúng các message lỗi."
        )
    )
    feedback_for_edit: str = Field(
        description=(
            "Tổng hợp các lỗi KHÔNG ĐẠT để truyền lại cho agent biên tập ở lần retry tiếp theo. "
            "Rỗng nếu verdict là PASS."
        )
    )
