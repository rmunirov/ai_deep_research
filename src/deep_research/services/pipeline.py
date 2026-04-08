"""Deterministic research pipeline that does not rely on autonomous tool calling.

Each stage is a focused LLM call with explicit inputs/outputs.
Works reliably with any model that can produce text.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from tavily import TavilyClient

from deep_research.config import DepthConfig, DepthPreset, Settings
from deep_research.services.stage_tracker import StageCallback

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    plan: str = ""
    search_results: list[dict[str, Any]] = field(default_factory=list)
    notes: str = ""
    analysis: str = ""
    report: str = ""
    tokens_input: int = 0
    tokens_output: int = 0


def _build_model(settings: Settings) -> BaseChatModel:
    import os

    model_str = settings.default_model
    kwargs: dict[str, Any] = {}
    if model_str.startswith("openai:"):
        kwargs["use_responses_api"] = False
        base_url = settings.openai_base_url or os.environ.get("OPENAI_BASE_URL")
        if base_url:
            kwargs["base_url"] = base_url
    return init_chat_model(model_str, **kwargs)


def _call_llm(
    model: BaseChatModel,
    system: str,
    user: str,
    result: PipelineResult,
) -> str:
    response = model.invoke([
        SystemMessage(content=system),
        HumanMessage(content=user),
    ])
    usage = response.usage_metadata or {}
    result.tokens_input += usage.get("input_tokens", 0)
    result.tokens_output += usage.get("output_tokens", 0)
    content = response.content
    return content if isinstance(content, str) else str(content)


def _tavily_search(
    queries: list[str],
    settings: Settings,
    max_results_per_query: int = 5,
) -> list[dict[str, Any]]:
    import os

    api_key = settings.tavily_api_key.get_secret_value()
    if not api_key:
        api_key = os.environ.get("TAVILY_API_KEY", "")
    client = TavilyClient(api_key=api_key)
    all_results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for q in queries:
        try:
            resp = client.search(q, max_results=max_results_per_query)
            for r in resp.get("results", []):
                url = r.get("url", "")
                if url not in seen_urls:
                    seen_urls.add(url)
                    all_results.append(r)
        except Exception:
            logger.warning("Tavily search failed for query: %s", q, exc_info=True)
    return all_results


def _format_sources(results: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "Без названия")
        url = r.get("url", "")
        content = r.get("content", "")
        parts.append(f"### Источник {i}: {title}\nURL: {url}\n\n{content}\n")
    return "\n".join(parts)


def run_pipeline(
    query: str,
    artifacts_dir: str,
    settings: Settings,
    depth: DepthPreset,
    on_stage: StageCallback | None = None,
) -> PipelineResult:
    """Execute a deterministic research pipeline."""
    limits = DepthConfig.get(depth)
    max_sources = limits["max_sources"]
    max_subtopics = limits["max_subtopics"]
    model = _build_model(settings)
    result = PipelineResult()
    lang = settings.language or "ru"

    def _stage(idx: int, pct: float = 50.0) -> None:
        if on_stage:
            on_stage(idx, pct)

    def _complete(idx: int) -> None:
        if on_stage:
            on_stage(idx, 100.0)

    # ── Stage 0: Planning ─────────────────────────────────────────────
    _stage(0)
    plan_text = _call_llm(
        model,
        system=(
            f"Ты — исследовательский планировщик. Язык ответа: {lang}. "
            f"Разбей тему на {max_subtopics} подтем. "
            "Для каждой подтемы дай 2–3 поисковых запроса (на русском и английском). "
            "Ответ — только Markdown, без пояснений."
        ),
        user=f"Тема исследования: {query}",
        result=result,
    )
    result.plan = plan_text

    plan_path = Path(artifacts_dir) / "plan.md"
    plan_path.write_text(plan_text, encoding="utf-8")
    _complete(0)

    # Extract search queries from plan
    search_queries = _extract_queries(plan_text, query)

    # ── Stage 1: Search ───────────────────────────────────────────────
    _stage(1)
    search_results = _tavily_search(
        search_queries,
        settings,
        max_results_per_query=max(1, max_sources // max(len(search_queries), 1)),
    )
    result.search_results = search_results[:max_sources]
    sources_text = _format_sources(result.search_results)
    _complete(1)

    # ── Stage 2: Notes ────────────────────────────────────────────────
    _stage(2)
    notes_text = _call_llm(
        model,
        system=(
            f"Ты — исследователь-аналитик. Язык ответа: {lang}. "
            "Из предоставленных источников извлеки ключевые факты, "
            "данные и цитаты. Сгруппируй по подтемам. "
            "Для каждого факта указывай [Источник N](url). "
            "Ответ — только Markdown."
        ),
        user=f"Тема: {query}\n\nИсточники:\n\n{sources_text}",
        result=result,
    )
    result.notes = notes_text

    notes_path = Path(artifacts_dir) / "notes" / "01_notes.md"
    notes_path.write_text(notes_text, encoding="utf-8")
    _complete(2)

    # ── Stage 3: Analysis ─────────────────────────────────────────────
    _stage(3)
    analysis_text = _call_llm(
        model,
        system=(
            f"Ты — аналитик. Язык ответа: {lang}. "
            "Проанализируй заметки: найди паттерны, противоречия, "
            "ключевые выводы. Укажи, что хорошо освещено, а где пробелы. "
            "Ответ — Markdown."
        ),
        user=f"Тема: {query}\n\nЗаметки:\n\n{notes_text}",
        result=result,
    )
    result.analysis = analysis_text
    _complete(3)

    # ── Stage 4: Report writing ───────────────────────────────────────
    _stage(4)
    source_refs = _build_source_references(result.search_results)
    report_text = _call_llm(
        model,
        system=(
            f"Ты — автор исследовательского отчёта. Язык ответа: {lang}. "
            "Напиши структурированный отчёт в академическом стиле. "
            "Структура: Введение → разделы по подтемам → Выводы → Источники. "
            "Каждое утверждение подкрепляй инлайн-ссылкой [текст](url). "
            "В конце — нумерованный список всех источников. "
            "Ответ — только Markdown."
        ),
        user=(
            f"Тема: {query}\n\n"
            f"Анализ:\n{analysis_text}\n\n"
            f"Заметки:\n{notes_text}\n\n"
            f"Доступные источники:\n{source_refs}"
        ),
        result=result,
    )
    result.report = report_text

    report_path = Path(artifacts_dir) / "report.md"
    report_path.write_text(report_text, encoding="utf-8")
    _complete(4)

    return result


def _extract_queries(plan_text: str, fallback_query: str) -> list[str]:
    """Pull quoted search queries from the plan markdown."""
    queries: list[str] = []
    for line in plan_text.splitlines():
        line = line.strip()
        if not line:
            continue
        for delim in ['"', '\u201c', '\u201e', '\u00ab']:
            if delim in line:
                parts = line.split(delim)
                for i in range(1, len(parts), 2):
                    q = parts[i].strip().rstrip('"\u201d\u201c\u00bb')
                    if len(q) > 5:
                        queries.append(q)
    if not queries:
        queries = [fallback_query, f"{fallback_query} overview", f"{fallback_query} tutorial"]
    return queries[:10]


def _build_source_references(results: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "")
        url = r.get("url", "")
        parts.append(f"{i}. [{title}]({url})")
    return "\n".join(parts)
