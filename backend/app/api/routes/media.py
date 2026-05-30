from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/media", tags=["media"])

ALLOWED_HOST_HINTS = (
    "cdninstagram.com",
    "fbcdn.net",
    "ytimg.com",
    "googleusercontent.com",
)


@router.get("/proxy")
async def proxy_media(url: str = Query(min_length=8)) -> StreamingResponse:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="Only HTTP(S) media URLs can be proxied.")
    if not any(host in parsed.netloc.lower() for host in ALLOWED_HOST_HINTS):
        raise HTTPException(status_code=400, detail="Media host is not allowed.")

    client = httpx.AsyncClient(timeout=30, follow_redirects=True)
    request = client.build_request(
        "GET",
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        },
    )
    response = await client.send(request, stream=True)
    if response.status_code >= 400:
        await client.aclose()
        raise HTTPException(status_code=502, detail="Could not fetch media.")

    async def body():
        try:
            async for chunk in response.aiter_bytes():
                yield chunk
        finally:
            await response.aclose()
            await client.aclose()

    return StreamingResponse(
        body(),
        media_type=response.headers.get("content-type", "application/octet-stream"),
        headers={"Cache-Control": "public, max-age=600"},
    )
