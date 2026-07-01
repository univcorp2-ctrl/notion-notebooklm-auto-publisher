from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from .config import Settings
from .models import ContentSource


class NotionService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = "https://api.notion.com/v1"

    @property
    def enabled(self) -> bool:
        return self.settings.notion_enabled

    def headers(self) -> dict[str, str]:
        if not self.settings.notion_token:
            raise RuntimeError("NOTION_TOKEN is not configured.")
        return {"Authorization": f"Bearer {self.settings.notion_token}", "Notion-Version": self.settings.notion_version, "Content-Type": "application/json"}

    def create_task(self, title: str, notes: str, source_urls: list[str] | None = None, output_dir: Path | None = None) -> dict[str, Any]:
        payload = {"parent": {"database_id": self.settings.notion_database_id}, "properties": {"Name": {"title": [{"text": {"content": title}}]}, "Status": {"status": {"name": "Ready"}}, "Sources": {"rich_text": [{"text": {"content": "\n".join(source_urls or [])[:1900]}}]}}, "children": [{"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": notes[:1900]}}]}}]}
        if not self.enabled:
            draft = {"status": "notion_not_configured", "payload": payload}
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
                (output_dir / "notion_task_draft.json").write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
            return draft
        response = httpx.post(f"{self.base_url}/pages", headers=self.headers(), json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    def query_ready_tasks(self) -> list[dict[str, Any]]:
        if not self.enabled:
            return []
        payload = {"filter": {"property": "Status", "status": {"equals": "Ready"}}}
        response = httpx.post(f"{self.base_url}/databases/{self.settings.notion_database_id}/query", headers=self.headers(), json=payload, timeout=30)
        response.raise_for_status()
        return response.json().get("results", [])

    def task_to_source(self, task: dict[str, Any]) -> ContentSource:
        props = task.get("properties", {})
        title = _read_title(props.get("Name")) or "Notion Task"
        sources = _read_rich_text(props.get("Sources"))
        return ContentSource(title=title, body=sources or title, source_type="notion", source_url=task.get("url"))


def _read_title(prop: dict[str, Any] | None) -> str | None:
    values = (prop or {}).get("title") or []
    return "".join(v.get("plain_text", "") for v in values).strip() or None


def _read_rich_text(prop: dict[str, Any] | None) -> str | None:
    values = (prop or {}).get("rich_text") or []
    return "".join(v.get("plain_text", "") for v in values).strip() or None
