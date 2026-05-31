from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    youtube_api_key: str | None = None
    apify_token: str | None = None
    cohere_api_key: str | None = None
    chroma_persist_dir: str = "./.chroma"

    cohere_chat_model: str = "command-a-plus-05-2026"
    cohere_embed_model: str = "embed-english-v3.0"
    whisper_model_size: str = "small"
    whisper_model_dir: str = "./.models/whisper"
    whisper_language: str | None = "hi"
    whisper_initial_prompt: str | None = "This audio may contain Hindi, Hinglish, or English. Transcribe the spoken words accurately; do not translate."
    media_download_dir: str = "/tmp/compismart_media"
    ytdlp_cookies_path: str | None = None
    environment: str = "development"
    log_level: str = "INFO"

    apify_instagram_actor: str = "apify/instagram-scraper"
    apify_instagram_fallback_actor: str | None = None
    apify_youtube_video_actor: str = "streamers/youtube-scraper"
    apify_youtube_shorts_actor: str = "streamers/youtube-shorts-scraper"
    apify_youtube_shorts_max_results: int = 50
    frontend_origin: str = "http://localhost:5173"
    cors_origin_regex: str | None = r"https://.*\.vercel\.app"
    cors_extra_origins: str = Field(default="")

    @property
    def cors_origins(self) -> List[str]:
        origins = [self.frontend_origin, "http://127.0.0.1:5173", "http://localhost:4173"]
        origins.extend([item.strip() for item in self.cors_extra_origins.split(",") if item.strip()])
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
