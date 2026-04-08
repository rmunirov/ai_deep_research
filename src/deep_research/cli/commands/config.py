"""CLI command: research config — view and modify configuration."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from deep_research.config import get_settings

console = Console()

config_app = typer.Typer(help="Управление конфигурацией")


@config_app.callback(invoke_without_command=True)
def config_show(ctx: typer.Context) -> None:
    """Показать текущую конфигурацию."""
    if ctx.invoked_subcommand is not None:
        return

    settings = get_settings()
    table = Table(title="Конфигурация", show_lines=True)
    table.add_column("Параметр", style="cyan")
    table.add_column("Значение", style="white")

    table.add_row("default_model", settings.default_model)
    table.add_row("language", settings.language)
    table.add_row("researches_dir", str(settings.researches_dir))
    table.add_row("database_url", settings.database_url.split("@")[-1])
    table.add_row("api_host", settings.api_host)
    table.add_row("api_port", str(settings.api_port))
    table.add_row("max_search_results", str(settings.max_search_results))
    has_key = bool(settings.tavily_api_key.get_secret_value())
    table.add_row("tavily_api_key", "***" if has_key else "[dim]не задан[/dim]")

    console.print(table)


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Название параметра"),
    value: str = typer.Argument(..., help="Новое значение"),
) -> None:
    """Установить параметр конфигурации (в текущей сессии)."""
    settings = get_settings()
    if not hasattr(settings, key):
        console.print(f"[red]Неизвестный параметр: {key}[/red]")
        raise typer.Exit(code=1)

    try:
        current = getattr(settings, key)
        if isinstance(current, int):
            setattr(settings, key, int(value))
        else:
            setattr(settings, key, value)
        console.print(f"[green]{key} = {value}[/green]")
    except Exception as exc:
        console.print(f"[red]Ошибка: {exc}[/red]")
        raise typer.Exit(code=1) from None
