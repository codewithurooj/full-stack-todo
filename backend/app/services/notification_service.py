"""Notification service for sending reminders"""
from datetime import datetime
from typing import List, Dict, Optional
import logging

from app.models.reminder import Reminder
from app.models.task import Task
from app.utils.notification import (
    batch_reminders,
    deduplicate_reminders,
    create_batched_notification_message,
    filter_delivered_reminders,
    group_by_user
)

logger = logging.getLogger(__name__)


def format_notification_message(
    task: Task,
    reminder: Reminder,
    user_timezone: str = "UTC"
) -> Dict[str, str]:
    """
    Format a notification message for a single reminder.

    Args:
        task: Task object
        reminder: Reminder object
        user_timezone: User's timezone for formatting times

    Returns:
        Dictionary with 'title', 'body', and 'tag' for notification

    Example:
        >>> msg = format_notification_message(task, reminder)
        >>> msg['title']
        'Task Due: Complete project proposal'
    """
    # Format time
    remind_time = reminder.remind_at.strftime('%I:%M %p')
    due_time = task.due_date.strftime('%I:%M %p') if task.due_date else 'No due date'

    # Build message
    message = {
        "title": f"Task Due: {task.title}",
        "body": f"Due at {due_time} (Reminder at {remind_time})",
        "tag": f"reminder-{reminder.id}",
        "data": {
            "task_id": task.id,
            "reminder_id": reminder.id,
            "user_id": task.user_id,
            "priority": task.priority
        }
    }

    return message


def send_notification(
    reminder: Reminder,
    task: Task,
    user_id: str
) -> Dict[str, any]:
    """
    Send a notification for a reminder (logs to console for MVP).

    In production, this would integrate with Web Push API, FCM, or similar.

    Args:
        reminder: Reminder object
        task: Task object
        user_id: User ID to send notification to

    Returns:
        Dictionary with notification details and delivery status

    Example:
        >>> result = send_notification(reminder, task, "user123")
        >>> result['status']
        'sent'
    """
    # Format message
    message = format_notification_message(task, reminder)

    # For MVP, log to console
    # In production, integrate with Web Push API
    logger.info(
        f"NOTIFICATION SENT: user={user_id}, task={task.id}, reminder={reminder.id}"
    )
    logger.info(f"  Title: {message['title']}")
    logger.info(f"  Body: {message['body']}")
    logger.info(f"  Tag: {message['tag']}")

    # Return delivery result
    return {
        "status": "sent",
        "notification_id": f"notif-{reminder.id}-{datetime.utcnow().timestamp()}",
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }


def batch_notifications(
    reminders: List[Reminder],
    window_minutes: int = 2
) -> List[List[Reminder]]:
    """
    Group reminders by time window to reduce notification spam.

    Args:
        reminders: List of reminder objects
        window_minutes: Size of batching window in minutes (default: 2)

    Returns:
        List of reminder batches

    Example:
        >>> # Reminders at 9:00, 9:01, 9:05
        >>> batches = batch_notifications(reminders, window_minutes=2)
        >>> len(batches)
        2  # First batch: 9:00-9:01, Second batch: 9:05
    """
    if not reminders:
        return []

    # Filter out already delivered reminders
    undelivered = filter_delivered_reminders(reminders)

    if not undelivered:
        logger.info("batch_notifications: no undelivered reminders")
        return []

    # Use utility function from notification.py
    batches = batch_reminders(undelivered, window_minutes=window_minutes)

    logger.info(
        f"batch_notifications: total_reminders={len(reminders)}, "
        f"undelivered={len(undelivered)}, batches={len(batches)}"
    )

    return batches


def deduplicate_notifications(
    reminders: List[Reminder],
    dedup_window_minutes: int = 5
) -> List[Reminder]:
    """
    Remove duplicate reminders within a time window.

    Deduplication is based on (task_id, user_id, remind_at) tuples.

    Args:
        reminders: List of reminder objects
        dedup_window_minutes: Deduplication window in minutes (default: 5)

    Returns:
        Deduplicated list of reminders

    Example:
        >>> # Two reminders for same task at 9:00 and 9:03
        >>> deduped = deduplicate_notifications(reminders, dedup_window_minutes=5)
        >>> len(deduped)
        1  # Only the 9:00 reminder is kept
    """
    if not reminders:
        return []

    # Use utility function from notification.py
    deduped = deduplicate_reminders(reminders, dedup_window_minutes=dedup_window_minutes)

    duplicates_removed = len(reminders) - len(deduped)
    if duplicates_removed > 0:
        logger.info(
            f"deduplicate_notifications: removed {duplicates_removed} duplicates, "
            f"kept {len(deduped)} reminders"
        )

    return deduped


def send_batched_notification(
    batch: List[Reminder],
    tasks: Dict[int, Task],
    user_id: str
) -> Dict[str, any]:
    """
    Send a batched notification for multiple reminders.

    Args:
        batch: List of reminders to send as one notification
        tasks: Dictionary mapping task_id to Task object
        user_id: User ID to send notification to

    Returns:
        Dictionary with notification details and delivery status
    """
    if not batch:
        logger.warning("send_batched_notification: empty batch")
        return {"status": "skipped", "reason": "empty_batch"}

    # Create enriched reminder objects with task titles
    enriched_batch = []
    for reminder in batch:
        task = tasks.get(reminder.task_id)
        if task:
            # Create a simple object with task_title attribute for formatting
            class EnrichedReminder:
                def __init__(self, reminder_obj, task_title):
                    self.task_id = reminder_obj.task_id
                    self.user_id = reminder_obj.user_id
                    self.remind_at = reminder_obj.remind_at
                    self.task_title = task_title

            enriched_batch.append(EnrichedReminder(reminder, task.title))

    # Create batched message
    message = create_batched_notification_message(enriched_batch)

    # For MVP, log to console
    logger.info(
        f"BATCHED NOTIFICATION SENT: user={user_id}, batch_size={len(batch)}"
    )
    logger.info(f"  Title: {message['title']}")
    logger.info(f"  Body: {message['body']}")
    logger.info(f"  Tag: {message['tag']}")

    # Return delivery result
    return {
        "status": "sent",
        "notification_id": f"batch-{datetime.utcnow().timestamp()}",
        "message": message,
        "reminder_count": len(batch),
        "timestamp": datetime.utcnow().isoformat()
    }


def queue_offline_notification(
    reminder: Reminder,
    task: Task,
    reason: str = "offline"
) -> Dict[str, any]:
    """
    Queue a notification for later delivery (when user is offline or delivery fails).

    For MVP, this marks the reminder as 'failed' for retry.
    In production, this would store in a persistent queue (Redis, DB, etc.).

    Args:
        reminder: Reminder object
        task: Task object
        reason: Reason for queueing (offline, error, etc.)

    Returns:
        Dictionary with queue details
    """
    logger.warning(
        f"queue_offline_notification: queued for retry. "
        f"reminder_id={reminder.id}, task_id={task.id}, reason={reason}"
    )

    # For MVP, we'll rely on the delivery_status='failed' flag
    # The reminder processor will retry failed notifications
    return {
        "status": "queued",
        "reminder_id": reminder.id,
        "task_id": task.id,
        "reason": reason,
        "queued_at": datetime.utcnow().isoformat()
    }


def process_user_reminders(
    reminders: List[Reminder],
    tasks: Dict[int, Task],
    user_id: str,
    enable_batching: bool = True,
    enable_deduplication: bool = True
) -> Dict[str, any]:
    """
    Process all reminders for a user with batching and deduplication.

    Args:
        reminders: List of reminders to process
        tasks: Dictionary mapping task_id to Task object
        user_id: User ID
        enable_batching: Whether to batch notifications (default: True)
        enable_deduplication: Whether to deduplicate (default: True)

    Returns:
        Dictionary with processing results
    """
    if not reminders:
        return {
            "user_id": user_id,
            "reminders_processed": 0,
            "notifications_sent": 0,
            "batches": 0
        }

    logger.info(
        f"process_user_reminders: processing {len(reminders)} reminders for user={user_id}"
    )

    # Step 1: Deduplicate
    processed_reminders = reminders
    if enable_deduplication:
        processed_reminders = deduplicate_notifications(processed_reminders)

    # Step 2: Batch
    notifications_sent = 0
    batches = 0

    if enable_batching and len(processed_reminders) > 1:
        # Batch reminders
        reminder_batches = batch_notifications(processed_reminders)
        batches = len(reminder_batches)

        for batch in reminder_batches:
            # Send batched notification
            result = send_batched_notification(batch, tasks, user_id)
            if result.get("status") == "sent":
                notifications_sent += 1
    else:
        # Send individual notifications
        for reminder in processed_reminders:
            task = tasks.get(reminder.task_id)
            if task:
                result = send_notification(reminder, task, user_id)
                if result.get("status") == "sent":
                    notifications_sent += 1
            else:
                logger.warning(
                    f"process_user_reminders: task not found for reminder. "
                    f"reminder_id={reminder.id}, task_id={reminder.task_id}"
                )

    logger.info(
        f"process_user_reminders: user={user_id}, processed={len(processed_reminders)}, "
        f"sent={notifications_sent}, batches={batches}"
    )

    return {
        "user_id": user_id,
        "reminders_processed": len(processed_reminders),
        "notifications_sent": notifications_sent,
        "batches": batches
    }
