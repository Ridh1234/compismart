from app.core.config import settings
from app.schemas.video import TranscriptChunk
from app.services.embedding_service import EmbeddingService


class VectorStoreService:
    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()

    async def store_chunks(self, session_id: str, chunks: list[TranscriptChunk]) -> None:
        if not chunks:
            return
        embeddings = await self.embedding_service.embed_texts([chunk.text for chunk in chunks])
        try:
            import chromadb
            from chromadb.config import Settings

            client = chromadb.PersistentClient(
                path=settings.chroma_persist_dir,
                settings=Settings(anonymized_telemetry=False),
            )
            collection = client.get_or_create_collection(name=f"compismart_{session_id}")
            collection.upsert(
                ids=[chunk.chunk_id for chunk in chunks],
                documents=[chunk.text for chunk in chunks],
                embeddings=embeddings,
                metadatas=[
                    {
                        "session_id": chunk.session_id,
                        "video_label": chunk.video_label,
                        "platform": chunk.platform,
                        "chunk_id": chunk.chunk_id,
                        "creator": chunk.creator or "",
                        "source_url": chunk.source_url,
                        "start_time": chunk.start_time or "",
                        "end_time": chunk.end_time or "",
                    }
                    for chunk in chunks
                ],
            )
        except Exception:
            # The in-memory session copy remains available for lexical fallback retrieval.
            return

    async def retrieve(self, session_id: str, query: str, fallback_chunks: list[TranscriptChunk], k: int = 5) -> list[TranscriptChunk]:
        try:
            import chromadb
            from chromadb.config import Settings

            query_embedding = await self.embedding_service.embed_query(query)
            client = chromadb.PersistentClient(
                path=settings.chroma_persist_dir,
                settings=Settings(anonymized_telemetry=False),
            )
            collection = client.get_or_create_collection(name=f"compismart_{session_id}")
            result_count = min(k, collection.count())
            if result_count == 0:
                return self._lexical_retrieve(query, fallback_chunks, k)
            result = collection.query(query_embeddings=[query_embedding], n_results=result_count)
            ids = result.get("ids", [[]])[0]
            documents = result.get("documents", [[]])[0]
            metadatas = result.get("metadatas", [[]])[0]
            chunks: list[TranscriptChunk] = []
            for chunk_id, text, metadata in zip(ids, documents, metadatas):
                chunks.append(
                    TranscriptChunk(
                        chunk_id=chunk_id,
                        session_id=session_id,
                        video_label=metadata.get("video_label"),
                        platform=metadata.get("platform"),
                        text=text,
                        source_url=metadata.get("source_url", ""),
                        creator=metadata.get("creator") or None,
                    )
                )
            if chunks:
                return chunks
        except Exception:
            pass
        return self._lexical_retrieve(query, fallback_chunks, k)

    def _lexical_retrieve(self, query: str, chunks: list[TranscriptChunk], k: int) -> list[TranscriptChunk]:
        query_terms = {term.strip(".,?!:;()[]{}").lower() for term in query.split() if len(term) > 2}
        scored: list[tuple[int, TranscriptChunk]] = []
        for chunk in chunks:
            terms = set(chunk.text.lower().split())
            score = len(query_terms & terms)
            scored.append((score, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _, chunk in scored[:k]]
