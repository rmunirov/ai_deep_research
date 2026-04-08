"""CLI command: research resume — resume a failed/cancelled research."""

from __future__ import annotations

import asyncio
import uuid

import typer
from rich.console import Console

console = Console()


def resume_command(
    research_id: str = typer.Argument(..., help="ID исследования для возобновления"),
) -> None:
    """Возобновить прерванное исследование."""
    from deep_research.services.research_service import ResearchService

    try:
        rid = uuid.UUID(research_id)
    except ValueError:
        console.print(f"[red]Неверный формат ID: {research_id}[/red]")
        raise typer.Exit(code=1) from None

    service = ResearchService()
    try:
        result = asyncio.run(service.resume_research(rid))
        console.print(
            f"[green]Исследование {result.id} возобновлено. "
            f"Статус: {result.status}[/green]"
        )
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from None
