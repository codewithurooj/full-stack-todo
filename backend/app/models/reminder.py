"""Reminder model and schemas for task notifications.

This module defines the Reminder model for scheduling and tracking
task notifications/reminders.
"""

from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class ReminderBase(SQLModel):
    """Base reminder fields"""
    task_id: int = Field(foreign_key="tasks.id", description="Task to remind about")
    offset_minutes: int = Field(
        ge=0,
        description="Minutes before due_date to send reminder (e.g., 15 for 15 min before)"
    )
    delivered: bool = Field(default=False, description="Whether reminder has been sent")
    delivery_status: str = Field(
        default="pending",
        regex="^(pending|sent|failed|dismissed|snoozed)$",
        description="Status of reminder delivery"
    )


class Reminder(ReminderBase, table=True):
    """Reminder database model"""
    __tablename__ = "reminders"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True, description="User who created the reminder")
    remind_at: datetime = Field(
        description="Absolute UTC time when reminder should trigger"
    )
    delivery_timestamp: Optional[datetime] = Field(
        default=None,
        description="When the reminder was actually delivered"
    )
    notification_id: Optional[str] = Field(
        default=None,
        max_length=255,
        description="External notification system ID"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True


class ReminderCreate(ReminderBase):
    """Schema for creating a reminder"""
    pass


class ReminderUpdate(SQLModel):
    """Schema for updating a reminder (all fields optional)"""
    offset_minutes: Optional[int] = Field(None, ge=0)
    delivered: Optional[bool] = None
    delivery_status: Optional[str] = Field(
        None,
        regex="^(pending|sent|failed|dismissed|snoozed)$"
    )
    delivery_timestamp: Optional[datetime] = None
    notification_id: Optional[str] = None
    remind_at: Optional[datetime] = None


class ReminderRead(ReminderBase):
    """Schema for reading a reminder"""
    id: int
    user_id: str
    remind_at: datetime
    delivery_timestamp: Optional[datetime]
    notification_id: Optional[str]
    created_at: datetime
    updated_at: datetime


class ReminderSnooze(SQLModel):
    """Schema for snoozing a reminder"""
    snooze_minutes: int = Field(
        ge=1,
        le=1440,
        description="Minutes to snooze (max 24 hours)"
    )
