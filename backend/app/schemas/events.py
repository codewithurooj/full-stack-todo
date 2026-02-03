"""
Event schema definitions for Kafka messages
Feature 011: Event-Driven Architecture with Kafka
"""
from pydantic import BaseModel, Field, UUID4
from datetime import datetime
from typing import Literal, Optional, Dict, Any, List


class TaskEventSchema(BaseModel):
    """Schema for task events published to task-events topic"""

    event_id: UUID4 = Field(..., description="Unique event identifier for idempotency")
    event_type: Literal["task.created", "task.updated", "task.deleted", "task.completed"] = Field(
        ..., description="Type of task operation"
    )
    schema_version: str = Field(default="1.0.0", description="Event schema version")
    timestamp: datetime = Field(..., description="Event generation time in UTC")
    user_id: str = Field(..., description="User who owns the task")
    task_id: int = Field(..., description="Task identifier")
    task_data: Dict[str, Any] = Field(..., description="Full task object at time of event")

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "event_type": "task.created",
                "schema_version": "1.0.0",
                "timestamp": "2026-01-12T10:30:00.000Z",
                "user_id": "user123",
                "task_id": 123,
                "task_data": {
                    "id": 123,
                    "user_id": "user123",
                    "title": "Buy groceries",
                    "description": "Milk, eggs, bread",
                    "completed": False,
                    "priority": "high",
                    "tags": ["shopping", "urgent"],
                    "recurring_pattern": "weekly",
                    "recurring_interval": 1,
                    "parent_task_id": None,
                    "due_date": "2026-01-19T09:00:00.000Z",
                    "created_at": "2026-01-12T10:30:00.000Z",
                    "updated_at": "2026-01-12T10:30:00.000Z",
                },
            }
        }


class ReminderEventSchema(BaseModel):
    """Schema for reminder events published to reminders topic"""

    event_id: UUID4 = Field(..., description="Unique event identifier")
    schema_version: str = Field(default="1.0.0", description="Event schema version")
    timestamp: datetime = Field(..., description="Event generation time in UTC")
    reminder_id: str = Field(..., description="Unique identifier for idempotency (reminder-{task_id}-{remind_at})")
    task_id: int = Field(..., description="Task to remind about")
    user_id: str = Field(..., description="User to notify")
    title: str = Field(..., description="Task title for notification body")
    remind_at: datetime = Field(..., description="When to send notification")
    due_date: Optional[datetime] = Field(None, description="Task due date for context")

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "660e8400-e29b-41d4-a716-446655440001",
                "schema_version": "1.0.0",
                "timestamp": "2026-01-12T10:30:00.000Z",
                "reminder_id": "reminder-123-2026-01-19T08:00:00Z",
                "task_id": 123,
                "user_id": "user123",
                "title": "Buy groceries",
                "remind_at": "2026-01-19T08:00:00.000Z",
                "due_date": "2026-01-19T09:00:00.000Z",
            }
        }


class TaskUpdateEventSchema(BaseModel):
    """Schema for real-time task update events published to task-updates topic (optional)"""

    event_id: UUID4 = Field(..., description="Unique event identifier")
    event_type: Literal["task.created", "task.updated", "task.deleted", "task.completed"] = Field(
        ..., description="Type of task operation"
    )
    schema_version: str = Field(default="1.0.0", description="Event schema version")
    timestamp: datetime = Field(..., description="Event generation time in UTC")
    user_id: str = Field(..., description="User who owns the task")
    task_id: int = Field(..., description="Task identifier")
    changes: Dict[str, Any] = Field(..., description="Fields that changed (for updates) or full object (for creates)")

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "770e8400-e29b-41d4-a716-446655440002",
                "event_type": "task.updated",
                "schema_version": "1.0.0",
                "timestamp": "2026-01-12T10:35:00.000Z",
                "user_id": "user123",
                "task_id": 123,
                "changes": {"title": "Buy groceries (updated)", "completed": True},
            }
        }
