import hashlib
import math

from app.core.config import settings


class EmbeddingService:
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if settings.cohere_api_key:
            try:
                import cohere

                client = cohere.Client(settings.cohere_api_key)
                response = client.embed(
                    texts=texts,
                    model=settings.cohere_embed_model,
                    input_type="search_document",
                )
                return [list(vector) for vector in response.embeddings]
            except Exception:
                pass
        return [self._local_embedding(text) for text in texts]

    async def embed_query(self, text: str) -> list[float]:
        if settings.cohere_api_key:
            try:
                import cohere

                client = cohere.Client(settings.cohere_api_key)
                response = client.embed(
                    texts=[text],
                    model=settings.cohere_embed_model,
                    input_type="search_query",
                )
                return list(response.embeddings[0])
            except Exception:
                pass
        return self._local_embedding(text)

    def _local_embedding(self, text: str, dims: int = 384) -> list[float]:
        vector = [0.0] * dims
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:2], "big") % dims
            vector[index] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]
