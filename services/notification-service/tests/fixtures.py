"""
Test fixtures for notification service
"""
import pytest
from datetime import datetime, timedelta


@pytest.fixture
def sample_reminder_event():
    """Sample reminder event from Kafka"""
    return {
        "event_id": "660e8400-e29b-41d4-a716-446655440001",
        "schema_version": "1.0.0",
        "timestamp": "2026-01-12T10:30:00.000Z",
        "reminder_id": "reminder-123-2026-01-19T08:00:00Z",
        "task_id": 123,
        "user_id": 456,
        "title": "Buy groceries",
        "remind_at": "2026-01-19T08:00:00.000Z",
        "due_date": "2026-01-19T09:00:00.000Z"
    }


@pytest.fixture
def past_reminder_event():
    """Reminder event that should trigger immediately"""
    past_time = (datetime.utcnow() - timedelta(minutes=5)).isoformat() + "Z"
    return {
        "event_id": "660e8400-e29b-41d4-a716-446655440002",
        "schema_version": "1.0.0",
        "timestamp": "2026-01-12T10:30:00.000Z",
        "reminder_id": "reminder-124-past",
        "task_id": 124,
        "user_id": 456,
        "title": "Past reminder",
        "remind_at": past_time,
        "due_date": "2026-01-19T09:00:00.000Z"
    }


@pytest.fixture
def future_reminder_event():
    """Reminder event scheduled for future"""
    future_time = (datetime.utcnow() + timedelta(minutes=5)).isoformat() + "Z"
    return {
        "event_id": "660e8400-e29b-41d4-a716-446655440003",
        "schema_version": "1.0.0",
        "timestamp": "2026-01-12T10:30:00.000Z",
        "reminder_id": "reminder-125-future",
        "task_id": 125,
        "user_id": 456,
        "title": "Future reminder",
        "remind_at": future_time,
        "due_date": "2026-01-19T09:00:00.000Z"
    }


@pytest.fixture
def invalid_reminder_event():
    """Invalid reminder event (missing fields)"""
    return {
        "event_id": "660e8400-e29b-41d4-a716-446655440004",
        "schema_version": "1.0.0",
        "timestamp": "2026-01-12T10:30:00.000Z",
        # Missing required fields
    }


@pytest.fixture
def sample_push_subscription():
    """Sample push subscription"""
    return {
        "id": 1,
        "user_id": 456,
        "endpoint": "https://fcm.googleapis.com/fcm/send/abc123",
        "p256dh": "BCVxsr7N_eNgVRqvHtD0zTZsEc6-VV-JvLexhqUzORcx",
        "auth": "BTBZMqHH6r4Tts7J_aSIgg",
        "active": True
    }
