"""Domain schemas for research notes with YAML frontmatter."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class NoteFrontmatter(BaseModel):
    title: str
    source_url: str
    source_title: str
    source_type: str = Field(description="web | arxiv | wikipedia")
    relevance: float = Field(ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    subtopic: str


class NoteContent(BaseModel):
    frontmatter: NoteFrontmatter
    body: str = Field(description="Markdown body after frontmatter")

    def to_markdown(self) -> str:
        import yaml

        fm = self.frontmatter.model_dump(mode="json")
        yaml_str = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
        return f"---\n{yaml_str}---\n\n{self.body}"
