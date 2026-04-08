"""Reviewer subagent configuration."""

from __future__ import annotations

from typing import Any

from deep_research.agents.prompts.reviewer import REVIEWER_PROMPT
from deep_research.config import Settings


def create_reviewer_config(settings: Settings) -> dict[str, Any]:
    return {
        "name": "reviewer",
        "description": "Проверяет качество отчёта, корректность цитирования и полноту",
        "system_prompt": REVIEWER_PROMPT,
        "tools": [],
        "model": settings.reviewer_model or settings.default_model,
    }
