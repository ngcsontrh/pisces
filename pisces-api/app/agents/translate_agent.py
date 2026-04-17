"""Translate agent: uses LLM to directly translate Chinese text to Vietnamese, incorporating review feedback on retry."""

from __future__ import annotations

import logging
from typing import cast

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import get_llm
from app.core.prompts import build_names_text, load_prompt
from app.graph.state import ChapterState
from app.schemas.graph.translate import TranslateResult

logger = logging.getLogger(__name__)


async def translate_agent(state: ChapterState) -> dict:
    """Node: Call LLM to directly translate Chinese text to Vietnamese.

    On retry passes, ``review_result.feedback_for_edit`` contains specific errors
    flagged by the review agent, injected into the user prompt.
    """
    prompt = load_prompt("translate_vietnamese")

    review_result = state.get("review_result")
    feedback = review_result.feedback_for_edit.strip() if review_result else ""
    if feedback:
        feedback_section = (
            "**Feedback từ lần review trước (ưu tiên sửa những lỗi này):**\n" + feedback
        )
    else:
        feedback_section = ""

    previous_summary = state.get("previous_summary", "").strip()
    if previous_summary:
        context_section = "**Ngữ cảnh từ chương trước (để dịch mạch lạc, đúng nhân xưng):**\n" + previous_summary
    else:
        context_section = ""

    names_text = build_names_text(state.get("names_result"))

    user_text = (
        prompt["user"]
        .replace("{{chinese_text}}", state["chinese_text"])
        .replace("{{context_section}}", context_section)
        .replace("{{feedback_section}}", feedback_section)
    )

    system_text = prompt["system"].replace("{{names_dict}}", names_text)

    retry = state.get("retry_count", 0)
    logger.info("Context section: %s", context_section)
    logger.info("Feedback section: %s", feedback_section)
    logger.info("Running translate (attempt %d)...", retry + 1)

    llm = get_llm(model=prompt["model"], temperature=0.3)
    structured_llm = llm.with_structured_output(TranslateResult, method="json_schema")

    try:
        result = cast(
            TranslateResult,
            await structured_llm.ainvoke(
                [
                    SystemMessage(content=system_text),
                    HumanMessage(content=user_text),
                ]
            ),
        )
    except Exception as exc:
        raise RuntimeError(f"[translate_agent] LLM call failed: {exc}") from exc

    return {"translate_result": result}
