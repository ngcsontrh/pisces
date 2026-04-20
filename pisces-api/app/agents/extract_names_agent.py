"""Extract names agent: uses LLM to extract proper nouns from the chapter."""

from __future__ import annotations

import logging
from typing import cast

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import get_llm
from app.core.prompts import load_prompt
from app.graph.state import ChapterState
from app.schemas.graph.names import NamesExtractionResult

logger = logging.getLogger(__name__)


async def extract_names_agent(state: ChapterState) -> dict:
    """Node: Call LLM to extract and unify proper names from the chapter.

    The glossary is pre-loaded by ``TranslationService`` and injected into
    ``state["glossary_text"]`` — agents never touch the database directly.
    """
    glossary_text = state.get("glossary_text", "").strip()

    prompt = load_prompt("extract_names")

    user_text = (
        prompt["user"]
        .replace("{{chinese_text}}", state["chinese_text"])
        .replace("{{glossary}}", glossary_text)
    )

    llm = get_llm(model=prompt["model"], temperature=0.2)
    structured_llm = llm.with_structured_output(
        NamesExtractionResult, method="json_schema"
    )

    try:
        result = cast(
            NamesExtractionResult,
            await structured_llm.ainvoke(
                [
                    SystemMessage(content=prompt["system"]),
                    HumanMessage(content=user_text),
                ]
            ),
        )
    except Exception as exc:
        raise RuntimeError(f"[extract_names_agent] LLM call failed: {exc}") from exc

    logger.info("Found %d proper names.", len(result.names))
    for name in result.names:
        logger.debug("  [%s] %s → %s", name.category, name.chinese, name.unified)

    return {"names_result": result}
