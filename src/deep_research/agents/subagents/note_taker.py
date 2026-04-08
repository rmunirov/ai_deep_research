"""NoteTaker subagent configuration."""

from __future__ import annotations

from typing import Any

from deep_research.agents.prompts.note_taker import NOTE_TAKER_PROMPT
from deep_research.config import Settings


def create_note_taker_config(settings: Settings) -> dict[str, Any]:
    return {
        "name": "note_taker",
        "description": (
            "Извлекает ключевые факты из сырых данных и создаёт структурированные заметки"
        ),
        "system_prompt": NOTE_TAKER_PROMPT,
        "tools": [],
        "model": settings.note_taker_model or settings.default_model,
    }
