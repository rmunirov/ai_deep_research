"""Wikipedia article search and extraction tool."""

from __future__ import annotations

from typing import Any

import wikipediaapi
from langchain.tools import tool


@tool
def wikipedia_search(query: str, lang: str = "ru") -> dict[str, Any]:
    """Search Wikipedia and return the article summary and sections.

    Args:
        query: Topic or article title to search for.
        lang: Wikipedia language edition (default: ru).

    Returns:
        Dict with title, summary, url, and sections list.
    """
    wiki = wikipediaapi.Wikipedia(
        user_agent="DeepResearchAgent/0.1 (research tool)",
        language=lang,
    )

    page = wiki.page(query)
    if not page.exists():
        wiki_en = wikipediaapi.Wikipedia(
            user_agent="DeepResearchAgent/0.1 (research tool)",
            language="en",
        )
        page = wiki_en.page(query)
        if not page.exists():
            return {"title": query, "summary": "", "url": "", "sections": [], "found": False}

    sections = []
    for section in page.sections:
        sections.append({"title": section.title, "text": section.text[:2000]})

    return {
        "title": page.title,
        "summary": page.summary[:3000],
        "url": page.fullurl,
        "sections": sections[:10],
        "found": True,
    }
