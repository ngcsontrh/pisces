"""Shared prompt utilities used across multiple agents."""

from __future__ import annotations

from pathlib import Path

import yaml

from app.schemas.graph.names import NamesExtractionResult

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def load_prompt(prompt_name: str) -> dict:
    """Load and parse a YAML prompt file by name (without extension).

    Example::

        prompt = load_prompt("translate_vietnamese")
    """
    path = _PROMPTS_DIR / f"{prompt_name}.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_names_text(names_result: NamesExtractionResult | None) -> str:
    """Format extracted proper names as a readable list for LLM prompts.

    Returns a Vietnamese-language fallback message when ``names_result`` is
    ``None`` or contains no names.
    """
    if not names_result or not names_result.names:
        return "Không có tên riêng đặc biệt trong đoạn này."
    lines = [f"- [{n.category}] {n.chinese} → {n.unified}" for n in names_result.names]
    return "\n".join(lines)
