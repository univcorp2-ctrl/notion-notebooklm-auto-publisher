from __future__ import annotations

import json
from pathlib import Path

from .config import Settings
from .ingest import load_sources_from_dir
from .media import MediaBuilder
from .mixer import build_content_package
from .models import ContentSource, PipelineResult
from .notebooklm import ManualNotebookLMExportIngestor
from .notion import NotionService
from .publishers.tiktok import TikTokPublisher
from .publishers.youtube import YouTubePublisher
from .quality import assess_quality


def run_pipeline(settings: Settings, sources_dir: Path, theme: str, dry_run: bool | None = None, publish: bool = False, render_media: bool = True) -> PipelineResult:
    if dry_run is not None:
        settings.dry_run = dry_run
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    sources = _collect_sources(settings, sources_dir)
    if len(sources) < 2:
        if settings.dry_run:
            sources.extend(_sample_sources())
        else:
            raise ValueError("2つ以上の素材が必要です。Notion/NotebookLM/ローカル素材を追加してください。")
    package = build_content_package(sources=sources, theme=theme, settings=settings)
    quality_report = assess_quality(package.sources, package.script, package.article, settings.min_quality_score)
    package_dir = settings.output_dir / package.package_id
    package_dir.mkdir(parents=True, exist_ok=True)
    article_path = package_dir / "article.md"
    script_path = package_dir / "script.txt"
    quality_report_path = package_dir / "quality_report.json"
    article_path.write_text(package.article, encoding="utf-8")
    script_path.write_text(package.script, encoding="utf-8")
    quality_report_path.write_text(quality_report.model_dump_json(indent=2), encoding="utf-8")
    (package_dir / "package.json").write_text(package.model_dump_json(indent=2), encoding="utf-8")
    media_paths: list[Path] = []
    if render_media:
        media = MediaBuilder(settings)
        image_paths = media.generate_images(package.image_prompts, package_dir / "images", package.title)
        audio_path = media.generate_audio(package.script, package_dir / "audio.wav")
        video_path = media.compose_video(image_paths, audio_path, package_dir / "vertical_video.mp4")
        media_paths.extend(image_paths + [audio_path, video_path])
    publish_reports: list[Path] = []
    if publish:
        video_candidate = next((p for p in media_paths if p.suffix.lower() == ".mp4"), package_dir / "vertical_video.mp4")
        publish_reports.append(YouTubePublisher(settings).publish(video_candidate, package.title, package.description, package.hashtags, package_dir))
        publish_reports.append(TikTokPublisher(settings).publish(video_candidate, package.title, package.description, package.hashtags, package_dir))
    manifest = {"package_id": package.package_id, "title": package.title, "quality_score": quality_report.score, "quality_passed": quality_report.passed, "dry_run": settings.dry_run, "article_path": str(article_path), "script_path": str(script_path), "media_paths": [str(p) for p in media_paths], "publish_reports": [str(p) for p in publish_reports]}
    (package_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return PipelineResult(package_id=package.package_id, output_dir=package_dir, article_path=article_path, script_path=script_path, quality_report_path=quality_report_path, media_paths=media_paths, publish_reports=publish_reports, quality_score=quality_report.score, dry_run=settings.dry_run)


def _collect_sources(settings: Settings, sources_dir: Path) -> list[ContentSource]:
    sources = load_sources_from_dir(sources_dir)
    sources.extend(ManualNotebookLMExportIngestor(settings.data_dir / "notebooklm_exports").load())
    notion = NotionService(settings)
    for task in notion.query_ready_tasks():
        sources.append(notion.task_to_source(task))
    return [s for s in sources if s.body.strip()]


def _sample_sources() -> list[ContentSource]:
    return [ContentSource(title="Notionで企画をタスク化する理由", body="Notionにテーマ、素材URL、進行状況、投稿先、結果を集約すると、AI生成の前後工程が見える化される。", source_type="sample"), ContentSource(title="NotebookLM音声概要を素材化する理由", body="NotebookLMの音声概要は理解しやすいが、そのまま投稿すると独自性が弱い。別素材と比較し、反論や具体例を足す必要がある。", source_type="sample")]
