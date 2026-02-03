"""
Dapr Event Publisher
Feature: 012-dapr-integration
Purpose: Publish events to Kafka via Dapr pub/sub HTTP APIs with CloudEvent metadata
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from app.config import settings
from app.services.dapr_client import get_dapr_client

logger = logging.getLogger(__name__)

# CloudEvent constants
CE_SPEC_VERSION = "1.0"
CE_SOURCE = "todo-app/backend-service"


class DaprEventPublisher:
    """
    Publishes events to Kafka via Dapr pub/sub API.
    Adds CloudEvent metadata (event_id, correlation_id, timestamp) to all events.
    """

    def __init__(
        self,
        pubsub_name: str = None,
        source: str = CE_SOURCE
    ):
        self.pubsub_name = pubsub_name or settings.DAPR_PUBSUB_NAME
        self.source = source
        self.publish_count = 0
        self.error_count = 0

    def _create_cloud_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        event_id: Optional[UUID] = None,
        correlation_id: Optional[str] = None
    ) -> tuple[Dict[str, Any], Dict[str, str]]:
        """
        Create CloudEvent envelope with metadata.

        Returns:
            Tuple of (data with embedded event metadata, CloudEvent headers)
        """
        # Generate event ID if not provided
        eid = str(event_id) if event_id else str(uuid.uuid4())

        # Add event metadata to data
        enriched_data = {
            **data,
            "event_id": eid,
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if correlation_id:
            enriched_data["correlation_id"] = correlation_id

        # CloudEvent metadata headers
        ce_headers = {
            "specversion": CE_SPEC_VERSION,
            "id": eid,
            "type": event_type,
            "source": self.source,
            "time": enriched_data["timestamp"],
        }

        if correlation_id:
            ce_headers["correlationid"] = correlation_id

        return enriched_data, ce_headers

    async def publish_task_event(
        self,
        event_type: str,
        user_id: str,
        task_id: int,
        task_data: Dict[str, Any],
        event_id: Optional[UUID] = None,
        correlation_id: Optional[str] = None
    ) -> Optional[UUID]:
        """
        Publish a task event to the task-events topic.

        Args:
            event_type: Event type (task.created, task.updated, task.deleted, task.completed)
            user_id: User who performed the operation
            task_id: Task identifier
            task_data: Full task object as dict
            event_id: Optional event ID for idempotency
            correlation_id: Optional correlation ID for distributed tracing

        Returns:
            UUID of published event, or None if publishing failed
        """
        data = {
            "task_id": task_id,
            "user_id": user_id,
            "task_data": task_data,
        }

        enriched_data, ce_headers = self._create_cloud_event(
            event_type=event_type,
            data=data,
            event_id=event_id,
            correlation_id=correlation_id
        )

        client = get_dapr_client()
        success = await client.publish_event(
            pubsub_name=self.pubsub_name,
            topic="task-events",
            data=enriched_data,
            metadata=ce_headers
        )

        if success:
            self.publish_count += 1
            logger.info(
                f"Published {event_type} event via Dapr: task_id={task_id}, "
                f"event_id={enriched_data['event_id']}"
            )
            return UUID(enriched_data["event_id"])
        else:
            self.error_count += 1
            logger.error(f"Failed to publish {event_type} event via Dapr for task {task_id}")
            return None

    async def publish_reminder_event(
        self,
        user_id: str,
        task_id: int,
        remind_at: str,
        task_data: Dict[str, Any],
        reminder_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> Optional[UUID]:
        """
        Publish a reminder event to the reminders topic.

        Args:
            user_id: User who owns the task
            task_id: Task identifier
            remind_at: Reminder timestamp (ISO 8601)
            task_data: Full task object as dict
            reminder_id: Optional reminder ID
            correlation_id: Optional correlation ID for distributed tracing

        Returns:
            UUID of published event, or None if publishing failed
        """
        data = {
            "task_id": task_id,
            "user_id": user_id,
            "title": task_data.get("title", ""),
            "remind_at": remind_at,
            "task_data": task_data,
        }

        if reminder_id:
            data["reminder_id"] = reminder_id

        enriched_data, ce_headers = self._create_cloud_event(
            event_type="reminder.scheduled",
            data=data,
            correlation_id=correlation_id
        )

        client = get_dapr_client()
        success = await client.publish_event(
            pubsub_name=self.pubsub_name,
            topic="reminders",
            data=enriched_data,
            metadata=ce_headers
        )

        if success:
            self.publish_count += 1
            logger.info(
                f"Published reminder event via Dapr: task_id={task_id}, "
                f"remind_at={remind_at}, event_id={enriched_data['event_id']}"
            )
            return UUID(enriched_data["event_id"])
        else:
            self.error_count += 1
            logger.error(f"Failed to publish reminder event via Dapr for task {task_id}")
            return None

    async def publish_task_update_event(
        self,
        user_id: str,
        task_id: int,
        changes: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> Optional[UUID]:
        """
        Publish a task update event to the task-updates topic (for WebSocket real-time updates).

        Args:
            user_id: User who made the change
            task_id: Task identifier
            changes: Dict of field changes {field: {old: val, new: val}}
            correlation_id: Optional correlation ID for distributed tracing

        Returns:
            UUID of published event, or None if publishing failed
        """
        data = {
            "task_id": task_id,
            "user_id": user_id,
            "changes": changes,
        }

        enriched_data, ce_headers = self._create_cloud_event(
            event_type="task.field_changed",
            data=data,
            correlation_id=correlation_id
        )

        client = get_dapr_client()
        success = await client.publish_event(
            pubsub_name=self.pubsub_name,
            topic="task-updates",
            data=enriched_data,
            metadata=ce_headers
        )

        if success:
            self.publish_count += 1
            return UUID(enriched_data["event_id"])
        else:
            self.error_count += 1
            return None


# Global Dapr event publisher instance
_dapr_publisher: Optional[DaprEventPublisher] = None


def get_dapr_publisher() -> DaprEventPublisher:
    """Get or create the global Dapr event publisher instance."""
    global _dapr_publisher
    if _dapr_publisher is None:
        _dapr_publisher = DaprEventPublisher()
    return _dapr_publisher
