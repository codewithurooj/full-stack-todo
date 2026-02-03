"""Notification batching and deduplication utilities.

This module provides functions for batching reminders by time window
and deduplicating notifications to prevent spam.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ReminderBatch:
    """A batch of reminders grouped by time window."""
    window_start: datetime
    window_end: datetime
    reminders: List['Reminder']

    @property
    def count(self) -> int:
        """Get the number of reminders in this batch."""
        return len(self.reminders)


def batch_reminders(
    reminders: List['Reminder'],
    window_minutes: int = 5
) -> List[List['Reminder']]:
    """Group reminders by time window to reduce notification spam.

    Args:
        reminders: List of reminder objects (must have remind_at attribute)
        window_minutes: Size of batching window in minutes (default: 5)

    Returns:
        List of reminder batches, each batch contains reminders within the window

    Raises:
        ValueError: If window_minutes is invalid or reminders lack remind_at

    Example:
        >>> # Reminders at 9:00, 9:02, 9:04, 9:10
        >>> batches = batch_reminders(reminders, window_minutes=5)
        >>> len(batches)
        2  # First batch: 9:00-9:04, Second batch: 9:10
    """
    if window_minutes <= 0:
        raise ValueError("window_minutes must be positive")

    if not reminders:
        return []

    # Validate reminders have remind_at attribute
    if not all(hasattr(r, 'remind_at') for r in reminders):
        raise ValueError("All reminders must have a 'remind_at' attribute")

    # Sort reminders by remind_at time
    sorted_reminders = sorted(reminders, key=lambda r: r.remind_at)

    batches = []
    current_batch = [sorted_reminders[0]]

    for reminder in sorted_reminders[1:]:
        # Calculate time difference in minutes
        time_diff = (reminder.remind_at - current_batch[0].remind_at).total_seconds() / 60

        if time_diff <= window_minutes:
            # Add to current batch
            current_batch.append(reminder)
        else:
            # Start new batch
            batches.append(current_batch)
            current_batch = [reminder]

    # Don't forget the last batch
    batches.append(current_batch)

    return batches


def deduplicate_reminders(
    reminders: List['Reminder'],
    dedup_window_minutes: int = 5
) -> List['Reminder']:
    """Remove duplicate reminders within a time window.

    Deduplication is based on (task_id, user_id, remind_at) tuples.
    If multiple reminders exist for the same task within the dedup window,
    only the earliest one is kept.

    Args:
        reminders: List of reminder objects
        dedup_window_minutes: Deduplication window in minutes

    Returns:
        Deduplicated list of reminders

    Example:
        >>> # Two reminders for same task at 9:00 and 9:03
        >>> deduped = deduplicate_reminders(reminders, dedup_window_minutes=5)
        >>> len(deduped)
        1  # Only the 9:00 reminder is kept
    """
    if not reminders:
        return []

    # Validate required attributes
    required_attrs = ['task_id', 'user_id', 'remind_at']
    if not all(all(hasattr(r, attr) for attr in required_attrs) for r in reminders):
        raise ValueError(f"All reminders must have attributes: {', '.join(required_attrs)}")

    # Sort by remind_at
    sorted_reminders = sorted(reminders, key=lambda r: r.remind_at)

    # Track seen (task_id, user_id) pairs with their earliest remind_at
    seen: Dict[Tuple[int, str], datetime] = {}
    deduped = []

    for reminder in sorted_reminders:
        key = (reminder.task_id, reminder.user_id)

        if key not in seen:
            # First occurrence, keep it
            seen[key] = reminder.remind_at
            deduped.append(reminder)
        else:
            # Check if within dedup window
            time_diff = (reminder.remind_at - seen[key]).total_seconds() / 60

            if time_diff > dedup_window_minutes:
                # Outside window, keep it and update tracking
                seen[key] = reminder.remind_at
                deduped.append(reminder)
            # else: within window, skip (duplicate)

    return deduped


def create_batched_notification_message(
    batch: List['Reminder'],
    user_timezone: str = "UTC"
) -> Dict[str, str]:
    """Create a notification message for a batch of reminders.

    Args:
        batch: List of reminders to include in notification
        user_timezone: User's timezone for formatting times

    Returns:
        Dictionary with 'title' and 'body' for notification

    Example:
        >>> msg = create_batched_notification_message(batch)
        >>> msg['title']
        'Task Due: Complete project proposal'
        >>> msg['body']
        'Due at 9:00 AM'
    """
    if not batch:
        return {"title": "", "body": ""}

    if len(batch) == 1:
        # Single reminder
        reminder = batch[0]
        task_title = getattr(reminder, 'task_title', 'Task')
        remind_time = reminder.remind_at.strftime('%I:%M %p')

        return {
            "title": f"Task Due: {task_title}",
            "body": f"Due at {remind_time}",
            "tag": f"reminder-{reminder.task_id}"
        }
    else:
        # Multiple reminders
        task_list = []
        for reminder in batch[:5]:  # Limit to first 5
            task_title = getattr(reminder, 'task_title', f'Task {reminder.task_id}')
            task_list.append(f"• {task_title}")

        if len(batch) > 5:
            task_list.append(f"• ... and {len(batch) - 5} more")

        return {
            "title": f"{len(batch)} Tasks Due Soon",
            "body": "\n".join(task_list),
            "tag": "reminder-batch"
        }


def filter_delivered_reminders(reminders: List['Reminder']) -> List['Reminder']:
    """Filter out reminders that have already been delivered.

    Args:
        reminders: List of reminder objects

    Returns:
        List of undelivered reminders

    Example:
        >>> undelivered = filter_delivered_reminders(all_reminders)
        >>> all(not r.delivered for r in undelivered)
        True
    """
    if not reminders:
        return []

    # Validate delivered attribute exists
    if not all(hasattr(r, 'delivered') for r in reminders):
        raise ValueError("All reminders must have a 'delivered' attribute")

    return [r for r in reminders if not r.delivered]


def filter_pending_reminders(
    reminders: List['Reminder'],
    current_time: Optional[datetime] = None,
    lookahead_minutes: int = 5
) -> List['Reminder']:
    """Filter reminders that are due within the lookahead window.

    Args:
        reminders: List of reminder objects
        current_time: Reference time (default: now)
        lookahead_minutes: How far ahead to look for reminders

    Returns:
        List of reminders due within the lookahead window

    Example:
        >>> # Current time is 9:00, lookahead is 5 minutes
        >>> # Returns reminders due between 9:00 and 9:05
        >>> pending = filter_pending_reminders(reminders, lookahead_minutes=5)
    """
    if not reminders:
        return []

    if current_time is None:
        current_time = datetime.utcnow()

    # Calculate lookahead window
    window_end = current_time + timedelta(minutes=lookahead_minutes)

    # Filter reminders within window
    pending = [
        r for r in reminders
        if current_time <= r.remind_at <= window_end
    ]

    return pending


def calculate_notification_priority(reminder: 'Reminder') -> str:
    """Calculate notification priority based on urgency.

    Args:
        reminder: Reminder object with remind_at attribute

    Returns:
        Priority level: 'high', 'medium', or 'low'

    Example:
        >>> # Reminder in 5 minutes
        >>> priority = calculate_notification_priority(reminder)
        >>> priority
        'high'
    """
    now = datetime.utcnow()

    # Ensure remind_at is timezone-aware for comparison
    remind_at = reminder.remind_at
    if remind_at.tzinfo is None:
        from pytz import UTC
        remind_at = UTC.localize(remind_at)
        now = UTC.localize(now) if now.tzinfo is None else now

    time_until = (remind_at - now).total_seconds() / 60  # minutes

    if time_until <= 15:
        return 'high'
    elif time_until <= 60:
        return 'medium'
    else:
        return 'low'


def should_send_notification(
    reminder: 'Reminder',
    current_time: Optional[datetime] = None,
    tolerance_minutes: int = 2
) -> bool:
    """Determine if a notification should be sent now.

    Args:
        reminder: Reminder object
        current_time: Current time (default: now)
        tolerance_minutes: Tolerance window around remind_at time

    Returns:
        True if notification should be sent

    Example:
        >>> # Reminder at 9:00, current time 9:01, tolerance 2 minutes
        >>> should_send_notification(reminder)
        True
    """
    if current_time is None:
        current_time = datetime.utcnow()

    # Check if already delivered
    if hasattr(reminder, 'delivered') and reminder.delivered:
        return False

    # Calculate time difference
    time_diff = abs((reminder.remind_at - current_time).total_seconds() / 60)

    # Within tolerance window?
    return time_diff <= tolerance_minutes


def group_by_user(reminders: List['Reminder']) -> Dict[str, List['Reminder']]:
    """Group reminders by user_id.

    Args:
        reminders: List of reminder objects

    Returns:
        Dictionary mapping user_id to list of reminders

    Example:
        >>> grouped = group_by_user(all_reminders)
        >>> grouped['user123']
        [<Reminder 1>, <Reminder 2>]
    """
    if not reminders:
        return {}

    # Validate user_id attribute
    if not all(hasattr(r, 'user_id') for r in reminders):
        raise ValueError("All reminders must have a 'user_id' attribute")

    grouped: Dict[str, List['Reminder']] = {}

    for reminder in reminders:
        user_id = reminder.user_id
        if user_id not in grouped:
            grouped[user_id] = []
        grouped[user_id].append(reminder)

    return grouped
