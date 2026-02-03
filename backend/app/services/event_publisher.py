"""
Event publishing helper module
Provides functions to publish Kafka events without circular imports
Feature 011: Event-Driven Architecture
Feature 012: Dapr Integration - Now supports Dapr pub/sub with Kafka fallback
"""
import logging
from typing import Optional, Dict, Any
from uuid import UUID

from app.config import settings

logger = logging.getLogger(__name__)

# Global reference to Kafka producer - will be set by main.py (fallback)
_producer = None

# Global reference to Dapr publisher
_dapr_publisher = None


def set_producer(producer):
    """Set the global Kafka producer instance (fallback for when Dapr is unavailable)"""
    global _producer
    _producer = producer


def _get_dapr_publisher():
    """Lazy load Dapr publisher to avoid circular imports"""
    global _dapr_publisher
    if _dapr_publisher is None and settings.DAPR_ENABLED:
        from app.services.dapr_event_publisher import get_dapr_publisher
        _dapr_publisher = get_dapr_publisher()
    return _dapr_publisher


async def publish_task_event(
    event_type: str,
    user_id: str,
    task_id: int,
    task_data: Dict[str, Any],
    event_id: Optional[UUID] = None
) -> Optional[UUID]:
    """
    Publish a task event to Kafka via Dapr (preferred) or direct Kafka producer (fallback)

    Args:
        event_type: Event type (task.created, task.updated, task.deleted, task.completed)
        user_id: User who performed the operation
        task_id: Task identifier
        task_data: Full task object as dict
        event_id: Optional event ID for idempotency

    Returns:
        UUID of published event, or None if publishing failed or no publisher available
    """
    # Try Dapr pub/sub first if enabled (Feature 012)
    dapr_publisher = _get_dapr_publisher()
    if dapr_publisher is not None:
        try:
            result = await dapr_publisher.publish_task_event(
                event_type=event_type,
                user_id=user_id,
                task_id=task_id,
                task_data=task_data,
                event_id=event_id
            )
            if result is not None:
                return result
            # If Dapr publish returned None, fall through to Kafka fallback
            logger.warning(f"Dapr publish failed, trying Kafka fallback for {event_type}")
        except Exception as e:
            logger.warning(f"Dapr publish error, using Kafka fallback: {e}")

    # Fallback to direct Kafka producer (Feature 011)
    if _producer is None or not _producer.is_started:
        logger.warning(f"No publisher available, skipping event: {event_type}")
        return None

    try:
        return await _producer.publish_task_event(
            event_type=event_type,
            user_id=user_id,
            task_id=task_id,
            task_data=task_data,
            event_id=event_id
        )
    except Exception as e:
        logger.error(f"Failed to publish {event_type} event for task {task_id}: {e}")
        return None


async def publish_reminder_event(
    user_id: str,
    task_id: int,
    remind_at: str,
    task_data: Dict[str, Any],
    reminder_id: Optional[str] = None
) -> Optional[UUID]:
    """
    Publish a reminder event to Kafka via Dapr (preferred) or direct Kafka producer (fallback)

    Args:
        user_id: User who owns the task
        task_id: Task identifier
        remind_at: Reminder timestamp (ISO 8601)
        task_data: Full task object as dict
        reminder_id: Optional reminder ID (format: reminder-{task_id}-{remind_at})

    Returns:
        UUID of published event, or None if publishing failed or no publisher available
    """
    # Try Dapr pub/sub first if enabled (Feature 012)
    dapr_publisher = _get_dapr_publisher()
    if dapr_publisher is not None:
        try:
            result = await dapr_publisher.publish_reminder_event(
                user_id=user_id,
                task_id=task_id,
                remind_at=remind_at,
                task_data=task_data,
                reminder_id=reminder_id
            )
            if result is not None:
                return result
            logger.warning(f"Dapr publish failed, trying Kafka fallback for reminder")
        except Exception as e:
            logger.warning(f"Dapr publish error, using Kafka fallback: {e}")

    # Fallback to direct Kafka producer (Feature 011)
    if _producer is None or not _producer.is_started:
        logger.warning(f"No publisher available, skipping reminder event for task {task_id}")
        return None

    try:
        return await _producer.publish_reminder_event(
            user_id=user_id,
            task_id=task_id,
            remind_at=remind_at,
            task_data=task_data,
            reminder_id=reminder_id
        )
    except Exception as e:
        logger.error(f"Failed to publish reminder event for task {task_id}: {e}")
        return None
