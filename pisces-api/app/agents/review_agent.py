"""Review agent: uses LLM to review the edited translation with structured output."""

from __future__ import annotations

import logging
from typing import cast

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import get_llm
from app.core.prompts import build_names_text, load_prompt
from app.graph.state import ChapterState
from app.schemas.graph.review import ReviewResult, Verdict

logger = logging.getLogger(__name__)


async def review_agent(state: ChapterState) -> dict:
    """Node 4: Review the edited translation; returns structured ReviewResult."""
    prompt = load_prompt("review")

    translate_result = state.get("translate_result")
    translated_text = translate_result.translated_text if translate_result else ""

    names_text = build_names_text(state.get("names_result"))

    user_text = (
        prompt["user"]
        .replace("{{chinese_text}}", state["chinese_text"])
        .replace("{{translated_text}}", translated_text)
    )

    system_text = prompt["system"].replace("{{names_dict}}", names_text)

    retry = state.get("retry_count", 0)
    logger.info("Running review (attempt %d)...", retry + 1)

    llm = get_llm(model=prompt["model"], temperature=0.1)
    structured_llm = llm.with_structured_output(ReviewResult, method="json_schema")

    try:
        result = cast(
            ReviewResult | None,
            await structured_llm.ainvoke(
                [
                    SystemMessage(content=system_text),
                    HumanMessage(content=user_text),
                ]
            ),
        )
        if result is None:
            raise RuntimeError(
                "[review_agent] LLM returned unparseable response (result=None)"
            )
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"[review_agent] LLM call failed: {exc}") from exc

    logger.info("Verdict: %s", result.verdict)
    if result.verdict == Verdict.FAIL:
        failed = [c for c in result.criteria if not c.passed]
        for c in failed:
            logger.warning("  ✗ [%s] %s", c.criterion, c.message)

    return {
        "review_result": result,
        "final_text": result.final_text,
    }
