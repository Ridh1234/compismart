# CompiSMART PRD

## Full-Stack RAG Chatbot for Comparing YouTube Shorts and Instagram Reels

---

## 1. Product Summary

CompiSMART is a full-stack AI application that helps creators compare the performance of two short-form videos: one YouTube Short and one Instagram Reel.

The user provides two video URLs. The system dynamically extracts metadata, transcript, engagement metrics, and creator information for both videos. It then builds a RAG knowledge base from the transcripts and metadata so the user can ask natural language questions about why one video performed better than the other.

The product is not a generic chatbot. It is a creator-performance analysis tool powered by retrieval, structured video metadata, and conversational reasoning.

---

## 2. Core Objective

Build a working full-stack RAG chatbot that can:

1. Accept one YouTube Short URL and one Instagram Reel URL.
2. Fetch metadata and transcript for both videos.
3. Calculate engagement rate for both videos.
4. Chunk and embed transcripts.
5. Store transcript chunks in a vector database.
6. Provide a streaming chat interface.
7. Answer creator-focused questions using RAG.
8. Cite the source video and transcript chunk used in each answer.
9. Maintain conversation memory across turns.

---

## 3. Scope

### In Scope

The application must include:

* URL input for YouTube Shorts and Instagram Reels.
* Dynamic video metadata extraction.
* Transcript extraction.
* Fallback transcription when transcript is unavailable.
* Engagement rate calculation.
* Transcript chunking.
* Embedding generation.
* Vector database storage.
* RAG-based question answering.
* Streaming AI responses.
* Source citations.
* Conversation memory.
* Side-by-side video comparison UI.
* Clean README explaining architecture, trade-offs, setup, and scalability.

### Out of Scope

The following are not required for the first version:

* User authentication.
* Billing.
* User accounts.
* Saved history.
* Admin dashboard.
* Multi-user workspace.
* Video editing.
* Video uploading.
* Social media posting.
* Production-grade analytics dashboard.
* Long-term persistent user storage.

Authentication is intentionally excluded because it is not required in the assignment and would add unnecessary complexity.

---

## 4. Target User

The primary user is a short-form video creator, creator strategist, or social media analyst who wants to understand why one video performed better than another.

They want answers like:

* Why did Video A get more engagement than Video B?
* What did the stronger video do better in the opening hook?
* Which video had a clearer structure?
* Which creator had higher audience leverage?
* What should be changed in the weaker video?

---

## 5. User Journey

### Step 1: Landing Page

The user opens the application and sees a focused comparison screen.

They are shown:

* Product name.
* Short explanation.
* Input field for Video A: YouTube Short URL.
* Input field for Video B: Instagram Reel URL.
* Analyze button.

The interface should immediately communicate that this is a comparison tool, not a general chatbot.

---

### Step 2: User Enters Video URLs

The user enters:

* A YouTube Short URL.
* An Instagram Reel URL.

The system should validate that:

* Video A is a valid YouTube URL.
* Video B is a valid Instagram Reel URL.
* Both fields are present.

If validation fails, the user receives a clear inline error message.

Example:

“Please enter a valid Instagram Reel URL for Video B.”

---

### Step 3: User Starts Analysis

The user clicks Analyze.

The frontend sends both URLs to the backend through the `/analyze` endpoint.

During processing, the frontend shows a clear step-based loading state:

1. Fetching video metadata.
2. Extracting transcripts.
3. Calculating engagement.
4. Building knowledge base.
5. Preparing chat.

This is important because metadata extraction and transcription may take time.

---

### Step 4: Backend Processes Both Videos

The backend performs an end-to-end ingestion pipeline.

For each video, it extracts:

* Platform.
* Creator name.
* Follower or subscriber count if available.
* Title or caption.
* Views.
* Likes.
* Comments.
* Hashtags.
* Upload date.
* Duration.
* Transcript.
* Transcript source.

Then it calculates engagement rate:

Engagement Rate = (likes + comments) / views × 100

---

### Step 5: Backend Builds RAG Knowledge Base

The transcript of each video is split into chunks.

Each chunk is tagged with:

* Session ID.
* Video label: A or B.
* Platform.
* Creator.
* Chunk ID.
* Start timestamp if available.
* End timestamp if available.
* Original transcript text.

The chunks are embedded using Cohere embeddings and stored in ChromaDB.

---

### Step 6: User Enters Analysis Workspace

After analysis completes, the user is taken to the main workspace.

The workspace contains:

* Left panel: Video A details.
* Center panel: Chat interface.
* Right panel: Video B details.

The page should feel like a professional analytical workspace.

---

### Step 7: User Chats with the System

The user can ask questions such as:

* Why did Video A get more engagement than Video B?
* What is the engagement rate of each?
* Compare the hooks in the first five seconds.
* Who is the creator of Video B and what is their follower count?
* Suggest improvements for Video B based on what worked in Video A.

The system retrieves relevant transcript chunks and metadata, sends them to the LLM, and streams a response back to the frontend.

---

## 6. Functional Requirements

## 6.1 URL Input

The application must provide two URL inputs:

* YouTube Short URL.
* Instagram Reel URL.

Requirements:

* Inputs must be clearly labeled.
* User should not be confused about which video is A or B.
* Validation must happen before analysis starts.
* Invalid URLs should show helpful errors.
* The Analyze button should be disabled during processing.

---

## 6.2 Video Metadata Extraction

The system must extract metadata dynamically.

### YouTube Metadata

Use YouTube Data API.

Required fields:

* Video ID.
* Title.
* Channel name.
* Channel ID.
* View count.
* Like count.
* Comment count.
* Published date.
* Duration.
* Subscriber count if available.
* Description.
* Hashtags if available.

### Instagram Reel Metadata

Use Apify Instagram scraper.

Required fields where available:

* Reel URL.
* Creator username.
* Creator display name if available.
* Follower count if available.
* Caption.
* Like count.
* Comment count.
* View count or play count.
* Upload date.
* Duration.
* Hashtags.
* Thumbnail if available.

If a field is unavailable, the system should not fake it. It should mark it as unavailable.

Example:

“Follower count unavailable from public source.”

---

## 6.3 Transcript Extraction

The system must retrieve or generate transcripts for both videos.

### YouTube Transcript

Use one or more of:

* YouTube transcript API.
* Captions if available.
* Whisper fallback if transcript is unavailable.

### Instagram Transcript

Instagram Reels usually do not expose reliable public transcripts.

Use:

* Apify transcript field if available.
* Otherwise download audio/video if available.
* Use Whisper or another transcription fallback.

Transcript output should include:

* Text.
* Source type.
* Timestamp segments if available.

Possible transcript source values:

* official_caption
* scraped_caption
* whisper_generated
* unavailable

If transcript extraction fails completely, the system should still continue with metadata-only analysis, but it should clearly tell the user that transcript-level analysis is limited.

---

## 6.4 Engagement Calculation

The backend must calculate engagement rate for each video.

Formula:

Engagement Rate = (likes + comments) / views × 100

Rules:

* If views are unavailable, engagement rate should be marked unavailable.
* If likes or comments are unavailable, show partial data clearly.
* Do not invent missing numbers.
* Format engagement rate to two decimal places.

Example output:

Video A Engagement Rate: 6.42%

Video B Engagement Rate: 3.18%

---

## 6.5 Chunking

Use LangChain text splitting.

Recommended chunking configuration:

* Chunk size: 500 characters.
* Chunk overlap: 100 characters.

Each transcript chunk must be stored with metadata.

Example chunk ID format:

* A-001
* A-002
* B-001
* B-002

Each chunk must preserve the source video label.

---

## 6.6 Embeddings

Use Cohere embeddings.

Recommended model:

* embed-english-v3.0

The embedding service should:

* Accept transcript chunks.
* Generate vector embeddings.
* Store vectors in ChromaDB.
* Preserve metadata for retrieval and citation.

---

## 6.7 Vector Database

Use ChromaDB for the MVP.

Reason:

* Free.
* Local-first.
* Simple setup.
* Good for demo and screening project.
* No external vector database account required.

Each collection should be scoped by session.

Collection naming example:

compismart_{session_id}

Stored document metadata must include:

* session_id
* video_label
* platform
* chunk_id
* creator
* source_url
* start_time
* end_time

---

## 6.8 RAG Chat

The chat system must use LangChain or LangGraph.

For each user question, the backend should:

1. Receive user message and session ID.
2. Load conversation history.
3. Retrieve relevant transcript chunks from ChromaDB.
4. Add structured metadata for both videos.
5. Build a grounded prompt.
6. Call Cohere LLM.
7. Stream answer to frontend.
8. Return citations.

The answer must be based on:

* Retrieved transcript chunks.
* Extracted metadata.
* Engagement calculations.
* Previous conversation context.

The model should avoid unsupported claims.

---

## 6.9 Source Citations

Every answer should include source references.

Citation format:

* Video A / Chunk A-001
* Video B / Chunk B-003
* Video A / Metadata
* Video B / Metadata

Example answer ending:

Sources:

* Video A / Chunk A-001
* Video B / Chunk B-001
* Video A / Metadata

The UI should display citations visually under each AI response.

---

## 6.10 Streaming Responses

The chat response must stream token-by-token or chunk-by-chunk to the frontend.

The user should see the answer being generated live.

This is required for a modern AI product feel and is explicitly mentioned in the assignment.

---

## 6.11 Conversation Memory

The system must remember prior conversation turns within the current session.

Example:

User: “Why did A perform better?”

Assistant: Gives answer.

User: “Now improve B.”

The assistant should understand that B means Video B from the current comparison.

Memory does not need to persist after the session ends.

---

# 7. Frontend Product Requirements

## 7.1 Design Direction

The frontend should not look like a rushed AI-generated demo.

It should feel:

* Minimal.
* Premium.
* Calm.
* Analytical.
* Fast.
* Professional.

Avoid:

* Excessive gradients.
* Cartoon icons.
* Neon effects.
* Heavy animations.
* Cluttered dashboards.
* Over-designed “vibe-coded” UI.

Reference feeling:

* Linear.
* Stripe.
* Vercel.
* Perplexity.
* Notion.

---

## 7.2 Visual Style

### Color Palette

Background:

#0B0D10

Surface:

#111418

Elevated Surface:

#151A20

Border:

#242A32

Primary Text:

#F8FAFC

Secondary Text:

#AAB4C0

Muted Text:

#6B7280

Accent Blue:

#4F8CFF

Success Green:

#22C55E

Warning Amber:

#F59E0B

Error Red:

#EF4444

---

## 7.3 Typography

Primary font:

Inter

Fallback:

system-ui, sans-serif

Typography scale:

* Page title: 36px / 44px
* Section title: 22px / 30px
* Card title: 16px / 24px
* Body: 15px / 24px
* Metadata: 13px / 20px
* Citation text: 12px / 18px

Text should feel readable and spacious.

---

## 7.4 Layout

Desktop layout:

Three-column workspace.

Left:

Video A card.

Center:

Chat panel.

Right:

Video B card.

Recommended width distribution:

* Left: 28%
* Center: 44%
* Right: 28%

Mobile layout:

* Inputs on top.
* Video cards stacked.
* Chat below.
* Sticky chat input.

---

## 7.5 Landing Page UI

Landing page sections:

### Header

* Logo: CompiSMART
* Small tagline: Compare short-form videos with AI.

No navigation needed.

### Hero Section

Headline:

“Understand why one short-form video outperformed another.”

Subheadline:

“Compare a YouTube Short and an Instagram Reel using transcripts, engagement metrics, and RAG-powered creator analysis.”

### Input Panel

Two inputs:

* YouTube Short URL
* Instagram Reel URL

Button:

Analyze Videos

### Trust/Feature Row

Small feature chips:

* Dynamic metadata
* Transcript RAG
* Engagement scoring
* Source citations
* Streaming chat

---

## 7.6 Loading Experience

After clicking Analyze, show a processing card.

Steps:

1. Reading video URLs.
2. Fetching metadata.
3. Extracting transcripts.
4. Creating embeddings.
5. Building comparison workspace.

Each step should show:

* Pending
* In progress
* Done
* Failed if error occurs

This makes the app feel reliable even if processing takes time.

---

## 7.7 Video Comparison Cards

Each video card should show:

* Platform badge.
* Video label: Video A or Video B.
* Creator name.
* Follower/subscriber count.
* Views.
* Likes.
* Comments.
* Engagement rate.
* Upload date.
* Duration.
* Hashtags.
* Transcript availability.
* Short transcript preview.

Important metric:

Engagement rate should be visually emphasized.

Example:

Engagement Rate

6.42%

---

## 7.8 Chat Panel

The chat panel should include:

* Suggested questions.
* Message history.
* Streaming assistant response.
* Source citations.
* Chat input.

Suggested questions:

* Why did A perform better?
* Compare the first 5 seconds.
* What is each engagement rate?
* Improve Video B.
* Compare the hooks.
* Compare clarity and pacing.

User should be able to click a suggested question and send it instantly.

---

## 7.9 Empty States

Before analysis:

“Enter one YouTube Short and one Instagram Reel to begin.”

If transcript unavailable:

“Transcript was unavailable for this video. Analysis will rely on metadata and caption.”

If metadata partially unavailable:

“Some Instagram metrics were unavailable from public sources.”

---

## 7.10 Error States

Errors should be readable and non-technical.

Examples:

Invalid YouTube URL:

“Video A must be a valid YouTube Short URL.”

Instagram scrape failed:

“We could not fetch Instagram metadata for this Reel. Try a public Reel URL.”

Transcript failed:

“We could not generate a transcript. Metadata analysis is still available.”

Backend unavailable:

“Analysis service is currently unreachable. Please try again.”

---

# 8. Backend Product Requirements

## 8.1 Backend Stack

Use:

* Python 3.12
* FastAPI
* LangChain
* ChromaDB
* Cohere
* YouTube Data API
* Apify
* Whisper fallback if feasible

---

## 8.2 Backend Folder Structure

Recommended structure:

backend/

app/

main.py

api/

routes/

analysis.py

chat.py

health.py

schemas/

analysis.py

chat.py

video.py

services/

youtube_service.py

instagram_service.py

transcript_service.py

engagement_service.py

chunking_service.py

embedding_service.py

vectorstore_service.py

rag_service.py

memory_service.py

core/

config.py

logging.py

errors.py

utils/

url_parser.py

formatters.py

requirements.txt

.env.example

README.md

---

## 8.3 Environment Variables

Required:

YOUTUBE_API_KEY

APIFY_TOKEN

COHERE_API_KEY

CHROMA_PERSIST_DIR

Optional:

COHERE_CHAT_MODEL

COHERE_EMBED_MODEL

WHISPER_MODEL_SIZE

ENVIRONMENT

LOG_LEVEL

---

## 8.4 API Endpoints

### GET /health

Purpose:

Check if backend is running.

Response:

{
"status": "ok"
}

---

### POST /analyze

Purpose:

Analyze both videos and create a RAG session.

Request:

{
"video_a_url": "https://youtube.com/shorts/...",
"video_b_url": "https://instagram.com/reel/..."
}

Response:

{
"session_id": "uuid",
"video_a": {
"label": "A",
"platform": "youtube",
"creator": "...",
"views": 100000,
"likes": 8000,
"comments": 300,
"engagement_rate": 8.3,
"duration": "00:00:31",
"upload_date": "...",
"hashtags": [],
"transcript_status": "available"
},
"video_b": {
"label": "B",
"platform": "instagram",
"creator": "...",
"views": 75000,
"likes": 3000,
"comments": 120,
"engagement_rate": 4.16,
"duration": "00:00:27",
"upload_date": "...",
"hashtags": [],
"transcript_status": "available"
}
}

---

### POST /chat

Purpose:

Ask questions about the analyzed videos.

Request:

{
"session_id": "uuid",
"message": "Why did Video A perform better?"
}

Response:

Streaming response containing:

* Generated text.
* Citations.
* Retrieved chunks.

Implementation may use Server-Sent Events.

---

## 8.5 Internal Data Models

### VideoMetadata

Fields:

* label
* platform
* source_url
* creator_name
* creator_handle
* follower_count
* title_or_caption
* views
* likes
* comments
* hashtags
* upload_date
* duration_seconds
* engagement_rate
* thumbnail_url

---

### TranscriptChunk

Fields:

* chunk_id
* session_id
* video_label
* platform
* text
* start_time
* end_time
* source_url

---

### ChatMessage

Fields:

* role
* content
* timestamp

---

### Citation

Fields:

* video_label
* chunk_id
* platform
* text_preview

---

## 8.6 Backend Processing Pipeline

### Pipeline Overview

Input URLs

↓

Validate URLs

↓

Detect platforms

↓

Fetch YouTube metadata

↓

Fetch Instagram metadata

↓

Fetch or generate transcripts

↓

Calculate engagement

↓

Chunk transcripts

↓

Generate embeddings

↓

Store chunks in ChromaDB

↓

Create session

↓

Return structured video comparison data

---

## 8.7 RAG Prompting Requirements

The RAG prompt should include:

* User question.
* Video A metadata.
* Video B metadata.
* Retrieved chunks.
* Conversation history.
* Clear instruction to avoid unsupported claims.
* Clear instruction to cite sources.

The assistant should answer like a creator strategist, not like a generic chatbot.

Tone:

* Clear.
* Practical.
* Analytical.
* Direct.
* Useful.

---

## 8.8 RAG Answer Requirements

Responses should:

* Directly answer the question.
* Use engagement data when relevant.
* Compare Video A and Video B explicitly.
* Mention uncertainty when data is missing.
* Include practical improvement suggestions.
* Cite chunks and metadata.
* Avoid hallucinating unavailable metrics.

---

## 8.9 Memory Requirements

Store memory in process for MVP.

Memory should be session-scoped.

Each session stores:

* User messages.
* Assistant messages.
* Video metadata.
* RAG collection reference.

No long-term persistence required.

---

## 8.10 Error Handling

Backend should handle:

* Invalid URLs.
* YouTube API failure.
* Apify failure.
* Missing metadata.
* Missing transcript.
* Embedding failure.
* Vector DB failure.
* LLM failure.

Errors should return clean API responses.

Example:

{
"error": "instagram_metadata_unavailable",
"message": "Could not fetch metadata for this Instagram Reel. Please use a public Reel URL."
}

---

# 9. System Architecture

## High-Level Architecture

Frontend

↓

FastAPI Backend

↓

Platform Services

* YouTube Service
* Instagram Service

↓

Transcript Service

↓

Engagement Service

↓

LangChain Chunking

↓

Cohere Embeddings

↓

ChromaDB

↓

LangChain RAG Chain

↓

Cohere Chat Model

↓

Streaming Response

↓

Frontend Chat UI

---

# 10. Technology Choices

## Frontend

React + Vite + TypeScript

Reason:

Fast development, simple deployment, lightweight, good for single-page AI apps.

TailwindCSS

Reason:

Fast styling, consistent spacing, easy responsive design.

TanStack Query

Reason:

Clean API state management for analysis and chat flows.

---

## Backend

FastAPI

Reason:

Fast Python API framework, async support, clean docs, good for AI backends.

LangChain

Reason:

Required by assignment and useful for chunking, retrieval, prompt orchestration, and RAG pipeline.

ChromaDB

Reason:

Free, local-first, easy to run in a demo, no external infra needed.

Cohere

Reason:

Single provider for both embeddings and chat generation. Reduces integration complexity.

YouTube Data API

Reason:

Official way to fetch YouTube video metadata.

Apify

Reason:

Reliable way to fetch Instagram Reel data within deadline without building fragile scraping infrastructure.

---

# 11. Scalability and Cost Strategy

For MVP, the system can run synchronously.

For production at 1000 creators per day:

### Main Cost Controls

1. Cache video metadata by URL.
2. Cache transcripts by URL.
3. Cache embeddings by video hash.
4. Avoid reprocessing the same video.
5. Use background workers for long-running transcription.
6. Use cheaper models for simple metadata Q&A.
7. Use LLM only when the user asks chat questions.
8. Use batch embedding requests.
9. Store transcript chunks once and reuse them.
10. Move from ChromaDB to Qdrant or pgvector for production.

---

## 12. Production Upgrade Path

MVP:

* FastAPI
* ChromaDB
* In-memory sessions

Production:

* FastAPI
* PostgreSQL
* Redis
* Qdrant or pgvector
* Celery/RQ workers
* Object storage for media/transcripts
* Persistent sessions
* Rate limiting
* Authentication
* Logging and monitoring

Authentication should only be added in production when users need saved history or private workspaces.

---

# 13. Acceptance Criteria

The project is complete when:

1. User can enter one YouTube Short and one Instagram Reel.
2. Backend dynamically fetches metadata for both.
3. Backend extracts or generates transcripts.
4. Engagement rate is calculated correctly.
5. Transcript chunks are embedded and stored in ChromaDB.
6. Chat answers use RAG.
7. Chat responses stream.
8. Answers include citations.
9. Chat maintains memory in the same session.
10. Frontend shows side-by-side video cards.
11. UI is clean, minimal, and responsive.
12. README explains setup, architecture, trade-offs, cost, and scalability.
13. Demo works from start to finish without hard-coded outputs.

---

# 14. Demo Requirements

The final demo should show:

1. Opening the website.
2. Entering one YouTube Short URL.
3. Entering one Instagram Reel URL.
4. Clicking Analyze.
5. Seeing metadata and engagement rate for both.
6. Asking: “What is the engagement rate of each?”
7. Asking: “Compare the hooks in the first 5 seconds.”
8. Asking: “Why did Video A perform better?”
9. Asking: “Suggest improvements for Video B.”
10. Showing citations in the answers.
11. Showing streaming responses.
12. Briefly explaining architecture and scalability.

---

# 15. Final Submission Format

Project URL

[deployed website URL]

Project Description

CompiSMART is a full-stack RAG chatbot that compares a YouTube Short and an Instagram Reel using metadata, transcripts, embeddings, vector search, and streaming AI responses. It calculates engagement rates, analyzes hooks and content structure, cites transcript chunks, and provides creator-focused improvement suggestions.

Loom URL

[demo video URL]

GitHub Repo

[repository URL]

---

# 16. Implementation Priority

Build in this order:

1. Backend health endpoint.
2. Frontend landing page.
3. YouTube metadata service.
4. Instagram metadata service with Apify.
5. Transcript extraction.
6. Engagement calculation.
7. Chunking.
8. Cohere embeddings.
9. ChromaDB storage.
10. RAG chat endpoint.
11. Streaming response.
12. Frontend analysis workspace.
13. Source citation display.
14. Error handling.
15. README and Loom demo script.

---

# 17. Engineering Principle

The project should be built like a real internal engineering tool.

Every feature should be dynamic.

No fake outputs.

No hard-coded analysis.

No pretending missing data exists.

The system should gracefully handle unavailable metadata and explain limitations clearly.

The final result should demonstrate not just AI prompting, but practical engineering judgment.
