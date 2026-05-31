from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analysis, chat, health, media
from app.core.config import settings
from app.core.logging import configure_logging


configure_logging()


app = FastAPI(
    title="CompiSMART API",
    version="1.0.0",
    description="Full-stack RAG API for comparing a YouTube Short and an Instagram Reel.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok", "service": "compismart-api"}

app.include_router(health.router)
app.include_router(analysis.router)
app.include_router(chat.router)
app.include_router(media.router)
