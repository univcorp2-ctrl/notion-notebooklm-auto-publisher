from __future__ import annotations

import json
from pathlib import Path

from .models import ContentSource

SUPPORTED_EXTENSIONS = {".md", ".txt", ".json"}


def load_sources_from_dir(path: Path) -> list[ContentSource]:
    if not path.exists():
        return []
    sources: list[ContentSource] = []
    for file_path in sorted(path.rglob("*")):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            sources.extend(load_sources_from_file(file_path))
    return [s for s in sources if s.body.strip()]


def load_sources_from_file(path: Path) -> list[ContentSource]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() != ".json":
        return [ContentSource(title=_pretty_title(path.stem), body=text.strip(), source_type="file", source_url=str(path))]
    payload = json.loads(text)
    if isinstance(payload, dict) and "sources" in payload:
        payload = payload["sources"]
    if isinstance(payload, list):
        return [_source_from_mapping(item, path) for item in payload]
    if isinstance(payload, dict):
        return [_source_from_mapping(payload, path)]
    raise ValueError(f"Unsupported JSON source format: {path}")


def _source_from_mapping(item: dict, path: Path) -> ContentSource:
    return ContentSource(
        title=str(item.get("title") or _pretty_title(path.stem)),
        body=str(item.get("body") or item.get("content") or item.get("text") or "").strip(),
        source_type=str(item.get("source_type") or "json"),
        source_url=item.get("source_url") or item.get("url") or str(path),
        author=item.get("author"),
        license_note=item.get("license_note") or item.get("license"),
    )


def _pretty_title(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").title()
