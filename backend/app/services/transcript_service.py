import asyncio
import json
import logging
import re
import shutil
import hashlib
import os
from pathlib import Path
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.schemas.video import TranscriptBundle, TranscriptSegment, VideoMetadata


logger = logging.getLogger(__name__)


class TranscriptService:
    _last_media_error: str | None = None

    async def attach_transcript(self, video: VideoMetadata) -> VideoMetadata:
        logger.info("transcript_attach_started label=%s platform=%s", video.label, video.platform)
        if video.transcript.text:
            logger.info("transcript_attach_skipped label=%s reason=existing_transcript", video.label)
            return video

        if video.platform == "youtube" and video.video_id:
            bundle = await self._youtube_transcript(video.video_id)
            if bundle.source_type != "unavailable":
                video.transcript = bundle
                return video

            ytdlp_caption_bundle = await self._ytdlp_subtitle_transcript(video.source_url)
            if ytdlp_caption_bundle.source_type != "unavailable":
                video.transcript = ytdlp_caption_bundle
                video.warnings.append("YouTube subtitles were loaded through yt-dlp caption metadata.")
                return video

            whisper_bundle = await self._whisper_transcript(video)
            if whisper_bundle.source_type != "unavailable":
                video.transcript = whisper_bundle
                video.warnings.append("No YouTube caption track was available; Whisper generated the transcript.")
                return video

            video.transcript = bundle
            if whisper_bundle.warning:
                video.warnings.append(whisper_bundle.warning)
            video.warnings.append("Transcript was unavailable for this YouTube Short.")
            return video

        whisper_bundle = await self._whisper_transcript(video)
        if whisper_bundle.source_type != "unavailable":
            video.transcript = whisper_bundle
            video.warnings.append("Whisper generated the transcript from downloaded media.")
            return video
        if whisper_bundle.warning:
            video.warnings.append(whisper_bundle.warning)

        fallback = video.title_or_caption or ""
        if fallback:
            video.transcript = TranscriptBundle(
                text=fallback,
                source_type="scraped_caption",
                segments=[TranscriptSegment(text=fallback)],
                warning="Caption used because a full transcript was unavailable.",
            )
            video.warnings.append("Full transcript unavailable; caption-level analysis will be used.")
        else:
            video.transcript = TranscriptBundle(
                source_type="unavailable",
                warning="Transcript was unavailable for this video.",
            )
            video.warnings.append("Transcript unavailable; analysis will rely on metadata.")
        return video

    async def _youtube_transcript(self, video_id: str) -> TranscriptBundle:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi

            entries = YouTubeTranscriptApi.get_transcript(video_id)
            segments = [
                TranscriptSegment(
                    text=item.get("text", ""),
                    start_time=item.get("start"),
                    end_time=(item.get("start") or 0) + (item.get("duration") or 0),
                )
                for item in entries
                if item.get("text")
            ]
            return TranscriptBundle(
                text=" ".join(segment.text for segment in segments),
                source_type="official_caption",
                segments=segments,
            )
        except Exception as exc:
            logger.warning("youtube_caption_unavailable video_id=%s error=%s", video_id, exc)
            return TranscriptBundle(
                source_type="unavailable",
                warning="No YouTube caption track was available.",
            )

    async def _ytdlp_subtitle_transcript(self, url: str) -> TranscriptBundle:
        try:
            subtitle_url = await asyncio.to_thread(self._get_ytdlp_subtitle_url, url)
            if not subtitle_url:
                return TranscriptBundle(source_type="unavailable", warning="yt-dlp did not find subtitle metadata.")

            async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                response = await client.get(subtitle_url)
                if response.status_code >= 400:
                    return TranscriptBundle(source_type="unavailable", warning=f"yt-dlp subtitle download failed with HTTP {response.status_code}.")

            segments = _parse_caption_text(response.text)
            text = " ".join(segment.text for segment in segments).strip()
            if not self._is_meaningful_transcript(text):
                return TranscriptBundle(source_type="unavailable", warning="yt-dlp subtitles were not meaningful enough for analysis.")
            return TranscriptBundle(text=text, source_type="official_caption", segments=segments)
        except Exception as exc:
            logger.warning("ytdlp_subtitle_transcript_failed url=%s error=%s", url, exc)
            return TranscriptBundle(source_type="unavailable", warning=f"yt-dlp subtitle extraction failed: {exc}")

    def _get_ytdlp_subtitle_url(self, url: str) -> str | None:
        from yt_dlp import YoutubeDL

        options = {
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": 30,
            "retries": 1,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en", "en-US", "en.*", "all"],
        }
        if settings.ytdlp_cookies_path:
            options["cookiefile"] = settings.ytdlp_cookies_path

        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)

        for collection_name in ("subtitles", "automatic_captions"):
            collection = info.get(collection_name) or {}
            subtitle_url = _select_subtitle_url(collection)
            if subtitle_url:
                logger.info("ytdlp_subtitle_url_found collection=%s", collection_name)
                return subtitle_url
        return None

    async def _whisper_transcript(self, video: VideoMetadata) -> TranscriptBundle:
        logger.info("whisper_media_prepare_started label=%s platform=%s", video.label, video.platform)
        media_path = await self._download_media(video)
        if not media_path:
            logger.warning(
                "whisper_media_prepare_failed label=%s platform=%s error=%s",
                video.label,
                video.platform,
                self._last_media_error,
            )
            return TranscriptBundle(
                source_type="unavailable",
                warning=self._last_media_error or "No downloadable media was available for Whisper.",
            )

        try:
            logger.info("whisper_transcription_started label=%s platform=%s media_path=%s", video.label, video.platform, media_path)
            result = await asyncio.to_thread(self._run_whisper, media_path)
            segments = [
                TranscriptSegment(
                    text=str(item.get("text", "")).strip(),
                    start_time=item.get("start"),
                    end_time=item.get("end"),
                )
                for item in result.get("segments", [])
                if str(item.get("text", "")).strip()
            ]
            text = " ".join(segment.text for segment in segments).strip() or str(result.get("text", "")).strip()
            if not self._is_meaningful_transcript(text):
                logger.warning("whisper_transcription_unusable label=%s platform=%s", video.label, video.platform)
                return TranscriptBundle(source_type="unavailable", warning="Whisper did not detect enough speech to build a useful transcript.")
            logger.info("whisper_transcription_done label=%s platform=%s chars=%s", video.label, video.platform, len(text))
            return TranscriptBundle(text=text, source_type="whisper_generated", segments=segments)
        except Exception as exc:
            logger.exception(
                "whisper_transcription_failed label=%s platform=%s media_path=%s",
                video.label,
                video.platform,
                media_path,
            )
            return TranscriptBundle(source_type="unavailable", warning=f"Whisper transcription failed: {exc}")
        finally:
            try:
                Path(media_path).unlink(missing_ok=True)
            except Exception:
                pass

    def _run_whisper(self, media_path: str) -> dict:
        self._ensure_ffmpeg_on_path()
        import whisper

        model = whisper.load_model(settings.whisper_model_size, download_root=settings.whisper_model_dir)
        return model.transcribe(media_path, fp16=False, verbose=False)

    async def _download_media(self, video: VideoMetadata) -> str | None:
        self._last_media_error = None
        direct_media_url = video.audio_url or video.media_url
        if direct_media_url:
            path = await self._download_direct_media(direct_media_url, video.label)
            if path:
                return path
        return await asyncio.to_thread(self._download_with_ytdlp, video.source_url, video.label)

    async def _download_direct_media(self, url: str, label: str) -> str | None:
        media_dir = Path(settings.media_download_dir)
        media_dir.mkdir(parents=True, exist_ok=True)
        suffix = Path(urlparse(url).path).suffix or ".mp4"
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
        path = media_dir / f"{label.lower()}-{digest}{suffix}"
        try:
            async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
                async with client.stream("GET", url) as response:
                    if response.status_code >= 400:
                        self._last_media_error = f"Direct media download failed with HTTP {response.status_code}."
                        return None
                    with path.open("wb") as file:
                        async for chunk in response.aiter_bytes():
                            file.write(chunk)
            return str(path)
        except Exception as exc:
            logger.exception("direct_media_download_failed label=%s url=%s", label, url)
            self._last_media_error = f"Direct media download failed before Whisper could run: {exc}"
            path.unlink(missing_ok=True)
            return None

    def _download_with_ytdlp(self, url: str, label: str) -> str | None:
        media_dir = Path(settings.media_download_dir)
        media_dir.mkdir(parents=True, exist_ok=True)
        output_template = str(media_dir / f"{label.lower()}-%(id)s.%(ext)s")
        try:
            from yt_dlp import YoutubeDL

            options = {
                "format": "bestaudio/best",
                "outtmpl": output_template,
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "socket_timeout": 30,
                "retries": 1,
            }
            if settings.ytdlp_cookies_path:
                options["cookiefile"] = settings.ytdlp_cookies_path
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded = Path(ydl.prepare_filename(info))
                if downloaded.exists():
                    return str(downloaded)
                candidates = sorted(media_dir.glob(f"{label.lower()}-{info.get('id')}.*"))
                return str(candidates[0]) if candidates else None
        except Exception as exc:
            logger.warning("ytdlp_media_download_failed label=%s url=%s error=%s", label, url, exc)
            self._last_media_error = f"yt-dlp media download failed: {exc}"
            return None

    def _is_meaningful_transcript(self, text: str) -> bool:
        alnum_count = sum(character.isalnum() for character in text)
        word_count = len([word for word in text.split() if any(character.isalnum() for character in word)])
        return alnum_count >= 20 and word_count >= 4

    def _ensure_ffmpeg_on_path(self) -> None:
        try:
            import imageio_ffmpeg

            ffmpeg_source = Path(imageio_ffmpeg.get_ffmpeg_exe())
            shim_dir = Path(settings.media_download_dir) / "bin"
            shim_dir.mkdir(parents=True, exist_ok=True)
            shim_path = shim_dir / "ffmpeg"
            if not shim_path.exists():
                try:
                    shim_path.symlink_to(ffmpeg_source)
                except Exception:
                    shutil.copy2(ffmpeg_source, shim_path)
                    shim_path.chmod(0o755)
            os.environ["PATH"] = f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        except Exception:
            return


def _select_subtitle_url(collection: dict) -> str | None:
    preferred_languages = ["en", "en-US", "en-GB"]
    languages = preferred_languages + sorted(collection.keys())
    seen: set[str] = set()
    preferred_exts = ["json3", "vtt", "srv3", "ttml"]
    for language in languages:
        if language in seen:
            continue
        seen.add(language)
        tracks = collection.get(language)
        if not isinstance(tracks, list):
            continue
        for ext in preferred_exts:
            for track in tracks:
                if not isinstance(track, dict):
                    continue
                if track.get("ext") == ext and track.get("url"):
                    return str(track["url"])
        for track in tracks:
            if isinstance(track, dict) and track.get("url"):
                return str(track["url"])
    return None


def _parse_caption_text(payload: str) -> list[TranscriptSegment]:
    stripped = payload.lstrip()
    if stripped.startswith("{"):
        return _parse_json3_captions(payload)
    return _parse_vtt_captions(payload)


def _parse_json3_captions(payload: str) -> list[TranscriptSegment]:
    data = json.loads(payload)
    segments: list[TranscriptSegment] = []
    for event in data.get("events", []):
        parts = event.get("segs") or []
        text = "".join(str(part.get("utf8", "")) for part in parts if isinstance(part, dict)).strip()
        if not text:
            continue
        start_ms = event.get("tStartMs")
        duration_ms = event.get("dDurationMs")
        start = float(start_ms) / 1000 if start_ms is not None else None
        end = (float(start_ms + duration_ms) / 1000) if start_ms is not None and duration_ms is not None else None
        segments.append(TranscriptSegment(text=_clean_caption_text(text), start_time=start, end_time=end))
    return segments


def _parse_vtt_captions(payload: str) -> list[TranscriptSegment]:
    segments: list[TranscriptSegment] = []
    current_lines: list[str] = []
    current_start: float | None = None
    current_end: float | None = None

    def flush() -> None:
        nonlocal current_lines, current_start, current_end
        text = _clean_caption_text(" ".join(current_lines))
        if text:
            segments.append(TranscriptSegment(text=text, start_time=current_start, end_time=current_end))
        current_lines = []
        current_start = None
        current_end = None

    for raw_line in payload.splitlines():
        line = raw_line.strip()
        if not line or line == "WEBVTT" or line.startswith(("Kind:", "Language:", "NOTE")):
            flush()
            continue
        if "-->" in line:
            flush()
            start_text, end_text = [part.strip().split(" ")[0] for part in line.split("-->", 1)]
            current_start = _timestamp_to_seconds(start_text)
            current_end = _timestamp_to_seconds(end_text)
            continue
        if re.match(r"^\d+$", line):
            continue
        current_lines.append(line)
    flush()
    return segments


def _timestamp_to_seconds(value: str) -> float | None:
    try:
        parts = value.replace(",", ".").split(":")
        seconds = 0.0
        for part in parts:
            seconds = seconds * 60 + float(part)
        return seconds
    except ValueError:
        return None


def _clean_caption_text(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = re.sub(r"\s+", " ", text)
    return text.strip()
