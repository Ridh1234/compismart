import logging
from collections.abc import Awaitable, Callable
from uuid import uuid4

from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.services.chunking_service import ChunkingService
from app.services.engagement_service import calculate_engagement_rate
from app.services.instagram_service import InstagramService
from app.services.memory_service import MemoryService, SessionState
from app.services.transcript_service import TranscriptService
from app.services.vectorstore_service import VectorStoreService
from app.services.youtube_service import YouTubeService


logger = logging.getLogger(__name__)
ProgressCallback = Callable[[dict], Awaitable[None]]


class AnalysisService:
    def __init__(self) -> None:
        self.youtube = YouTubeService()
        self.instagram = InstagramService()
        self.transcripts = TranscriptService()
        self.chunker = ChunkingService()
        self.vectorstore = VectorStoreService()
        self.memory = MemoryService()

    async def analyze(self, payload: AnalysisRequest, progress: ProgressCallback | None = None) -> AnalysisResponse:
        session_id = uuid4().hex
        logger.info("analysis_started session_id=%s", session_id)

        await self._progress(progress, "validate_urls", "started", 0, "Validating video URLs")
        await self._progress(progress, "validate_urls", "done", 0, "Video URLs accepted")

        await self._progress(progress, "fetch_youtube_metadata", "started", 1, "Fetching YouTube metadata")
        logger.info("analysis_phase session_id=%s phase=fetch_youtube_metadata", session_id)
        video_a = await self.youtube.fetch_metadata(str(payload.video_a_url))
        logger.info("analysis_phase_done session_id=%s phase=fetch_youtube_metadata", session_id)
        await self._progress(progress, "fetch_youtube_metadata", "done", 1, "YouTube metadata fetched")

        await self._progress(progress, "fetch_instagram_metadata", "started", 2, "Fetching Instagram metadata")
        logger.info("analysis_phase session_id=%s phase=fetch_instagram_metadata", session_id)
        video_b = await self.instagram.fetch_metadata(str(payload.video_b_url))
        logger.info("analysis_phase_done session_id=%s phase=fetch_instagram_metadata", session_id)
        await self._progress(progress, "fetch_instagram_metadata", "done", 2, "Instagram metadata fetched")

        await self._progress(progress, "attach_youtube_transcript", "started", 3, "Extracting YouTube transcript")
        logger.info("analysis_phase session_id=%s phase=attach_youtube_transcript", session_id)
        video_a = await self.transcripts.attach_transcript(video_a)
        logger.info(
            "analysis_phase_done session_id=%s phase=attach_youtube_transcript source=%s warnings=%s",
            session_id,
            video_a.transcript.source_type,
            len(video_a.warnings),
        )
        await self._progress(
            progress,
            "attach_youtube_transcript",
            "done",
            3,
            "YouTube transcript step finished",
            {"source": video_a.transcript.source_type, "warnings": len(video_a.warnings)},
        )

        await self._progress(progress, "attach_instagram_transcript", "started", 4, "Downloading Instagram media and transcribing with Whisper when needed")
        logger.info("analysis_phase session_id=%s phase=attach_instagram_transcript", session_id)
        video_b = await self.transcripts.attach_transcript(video_b)
        logger.info(
            "analysis_phase_done session_id=%s phase=attach_instagram_transcript source=%s warnings=%s",
            session_id,
            video_b.transcript.source_type,
            len(video_b.warnings),
        )
        await self._progress(
            progress,
            "attach_instagram_transcript",
            "done",
            4,
            "Instagram transcript step finished",
            {"source": video_b.transcript.source_type, "warnings": len(video_b.warnings)},
        )

        await self._progress(progress, "calculate_engagement", "started", 5, "Calculating engagement")
        logger.info("analysis_phase session_id=%s phase=calculate_engagement", session_id)
        video_a.engagement_rate = calculate_engagement_rate(video_a.likes, video_a.comments, video_a.views)
        video_b.engagement_rate = calculate_engagement_rate(video_b.likes, video_b.comments, video_b.views)
        if video_a.engagement_rate is None:
            video_a.warnings.append("Engagement rate unavailable because one or more metrics are missing.")
        if video_b.engagement_rate is None:
            video_b.warnings.append("Engagement rate unavailable because one or more metrics are missing.")
        await self._progress(progress, "calculate_engagement", "done", 5, "Engagement calculated")

        await self._progress(progress, "chunk_and_store", "started", 6, "Building transcript chunks and retrieval index")
        logger.info("analysis_phase session_id=%s phase=chunk_and_store", session_id)
        chunks = self.chunker.chunk_video(session_id, video_a) + self.chunker.chunk_video(session_id, video_b)
        await self.vectorstore.store_chunks(session_id, chunks)
        logger.info("analysis_phase_done session_id=%s phase=chunk_and_store chunks=%s", session_id, len(chunks))
        await self._progress(progress, "chunk_and_store", "done", 6, "Retrieval index built", {"chunks": len(chunks)})

        await self._progress(progress, "prepare_workspace", "started", 7, "Preparing workspace")
        self.memory.create_session(
            SessionState(
                session_id=session_id,
                video_a=video_a,
                video_b=video_b,
                chunks=chunks,
            )
        )

        warnings = [*video_a.warnings, *video_b.warnings]
        await self._progress(progress, "prepare_workspace", "done", 7, "Workspace ready", {"warnings": len(warnings)})
        logger.info("analysis_completed session_id=%s warnings=%s", session_id, len(warnings))
        return AnalysisResponse(session_id=session_id, video_a=video_a, video_b=video_b, warnings=warnings)

    async def _progress(
        self,
        progress: ProgressCallback | None,
        phase: str,
        status: str,
        step_index: int,
        message: str,
        extra: dict | None = None,
    ) -> None:
        if not progress:
            return
        event = {
            "phase": phase,
            "status": status,
            "step_index": step_index,
            "message": message,
        }
        if extra:
            event.update(extra)
        await progress(event)
