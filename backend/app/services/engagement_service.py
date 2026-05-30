def calculate_engagement_rate(likes: int | None, comments: int | None, views: int | None) -> float | None:
    if views is None or views <= 0:
        return None
    if likes is None or comments is None:
        return None
    return round(((likes + comments) / views) * 100, 2)
