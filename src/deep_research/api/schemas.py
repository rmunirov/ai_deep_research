"""API request/response Pydantic models (separate from domain schemas)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class ResearchCreateRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Тема исследования")
    depth: str = Field(default="standard", description="quick / standard / deep")
    interactive: bool = Field(default=True, description="Разрешить агенту задавать вопросы")


class ResearchResponse(BaseModel):
    id: uuid.UUID
    query: str
    status: str
    depth: str
    artifacts_dir: str | None = None
    config_snapshot: dict[str, Any] | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime
    total_tokens_input: int = 0
    total_tokens_output: int = 0
    total_cost_usd: Decimal = Decimal("0")


class ResearchListItem(BaseModel):
    id: uuid.UUID
    query: str
    status: str
    depth: str
    created_at: datetime
    completed_at: datetime | None = None
    total_cost_usd: Decimal = Decimal("0")


class ResearchListResponse(BaseModel):
    items: list[ResearchListItem]
    total: int


class ExportRequest(BaseModel):
    format: str = Field(default="html", description="html / pdf")


class ExportResponse(BaseModel):
    path: str
    format: str


class ConfigResponse(BaseModel):
    default_model: str
    language: str
    researches_dir: str
    api_host: str
    api_port: int
    max_search_results: int


class ConfigUpdateRequest(BaseModel):
    default_model: str | None = None
    language: str | None = None
    max_search_results: int | None = None
