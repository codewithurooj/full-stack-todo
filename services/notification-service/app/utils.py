"""
Helper functions for notification service
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


class NotificationBatcher:
    """Batches notifications within a time window"""

    def __init__(self, window_seconds: int = 120):
        self.window_seconds = window_seconds
        self.batches: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        self.batch_timers: Dict[int, asyncio.Task] = {}

    async def add_notification(self, user_id: int, notification: Dict[str, Any]) -> None:
        """Add notification to batch for user"""
        self.batches[user_id].append(notification)

        # Start or reset batch timer
        if user_id in self.batch_timers:
            self.batch_timers[user_id].cancel()

        self.batch_timers[user_id] = asyncio.create_task(
            self._flush_after_delay(user_id)
        )

    async def _flush_after_delay(self, user_id: int) -> None:
        """Flush batch after window expires"""
        await asyncio.sleep(self.window_seconds)
        await self.flush_batch(user_id)

    async def flush_batch(self, user_id: int) -> List[Dict[str, Any]]:
        """Get and clear batch for user"""
        notifications = self.batches.pop(user_id, [])
        if user_id in self.batch_timers:
            self.batch_timers[user_id].cancel()
            del self.batch_timers[user_id]
        return notifications

    def get_batch_size(self, user_id: int) -> int:
        """Get current batch size for user"""
        return len(self.batches.get(user_id, []))


class RateLimiter:
    """Rate limits notifications per user"""

    def __init__(self, max_per_window: int = 10, window_seconds: int = 60):
        self.max_per_window = max_per_window
        self.window_seconds = window_seconds
        self.user_counters: Dict[int, List[datetime]] = defaultdict(list)

    def is_allowed(self, user_id: int) -> bool:
        """Check if user can receive notification"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)

        # Clean old timestamps
        self.user_counters[user_id] = [
            ts for ts in self.user_counters[user_id]
            if ts > window_start
        ]

        # Check limit
        if len(self.user_counters[user_id]) >= self.max_per_window:
            logger.warning(
                f"Rate limit exceeded for user {user_id}: "
                f"{len(self.user_counters[user_id])} notifications in last {self.window_seconds}s"
            )
            return False

        # Add timestamp
        self.user_counters[user_id].append(now)
        return True

    def get_remaining(self, user_id: int) -> int:
        """Get remaining notification quota for user"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)

        # Clean old timestamps
        self.user_counters[user_id] = [
            ts for ts in self.user_counters[user_id]
            if ts > window_start
        ]

        return max(0, self.max_per_window - len(self.user_counters[user_id]))


def validate_reminder_event(event: Dict[str, Any]) -> bool:
    """Validate reminder event schema"""
    required_fields = [
        'event_id', 'schema_version', 'timestamp',
        'reminder_id', 'task_id', 'user_id',
        'title', 'remind_at'
    ]

    for field in required_fields:
        if field not in event:
            logger.error(f"Missing required field: {field}")
            return False

    return True


def parse_iso_datetime(dt_string: str) -> Optional[datetime]:
    """Parse ISO 8601 datetime string"""
    try:
        # Handle both with and without microseconds
        if '.' in dt_string:
            return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        else:
            return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
    except Exception as e:
        logger.error(f"Failed to parse datetime '{dt_string}': {e}")
        return None


def calculate_delay(remind_at: datetime) -> float:
    """Calculate delay in seconds until remind_at time"""
    now = datetime.utcnow()
    delay = (remind_at - now).total_seconds()
    return max(0, delay)  # Don't return negative delays
