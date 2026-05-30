from app.schemas.video import TranscriptChunk, VideoMetadata


class ChunkingService:
    def chunk_video(self, session_id: str, video: VideoMetadata) -> list[TranscriptChunk]:
        text = video.transcript.text or video.title_or_caption or ""
        if not text.strip():
            return []

        pieces = self._split(text)
        chunks: list[TranscriptChunk] = []
        for index, piece in enumerate(pieces, start=1):
            chunks.append(
                TranscriptChunk(
                    chunk_id=f"{video.label}-{index:03d}",
                    session_id=session_id,
                    video_label=video.label,
                    platform=video.platform,
                    text=piece,
                    source_url=video.source_url,
                    creator=video.creator_name or video.creator_handle,
                )
            )
        return chunks

    def _split(self, text: str) -> list[str]:
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter

            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
            return splitter.split_text(text)
        except Exception:
            chunks: list[str] = []
            start = 0
            while start < len(text):
                chunks.append(text[start : start + 500])
                start += 400
            return chunks
