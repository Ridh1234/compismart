import asyncio
import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.errors import AppError
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.services.analysis_service import AnalysisService

router = APIRouter(tags=["analysis"])
logger = logging.getLogger(__name__)


def sse(event: str, data: object) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(payload: AnalysisRequest) -> AnalysisResponse:
    try:
        return await AnalysisService().analyze(payload)
    except AppError as exc:
        logger.warning("analysis_app_error code=%s message=%s", exc.code, exc.message)
        raise HTTPException(status_code=exc.status_code, detail={"error": exc.code, "message": exc.message}) from exc
    except Exception as exc:
        logger.exception("analysis_unhandled_error")
        raise HTTPException(
            status_code=500,
            detail={"error": "analysis_unhandled_error", "message": f"Analysis failed unexpectedly: {exc}"},
        ) from exc


@router.post("/analyze/stream")
async def analyze_stream(payload: AnalysisRequest) -> StreamingResponse:
    async def stream():
        task = None
        try:
            queue: asyncio.Queue[str] = asyncio.Queue()
            latest_progress: dict = {
                "phase": "starting",
                "status": "started",
                "step_index": 0,
                "message": "Starting backend analysis",
            }

            async def progress(event: dict) -> None:
                latest_progress.update(event)
                await queue.put(sse("progress", event))

            task = asyncio.create_task(AnalysisService().analyze(payload, progress=progress))

            while not task.done() or not queue.empty():
                try:
                    yield await asyncio.wait_for(queue.get(), timeout=5)
                except asyncio.TimeoutError:
                    yield sse(
                        "heartbeat",
                        {
                            **latest_progress,
                            "message": f"Still working: {latest_progress.get('message', 'analysis in progress')}",
                        },
                    )

            result = await task
            yield sse("result", result.model_dump())
            yield sse("done", {"ok": True})
        except AppError as exc:
            logger.warning("analysis_app_error code=%s message=%s", exc.code, exc.message)
            yield sse("error", {"error": exc.code, "message": exc.message})
        except Exception as exc:
            logger.exception("analysis_unhandled_error")
            yield sse("error", {"error": "analysis_unhandled_error", "message": f"Analysis failed unexpectedly: {exc}"})
        finally:
            if task and not task.done():
                task.cancel()

    return StreamingResponse(stream(), media_type="text/event-stream")
