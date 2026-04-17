"""LangGraph pipeline: wires all agents into a stateful graph with retry logic."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from langgraph.graph import END, START, StateGraph

from app.agents.extract_names_agent import extract_names_agent
from app.agents.review_agent import review_agent
from app.agents.summarize_agent import summarize_agent
from app.agents.translate_agent import translate_agent
from app.graph.state import ChapterState
from app.schemas.graph.review import Verdict

logger = logging.getLogger(__name__)


async def save_node(state: ChapterState) -> dict:
    """Write the final translation to the output file."""
    output_path = Path(state["output_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    await asyncio.to_thread(
        output_path.write_text, state["final_text"], encoding="utf-8"
    )
    logger.info("Saved → %s", output_path)
    return {}


def _route_after_review(state: ChapterState) -> str:
    """Decide: retry edit or save."""
    review_result = state.get("review_result")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)

    if review_result is None or review_result.verdict == Verdict.PASS:
        return "save"
    if retry_count >= max_retries:
        logger.warning("Max retries (%d) reached — saving as-is.", max_retries)
        return "save"
    return "retry"


def _increment_retry(state: ChapterState) -> dict:
    """Increment retry counter before looping back to translate_agent."""
    return {"retry_count": state.get("retry_count", 0) + 1}


# noinspection PyTypeChecker
def build_graph() -> StateGraph:
    """Build and compile the multi-agent translation graph."""
    graph = StateGraph(ChapterState)

    graph.add_node("extract_names_agent", extract_names_agent)
    graph.add_node("translate_agent", translate_agent)
    graph.add_node("review_agent", review_agent)
    graph.add_node("increment_retry", _increment_retry)
    graph.add_node("save_node", save_node)
    graph.add_node("summarize_agent", summarize_agent)

    graph.add_edge(START, "extract_names_agent")
    graph.add_edge("extract_names_agent", "translate_agent")
    graph.add_edge("translate_agent", "review_agent")
    graph.add_conditional_edges(
        "review_agent",
        _route_after_review,
        {
            "save": "save_node",
            "retry": "increment_retry"
        },
    )
    graph.add_edge("increment_retry", "translate_agent")
    graph.add_edge("save_node", "summarize_agent")
    graph.add_edge("summarize_agent", END)

    return graph.compile()