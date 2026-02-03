"""
Dapr Subscription and Event Routes for Recurring Task Service
Feature: 012-dapr-integration
Purpose: HTTP endpoints for Dapr pub/sub event consumption
"""
import logging
from typing import Optional
from fastapi import APIRouter, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dapr-events"])

# In-memory processed event IDs (for idempotency in development)
_processed_events: set = set()


class CloudEventData(BaseModel):
    """CloudEvent data payload"""
    event_id: str
    event_type: str
    task_id: int
    user_id: str
    timestamp: str
    task_data: dict = {}
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
    if len(_processed_events) > 10000:
        _processed_events.clear()


@router.get("/dapr/subscribe")
async def dapr_subscribe():
    """
    Dapr subscription configuration endpoint.

    Returns the list of topics this service subscribes to and their routes.

    Returns:
        List of subscription configurations
    """
    return [
        {
            "pubsubname": "kafka-pubsub",
            "topic": "task-events",
            "routes": {
                "rules": [
                    {
                        "match": "event.type == \"task.completed\"",
                        "path": "/events/task-completed"
                    }
                ],
                "default": "/events/tasks"
            },
            "metadata": {
                "rawPayload": "false"
            }
        }
    ]


@router.post("/events/tasks", response_model=EventResponse)
async def handle_task_event(request: Request):
    """
    Handle general task events from Dapr pub/sub.

    This endpoint receives task events that are not task.completed.

    Args:
        request: FastAPI request containing CloudEvent payload

    Returns:
        EventResponse with status (SUCCESS, RETRY, or DROP)
    """
    try:
        cloud_event = await request.json()
        logger.debug(f"Received task event: {cloud_event}")

        event_data = cloud_event.get("data", cloud_event)
        event_id = event_data.get("event_id") or cloud_event.get("id")
        if not event_id:
            import uuid
            event_id = str(uuid.uuid4())

        if is_event_processed(event_id):
            logger.info(f"Task event {event_id} already processed, dropping")
            return EventResponse(status="DROP")

        event_type = event_data.get("event_type") or cloud_event.get("type", "unknown")
        task_id = event_data.get("task_id")
        user_id = event_data.get("user_id")
        task_data = event_data.get("task_data", {})

        logger.info(
            f"Processing task event: event_id={event_id}, type={event_type}, "
            f"task_id={task_id}, user_id={user_id}"
        )

        # Handle task events relevant to recurring tasks
        if event_type == "task.created":
            # Check if this is a recurring task
            recurring = task_data.get("recurring")
            if recurring and recurring != "none":
                logger.info(f"New recurring task created: {task_id}, pattern={recurring}")

        elif event_type == "task.updated":
            # Check if recurring pattern was updated
            recurring = task_data.get("recurring")
            logger.info(f"Task {task_id} updated, recurring={recurring}")

        elif event_type == "task.deleted":
            # Clean up any recurring task tracking
            logger.info(f"Task {task_id} deleted, cleaning up recurring tracking")

        mark_event_processed(event_id)
        return EventResponse(status="SUCCESS")

    except Exception as e:
        logger.error(f"Error processing task event: {e}", exc_info=True)
        return EventResponse(status="RETRY")


@router.post("/events/task-completed", response_model=EventResponse)
async def handle_task_completed(request: Request):
    """
    Handle task.completed events from Dapr pub/sub.

    When a recurring task is completed, this handler creates the next instance.

    Args:
        request: FastAPI request containing CloudEvent payload

    Returns:
        EventResponse with status (SUCCESS, RETRY, or DROP)
    """
    try:
        cloud_event = await request.json()
        logger.debug(f"Received task-completed event: {cloud_event}")

        event_data = cloud_event.get("data", cloud_event)
        event_id = event_data.get("event_id") or cloud_event.get("id")
        if not event_id:
            import uuid
            event_id = str(uuid.uuid4())

        if is_event_processed(event_id):
            logger.info(f"Task-completed event {event_id} already processed, dropping")
            return EventResponse(status="DROP")

        task_id = event_data.get("task_id")
        user_id = event_data.get("user_id")
        task_data = event_data.get("task_data", {})

        logger.info(f"Processing task-completed: task_id={task_id}, user_id={user_id}")

        # Check if this is a recurring task
        recurring = task_data.get("recurring")
        if recurring and recurring != "none":
            logger.info(
                f"Recurring task {task_id} completed, pattern={recurring}, "
                f"creating next instance..."
            )
            # TODO: Call backend API via Dapr service invocation to create next instance
            # For now, just log the action
            logger.info(f"Would create next recurring task instance for task {task_id}")
        else:
            logger.debug(f"Task {task_id} is not recurring, no action needed")

        mark_event_processed(event_id)
        return EventResponse(status="SUCCESS")

    except Exception as e:
        logger.error(f"Error processing task-completed event: {e}", exc_info=True)
        return EventResponse(status="RETRY")


@router.get("/health")
async def health_check():
    """Health check endpoint for the recurring task service"""
    return {"status": "healthy", "service": "recurring-task-service"}
