"""Domain schemas for research lifecycle events (SSE / DB)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ResearchEvent(BaseModel):
    research_id: uuid.UUID
    event_type: str
    agent_name: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)


class StageStartEvent(ResearchEvent):
    event_type: str = "stage_start"
    stage: str = ""
    stage_index: int = 0
    total_stages: int = 5


class StageEndEvent(ResearchEvent):
    event_type: str = "stage_end"
    stage: str = ""
    stage_index: int = 0


class SourceFoundEvent(ResearchEvent):
    event_type: str = "source_found"
    url: str = ""
    title: str = ""
    source_type: str = ""


class NoteCreatedEvent(ResearchEvent):
    event_type: str = "note_created"
    note_path: str = ""
    subtopic: str = ""


class ErrorEvent(ResearchEvent):
    event_type: str = "error"
    message: str = ""
    recoverable: bool = True


class CompletionEvent(ResearchEvent):
    event_type: str = "completed"
    report_path: str = ""
    total_sources: int = 0
    elapsed_seconds: float = 0.0
