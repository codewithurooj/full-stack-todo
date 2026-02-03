"""
Dapr Subscription and Event Routes for Notification Service
Feature: 012-dapr-integration
Purpose: HTTP endpoints for Dapr pub/sub event consumption
"""
import logging
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dapr-events"])

# In-memory processed event IDs (for idempotency in development)
# In production, use a database table like processed_events
_processed_events: set = set()


class CloudEventData(BaseModel):
    """CloudEvent data payload"""
    event_id: str
    event_type: str
    task_id: int
    user_id: str
    timestamp: str
    task_data: dict = {}
    title: Optional[str] = None
    remind_at: Optional[str] = None
    reminder_id: Optional[str] = None
    correlation_id: Optional[str] = None


class EventResponse(BaseModel):
    """Dapr event handler response"""
    status: str  # SUCCESS, RETRY, DROP


def is_event_processed(event_id: str) -> bool:
    """Check if event has already been processed (idempotency check)"""
    return event_id in _processed_events


def mark_event_processed(event_id: str) -> None:
    """Mark event as processed"""
    _processed_events.add(event_id)
    # Limit memory usage by keeping only recent events
    if len(_processed_events) > 10000:
        # Remove oldest entries (simple approach - in production use TTL)
        _processed_events.clear()


@router.get("/dapr/subscribe")
async def dapr_subscribe():
    """
    Dapr subscription configuration endpoint.

    Returns the list of topics this service subscribes to and their routes.
    Dapr calls this endpoint on startup to configure subscriptions.

    Returns:
        List of subscription configurations
    """
    return [
        {
            "pubsubname": "kafka-pubsub",
            "topic": "reminders",
            "route": "/events/reminders",
            "metadata": {
                "rawPayload": "false"
            }
        },
        {
            "pubsubname": "kafka-pubsub",
            "topic": "task-events",
            "route": "/events/tasks",
            "metadata": {
                "rawPayload": "false"
            }
        }
    ]


@router.post("/events/reminders", response_model=EventResponse)
async def handle_reminder_event(request: Request):
    """
    Handle reminder events from Dapr pub/sub.

    This endpoint receives reminder events when it's time to send a notification.

    Args:
        request: FastAPI request containing CloudEvent payload

    Returns:
        EventResponse with status (SUCCESS, RETRY, or DROP)
    """
    try:
        # Parse CloudEvent from request
        cloud_event = await request.json()
        logger.debug(f"Received reminder event: {cloud_event}")

        # Extract event data (may be nested in 'data' for CloudEvents)
        event_data = cloud_event.get("data", cloud_event)

        # Get event ID for idempotency
        event_id = event_data.get("event_id") or cloud_event.get("id")
        if not event_id:
            logger.warning("Reminder event missing event_id, generating one")
            import uuid
            event_id = str(uuid.uuid4())

        # Idempotency check
        if is_event_processed(event_id):
            logger.info(f"Reminder event {event_id} already processed, dropping")
            return EventResponse(status="DROP")

        # Extract reminder data
        task_id = event_data.get("task_id")
        user_id = event_data.get("user_id")
        title = event_data.get("title", "")
        remind_at = event_data.get("remind_at")

        logger.info(
            f"Processing reminder event: event_id={event_id}, task_id={task_id}, "
            f"user_id={user_id}, remind_at={remind_at}"
        )

        # TODO: Send notification via Web Push
        # For now, just log that we would send a notification
        logger.info(f"Would send notification for task '{title}' to user {user_id}")

        # Mark as processed
        mark_event_processed(event_id)

        return EventResponse(status="SUCCESS")

    except Exception as e:
        logger.error(f"Error processing reminder event: {e}", exc_info=True)
        # Return RETRY for transient errors, DROP for permanent errors
        return EventResponse(status="RETRY")


@router.post("/events/tasks", response_model=EventResponse)
async def handle_task_event(request: Request):
    """
    Handle task events from Dapr pub/sub.

    This endpoint receives task events (created, updated, completed, deleted)
    for sending relevant notifications.

    Args:
        request: FastAPI request containing CloudEvent payload

    Returns:
        EventResponse with status (SUCCESS, RETRY, or DROP)
    """
    try:
        # Parse CloudEvent from request
        cloud_event = await request.json()
        logger.debug(f"Received task event: {cloud_event}")

        # Extract event data
        event_data = cloud_event.get("data", cloud_event)

        # Get event ID for idempotency
        event_id = event_data.get("event_id") or cloud_event.get("id")
        if not event_id:
            logger.warning("Task event missing event_id, generating one")
            import uuid
            event_id = str(uuid.uuid4())

        # Idempotency check
        if is_event_processed(event_id):
            logger.info(f"Task event {event_id} already processed, dropping")
            return EventResponse(status="DROP")

        # Extract task data
        event_type = event_data.get("event_type") or cloud_event.get("type", "unknown")
        task_id = event_data.get("task_id")
        user_id = event_data.get("user_id")
        task_data = event_data.get("task_data", {})

        logger.info(
            f"Processing task event: event_id={event_id}, type={event_type}, "
            f"task_id={task_id}, user_id={user_id}"
        )

        # Handle different event types
        if event_type == "task.completed":
            logger.info(f"Task {task_id} completed - could send completion notification")
        elif event_type == "task.created":
            logger.info(f"Task {task_id} created - tracking for reminders")
        elif event_type == "task.updated":
            logger.info(f"Task {task_id} updated - checking if reminder needs update")
        elif event_type == "task.deleted":
            logger.info(f"Task {task_id} deleted - cancelling any scheduled reminders")

        # Mark as processed
        mark_event_processed(event_id)

        return EventResponse(status="SUCCESS")

    except Exception as e:
        logger.error(f"Error processing task event: {e}", exc_info=True)
        return EventResponse(status="RETRY")


@router.post("/jobs/reminder", response_model=EventResponse)
async def handle_reminder_job(request: Request):
    """
    Handle Dapr Jobs API callback for scheduled reminders (T042).

    This endpoint is called by Dapr when a scheduled reminder job fires.
    The job payload contains task details for sending the notification.

    Args:
        request: FastAPI request containing job payload

    Returns:
        EventResponse with status (SUCCESS, RETRY, or DROP)
    """
    try:
        # Parse job payload from Dapr Jobs API
        job_data = await request.json()
        logger.debug(f"Received reminder job: {job_data}")

        # Extract payload - Dapr Jobs wraps data in a specific format
        # The data field contains a StringValue with JSON-encoded payload
        data = job_data.get("data", {})
        if isinstance(data, dict) and "value" in data:
            import json
            payload = json.loads(data["value"])
        else:
            payload = data

        # Extract reminder details
        task_id = payload.get("task_id")
        user_id = payload.get("user_id")
        title = payload.get("title", "Task reminder")
        reminder_type = payload.get("reminder_type", "unknown")
        due_date = payload.get("due_date")

        logger.info(
            f"Processing reminder job: task_id={task_id}, user_id={user_id}, "
            f"reminder_type={reminder_type}, due_date={due_date}"
        )

        # Send notification based on reminder type
        if reminder_type == "24h":
            message = f"Reminder: '{title}' is due in 24 hours"
        elif reminder_type == "1h":
            message = f"Urgent: '{title}' is due in 1 hour!"
        else:
            message = f"Reminder: '{title}'"

        # TODO: Send actual notification via Web Push
        # For now, log the notification
        logger.info(f"Would send notification to user {user_id}: {message}")

        return EventResponse(status="SUCCESS")

    except Exception as e:
        logger.error(f"Error processing reminder job: {e}", exc_info=True)
        return EventResponse(status="RETRY")


@router.get("/health")
async def health_check():
    """Health check endpoint for the notification service"""
    return {"status": "healthy", "service": "notification-service"}
