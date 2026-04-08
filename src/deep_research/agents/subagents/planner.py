"""Planner subagent configuration."""

from __future__ import annotations

from typing import Any

from deep_research.agents.prompts.planner import PLANNER_PROMPT
from deep_research.config import DepthConfig, DepthPreset, Settings


def create_planner_config(settings: Settings, depth: DepthPreset) -> dict[str, Any]:
    limits = DepthConfig.get(depth)
    prompt = PLANNER_PROMPT.replace("{max_subtopics}", str(limits["max_subtopics"]))
    return {
        "name": "planner",
        "description": "Декомпозирует тему на подтемы и формулирует поисковые запросы",
        "system_prompt": prompt,
        "tools": [],
        "model": settings.planner_model or settings.default_model,
    }
