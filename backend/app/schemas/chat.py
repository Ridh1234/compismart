from pydantic import BaseModel, Field

from app.schemas.video import Citation


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1)


class ChatFinalPayload(BaseModel):
    citations: list[Citation]
