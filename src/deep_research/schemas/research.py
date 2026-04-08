"""Domain schemas for research lifecycle."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from deep_research.config import DepthPreset


class ResearchCreate(BaseModel):
    query: str = Field(..., min_length=3, description="Research topic / question")
    depth: DepthPreset = DepthPreset.STANDARD
    interactive: bool = True


class ResearchSummary(BaseModel):
    id: uuid.UUID
    query: str
    status: str
    depth: str
    created_at: datetime
    completed_at: datetime | None = None
    total_cost_usd: Decimal = Decimal("0")


class ResearchDetail(BaseModel):
    id: uuid.UUID
    query: str
    status: str
    depth: str
    config_snapshot: dict[str, Any] | None = None
    artifacts_dir: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime
    total_tokens_input: int = 0
    total_tokens_output: int = 0
    total_cost_usd: Decimal = Decimal("0")
