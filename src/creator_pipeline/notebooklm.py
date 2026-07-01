from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from .config import Settings
from .ingest import load_sources_from_dir
from .models import ContentSource


class ManualNotebookLMExportIngestor:
    def __init__(self, export_dir: Path):
        self.export_dir = export_dir

    def load(self) -> list[ContentSource]:
        sources = load_sources_from_dir(self.export_dir)
        for source in sources:
            source.source_type = "notebooklm-manual-export"
        return sources


class NotebookLMEnterpriseClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def enabled(self) -> bool:
        return self.settings.notebooklm_enterprise_enabled

    def request_audio_overview(self, custom_prompt: str | None = None) -> dict[str, Any]:
        if not self.enabled:
            return {"status": "notebooklm_enterprise_not_configured"}
        url = f"{self.settings.notebooklm_enterprise_api_base.rstrip('/')}/v1/{self.settings.notebooklm_notebook_resource}:audioOverview"
        headers = {"Authorization": f"Bearer {self.settings.notebooklm_enterprise_access_token}", "Content-Type": "application/json"}
        payload = {"customPrompt": custom_prompt} if custom_prompt else {}
        response = httpx.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
