"""Writer subagent configuration."""

from __future__ import annotations

from typing import Any

from deep_research.agents.prompts.writer import WRITER_PROMPT
from deep_research.config import Settings


def create_writer_config(settings: Settings) -> dict[str, Any]:
    return {
        "name": "writer",
        "description": "Пишет итоговый отчёт в академическом стиле с инлайн-цитированием",
        "system_prompt": WRITER_PROMPT,
        "tools": [],
        "model": settings.writer_model or settings.default_model,
    }
