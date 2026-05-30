import logging

import httpx

from app.core.config import settings
from app.core.errors import AppError
from app.schemas.video import TranscriptBundle, TranscriptSegment, VideoMetadata
from app.utils.formatters import parse_hashtags, seconds_from_iso8601_duration
from app.utils.url_parser import parse_youtube_video_id


logger = logging.getLogger(__name__)


class YouTubeService:
    async def fetch_metadata(self, url: str) -> VideoMetadata:
        video_id = parse_youtube_video_id(url)
        if not settings.youtube_api_key:
            raise AppError(
                "youtube_api_key_missing",
                "YOUTUBE_API_KEY is required to fetch YouTube metadata dynamically.",
                status_code=503,
            )

        async with httpx.AsyncClient(timeout=25) as client:
            video_resp = await client.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params={
                    "part": "snippet,statistics,contentDetails",
                    "id": video_id,
                    "key": settings.youtube_api_key,
                },
            )
            video_resp.raise_for_status()
            data = video_resp.json()
            items = data.get("items", [])
            if not items:
                raise AppError("youtube_video_not_found", "Could not fetch YouTube metadata for Video A.", 404)

            item = items[0]
            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})
            content = item.get("contentDetails", {})
            channel_id = snippet.get("channelId")
            subscribers = None

            if channel_id:
                channel_resp = await client.get(
                    "https://www.googleapis.com/youtube/v3/channels",
                    params={
                        "part": "statistics",
                        "id": channel_id,
                        "key": settings.youtube_api_key,
                    },
                )
                if channel_resp.status_code == 200:
                    channel_items = channel_resp.json().get("items", [])
                    if channel_items:
                        raw = channel_items[0].get("statistics", {}).get("subscriberCount")
                        subscribers = int(raw) if raw is not None else None

        description = snippet.get("description") or ""
        title = snippet.get("title")
        video = VideoMetadata(
            label="A",
            platform="youtube",
            source_url=url,
            video_id=video_id,
            creator_name=snippet.get("channelTitle"),
            creator_handle=channel_id,
            follower_count=subscribers,
            title_or_caption=title,
            views=_to_int(statistics.get("viewCount")),
            likes=_to_int(statistics.get("likeCount")),
            comments=_to_int(statistics.get("commentCount")),
            hashtags=parse_hashtags(f"{title or ''} {description}"),
            upload_date=snippet.get("publishedAt"),
            duration_seconds=seconds_from_iso8601_duration(content.get("duration")),
            thumbnail_url=((snippet.get("thumbnails") or {}).get("high") or {}).get("url"),
            warnings=[] if subscribers is not None else ["Subscriber count unavailable from public source."],
        )
        return await self._enrich_with_apify_short(video, channel_id, video_id, snippet.get("publishedAt"))

    async def _enrich_with_apify_short(
        self,
        video: VideoMetadata,
        channel_id: str | None,
        video_id: str,
        published_at: str | None,
    ) -> VideoMetadata:
        if not settings.apify_token or not channel_id:
            return video

        actor_id = settings.apify_youtube_shorts_actor.replace("/", "~")
        payload = {
            "channels": [f"https://www.youtube.com/channel/{channel_id}"],
            "maxResultsShorts": settings.apify_youtube_shorts_max_results,
            "sortChannelShortsBy": "OLDEST" if published_at else "NEWEST",
        }
        if published_at:
            payload["oldestPostDate"] = published_at[:10]

        try:
            async with httpx.AsyncClient(timeout=180) as client:
                response = await client.post(
                    f"https://api.apify.com/v2/actors/{actor_id}/run-sync-get-dataset-items",
                    params={"token": settings.apify_token, "clean": "true"},
                    json=payload,
                )
            if response.status_code >= 400:
                logger.warning("youtube_apify_enrichment_failed status=%s body=%s", response.status_code, response.text[:300])
                video.warnings.append("YouTube Shorts Apify enrichment failed; using YouTube Data API metadata.")
                return video

            items = response.json()
            match = _find_short_item(items, video_id)
            if not match:
                logger.warning("youtube_apify_enrichment_no_match video_id=%s items=%s", video_id, len(items))
                video.warnings.append("YouTube Shorts Apify enrichment did not find the requested Short.")
                return video

            video.creator_name = _first(match, "channelName") or video.creator_name
            video.creator_handle = _first(match, "channelUsername", "channelId") or video.creator_handle
            video.follower_count = _to_int(_first(match, "numberOfSubscribers")) or video.follower_count
            video.title_or_caption = _first(match, "title", "text") or video.title_or_caption
            video.views = _to_int(_first(match, "viewCount", "views")) or video.views
            video.likes = _to_int(_first(match, "likes", "likeCount")) or video.likes
            video.comments = _to_int(_first(match, "commentsCount", "commentCount")) or video.comments
            video.upload_date = _first(match, "date") or video.upload_date
            video.duration_seconds = _duration_to_seconds(_first(match, "duration")) or video.duration_seconds
            video.thumbnail_url = _first(match, "thumbnailUrl") or video.thumbnail_url
            video.hashtags = _hashtags_from_item(match) or video.hashtags

            transcript = _transcript_from_subtitles(_first(match, "subtitles"))
            if transcript:
                video.transcript = transcript
                video.warnings.append("YouTube transcript was loaded from Apify Shorts subtitles.")
            else:
                video.warnings.append("YouTube Shorts Apify metadata loaded, but no subtitle transcript was provided.")
            return video
        except Exception as exc:
            logger.exception("youtube_apify_enrichment_exception video_id=%s", video_id)
            video.warnings.append(f"YouTube Shorts Apify enrichment failed: {exc}")
            return video


def _to_int(value: object) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _first(mapping: dict, *keys: str):
    for key in keys:
        value = mapping.get(key)
        if value not in (None, ""):
            return value
    return None


def _find_short_item(items: list[dict], video_id: str) -> dict | None:
    for item in items:
        item_id = str(_first(item, "id", "videoId", "video_id") or "")
        url = str(_first(item, "url", "fromYTUrl") or "")
        if item_id == video_id or f"/{video_id}" in url or f"v={video_id}" in url:
            return item
    return None


def _hashtags_from_item(item: dict) -> list[str]:
    value = _first(item, "hashtags")
    if isinstance(value, list):
        tags = [str(tag) for tag in value if str(tag).strip()]
        return [tag if tag.startswith("#") else f"#{tag}" for tag in tags]
    return parse_hashtags(f"{_first(item, 'title', 'text') or ''}")


def _duration_to_seconds(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    parts = str(value).split(":")
    try:
        numbers = [int(part) for part in parts]
    except ValueError:
        return None
    seconds = 0
    for number in numbers:
        seconds = seconds * 60 + number
    return seconds


def _transcript_from_subtitles(value: object) -> TranscriptBundle | None:
    segments = _subtitle_segments(value)
    text = " ".join(segment.text for segment in segments).strip()
    if not text:
        return None
    return TranscriptBundle(text=text, source_type="scraped_caption", segments=segments)


def _subtitle_segments(value: object) -> list[TranscriptSegment]:
    if isinstance(value, str):
        stripped = value.strip()
        return [TranscriptSegment(text=stripped)] if stripped else []
    if isinstance(value, list):
        segments: list[TranscriptSegment] = []
        for item in value:
            if isinstance(item, dict):
                text = str(_first(item, "text", "caption", "line", "value") or "").strip()
                if text:
                    start = _to_float(_first(item, "start", "startTime", "offset"))
                    end = _to_float(_first(item, "end", "endTime"))
                    duration = _to_float(_first(item, "duration"))
                    segments.append(TranscriptSegment(text=text, start_time=start, end_time=end or ((start or 0) + duration if duration else None)))
            else:
                segments.extend(_subtitle_segments(item))
        return segments
    if isinstance(value, dict):
        for key in ("items", "segments", "subtitles", "captions", "lines"):
            if key in value:
                return _subtitle_segments(value[key])
        text = str(_first(value, "text", "caption", "value") or "").strip()
        return [TranscriptSegment(text=text)] if text else []
    return []


def _to_float(value: object) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
