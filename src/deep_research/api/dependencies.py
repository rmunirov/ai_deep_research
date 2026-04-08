"""FastAPI dependency injection providers."""

from __future__ import annotations

from functools import lru_cache

from deep_research.config import Settings, get_settings
from deep_research.services.event_emitter import EventEmitter, get_event_emitter
from deep_research.services.research_service import ResearchService


def get_settings_dep() -> Settings:
    return get_settings()


@lru_cache(maxsize=1)
def get_research_service() -> ResearchService:
    return ResearchService()


def get_emitter_dep() -> EventEmitter:
    return get_event_emitter()
