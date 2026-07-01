from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field


class ContentSource(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    title: str
    body: str
    source_type: str = "manual"
    source_url: str | None = None
    author: str | None = None
    license_note: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ContentPackage(BaseModel):
    package_id: str = Field(default_factory=lambda: uuid4().hex[:12])
    title: str
    theme: str
    script: str
    article: str
    summary: str
    description: str
    hashtags: list[str]
    image_prompts: list[str]
    sources: list[ContentSource]


class QualityReport(BaseModel):
    score: int
    passed: bool
    flags: list[str]
    checks: dict[str, int | float | str | bool]


class PipelineResult(BaseModel):
    package_id: str
    output_dir: Path
    article_path: Path
    script_path: Path
    quality_report_path: Path
    media_paths: list[Path]
    publish_reports: list[Path]
    quality_score: int
    dry_run: bool
