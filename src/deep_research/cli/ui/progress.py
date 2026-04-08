"""Rich progress bar for research stages."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)

STAGES = [
    "Планирование",
    "Поиск и сбор данных",
    "Создание заметок",
    "Анализ и синтез",
    "Написание отчёта",
]


class ResearchProgress:
    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
        )
        self.tasks: dict[int, TaskID] = {}

    def show_header(self, research_id: str, query: str, depth: str) -> None:
        self.console.print(
            Panel(
                f"[bold]Исследование #{research_id[:8]}[/bold]\n"
                f"Тема: {query}\n"
                f"Глубина: {depth}",
                title="Deep Research Agent",
                border_style="cyan",
            )
        )

    def start(self) -> Progress:
        for i, stage in enumerate(STAGES):
            task_id = self.progress.add_task(
                f"[{i + 1}/{len(STAGES)}] {stage}",
                total=100,
            )
            self.tasks[i] = task_id
        return self.progress

    def update_stage(self, stage_index: int, completed: float = 100) -> None:
        """Update a stage's progress bar.

        Matches ``StageCallback`` signature ``(int, float) → None``.
        """
        task_id = self.tasks.get(stage_index)
        if task_id is not None:
            self.progress.update(task_id, completed=completed)

    def show_completion(
        self,
        report_path: str,
        artifacts_dir: str,
        cost_usd: float,
        tokens_in: int,
        tokens_out: int,
        elapsed: float,
    ) -> None:
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        self.console.print()
        self.console.print(
            f"[bold green]Исследование завершено за {minutes}m {seconds}s[/bold green]"
        )
        self.console.print(f"  Отчёт: [link={report_path}]{report_path}[/link]")
        self.console.print(f"  Артефакты: {artifacts_dir}")
        self.console.print(
            f"  Стоимость: ~${cost_usd:.4f} "
            f"({tokens_in:,} input / {tokens_out:,} output tokens)"
        )

    def show_error(self, message: str) -> None:
        self.console.print(f"\n[bold red]Ошибка:[/bold red] {message}")
