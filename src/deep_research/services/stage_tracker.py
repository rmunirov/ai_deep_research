"""LangChain callback that maps tool calls to research stages."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler

logger = logging.getLogger(__name__)

SUBAGENT_TO_STAGE: dict[str, int] = {
    "planner": 0,
    "searcher": 1,
    "note_taker": 2,
    "analyst": 3,
    "writer": 4,
    "reviewer": 4,
}

SEARCH_TOOLS = {"tavily_search", "web_scrape", "arxiv_search", "wikipedia_search"}

StageCallback = Callable[[int, float], None]
"""Signature: (stage_index, completed_pct) → None."""


class StageTrackerCallback(BaseCallbackHandler):
    """Tracks research stage transitions by intercepting tool calls.

    Heuristics:
    - ``task`` tool with a known ``subagent_type`` → corresponding stage.
    - Direct search-tool calls → stage 1 (search).
    - ``write_file`` with ``plan`` in path → stage 0 done.
    - ``write_file`` with ``notes/`` in path → stage 2 done.
    - ``write_file`` with ``report`` in path → stage 4 done.
    """

    def __init__(self, on_stage: StageCallback) -> None:
        super().__init__()
        self._on_stage = on_stage
        self._completed: set[int] = set()
        self._current: int = -1

    def _advance_to(self, stage: int, pct: float = 50.0) -> None:
        """Mark all prior stages as 100% and set *stage* to *pct*."""
        for prev in range(stage):
            if prev not in self._completed:
                self._completed.add(prev)
                self._on_stage(prev, 100.0)
        if stage != self._current:
            self._current = stage
            self._on_stage(stage, pct)

    def _complete(self, stage: int) -> None:
        if stage not in self._completed:
            self._completed.add(stage)
            self._on_stage(stage, 100.0)

    def _parse_task_subagent(self, input_str: str, kwargs: dict[str, Any]) -> str | None:
        inputs: dict[str, Any] | None = kwargs.get("inputs")
        if isinstance(inputs, dict):
            val = inputs.get("subagent_type")
            if isinstance(val, str):
                return val
        try:
            data = json.loads(input_str)
            if isinstance(data, dict):
                return data.get("subagent_type")  # type: ignore[return-value]
        except (json.JSONDecodeError, TypeError):
            pass
        return None

    # -- LangChain callback hooks ------------------------------------------

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        tool_name: str = serialized.get("name", "")

        if tool_name == "task":
            subagent = self._parse_task_subagent(input_str, kwargs)
            if subagent and subagent in SUBAGENT_TO_STAGE:
                self._advance_to(SUBAGENT_TO_STAGE[subagent])
            return

        if tool_name in SEARCH_TOOLS:
            self._advance_to(1)
            return

        if tool_name == "write_file":
            path = ""
            inputs: dict[str, Any] | None = kwargs.get("inputs")
            if isinstance(inputs, dict):
                path = inputs.get("file_path", "") or inputs.get("path", "")
            if not path:
                try:
                    data = json.loads(input_str)
                    if isinstance(data, dict):
                        path = data.get("file_path", "") or data.get("path", "")
                except (json.JSONDecodeError, TypeError):
                    pass
            path_lower = str(path).lower()
            if "plan" in path_lower:
                self._complete(0)
            elif "notes/" in path_lower or "notes\\" in path_lower:
                self._advance_to(2)
            elif "report" in path_lower:
                self._advance_to(4)

    def finish_all(self) -> None:
        """Mark all 5 stages as 100%."""
        for i in range(5):
            self._complete(i)
