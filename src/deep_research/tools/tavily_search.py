"""Tavily AI-optimized web search tool."""

from __future__ import annotations

import os
from typing import Any, Literal

from langchain.tools import tool
from tavily import TavilyClient

from deep_research.config import get_settings


def _get_client() -> TavilyClient:
    api_key = get_settings().tavily_api_key.get_secret_value()
    if not api_key:
        api_key = os.environ.get("TAVILY_API_KEY", "")
    return TavilyClient(api_key=api_key)


@tool
def tavily_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
) -> dict[str, Any]:
    """Search the web using Tavily AI-optimized search engine.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return (1-20).
        topic: Search topic category.
        include_raw_content: If True, include full page content.

    Returns:
        Dict with 'results' list containing url, title, content, score.
    """
    client = _get_client()
    return client.search(  # type: ignore[no-any-return]
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )
