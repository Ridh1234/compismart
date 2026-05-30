from pydantic import BaseModel, Field

from app.schemas.video import VideoMetadata


class AnalysisRequest(BaseModel):
    video_a_url: str = Field(min_length=1)
    video_b_url: str = Field(min_length=1)


class AnalysisResponse(BaseModel):
    session_id: str
    video_a: VideoMetadata
    video_b: VideoMetadata
    warnings: list[str] = Field(default_factory=list)
