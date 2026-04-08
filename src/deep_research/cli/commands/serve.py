"""CLI command: research serve — start the FastAPI server."""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()


def serve_command(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Адрес хоста"),
    port: int = typer.Option(8000, "--port", "-p", help="Порт"),
    reload: bool = typer.Option(False, "--reload", help="Автоперезагрузка при изменениях"),
) -> None:
    """Запустить API сервер (uvicorn)."""
    import uvicorn

    console.print(f"[bold cyan]Запуск сервера на {host}:{port}[/bold cyan]")
    console.print(f"  Документация: http://{host}:{port}/docs")
    console.print()

    uvicorn.run(
        "deep_research.main:app",
        host=host,
        port=port,
        reload=reload,
    )
