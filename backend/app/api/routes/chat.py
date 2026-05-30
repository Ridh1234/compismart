import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.errors import AppError
from app.schemas.chat import ChatRequest
from app.services.rag_service import RagService

router = APIRouter(tags=["chat"])


def sse(event: str, data: object) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/chat")
async def chat(payload: ChatRequest) -> StreamingResponse:
    service = RagService()

    async def stream():
        try:
            async for event in service.stream_answer(payload.session_id, payload.message):
                yield sse(event["event"], event["data"])
        except AppError as exc:
            yield sse("error", {"error": exc.code, "message": exc.message})
        except Exception as exc:
            yield sse("error", {"error": "chat_failed", "message": str(exc)})

    if not payload.message.strip():
        raise HTTPException(status_code=422, detail={"error": "empty_message", "message": "Message cannot be empty."})

    return StreamingResponse(stream(), media_type="text/event-stream")
