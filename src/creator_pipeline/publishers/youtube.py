from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from ..config import Settings

YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


class YouTubePublisher:
    def __init__(self, settings: Settings):
        self.settings = settings

    def publish(self, video_path: Path, title: str, description: str, hashtags: list[str], output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "youtube_publish_report.json"
        if self.settings.dry_run or not self.settings.youtube_enabled:
            report = {"status": "dry_run" if self.settings.dry_run else "youtube_not_configured", "video_path": str(video_path), "title": title, "description": description, "hashtags": hashtags, "privacy_status": self.settings.youtube_privacy_status}
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            return report_path
        credentials = Credentials.from_authorized_user_info(json.loads(self.settings.youtube_token_json or "{}"), scopes=YOUTUBE_SCOPES)
        youtube = build("youtube", "v3", credentials=credentials)
        body: dict[str, Any] = {"snippet": {"title": title[:100], "description": f"{description}\n\n{' '.join(hashtags)}"[:5000], "tags": [tag.lstrip("#") for tag in hashtags][:20], "categoryId": "22"}, "status": {"privacyStatus": self.settings.youtube_privacy_status}}
        media = MediaFileUpload(str(video_path), mimetype="video/mp4", chunksize=-1, resumable=True)
        response = youtube.videos().insert(part="snippet,status", body=body, media_body=media).execute()
        report_path.write_text(json.dumps({"status": "published", "response": response}, ensure_ascii=False, indent=2), encoding="utf-8")
        return report_path
