from dataclasses import dataclass, field

from app.schemas.video import ChatMessage, TranscriptChunk, VideoMetadata


@dataclass
class SessionState:
    session_id: str
    video_a: VideoMetadata
    video_b: VideoMetadata
    chunks: list[TranscriptChunk] = field(default_factory=list)
    messages: list[ChatMessage] = field(default_factory=list)


class MemoryService:
    _sessions: dict[str, SessionState] = {}

    def create_session(self, state: SessionState) -> None:
        self._sessions[state.session_id] = state

    def get_session(self, session_id: str) -> SessionState | None:
        return self._sessions.get(session_id)

    def add_message(self, session_id: str, message: ChatMessage) -> None:
        session = self.get_session(session_id)
        if session:
            session.messages.append(message)
