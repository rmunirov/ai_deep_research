"""CLI command: research run — start a new research."""

from __future__ import annotations

import asyncio
import time

import typer
from rich.console import Console

from deep_research.config import DepthPreset

console = Console()


def run_command(
    query: str = typer.Argument(..., help="Тема исследования"),
    depth: str = typer.Option("standard", "--depth", "-d", help="quick / standard / deep"),
    no_interact: bool = typer.Option(False, "--no-interact", help="Отключить интерактивный режим"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Подробный вывод"),
) -> None:
    """Запустить новое исследование по заданной теме."""
    from deep_research.cli.ui.progress import ResearchProgress
    from deep_research.schemas.research import ResearchCreate
    from deep_research.services.research_service import ResearchService

    try:
        depth_preset = DepthPreset(depth)
    except ValueError:
        console.print(f"[red]Неизвестная глубина: {depth}. Используйте quick/standard/deep.[/red]")
        raise typer.Exit(code=1) from None

    request = ResearchCreate(
        query=query,
        depth=depth_preset,
        interactive=not no_interact,
    )

    progress = ResearchProgress(console)
    progress.show_header("...", query, depth)

    service = ResearchService()
    start_time = time.time()

    try:
        with progress.start():
            result = asyncio.run(
                service.start_research(request, on_stage=progress.update_stage)
            )
    except KeyboardInterrupt:
        progress.show_error("Прервано пользователем")
        raise typer.Exit(code=130) from None
    except Exception as exc:
        progress.show_error(str(exc))
        raise typer.Exit(code=1) from None

    elapsed = time.time() - start_time
    progress.show_completion(
        report_path=f"{result.artifacts_dir}/report.md",
        artifacts_dir=result.artifacts_dir or "",
        cost_usd=float(result.total_cost_usd),
        tokens_in=result.total_tokens_input,
        tokens_out=result.total_tokens_output,
        elapsed=elapsed,
    )
