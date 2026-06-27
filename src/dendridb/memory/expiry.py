from datetime import UTC, datetime, timedelta


def compute_expires_at(
    ttl_seconds: int | None,
    *,
    from_time: datetime | None = None,
) -> datetime | None:
    """Return absolute expiry time from a TTL, or None if no TTL."""
    if ttl_seconds is None:
        return None
    base = from_time or datetime.now(UTC)
    return base + timedelta(seconds=ttl_seconds)


def is_expired(expires_at: datetime | None, *, now: datetime | None = None) -> bool:
    """Return True when the item has passed its expiry time."""
    if expires_at is None:
        return False
    current = now or datetime.now(UTC)
    return expires_at <= current
