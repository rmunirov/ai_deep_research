"""Application configuration with Pydantic Settings."""

from __future__ import annotations

import enum
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(override=False)


class DepthPreset(enum.StrEnum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class DepthConfig:
    """Lookup table for depth-related limits."""

    _TABLE: dict[DepthPreset, dict[str, int]] = {
        DepthPreset.QUICK: {"max_sources": 5, "max_subtopics": 2},
        DepthPreset.STANDARD: {"max_sources": 15, "max_subtopics": 5},
        DepthPreset.DEEP: {"max_sources": 30, "max_subtopics": 10},
    }

    @classmethod
    def get(cls, preset: DepthPreset) -> dict[str, int]:
        return dict(cls._TABLE[preset])


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # -- LLM --
    default_model: str = "anthropic:claude-sonnet-4-6"
    openai_base_url: str | None = None
    planner_model: str | None = None
    searcher_model: str | None = None
    note_taker_model: str | None = None
    analyst_model: str | None = None
    writer_model: str | None = None
    reviewer_model: str | None = None

    # -- Search --
    tavily_api_key: SecretStr = SecretStr("")
    max_search_results: int = 10

    # -- Database --
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/deep_research"

    # -- Paths --
    researches_dir: Path = Path("./researches")

    # -- Server --
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    # -- Language --
    language: str = "ru"

    # -- YAML overlay --
    config_path: Path | None = None

    @model_validator(mode="before")
    @classmethod
    def _load_yaml_overlay(cls, data: Any) -> Any:  # noqa: ANN401
        if not isinstance(data, dict):
            return data
        default_cfg = Path.home() / ".config" / "deep-research" / "config.yaml"
        cfg_path = data.get("config_path") or default_cfg
        cfg_path = Path(cfg_path)
        if cfg_path.is_file():
            with open(cfg_path, encoding="utf-8") as fh:
                yaml_data = yaml.safe_load(fh) or {}
            if isinstance(yaml_data, dict):
                for key, value in yaml_data.items():
                    data.setdefault(key, value)
        return data

    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace("+asyncpg", "")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
