# CompiSMART

CompiSMART is a full-stack RAG chatbot that compares a YouTube Short and an Instagram Reel using metadata, transcripts, embeddings, vector search, and streaming AI responses. It calculates engagement rates, analyzes hooks and content structure, cites transcript chunks, and gives creator-focused improvement suggestions.

## What It Builds

- A focused React + Vite + TypeScript analytical workspace.
- A FastAPI backend with YouTube, Apify, Cohere, LangChain chunking, and ChromaDB integration points.
- Dynamic metadata extraction for YouTube Shorts and Instagram Reels.
- Transcript-aware RAG with source citations.
- Server-Sent Events streaming for chat responses.
- Session-scoped memory for follow-up questions.
- Graceful handling for missing metrics, captions, transcripts, vectors, or model access.

## Architecture

```text
React workspace
  -> POST /analyze
FastAPI ingestion pipeline
  -> YouTube Data API
  -> Apify Instagram scraper
  -> transcript extraction
  -> engagement calculation
  -> LangChain chunking
  -> Cohere embeddings
  -> ChromaDB session collection
  -> in-memory session state

React chat
  -> POST /chat
FastAPI SSE stream
  -> retrieve transcript chunks
  -> add video metadata + conversation memory
  -> Cohere chat stream
  -> return deltas + citations
```

The project intentionally avoids authentication, accounts, billing, and saved history because the PRD scopes this as an MVP screening project. Session memory is kept in process.

## Repository Structure

```text
backend/
  app/
    api/routes/          FastAPI route handlers
    core/                config, errors, logging
    schemas/             typed request/response models
    services/            platform, transcript, vector, RAG, memory services
    utils/               URL parsing and formatting helpers
  requirements.txt
  .env.example

frontend/
  src/
    App.tsx              product workspace
    lib/                 API client, types, formatters
    styles/main.css      Tailwind entry and base styling
  package.json
  vite.config.ts
```

## Requirements

- Python 3.12
- Node 20+
- YouTube Data API key
- Apify token with access to an Instagram Reel scraper actor
- Cohere API key
- Local Whisper fallback uses the `tiny` model by default and stores it under `backend/.models/whisper`.

## Environment

Backend:

```bash
cd backend
cp .env.example .env
```

Set:

```bash
YOUTUBE_API_KEY=...
APIFY_TOKEN=...
APIFY_INSTAGRAM_ACTOR=hpix/ig-reels-scraper
APIFY_INSTAGRAM_FALLBACK_ACTOR=apify/instagram-scraper
APIFY_YOUTUBE_SHORTS_ACTOR=streamers/youtube-shorts-scraper
COHERE_API_KEY=...
CHROMA_PERSIST_DIR=./.chroma
WHISPER_MODEL_SIZE=tiny
YTDLP_COOKIES_PATH=
```

`YTDLP_COOKIES_PATH` is optional. Use it only if YouTube blocks public media download and you have exported a valid cookies file for `yt-dlp`.

Frontend:

```bash
cd frontend
cp .env.example .env
```

Default:

```bash
VITE_API_BASE_URL=
```

Leaving `VITE_API_BASE_URL` empty lets Vite proxy `/analyze`, `/chat`, `/health`, and `/media` to the local backend during development.

## Local Development

Backend:

```bash
cd backend
bash scripts/bootstrap_backend.sh
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## API

### `GET /health`

```json
{ "status": "ok" }
```

### `POST /analyze`

```json
{
  "video_a_url": "https://youtube.com/shorts/...",
  "video_b_url": "https://instagram.com/reel/..."
}
```

Returns a session ID and typed metadata for both videos, including engagement rate and transcript status.

### `POST /chat`

```json
{
  "session_id": "uuid",
  "message": "Why did Video A perform better?"
}
```

Streams Server-Sent Events:

- `delta`: response text chunk.
- `citations`: transcript chunks used.
- `done`: completion marker.
- `error`: readable failure.

## Data Integrity

The backend does not invent metrics. If a public source or provider does not return a field, the response marks it as unavailable and the UI surfaces the limitation. Engagement rate is calculated only when views, likes, and comments are available:

```text
(likes + comments) / views * 100
```

## Trade-Offs

- ChromaDB is local-first and ideal for demos; production should move to Qdrant or pgvector.
- In-memory session storage keeps the MVP simple; production should use Redis/Postgres.
- Whisper fallback downloads short-form media when captions are unavailable, uses the local `tiny` model for fast CPU transcription, and reuses the model cache after the first download.
- Cohere is the primary embedding and chat provider. The development fallback keeps the app inspectable without keys, but complete assignment behavior requires Cohere credentials.

## Production Upgrade Path

- Add a background worker for ingestion and transcription.
- Cache metadata, transcripts, and embeddings by URL/video hash.
- Persist sessions, messages, and extracted video records in PostgreSQL.
- Replace local ChromaDB with Qdrant or pgvector.
- Add rate limiting, observability, retries, and provider-specific circuit breakers.
- Add auth only when saved history or private workspaces are required.

## Demo Script

1. Open the app at `http://localhost:5173`.
2. Enter one public YouTube Short URL.
3. Enter one public Instagram Reel URL.
4. Click **Analyze Videos**.
5. Show the stepped loading state.
6. Show side-by-side creator cards and engagement rates.
7. Ask: `What is the engagement rate of each?`
8. Ask: `Compare the hooks in the first 5 seconds.`
9. Ask: `Why did Video A perform better?`
10. Ask: `Suggest improvements for Video B.`
11. Point out citations under each answer.
12. Briefly explain the architecture and scalability path.

## Final Submission Fields

Project URL: `[deployed website URL]`

Project Description: `CompiSMART is a full-stack RAG chatbot that compares a YouTube Short and an Instagram Reel using metadata, transcripts, embeddings, vector search, and streaming AI responses. It calculates engagement rates, analyzes hooks and content structure, cites transcript chunks, and provides creator-focused improvement suggestions.`

Loom URL: `[demo video URL]`

GitHub Repo: `[repository URL]`
