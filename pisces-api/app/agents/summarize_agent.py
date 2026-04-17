"""Summarize agent: uses LLM to summarize the final translated chapter for future context."""

from __future__ import annotations

import logging
from typing import cast

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import get_llm
from app.core.prompts import load_prompt
from app.graph.state import ChapterState
from app.schemas.graph.summarize import SummarizeResult

logger = logging.getLogger(__name__)


async def summarize_agent(state: ChapterState) -> dict:
    """Read the final translated text and extract context for the next chapter."""
    prompt = load_prompt("summarize_chapter")

    final_text = state.get("final_text", "")
    if not final_text:
        logger.warning("[summarize_agent] No final_text found in state to summarize.")
        return {"current_summary": ""}

    user_text = prompt["user"].replace("{{previous_chapter_text}}", final_text)

    logger.info("Running summarize_agent to generate chapter background context...")

    llm = get_llm(model=prompt["model"], temperature=0.3)
    structured_llm = llm.with_structured_output(SummarizeResult, method="json_schema")

    try:
        result = cast(
            SummarizeResult | None,
            await structured_llm.ainvoke(
                [
                    SystemMessage(content=prompt["system"]),
                    HumanMessage(content=user_text),
                ]
            ),
        )
        if result is None:
            raise RuntimeError(
                "[summarize_agent] LLM returned unparseable response (result=None)"
            )
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"[summarize_agent] LLM call failed: {exc}") from exc

    logger.info("Summarization complete.")

    return {
        "current_summary": result.summary,
    }
