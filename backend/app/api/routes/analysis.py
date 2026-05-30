import logging

from fastapi import APIRouter, HTTPException

from app.core.errors import AppError
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.services.analysis_service import AnalysisService

router = APIRouter(tags=["analysis"])
logger = logging.getLogger(__name__)


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
