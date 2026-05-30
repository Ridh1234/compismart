from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Platform = Literal["youtube", "instagram"]
VideoLabel = Literal["A", "B"]
TranscriptSource = Literal["official_caption", "scraped_caption", "whisper_generated", "unavailable"]


class TranscriptSegment(BaseModel):
    text: str
    start_time: float | None = None
    end_time: float | None = None


class TranscriptBundle(BaseModel):
    text: str = ""
    source_type: TranscriptSource = "unavailable"
    segments: list[TranscriptSegment] = Field(default_factory=list)
    warning: str | None = None


class VideoMetadata(BaseModel):
    label: VideoLabel
    platform: Platform
    source_url: str
    video_id: str | None = None
    creator_name: str | None = None
    creator_handle: str | None = None
    follower_count: int | None = None
    title_or_caption: str | None = None
    views: int | None = None
    likes: int | None = None
    comments: int | None = None
    hashtags: list[str] = Field(default_factory=list)
    upload_date: str | None = None
    duration_seconds: int | None = None
    engagement_rate: float | None = None
    thumbnail_url: str | None = None
    media_url: str | None = None
    audio_url: str | None = None
    transcript: TranscriptBundle = Field(default_factory=TranscriptBundle)
    warnings: list[str] = Field(default_factory=list)


class TranscriptChunk(BaseModel):
    chunk_id: str
    session_id: str
    video_label: VideoLabel
    platform: Platform
    text: str
    source_url: str
    creator: str | None = None
    start_time: float | None = None
    end_time: float | None = None


class Citation(BaseModel):
    video_label: VideoLabel
    chunk_id: str
    platform: Platform
    text_preview: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
