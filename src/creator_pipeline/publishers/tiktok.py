from __future__ import annotations

import json
from pathlib import Path

import httpx

from ..config import Settings


class TikTokPublisher:
    def __init__(self, settings: Settings):
        self.settings = settings

    def publish(self, video_path: Path, title: str, description: str, hashtags: list[str], output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "tiktok_publish_report.json"
        caption = f"{title}\n\n{description}\n{' '.join(hashtags)}"[:2200]
        if self.settings.dry_run or not self.settings.tiktok_enabled:
            report = {"status": "dry_run" if self.settings.dry_run else "tiktok_not_configured", "video_path": str(video_path), "caption": caption, "privacy_level": self.settings.tiktok_privacy_level}
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            return report_path
        file_size = video_path.stat().st_size
        init_payload = {"post_info": {"title": caption, "privacy_level": self.settings.tiktok_privacy_level, "disable_duet": False, "disable_comment": False, "disable_stitch": False}, "source_info": {"source": "FILE_UPLOAD", "video_size": file_size, "chunk_size": file_size, "total_chunk_count": 1}}
        headers = {"Authorization": f"Bearer {self.settings.tiktok_access_token}", "Content-Type": "application/json; charset=UTF-8"}
        init_url = f"{self.settings.tiktok_api_base.rstrip('/')}/v2/post/publish/video/init/"
        init_response = httpx.post(init_url, headers=headers, json=init_payload, timeout=60)
        init_response.raise_for_status()
        init_data = init_response.json()
        upload_url = init_data.get("data", {}).get("upload_url")
        if not upload_url:
            raise RuntimeError(f"TikTok did not return upload_url: {init_data}")
        upload_headers = {"Content-Type": "video/mp4", "Content-Range": f"bytes 0-{file_size - 1}/{file_size}"}
        with video_path.open("rb") as fh:
            upload_response = httpx.put(upload_url, headers=upload_headers, content=fh.read(), timeout=300)
        upload_response.raise_for_status()
        report_path.write_text(json.dumps({"status": "uploaded", "init_response": init_data}, ensure_ascii=False, indent=2), encoding="utf-8")
        return report_path
