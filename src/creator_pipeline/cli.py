from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from .config import get_settings
from .notion import NotionService
from .pipeline import run_pipeline

app = typer.Typer(help="Notion + NotebookLM content remixing and publishing pipeline")
console = Console()


@app.command()
def run(
    sources: Path = typer.Option(Path("data/sample_sources"), help="Directory containing md/txt/json source files."),
    theme: str = typer.Option("NotionとNotebookLM素材から独自価値のあるAIラジオを作る", help="Content theme."),
    dry_run: bool = typer.Option(True, help="Do not call publishing APIs."),
    publish: bool = typer.Option(False, help="Create publish plans or publish when dry_run is false."),
    render_media: bool = typer.Option(True, help="Generate images/audio/video."),
) -> None:
    settings = get_settings()
    result = run_pipeline(settings=settings, sources_dir=sources, theme=theme, dry_run=dry_run, publish=publish, render_media=render_media)
    console.print({"package_id": result.package_id, "output_dir": str(result.output_dir), "quality_score": result.quality_score, "dry_run": result.dry_run})


@app.command("create-notion-task")
def create_notion_task(
    title: str = typer.Option(..., help="Task title."),
    notes: str = typer.Option("", help="Task notes."),
    source_url: list[str] = typer.Option(None, help="Source URL. Can be repeated."),
) -> None:
    settings = get_settings()
    response = NotionService(settings).create_task(title=title, notes=notes, source_urls=source_url or [], output_dir=settings.output_dir)
    console.print(response)


if __name__ == "__main__":
    app()
