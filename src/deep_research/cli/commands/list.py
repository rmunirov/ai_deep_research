"""CLI command: research list — list all researches."""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console

console = Console()


def list_command(
    status: str | None = typer.Option(None, "--status", "-s", help="Фильтр по статусу"),
    limit: int = typer.Option(50, "--limit", "-n", help="Максимум записей"),
) -> None:
    """Показать список исследований."""
    from deep_research.cli.ui.tables import print_research_list
    from deep_research.services.research_service import ResearchService

    service = ResearchService()
    items = asyncio.run(service.list_researches(status=status, limit=limit))

    if not items:
        console.print("[dim]Исследований пока нет.[/dim]")
        return

    print_research_list(items, console)
