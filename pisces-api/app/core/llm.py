"""Shared LangChain ChatOpenAI factory.

All agents should call ``get_llm()`` instead of constructing their own
``ChatOpenAI`` instances, centralising configuration in one place.
"""

from __future__ import annotations

import os

from langchain_openai import ChatOpenAI
from pydantic import SecretStr


def get_llm(
    model: str,
    temperature: float = 0.3,
    reasoning_effort: str = "high",
) -> ChatOpenAI:
    """Return a ``ChatOpenAI`` client configured for the given model.

    Args:
        model: Model name (e.g. ``"google/gemini-3.1-flash-lite-preview"``).
        temperature: Sampling temperature.
        reasoning_effort: Effort level for reasoning models (``"low"``/``"medium"``/``"high"``).
    """
    return ChatOpenAI(
        model=model,
        api_key=SecretStr(os.environ["OPENAI_API_KEY"]),
        base_url=os.environ["OPENAI_BASE_URL"],
        temperature=temperature,
        reasoning_effort=reasoning_effort,
    )
