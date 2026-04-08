"""Rich table formatters for CLI output."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from deep_research.schemas.research import ResearchDetail, ResearchSummary


def print_research_list(items: list[ResearchSummary], console: Console | None = None) -> None:
    console = console or Console()
    table = Table(title="Исследования", show_lines=True)
    table.add_column("ID", style="cyan", width=10)
    table.add_column("Запрос", style="white", max_width=40)
    table.add_column("Статус", style="bold")
    table.add_column("Глубина")
    table.add_column("Дата", style="dim")
    table.add_column("Стоимость", justify="right")

    status_colors = {
        "completed": "green",
        "failed": "red",
        "cancelled": "yellow",
        "pending": "dim",
    }

    for item in items:
        color = status_colors.get(item.status, "blue")
        table.add_row(
            str(item.id)[:8],
            item.query[:40],
            f"[{color}]{item.status}[/{color}]",
            item.depth,
            item.created_at.strftime("%Y-%m-%d %H:%M"),
            f"${item.total_cost_usd:.4f}",
        )

    console.print(table)


def print_research_detail(detail: ResearchDetail, console: Console | None = None) -> None:
    console = console or Console()

    status_colors = {
        "completed": "green",
        "failed": "red",
        "cancelled": "yellow",
    }
    color = status_colors.get(detail.status, "blue")

    lines = [
        f"[bold]ID:[/bold] {detail.id}",
        f"[bold]Запрос:[/bold] {detail.query}",
        f"[bold]Статус:[/bold] [{color}]{detail.status}[/{color}]",
        f"[bold]Глубина:[/bold] {detail.depth}",
        f"[bold]Артефакты:[/bold] {detail.artifacts_dir or 'N/A'}",
        f"[bold]Создано:[/bold] {detail.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
    ]
    if detail.started_at:
        lines.append(f"[bold]Начато:[/bold] {detail.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
    if detail.completed_at:
        lines.append(
            f"[bold]Завершено:[/bold] {detail.completed_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )
    if detail.error:
        lines.append(f"[bold red]Ошибка:[/bold red] {detail.error}")

    lines.append("")
    lines.append(
        f"[bold]Токены:[/bold] {detail.total_tokens_input:,} in / "
        f"{detail.total_tokens_output:,} out"
    )
    lines.append(f"[bold]Стоимость:[/bold] ${detail.total_cost_usd:.4f}")

    console.print(Panel("\n".join(lines), title="Исследование", border_style="cyan"))
