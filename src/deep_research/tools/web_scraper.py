"""Web page scraper: httpx + BeautifulSoup readability extraction."""

from __future__ import annotations

import re
from typing import Any

import httpx
from bs4 import BeautifulSoup
from langchain.tools import tool

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
}

_STRIP_TAGS = {"script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"}


def _extract_main_content(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(_STRIP_TAGS):
        tag.decompose()

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    main = soup.find("main") or soup.find("article") or soup.find("body")
    if main is None:
        return {"title": title, "content": "", "error": "No content found"}

    text = main.get_text(separator="\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return {"title": title, "content": text[:15_000]}


@tool
def web_scrape(url: str) -> dict[str, Any]:
    """Fetch and extract main text content from a web page.

    Args:
        url: Full URL of the page to scrape.

    Returns:
        Dict with 'title', 'content' (plain text), and 'url'.
    """
    last_error = ""
    for attempt in range(3):
        try:
            with httpx.Client(headers=_HEADERS, timeout=15, follow_redirects=True) as client:
                resp = client.get(url)
                resp.raise_for_status()
            result = _extract_main_content(resp.text)
            result["url"] = url
            return result
        except httpx.HTTPError as exc:
            last_error = f"Attempt {attempt + 1}: {exc}"

    return {"url": url, "title": "", "content": "", "error": last_error}
