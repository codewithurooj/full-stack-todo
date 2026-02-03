"""
Event Parser
Extracts audit log fields from Kafka events
"""
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


def parse_event_to_audit_log(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse a Kafka event and extract audit log fields

    Args:
        event: Kafka event dictionary

    Returns:
        Dictionary of audit log fields, or None if parsing fails

    Example event:
        {
            "event_id": "550e8400-e29b-41d4-a716-446655440000",
            "event_type": "task.created",
            "schema_version": "1.0.0",
            "timestamp": "2026-01-13T12:00:00Z",
            "user_id": "user123",
            "task_id": 42,
            "task_data": {...}
        }
    """
    try:
        # Extract required fields
        event_id_str = event.get("event_id")
        event_type = event.get("event_type")
        timestamp_str = event.get("timestamp")
        user_id = event.get("user_id")
        task_id = event.get("task_id")

        # Validate required fields
        if not event_id_str:
            logger.error("parse_event: missing event_id")
            return None

        if not event_type:
            logger.error(f"parse_event: missing event_type for event {event_id_str}")
            return None

        if not timestamp_str:
            logger.error(f"parse_event: missing timestamp for event {event_id_str}")
            return None

        if not user_id:
            logger.error(f"parse_event: missing user_id for event {event_id_str}")
            return None

        # Parse UUID
        try:
            event_id = UUID(event_id_str) if isinstance(event_id_str, str) else event_id_str
        except (ValueError, TypeError) as e:
            logger.error(f"parse_event: invalid event_id format '{event_id_str}': {e}")
            return None

        # Parse timestamp
        try:
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = timestamp_str
        except (ValueError, TypeError) as e:
            logger.error(f"parse_event: invalid timestamp format '{timestamp_str}': {e}")
            return None

        # Determine if system-generated (from recurring-task-service)
        source = event.get("source", "")
        task_data = event.get("task_data", {})
        parent_task_id = task_data.get("parent_task_id")

        system_generated = (
            source == "recurring-task-service" or
            (parent_task_id is not None and event_type == "task.created")
        )

        # Build audit log dictionary
        audit_log_data = {
            "event_id": event_id,
            "timestamp": timestamp,
            "user_id": user_id,
            "task_id": task_id,
            "operation_type": event_type,
            "event_payload": event,  # Store full event as JSONB
            "system_generated": system_generated
        }

        logger.debug(
            f"Parsed event: event_id={event_id}, type={event_type}, "
            f"user={user_id}, task={task_id}, system_generated={system_generated}"
        )

        return audit_log_data

    except Exception as e:
        logger.error(f"parse_event: unexpected error: {e}", exc_info=True)
        return None


def validate_event(event: Dict[str, Any]) -> bool:
    """
    Validate that event contains minimum required fields

    Args:
        event: Kafka event dictionary

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["event_id", "event_type", "timestamp", "user_id"]

    for field in required_fields:
        if field not in event or event[field] is None:
            logger.warning(f"validate_event: missing required field '{field}'")
            return False

    # Validate event_type format
    event_type = event.get("event_type", "")
    valid_types = ["task.created", "task.updated", "task.deleted", "task.completed"]

    if event_type not in valid_types:
        logger.warning(f"validate_event: unknown event_type '{event_type}'")
        # Don't reject - just warn, we want to log all events

    return True
