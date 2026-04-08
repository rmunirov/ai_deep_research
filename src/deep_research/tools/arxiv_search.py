"""ArXiv scientific paper search tool."""

from __future__ import annotations

from typing import Any

import arxiv
from langchain.tools import tool


@tool
def arxiv_search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Search ArXiv for scientific papers matching the query.

    Args:
        query: Search query for scientific papers.
        max_results: Maximum number of papers to return (1-20).

    Returns:
        List of dicts with title, authors, abstract, pdf_url, published.
    """
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    results: list[dict[str, Any]] = []
    for paper in client.results(search):
        results.append(
            {
                "title": paper.title,
                "authors": [a.name for a in paper.authors],
                "abstract": paper.summary,
                "pdf_url": paper.pdf_url,
                "published": paper.published.isoformat() if paper.published else None,
                "url": paper.entry_id,
            }
        )
    return results
