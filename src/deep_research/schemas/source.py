"""Domain schemas for source tracking."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Source(BaseModel):
    url: str
    title: str
    source_type: str = Field(description="web | arxiv | wikipedia")
    accessed_at: datetime
    relevance: float = Field(ge=0.0, le=1.0, default=0.5)
    snippet: str = ""


class SourceIndex(BaseModel):
    sources: list[Source] = Field(default_factory=list)

    def add(self, source: Source) -> None:
        if not any(s.url == source.url for s in self.sources):
            self.sources.append(source)
