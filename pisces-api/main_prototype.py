"""Main entry point: processes all raw chapters through the multi-agent pipeline."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from app.core.logging import setup_logging  # noqa: E402 — must follow load_dotenv
from app.graph.pipeline import build_graph  # noqa: E402

setup_logging()

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).parent
_RAW_DIR = _ROOT / "raws_chapters"
_OUT_DIR = _ROOT / "translated_chapters"
_MAX_RETRIES = 2


async def process_chapter(graph, chapter_path: Path, previous_summary: str) -> str:
    output_path = _OUT_DIR / chapter_path.name

    logger.info("=" * 60)
    logger.info("Processing: %s", chapter_path.name)
    logger.info("=" * 60)

    chinese_text = chapter_path.read_text(encoding="utf-8")

    initial_state = {
        "chapter_path": str(chapter_path),
        "output_path": str(output_path),
        "chinese_text": chinese_text,
        "names_result": None,
        "review_result": None,
        "final_text": "",
        "previous_summary": previous_summary,
        "current_summary": "",
        "retry_count": 0,
        "max_retries": _MAX_RETRIES,
    }

    final_state = await graph.ainvoke(initial_state)

    verdict = final_state.get("review_result")
    verdict_str = verdict.verdict if verdict else "N/A"
    retries = final_state.get("retry_count", 0)
    logger.info(
        "✓ Done — Final verdict: %s | Retries used: %d/%d",
        verdict_str,
        retries,
        _MAX_RETRIES,
    )
    logger.info("  Output: %s", output_path)

    return final_state.get("current_summary", "")


async def main() -> None:
    chapters = sorted(_RAW_DIR.glob("*.txt"))

    if not chapters:
        logger.warning("No .txt files found in %s", _RAW_DIR)
        return

    logger.info("Found %d chapter(s) to process.", len(chapters))
    logger.info("Output directory: %s", _OUT_DIR)

    graph = build_graph()

    previous_summary = ""

    for chapter_path in chapters:
        try:
            previous_summary = await process_chapter(
                graph, chapter_path, previous_summary
            )
        except Exception as exc:
            logger.exception("Failed to process %s: %s", chapter_path.name, exc)
            raise

    logger.info("=" * 60)
    logger.info("All %d chapter(s) processed.", len(chapters))
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
