# CompiSMART Backend

FastAPI service for dynamic short-form video ingestion, transcript chunking, vector storage, and streaming RAG chat.

## Services

- `YouTubeService`: fetches official YouTube metadata from the YouTube Data API.
- `InstagramService`: fetches public Reel metadata through Apify.
- `TranscriptService`: reads YouTube caption tracks and uses scraped Instagram text when available.
- `TranscriptService`: falls back to local Whisper `tiny` transcription from downloaded media when captions are unavailable.
- `ChunkingService`: chunks transcripts with LangChain text splitting.
- `EmbeddingService`: embeds with Cohere when configured; falls back to local lexical vectors for development retrieval only.
- `VectorStoreService`: stores chunks in ChromaDB and falls back to in-memory lexical retrieval if Chroma is unavailable.
- `RagService`: builds grounded prompts and streams Cohere chat responses with citations.

## Run

```bash
bash scripts/bootstrap_backend.sh
source .venv/bin/activate
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Set `YOUTUBE_API_KEY`, `APIFY_TOKEN`, and `COHERE_API_KEY` in `.env` for the complete dynamic pipeline.
