import re
from urllib.parse import parse_qs, urlparse

from app.core.errors import AppError


YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}
INSTAGRAM_HOSTS = {"instagram.com", "www.instagram.com", "m.instagram.com"}


def parse_youtube_video_id(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host not in YOUTUBE_HOSTS:
        raise AppError("invalid_youtube_url", "Video A must be a valid YouTube Short URL.")

    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]
    elif parsed.path.startswith("/shorts/"):
        video_id = parsed.path.split("/shorts/", 1)[1].split("/")[0]
    elif parsed.path.startswith("/watch"):
        video_id = parse_qs(parsed.query).get("v", [""])[0]
    else:
        match = re.search(r"/(?:embed|v)/([^/?#]+)", parsed.path)
        video_id = match.group(1) if match else ""

    if not re.match(r"^[A-Za-z0-9_-]{8,20}$", video_id):
        raise AppError("invalid_youtube_url", "Video A must be a valid YouTube Short URL.")
    return video_id


def validate_instagram_reel_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host not in INSTAGRAM_HOSTS:
        raise AppError("invalid_instagram_url", "Video B must be a valid Instagram Reel URL.")
    if not re.search(r"/(?:reel|p)/[^/]+", parsed.path):
        raise AppError("invalid_instagram_url", "Video B must be a valid Instagram Reel URL.")
    return url
