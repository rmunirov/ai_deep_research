"""Analyst subagent configuration."""

from __future__ import annotations

from typing import Any

from deep_research.agents.prompts.analyst import ANALYST_PROMPT
from deep_research.config import Settings


def create_analyst_config(settings: Settings) -> dict[str, Any]:
    return {
        "name": "analyst",
        "description": "Синтезирует информацию из заметок, находит противоречия и паттерны",
        "system_prompt": ANALYST_PROMPT,
        "tools": [],
        "model": settings.analyst_model or settings.default_model,
    }
