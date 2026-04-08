"""Orchestrator: assembles subagents and creates the main Deep Agent."""

from __future__ import annotations

import os
from typing import Any

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph

from deep_research.agents.prompts.orchestrator import ORCHESTRATOR_PROMPT
from deep_research.agents.subagents.analyst import create_analyst_config
from deep_research.agents.subagents.note_taker import create_note_taker_config
from deep_research.agents.subagents.planner import create_planner_config
from deep_research.agents.subagents.reviewer import create_reviewer_config
from deep_research.agents.subagents.searcher import create_searcher_config
from deep_research.agents.subagents.writer import create_writer_config
from deep_research.config import DepthConfig, DepthPreset, Settings
from deep_research.tools.arxiv_search import arxiv_search
from deep_research.tools.tavily_search import tavily_search
from deep_research.tools.web_scraper import web_scrape
from deep_research.tools.wikipedia_search import wikipedia_search


def _build_model(model_str: str, settings: Settings) -> BaseChatModel:
    """Create a LangChain chat model, applying base_url and disabling
    Responses API for local/custom OpenAI-compatible endpoints."""
    base_url = settings.openai_base_url or os.environ.get("OPENAI_BASE_URL")
    model_kwargs: dict[str, Any] = {}
    if model_str.startswith("openai:"):
        model_kwargs["use_responses_api"] = False
        if base_url:
            model_kwargs["base_url"] = base_url
    return init_chat_model(model_str, **model_kwargs)


def _build_orchestrator_prompt(depth: DepthPreset) -> str:
    limits = DepthConfig.get(depth)
    return (
        ORCHESTRATOR_PROMPT
        + f"\n## Ограничения текущего исследования\n"
        f"- Максимум источников: {limits['max_sources']}\n"
        f"- Максимум подтем: {limits['max_subtopics']}\n"
        f"- Пресет глубины: {depth.value}\n"
    )


def create_orchestrator(
    research_dir: str,
    settings: Settings,
    depth: DepthPreset,
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> CompiledStateGraph[Any]:
    """Build and return the main orchestrator Deep Agent."""
    model = _build_model(settings.default_model, settings)

    subagents: list[dict[str, Any]] = [
        create_planner_config(settings, depth),
        create_searcher_config(settings),
        create_note_taker_config(settings),
        create_analyst_config(settings),
        create_writer_config(settings),
        create_reviewer_config(settings),
    ]

    for sa in subagents:
        sa_model = sa.get("model")
        if isinstance(sa_model, str):
            sa["model"] = _build_model(sa_model, settings)

    kwargs: dict[str, Any] = {
        "model": model,
        "tools": [tavily_search, web_scrape, arxiv_search, wikipedia_search],
        "system_prompt": _build_orchestrator_prompt(depth),
        "subagents": subagents,
        "backend": FilesystemBackend(
            root_dir=research_dir,
            virtual_mode=False,
        ),
    }

    if checkpointer is not None:
        kwargs["checkpointer"] = checkpointer

    return create_deep_agent(**kwargs)
