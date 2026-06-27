from datetime import UTC, datetime, timedelta

import pytest

from dendridb.memory.expiry import compute_expires_at, is_expired


@pytest.mark.unit
def test_compute_expires_at_returns_none_without_ttl():
    assert compute_expires_at(None) is None


@pytest.mark.unit
def test_compute_expires_at_adds_seconds():
    base = datetime(2026, 1, 1, tzinfo=UTC)
    expires = compute_expires_at(120, from_time=base)
    assert expires == base + timedelta(seconds=120)


@pytest.mark.unit
def test_is_expired_false_when_no_expiry():
    assert is_expired(None) is False


@pytest.mark.unit
def test_is_expired_true_when_past():
    now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    past = now - timedelta(minutes=5)
    assert is_expired(past, now=now) is True


@pytest.mark.unit
def test_is_expired_false_when_future():
    now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    future = now + timedelta(minutes=5)
    assert is_expired(future, now=now) is False
