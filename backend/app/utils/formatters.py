import re


def parse_hashtags(text: str | None) -> list[str]:
    if not text:
        return []
    tags = re.findall(r"(?<!\w)#([A-Za-z0-9_]+)", text)
    return list(dict.fromkeys(f"#{tag}" for tag in tags))


def seconds_from_iso8601_duration(value: str | None) -> int | None:
    if not value:
        return None
    try:
        import isodate

        duration = isodate.parse_duration(value)
        return int(duration.total_seconds())
    except Exception:
        return None


def trim_preview(text: str, limit: int = 180) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "..."
