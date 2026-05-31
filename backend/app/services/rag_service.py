import asyncio
import logging

from app.core.config import settings
from app.core.errors import AppError
from app.schemas.video import ChatMessage, Citation, TranscriptChunk, VideoMetadata
from app.services.memory_service import MemoryService
from app.services.vectorstore_service import VectorStoreService
from app.utils.formatters import trim_preview


logger = logging.getLogger(__name__)


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
        try:
            import cohere

            client = cohere.ClientV2(api_key=settings.cohere_api_key)
            stream = client.chat_stream(
                model=settings.cohere_chat_model,
                messages=self._messages(video_a, video_b, history, chunks, message),
                temperature=0.3,
            )
            for event in stream:
                text = _cohere_event_text(event)
                if text:
                    yield text
        except Exception as exc:
            logger.exception("cohere_chat_failed model=%s", settings.cohere_chat_model)
            fallback = self._local_answer(video_a, video_b, chunks, message)
            fallback = f"Model response unavailable, so I’m answering from the stored analysis data. Reason: {exc}\n\n{fallback}"
            for token in self._chunk_text(fallback):
                yield token
                await asyncio.sleep(0.018)

    def _messages(
        self,
        video_a: VideoMetadata,
        video_b: VideoMetadata,
        history: list[ChatMessage],
        chunks: list[TranscriptChunk],
        message: str,
    ) -> list[dict[str, str]]:
        system = (
            "You are CompiSMART, a creator-performance analyst. Answer the user's exact question from the provided "
            "metadata, transcript chunks, and conversation history. Be direct, practical, and specific. Compare Video A "
            "and Video B when useful, but do not force a comparison when the user asks about only one video. Mention "
            "uncertainty when data is missing. Format every answer as clean Markdown: bold section headings like "
            "**Clarity**, bullet points for Video A and Video B, and a final **Sources** section. Do not use markdown "
            "tables. Use labels such as Video A / Chunk A-001 or Video B / Metadata."
        )
        context = (
            "Video A metadata:\n"
            f"{video_a.model_dump_json(indent=2)}\n\n"
            "Video B metadata:\n"
            f"{video_b.model_dump_json(indent=2)}\n\n"
            "Retrieved transcript chunks:\n"
            f"{[chunk.model_dump() for chunk in chunks]}"
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": context},
        ]
        for item in history[-8:]:
            messages.append({"role": item.role, "content": item.content})
        messages.append({"role": "user", "content": message})
        return messages

    def _local_answer(self, video_a: VideoMetadata, video_b: VideoMetadata, chunks: list[TranscriptChunk], message: str) -> str:
        lowered = message.lower()
        parts = [self._question_lead(video_a, video_b, lowered)]

        if _asks_for_metrics(lowered):
            parts.append(self._metrics_block(video_a, video_b))
        elif _asks_for_hook(lowered):
            parts.append(self._hook_block(chunks))
        elif _asks_for_summary(lowered):
            parts.append(self._summary_block(video_a, video_b, chunks))
        elif _asks_for_improvements(lowered):
            parts.append(
                "Practical next steps: tighten the opening hook, move the payoff earlier, remove slow setup, and reuse the clearer structure from the stronger performer where the transcript supports it."
            )
            parts.append(self._evidence_block(chunks, limit=4))
        else:
            parts.append(self._evidence_block(chunks, limit=4))

        parts.append("\nSources:\n" + "\n".join(self._source_lines(chunks)))
        return "\n\n".join(parts)

    def _question_lead(self, video_a: VideoMetadata, video_b: VideoMetadata, lowered: str) -> str:
        if "video a" in lowered and "video b" not in lowered:
            return self._single_video_lead(video_a)
        if "video b" in lowered and "video a" not in lowered:
            return self._single_video_lead(video_b)
        return f"{self._metric_sentence(video_a, video_b)} {self._winner(video_a, video_b)}"

    def _single_video_lead(self, video: VideoMetadata) -> str:
        rate = f"{video.engagement_rate:.2f}%" if video.engagement_rate is not None else "unavailable"
        views = _fmt_int(video.views)
        likes = _fmt_int(video.likes)
        comments = _fmt_int(video.comments)
        return f"Video {video.label} has {views} views, {likes} likes, {comments} comments, and an engagement rate of {rate}."

    def _metrics_block(self, video_a: VideoMetadata, video_b: VideoMetadata) -> str:
        return "\n".join(
            [
                "Metric snapshot:",
                f"- Video A: views={_fmt_int(video_a.views)}, likes={_fmt_int(video_a.likes)}, comments={_fmt_int(video_a.comments)}, engagement={_fmt_rate(video_a.engagement_rate)}",
                f"- Video B: views={_fmt_int(video_b.views)}, likes={_fmt_int(video_b.likes)}, comments={_fmt_int(video_b.comments)}, engagement={_fmt_rate(video_b.engagement_rate)}",
            ]
        )

    def _hook_block(self, chunks: list[TranscriptChunk]) -> str:
        if not chunks:
            return "I do not have transcript chunks for hook analysis, so I can only judge the hook from captions and metadata."
        lines = ["Hook read from the available transcript context:"]
        for chunk in chunks[:3]:
            lines.append(f"- Video {chunk.video_label}: {trim_preview(chunk.text, 180)}")
        lines.append("Treat this as directional when chunks do not include precise first-five-second timestamps.")
        return "\n".join(lines)

    def _summary_block(self, video_a: VideoMetadata, video_b: VideoMetadata, chunks: list[TranscriptChunk]) -> str:
        lines = [
            f"Video A: {trim_preview(video_a.title_or_caption or 'No caption available.', 180)}",
            f"Video B: {trim_preview(video_b.title_or_caption or 'No caption available.', 180)}",
        ]
        if chunks:
            lines.append("Relevant transcript context:")
            lines.extend(f"- Video {chunk.video_label}: {trim_preview(chunk.text, 180)}" for chunk in chunks[:3])
        return "\n".join(lines)

    def _evidence_block(self, chunks: list[TranscriptChunk], limit: int) -> str:
        if not chunks:
            return "No transcript chunks were available, so this answer is limited to metadata."
        lines = ["Most relevant evidence:"]
        lines.extend(f"- Video {chunk.video_label} / Chunk {chunk.chunk_id}: {trim_preview(chunk.text, 220)}" for chunk in chunks[:limit])
        return "\n".join(lines)

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


def _cohere_event_text(event: object) -> str | None:
    text = getattr(event, "text", None)
    if text:
        return str(text)
    delta = getattr(event, "delta", None)
    if delta is not None:
        message = getattr(delta, "message", None)
        content = getattr(message, "content", None)
        if isinstance(content, list):
            parts = [getattr(item, "text", None) for item in content]
            return "".join(str(part) for part in parts if part) or None
        if content is not None:
            content_text = getattr(content, "text", None)
            if content_text:
                return str(content_text)
    if isinstance(event, dict):
        return event.get("text") or (((event.get("delta") or {}).get("message") or {}).get("content") or {}).get("text")
    return None


def _asks_for_metrics(message: str) -> bool:
    return any(term in message for term in ("metric", "views", "likes", "comments", "engagement", "rate", "stats"))


def _asks_for_hook(message: str) -> bool:
    return any(term in message for term in ("hook", "first 3", "first 5", "opening", "intro"))


def _asks_for_summary(message: str) -> bool:
    return any(term in message for term in ("summary", "summarize", "what is", "what are", "about"))


def _asks_for_improvements(message: str) -> bool:
    return any(term in message for term in ("improve", "suggest", "better", "fix", "change", "recommend"))


def _fmt_int(value: int | None) -> str:
    return f"{value:,}" if value is not None else "unavailable"


def _fmt_rate(value: float | None) -> str:
    return f"{value:.2f}%" if value is not None else "unavailable"
