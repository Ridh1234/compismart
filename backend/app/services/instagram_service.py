import logging
import re

import httpx

from app.core.config import settings
from app.core.errors import AppError
from app.schemas.video import TranscriptBundle, TranscriptSegment, VideoMetadata
from app.utils.formatters import parse_hashtags
from app.utils.url_parser import validate_instagram_reel_url


logger = logging.getLogger(__name__)


class InstagramService:
    async def fetch_metadata(self, url: str) -> VideoMetadata:
        validate_instagram_reel_url(url)
        if not settings.apify_token:
            raise AppError(
                "apify_token_missing",
                "APIFY_TOKEN is required to fetch Instagram Reel metadata dynamically.",
                status_code=503,
            )

        items = await self._run_actor_with_fallback(url)
        if not items:
            raise AppError(
                "instagram_metadata_unavailable",
                "Could not fetch metadata for this Instagram Reel. Please use a public Reel URL.",
                status_code=404,
            )

        item = items[0]
        caption = _deep_text(item, "caption", "captionText", "caption_text", "text", "description", "edge_media_to_caption")
        transcript_text = _deep_text(item, "transcript", "videoTranscript", "video_transcript", "subtitles", "captions")
        transcript = TranscriptBundle()
        if transcript_text:
            transcript = TranscriptBundle(
                text=str(transcript_text),
                source_type="scraped_caption",
                segments=[TranscriptSegment(text=str(transcript_text))],
            )

        warnings: list[str] = []
        followers = _to_int(_deep_first(item, "followersCount", "ownerFollowersCount", "profileFollowers", "follower_count", "followers"))
        if followers is None:
            warnings.append("Follower count unavailable from public source.")

        views = _to_int(_deep_first(item, "videoViewCount", "videoPlayCount", "viewsCount", "playCount", "viewCount", "video_view_count"))
        if views is None:
            warnings.append("View count unavailable from public source.")

        return VideoMetadata(
            label="B",
            platform="instagram",
            source_url=url,
            video_id=str(_deep_first(item, "id", "shortCode", "shortcode", "code", "pk") or _code_from_url(url) or ""),
            creator_name=_deep_text(item, "ownerFullName", "fullName", "full_name", "username", "ownerUsername"),
            creator_handle=_deep_text(item, "ownerUsername", "username"),
            follower_count=followers,
            title_or_caption=caption,
            views=views,
            likes=_to_int(_deep_first(item, "likesCount", "likeCount", "like_count", "likes")),
            comments=_to_int(_deep_first(item, "commentsCount", "commentCount", "comment_count", "comments")),
            hashtags=parse_hashtags(str(caption or "")),
            upload_date=_deep_text(item, "timestamp", "takenAt", "taken_at", "createdAt", "date"),
            duration_seconds=_duration_to_seconds(_deep_first(item, "videoDuration", "duration", "video_duration")),
            thumbnail_url=_deep_url(item, "displayUrl", "thumbnailUrl", "imageUrl", "thumbnail_src", "display_url"),
            media_url=_deep_url(item, "videoUrl", "video_url", "video", "videoResources", "video_versions", "playback_url"),
            audio_url=_deep_url(item, "audioUrl", "audio_url", "audio", "audio_url", "clips_music_attribution_info"),
            transcript=transcript,
            warnings=warnings,
        )

    async def _run_actor_with_fallback(self, url: str) -> list[dict]:
        actors = [settings.apify_instagram_actor]
        if settings.apify_instagram_fallback_actor and settings.apify_instagram_fallback_actor not in actors:
            actors.append(settings.apify_instagram_fallback_actor)

        last_error = "No Instagram actor was attempted."
        async with httpx.AsyncClient(timeout=120) as client:
            for actor in actors:
                actor_id = actor.replace("/", "~")
                response = await client.post(
                    f"https://api.apify.com/v2/actors/{actor_id}/run-sync-get-dataset-items",
                    params={"token": settings.apify_token, "clean": "true"},
                    json=_actor_payload(actor, url),
                )
                if response.status_code < 400:
                    logger.info("instagram_actor_succeeded actor=%s", actor_id)
                    return response.json()

                last_error = response.text[:500]
                logger.warning("instagram_actor_failed actor=%s status=%s body=%s", actor_id, response.status_code, last_error)

        raise AppError(
            "instagram_metadata_unavailable",
            f"Could not fetch metadata for this Instagram Reel. Last Apify error: {last_error}",
            status_code=502,
        )


def _actor_payload(actor_name: str, url: str) -> dict:
    if "hpix" in actor_name or "ig-reels-scraper" in actor_name:
        return {
            "post_urls": [url],
            "target": "reels_only",
            "reels_count": 1,
            "include_raw_data": True,
            "skip_pinned": False,
            "proxyConfiguration": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
        }
    return {
        "directUrls": [url],
        "resultsLimit": 1,
        "resultsType": "reels",
        "addParentData": True,
    }


def _first(mapping: dict, *keys: str):
    for key in keys:
        value = mapping.get(key)
        if value not in (None, ""):
            return value
    return None


def _deep_first(value: object, *keys: str, depth: int = 0):
    if depth > 10:
        return None
    if isinstance(value, dict):
        for key in keys:
            direct = value.get(key)
            if direct not in (None, ""):
                return direct
        for nested in value.values():
            found = _deep_first(nested, *keys, depth=depth + 1)
            if found not in (None, ""):
                return found
    if isinstance(value, list):
        for item in value:
            found = _deep_first(item, *keys, depth=depth + 1)
            if found not in (None, ""):
                return found
    return None


def _deep_text(value: object, *keys: str) -> str | None:
    return _text_from_value(_deep_first(value, *keys))


def _text_from_value(value: object) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        parts = [_text_from_value(item) for item in value]
        text = " ".join(part for part in parts if part)
        return text or None
    if isinstance(value, dict):
        for key in ("text", "caption", "title", "value"):
            text = _text_from_value(value.get(key))
            if text:
                return text
        if "edges" in value:
            return _text_from_value(value.get("edges"))
        if "node" in value:
            return _text_from_value(value.get("node"))
    return None


def _first_url(mapping: dict, *keys: str) -> str | None:
    for key in keys:
        value = mapping.get(key)
        url = _extract_url(value)
        if url:
            return url
    return None


def _deep_url(value: object, *keys: str) -> str | None:
    direct = _deep_first(value, *keys)
    return _extract_url(direct)


def _extract_url(value: object) -> str | None:
    if isinstance(value, str):
        return value if value.startswith(("http://", "https://")) else None
    if isinstance(value, list):
        for item in value:
            url = _extract_url(item)
            if url:
                return url
    if isinstance(value, dict):
        for key in ("url", "src", "downloadUrl", "videoUrl", "audioUrl"):
            url = _extract_url(value.get(key))
            if url:
                return url
    return None


def _duration_to_seconds(value: object) -> int | None:
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str) and ":" in value:
        try:
            seconds = 0
            for part in value.split(":"):
                seconds = seconds * 60 + int(part)
            return seconds
        except ValueError:
            return None
    return _to_int(value)


def _code_from_url(url: str) -> str | None:
    match = re.search(r"/(?:reel|reels|p)/([^/?#]+)", url)
    return match.group(1) if match else None


def _to_int(value: object) -> int | None:
    try:
        return int(float(value)) if value is not None else None
    except (TypeError, ValueError):
        return None
