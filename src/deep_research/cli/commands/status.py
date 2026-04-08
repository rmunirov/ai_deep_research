"""CLI command: research status — show research details."""

from __future__ import annotations

import asyncio
import uuid

import typer
from rich.console import Console

console = Console()


def status_command(
    research_id: str = typer.Argument(..., help="ID исследования"),
) -> None:
    """Показать статус конкретного исследования."""
    from deep_research.cli.ui.tables import print_research_detail
    from deep_research.services.research_service import ResearchService

    try:
        rid = uuid.UUID(research_id)
    except ValueError:
        console.print(f"[red]Неверный формат ID: {research_id}[/red]")
        raise typer.Exit(code=1) from None

    service = ResearchService()
    try:
        detail = asyncio.run(service.get_detail(rid))
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from None

    print_research_detail(detail, console)
