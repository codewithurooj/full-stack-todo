"""Task model and schemas"""
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import ARRAY, String
from datetime import datetime
from typing import Optional, List


class TaskBase(SQLModel):
    """Base task fields"""
    title: str
    description: Optional[str] = None
    completed: bool = False
    priority: str = Field(default="medium", regex="^(high|medium|low)$")
    tags: List[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))

    # Due date and recurring fields (Feature 010)
    due_date: Optional[datetime] = None
    recurring_pattern: Optional[str] = Field(
        default=None,
        max_length=500,
        description="RFC 5545 RRULE or simple pattern (daily|weekly|monthly|custom)"
    )
    recurring_interval: Optional[int] = Field(
        default=None,
        ge=1,
        description="Interval between recurrences (e.g., 2 for every 2 days)"
    )
    recurring_days: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(ARRAY(String)),
        description="Days of week for weekly patterns (e.g., ['Monday', 'Friday'])"
    )
    recurring_end_date: Optional[datetime] = Field(
        default=None,
        description="End date for recurring pattern"
    )
    parent_task_id: Optional[int] = Field(
        default=None,
        foreign_key="tasks.id",
        description="Parent task ID if this is a recurring instance"
    )
    next_occurrence: Optional[datetime] = Field(
        default=None,
        description="Next scheduled occurrence for recurring tasks"
    )


class Task(TaskBase, table=True):
    """Task database model"""
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)  # JWT user ID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True


class TaskCreate(TaskBase):
    """Schema for creating a task"""
    pass


class TaskUpdate(SQLModel):
    """Schema for updating a task (all fields optional)"""
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[str] = Field(None, regex="^(high|medium|low)$")
    tags: Optional[List[str]] = None

    # Due date and recurring fields (Feature 010)
    due_date: Optional[datetime] = None
    recurring_pattern: Optional[str] = Field(None, max_length=500)
    recurring_interval: Optional[int] = Field(None, ge=1)
    recurring_days: Optional[List[str]] = None
    recurring_end_date: Optional[datetime] = None
    parent_task_id: Optional[int] = None
    next_occurrence: Optional[datetime] = None


class TaskRead(TaskBase):
    """Schema for reading a task"""
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
