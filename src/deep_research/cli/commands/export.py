"""CLI command: research export — export report to PDF/HTML."""

from __future__ import annotations

import asyncio
import uuid

import typer
from rich.console import Console

console = Console()


def export_command(
    research_id: str = typer.Argument(..., help="ID исследования"),
    fmt: str = typer.Option("html", "--format", "-f", help="Формат: html / pdf"),
) -> None:
    """Экспортировать отчёт в PDF или HTML."""
    from deep_research.services.research_service import ResearchService
    from deep_research.tools.export_tool import export_report

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

    if detail.artifacts_dir is None:
        console.print("[red]Каталог артефактов не найден.[/red]")
        raise typer.Exit(code=1)

    try:
        output_path = export_report(detail.artifacts_dir, fmt)
        console.print(f"[green]Экспортировано: {output_path}[/green]")
    except Exception as exc:
        console.print(f"[red]Ошибка экспорта: {exc}[/red]")
        raise typer.Exit(code=1) from None
