from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    dry_run: bool = Field(default=True, alias="DRY_RUN")
    data_dir: Path = Field(default=Path("data"), alias="DATA_DIR")
    output_dir: Path = Field(default=Path("dist"), alias="OUTPUT_DIR")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_text_model: str = Field(default="gpt-5.1-mini", alias="OPENAI_TEXT_MODEL")
    openai_image_model: str = Field(default="gpt-image-2", alias="OPENAI_IMAGE_MODEL")
    openai_tts_model: str = Field(default="gpt-4o-mini-tts", alias="OPENAI_TTS_MODEL")
    openai_tts_voice: str = Field(default="alloy", alias="OPENAI_TTS_VOICE")
    notion_token: str | None = Field(default=None, alias="NOTION_TOKEN")
    notion_database_id: str | None = Field(default=None, alias="NOTION_DATABASE_ID")
    notion_version: str = Field(default="2026-03-11", alias="NOTION_VERSION")
    notebooklm_enterprise_api_base: str = Field(default="https://notebooklm.googleapis.com", alias="NOTEBOOKLM_ENTERPRISE_API_BASE")
    notebooklm_enterprise_access_token: str | None = Field(default=None, alias="NOTEBOOKLM_ENTERPRISE_ACCESS_TOKEN")
    notebooklm_notebook_resource: str | None = Field(default=None, alias="NOTEBOOKLM_NOTEBOOK_RESOURCE")
    youtube_token_json: str | None = Field(default=None, alias="YOUTUBE_TOKEN_JSON")
    youtube_privacy_status: str = Field(default="private", alias="YOUTUBE_PRIVACY_STATUS")
    tiktok_access_token: str | None = Field(default=None, alias="TIKTOK_ACCESS_TOKEN")
    tiktok_privacy_level: str = Field(default="SELF_ONLY", alias="TIKTOK_PRIVACY_LEVEL")
    tiktok_api_base: str = Field(default="https://open.tiktokapis.com", alias="TIKTOK_API_BASE")
    min_quality_score: int = Field(default=70, alias="MIN_QUALITY_SCORE")

    @property
    def notion_enabled(self) -> bool:
        return bool(self.notion_token and self.notion_database_id)

    @property
    def youtube_enabled(self) -> bool:
        return bool(self.youtube_token_json)

    @property
    def tiktok_enabled(self) -> bool:
        return bool(self.tiktok_access_token)

    @property
    def notebooklm_enterprise_enabled(self) -> bool:
        return bool(self.notebooklm_enterprise_access_token and self.notebooklm_notebook_resource)


@lru_cache
def get_settings() -> Settings:
    return Settings()
