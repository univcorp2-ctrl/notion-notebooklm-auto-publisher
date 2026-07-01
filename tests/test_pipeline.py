from pathlib import Path

from creator_pipeline.config import Settings
from creator_pipeline.pipeline import run_pipeline


def test_pipeline_dry_run_without_media(tmp_path: Path) -> None:
    sources = tmp_path / "sources"
    sources.mkdir()
    (sources / "a.md").write_text("Notionで企画を管理し、投稿の目的を明確化する。", encoding="utf-8")
    (sources / "b.md").write_text("NotebookLMの音声概要を別素材と比較し、独自の意見を足す。", encoding="utf-8")
    settings = Settings(DRY_RUN=True, OUTPUT_DIR=tmp_path / "dist", DATA_DIR=tmp_path / "data")
    result = run_pipeline(settings=settings, sources_dir=sources, theme="テスト", dry_run=True, publish=True, render_media=False)
    assert result.article_path.exists()
    assert result.script_path.exists()
    assert result.quality_report_path.exists()
    assert result.dry_run is True
