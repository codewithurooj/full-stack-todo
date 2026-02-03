"""
Dapr Subscription and Event Routes for Audit Service
Feature: 012-dapr-integration
Purpose: HTTP endpoints for Dapr pub/sub event consumption - logs ALL task events
"""
import logging
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dapr-events"])

# In-memory processed event IDs (for idempotency in development)
_processed_events: set = set()

# In-memory audit log (for development - production uses database)
_audit_log: list = []


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


class AuditLogEntry(BaseModel):
    """Audit log entry"""
    event_id: str
    event_type: str
    task_id: int
    user_id: str
    timestamp: str
    task_data: dict
    received_at: str
    correlation_id: Optional[str] = None


def is_event_processed(event_id: str) -> bool:
    """Check if event has already been processed (idempotency check)"""
    return event_id in _processed_events


def mark_event_processed(event_id: str) -> None:
    """Mark event as processed"""
    _processed_events.add(event_id)
    if len(_processed_events) > 10000:
        _processed_events.clear()


def log_audit_event(entry: AuditLogEntry) -> None:
    """Store audit log entry (in-memory for development)"""
    _audit_log.append(entry.model_dump())
    # Keep only last 1000 entries in memory
    if len(_audit_log) > 1000:
        _audit_log.pop(0)


@router.get("/dapr/subscribe")
async def dapr_subscribe():
    """
    Dapr subscription configuration endpoint.

    Audit service subscribes to ALL task events for compliance logging.

    Returns:
        List of subscription configurations
    """
    return [
        {
            "pubsubname": "kafka-pubsub",
            "topic": "task-events",
            "route": "/events/tasks",
            "metadata": {
                "rawPayload": "false"
            }
        }
    ]


@router.post("/events/tasks", response_model=EventResponse)
async def handle_task_event(request: Request):
    """
    Handle ALL task events from Dapr pub/sub for audit logging.

    This endpoint receives every task event (created, updated, completed, deleted)
    and logs them to the audit trail.

    Args:
        request: FastAPI request containing CloudEvent payload

    Returns:
        EventResponse with status (SUCCESS, RETRY, or DROP)
    """
    try:
        cloud_event = await request.json()
        logger.debug(f"Received task event for audit: {cloud_event}")

        event_data = cloud_event.get("data", cloud_event)

        # Get event ID for idempotency
        event_id = event_data.get("event_id") or cloud_event.get("id")
        if not event_id:
            import uuid
            event_id = str(uuid.uuid4())

        # Idempotency check
        if is_event_processed(event_id):
            logger.info(f"Audit event {event_id} already processed, dropping")
            return EventResponse(status="DROP")

        # Extract event data
        event_type = event_data.get("event_type") or cloud_event.get("type", "unknown")
        task_id = event_data.get("task_id")
        user_id = event_data.get("user_id")
        task_data = event_data.get("task_data", {})
        timestamp = event_data.get("timestamp") or cloud_event.get("time", "")
        correlation_id = event_data.get("correlation_id")

        # Create audit log entry
        audit_entry = AuditLogEntry(
            event_id=event_id,
            event_type=event_type,
            task_id=task_id,
            user_id=user_id,
            timestamp=timestamp,
            task_data=task_data,
            received_at=datetime.now(timezone.utc).isoformat(),
            correlation_id=correlation_id
        )

        # Log to audit trail
        log_audit_event(audit_entry)

        logger.info(
            f"Audit logged: event_id={event_id}, type={event_type}, "
            f"task_id={task_id}, user_id={user_id}"
        )

        # Mark as processed
        mark_event_processed(event_id)

        return EventResponse(status="SUCCESS")

    except Exception as e:
        logger.error(f"Error processing audit event: {e}", exc_info=True)
        return EventResponse(status="RETRY")


@router.get("/audit/events")
async def get_audit_events(limit: int = 100, user_id: Optional[str] = None):
    """
    Retrieve audit log entries.

    Args:
        limit: Maximum number of entries to return
        user_id: Optional filter by user ID

    Returns:
        List of audit log entries
    """
    entries = _audit_log[-limit:]

    if user_id:
        entries = [e for e in entries if e.get("user_id") == user_id]

    return {"entries": entries, "total": len(entries)}


@router.get("/audit/events/{event_id}")
async def get_audit_event(event_id: str):
    """
    Retrieve a specific audit log entry by event ID.

    Args:
        event_id: Event ID to retrieve

    Returns:
        Audit log entry or 404
    """
    for entry in _audit_log:
        if entry.get("event_id") == event_id:
            return entry

    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Event not found")


@router.get("/health")
async def health_check():
    """Health check endpoint for the audit service"""
    return {
        "status": "healthy",
        "service": "audit-service",
        "audit_entries_in_memory": len(_audit_log)
    }
