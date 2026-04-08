"""LangChain callback handler for tracking LLM token usage and costs."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

# Rough $/1K token estimates (input/output) for common models
_COST_TABLE: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-6": (0.003, 0.015),
    "claude-sonnet-4-20250514": (0.003, 0.015),
    "gpt-5.2": (0.005, 0.015),
    "gpt-4o": (0.0025, 0.01),
    "gpt-5": (0.005, 0.015),
}


class CostTrackerCallback(BaseCallbackHandler):
    """Collects token usage per LLM call. Records are flushed to DB by the service layer."""

    def __init__(self, research_id: uuid.UUID) -> None:
        super().__init__()
        self.research_id = research_id
        self.records: list[dict[str, Any]] = []

    @staticmethod
    def estimate_cost(model: str, tokens_in: int, tokens_out: int) -> Decimal:
        for key, (cost_in, cost_out) in _COST_TABLE.items():
            if key in model:
                return Decimal(str(tokens_in * cost_in / 1000 + tokens_out * cost_out / 1000))
        return Decimal("0")

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        usage = (response.llm_output or {}).get("token_usage", {})
        tokens_in = usage.get("prompt_tokens", 0) or 0
        tokens_out = usage.get("completion_tokens", 0) or 0

        model = (response.llm_output or {}).get("model_name", "unknown")
        tags = kwargs.get("tags", ["orchestrator"])
        agent_name = tags[0] if tags else "orchestrator"

        self.records.append(
            {
                "research_id": self.research_id,
                "agent_name": agent_name,
                "model": model,
                "tokens_input": tokens_in,
                "tokens_output": tokens_out,
                "estimated_cost_usd": self.estimate_cost(model, tokens_in, tokens_out),
            }
        )

    @property
    def total_tokens_input(self) -> int:
        return sum(r["tokens_input"] for r in self.records)

    @property
    def total_tokens_output(self) -> int:
        return sum(r["tokens_output"] for r in self.records)

    @property
    def total_cost_usd(self) -> Decimal:
        return sum((r["estimated_cost_usd"] for r in self.records), Decimal("0"))
