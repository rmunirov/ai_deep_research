"""Searcher subagent configuration."""

from __future__ import annotations

from typing import Any

from deep_research.agents.prompts.searcher import SEARCHER_PROMPT
from deep_research.config import Settings
from deep_research.tools.arxiv_search import arxiv_search
from deep_research.tools.tavily_search import tavily_search
from deep_research.tools.web_scraper import web_scrape
from deep_research.tools.wikipedia_search import wikipedia_search


def create_searcher_config(settings: Settings) -> dict[str, Any]:
    return {
        "name": "searcher",
        "description": "Ищет информацию по заданным запросам через все доступные источники",
        "system_prompt": SEARCHER_PROMPT,
        "tools": [tavily_search, web_scrape, arxiv_search, wikipedia_search],
        "model": settings.searcher_model or settings.default_model,
    }
