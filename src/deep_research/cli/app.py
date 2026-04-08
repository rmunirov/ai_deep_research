"""Main Typer CLI application with all subcommands."""

from __future__ import annotations

import typer

from deep_research.cli.commands.config import config_app
from deep_research.cli.commands.export import export_command
from deep_research.cli.commands.list import list_command
from deep_research.cli.commands.resume import resume_command
from deep_research.cli.commands.run import run_command
from deep_research.cli.commands.serve import serve_command
from deep_research.cli.commands.status import status_command

app = typer.Typer(
    name="research",
    help="Deep Research Agent — AI-агент для многошагового исследования тем.",
    no_args_is_help=True,
)

app.command("run", help="Запустить новое исследование")(run_command)
app.command("list", help="Список исследований")(list_command)
app.command("status", help="Статус исследования")(status_command)
app.command("resume", help="Возобновить исследование")(resume_command)
app.command("export", help="Экспорт отчёта")(export_command)
app.command("serve", help="Запуск API сервера")(serve_command)
app.add_typer(config_app, name="config")


if __name__ == "__main__":
    app()
