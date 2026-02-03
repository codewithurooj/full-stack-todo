"""
Tests for utility functions
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from app.utils import (
    NotificationBatcher,
    RateLimiter,
    validate_reminder_event,
    parse_iso_datetime,
    calculate_delay
)
from tests.fixtures import sample_reminder_event, invalid_reminder_event


def test_validate_reminder_event_valid(sample_reminder_event):
    """Test validation accepts valid event"""
    assert validate_reminder_event(sample_reminder_event) is True


def test_validate_reminder_event_invalid(invalid_reminder_event):
    """Test validation rejects invalid event"""
    assert validate_reminder_event(invalid_reminder_event) is False


def test_parse_iso_datetime():
    """Test ISO datetime parsing"""
    # With milliseconds and Z
    dt1 = parse_iso_datetime("2026-01-19T08:00:00.000Z")
    assert dt1 is not None
    assert dt1.year == 2026

    # Without milliseconds
    dt2 = parse_iso_datetime("2026-01-19T08:00:00Z")
    assert dt2 is not None

    # Invalid format
    dt3 = parse_iso_datetime("invalid")
    assert dt3 is None


def test_calculate_delay():
    """Test delay calculation"""
    # Future time
    future = datetime.utcnow() + timedelta(hours=1)
    delay = calculate_delay(future)
    assert delay > 3500  # ~1 hour in seconds
    assert delay < 3700

    # Past time should return 0
    past = datetime.utcnow() - timedelta(hours=1)
    delay = calculate_delay(past)
    assert delay == 0


@pytest.mark.asyncio
async def test_notification_batcher():
    """Test notification batching"""
    batcher = NotificationBatcher(window_seconds=1)

    # Add notifications
    await batcher.add_notification(1, {"title": "Test 1"})
    await batcher.add_notification(1, {"title": "Test 2"})

    # Check batch size
    assert batcher.get_batch_size(1) == 2

    # Flush batch
    notifications = await batcher.flush_batch(1)
    assert len(notifications) == 2
    assert batcher.get_batch_size(1) == 0


def test_rate_limiter():
    """Test rate limiting"""
    limiter = RateLimiter(max_per_window=3, window_seconds=60)

    # Allow 3 notifications
    assert limiter.is_allowed(1) is True
    assert limiter.is_allowed(1) is True
    assert limiter.is_allowed(1) is True

    # 4th should be blocked
    assert limiter.is_allowed(1) is False

    # Check remaining quota
    assert limiter.get_remaining(1) == 0


def test_rate_limiter_different_users():
    """Test rate limiting is per-user"""
    limiter = RateLimiter(max_per_window=2, window_seconds=60)

    # User 1 exhausts limit
    assert limiter.is_allowed(1) is True
    assert limiter.is_allowed(1) is True
    assert limiter.is_allowed(1) is False

    # User 2 still has quota
    assert limiter.is_allowed(2) is True
    assert limiter.is_allowed(2) is True
    assert limiter.is_allowed(2) is False
