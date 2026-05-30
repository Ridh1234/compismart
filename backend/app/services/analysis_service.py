import logging
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


class AnalysisService:
    def __init__(self) -> None:
        self.youtube = YouTubeService()
        self.instagram = InstagramService()
        self.transcripts = TranscriptService()
        self.chunker = ChunkingService()
        self.vectorstore = VectorStoreService()
        self.memory = MemoryService()

    async def analyze(self, payload: AnalysisRequest) -> AnalysisResponse:
        session_id = uuid4().hex
        logger.info("analysis_started session_id=%s", session_id)

        logger.info("analysis_phase session_id=%s phase=fetch_youtube_metadata", session_id)
        video_a = await self.youtube.fetch_metadata(str(payload.video_a_url))
        logger.info("analysis_phase_done session_id=%s phase=fetch_youtube_metadata", session_id)

        logger.info("analysis_phase session_id=%s phase=fetch_instagram_metadata", session_id)
        video_b = await self.instagram.fetch_metadata(str(payload.video_b_url))
        logger.info("analysis_phase_done session_id=%s phase=fetch_instagram_metadata", session_id)

        logger.info("analysis_phase session_id=%s phase=attach_youtube_transcript", session_id)
        video_a = await self.transcripts.attach_transcript(video_a)
        logger.info(
            "analysis_phase_done session_id=%s phase=attach_youtube_transcript source=%s warnings=%s",
            session_id,
            video_a.transcript.source_type,
            len(video_a.warnings),
        )

        logger.info("analysis_phase session_id=%s phase=attach_instagram_transcript", session_id)
        video_b = await self.transcripts.attach_transcript(video_b)
        logger.info(
            "analysis_phase_done session_id=%s phase=attach_instagram_transcript source=%s warnings=%s",
            session_id,
            video_b.transcript.source_type,
            len(video_b.warnings),
        )

        logger.info("analysis_phase session_id=%s phase=calculate_engagement", session_id)
        video_a.engagement_rate = calculate_engagement_rate(video_a.likes, video_a.comments, video_a.views)
        video_b.engagement_rate = calculate_engagement_rate(video_b.likes, video_b.comments, video_b.views)
        if video_a.engagement_rate is None:
            video_a.warnings.append("Engagement rate unavailable because one or more metrics are missing.")
        if video_b.engagement_rate is None:
            video_b.warnings.append("Engagement rate unavailable because one or more metrics are missing.")

        logger.info("analysis_phase session_id=%s phase=chunk_and_store", session_id)
        chunks = self.chunker.chunk_video(session_id, video_a) + self.chunker.chunk_video(session_id, video_b)
        await self.vectorstore.store_chunks(session_id, chunks)
        logger.info("analysis_phase_done session_id=%s phase=chunk_and_store chunks=%s", session_id, len(chunks))

        self.memory.create_session(
            SessionState(
                session_id=session_id,
                video_a=video_a,
                video_b=video_b,
                chunks=chunks,
            )
        )

        warnings = [*video_a.warnings, *video_b.warnings]
        logger.info("analysis_completed session_id=%s warnings=%s", session_id, len(warnings))
        return AnalysisResponse(session_id=session_id, video_a=video_a, video_b=video_b, warnings=warnings)
