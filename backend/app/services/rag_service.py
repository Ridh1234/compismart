import asyncio

from app.core.config import settings
from app.core.errors import AppError
from app.schemas.video import ChatMessage, Citation, TranscriptChunk, VideoMetadata
from app.services.memory_service import MemoryService
from app.services.vectorstore_service import VectorStoreService
from app.utils.formatters import trim_preview


class RagService:
    def __init__(self) -> None:
        self.memory = MemoryService()
        self.vectorstore = VectorStoreService()

    async def stream_answer(self, session_id: str, message: str):
        session = self.memory.get_session(session_id)
        if not session:
            raise AppError("session_not_found", "Analysis session not found. Run analysis again.", 404)

        retrieved = await self.vectorstore.retrieve(session_id, message, session.chunks)
        citations = [
            Citation(
                video_label=chunk.video_label,
                chunk_id=chunk.chunk_id,
                platform=chunk.platform,
                text_preview=trim_preview(chunk.text),
            )
            for chunk in retrieved
        ]

        self.memory.add_message(session_id, ChatMessage(role="user", content=message))

        answer = ""
        if settings.cohere_api_key:
            async for token in self._cohere_stream(session.video_a, session.video_b, session.messages, retrieved, message):
                answer += token
                yield {"event": "delta", "data": {"text": token}}
        else:
            local_answer = self._local_answer(session.video_a, session.video_b, retrieved, message)
            for token in self._chunk_text(local_answer):
                answer += token
                yield {"event": "delta", "data": {"text": token}}
                await asyncio.sleep(0.018)

        self.memory.add_message(session_id, ChatMessage(role="assistant", content=answer))
        yield {"event": "citations", "data": {"citations": [citation.model_dump() for citation in citations]}}
        yield {"event": "done", "data": {"ok": True}}

    async def _cohere_stream(
        self,
        video_a: VideoMetadata,
        video_b: VideoMetadata,
        history: list[ChatMessage],
        chunks: list[TranscriptChunk],
        message: str,
    ):
        prompt = self._prompt(video_a, video_b, history, chunks, message)
        try:
            import cohere

            client = cohere.Client(settings.cohere_api_key)
            stream = client.chat_stream(model=settings.cohere_chat_model, message=prompt)
            for event in stream:
                text = getattr(event, "text", None)
                if text:
                    yield text
        except Exception:
            fallback = self._local_answer(video_a, video_b, chunks, message)
            for token in self._chunk_text(fallback):
                yield token
                await asyncio.sleep(0.018)

    def _prompt(
        self,
        video_a: VideoMetadata,
        video_b: VideoMetadata,
        history: list[ChatMessage],
        chunks: list[TranscriptChunk],
        message: str,
    ) -> str:
        return f"""
You are CompiSMART, a creator-performance analyst. Answer only from the metadata, transcript chunks, and conversation history below.
Be direct, practical, and clear. Compare Video A and Video B explicitly. Mention uncertainty when data is missing.
End with a short Sources section using labels like "Video A / Chunk A-001" and "Video B / Metadata".

Video A metadata:
{video_a.model_dump_json(indent=2)}

Video B metadata:
{video_b.model_dump_json(indent=2)}

Conversation history:
{[message.model_dump() for message in history[-8:]]}

Retrieved transcript chunks:
{[chunk.model_dump() for chunk in chunks]}

User question: {message}
"""

    def _local_answer(self, video_a: VideoMetadata, video_b: VideoMetadata, chunks: list[TranscriptChunk], message: str) -> str:
        winner = self._winner(video_a, video_b)
        parts = [
            self._metric_sentence(video_a, video_b),
            f"{winner} The strongest supported evidence is in the retrieved transcript context below.",
        ]
        if chunks:
            for chunk in chunks[:3]:
                parts.append(f"- Video {chunk.video_label} / Chunk {chunk.chunk_id}: {trim_preview(chunk.text, 220)}")
        else:
            parts.append("No transcript chunks were available, so this answer is limited to metadata.")

        lowered = message.lower()
        if "improve" in lowered or "suggest" in lowered or "better" in lowered:
            parts.append(
                "Practical next steps: tighten the opening hook, make the payoff explicit earlier, remove any slow setup, and mirror the clearer structure from the stronger performer where the transcript supports it."
            )
        if "hook" in lowered or "first 5" in lowered:
            parts.append(
                "For hook analysis, treat transcript evidence as directional unless timestamped segments are present; captions often lack exact first-five-second boundaries."
            )

        parts.append("\nSources:\n" + "\n".join(self._source_lines(chunks)))
        return "\n\n".join(parts)

    def _metric_sentence(self, video_a: VideoMetadata, video_b: VideoMetadata) -> str:
        a_rate = f"{video_a.engagement_rate:.2f}%" if video_a.engagement_rate is not None else "unavailable"
        b_rate = f"{video_b.engagement_rate:.2f}%" if video_b.engagement_rate is not None else "unavailable"
        return f"Video A engagement rate is {a_rate}; Video B engagement rate is {b_rate}."

    def _winner(self, video_a: VideoMetadata, video_b: VideoMetadata) -> str:
        if video_a.engagement_rate is None or video_b.engagement_rate is None:
            return "A performance winner cannot be stated confidently because one or both engagement rates are unavailable."
        if video_a.engagement_rate > video_b.engagement_rate:
            return "Video A is stronger on engagement rate."
        if video_b.engagement_rate > video_a.engagement_rate:
            return "Video B is stronger on engagement rate."
        return "The videos are tied on engagement rate."

    def _source_lines(self, chunks: list[TranscriptChunk]) -> list[str]:
        lines = [f"* Video {chunk.video_label} / Chunk {chunk.chunk_id}" for chunk in chunks[:5]]
        if not lines:
            lines = ["* Video A / Metadata", "* Video B / Metadata"]
        else:
            lines.extend(["* Video A / Metadata", "* Video B / Metadata"])
        return lines

    def _chunk_text(self, text: str, size: int = 18):
        index = 0
        while index < len(text):
            yield text[index : index + size]
            index += size
