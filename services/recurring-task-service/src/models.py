"""
Database Models
SQLModel definitions for recurring task service
"""
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional, List


class Task(SQLModel, table=True):
    """Task model matching backend database schema"""
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    title: str
    description: Optional[str] = None
    completed: bool = False
    priority: str = "medium"  # low, medium, high
    tags: List[str] = Field(default=[], sa_column_kwargs={"type_": "JSON"})

    # Recurring fields (Feature 010)
    recurring_pattern: str = "none"  # none, daily, weekly, monthly
    recurring_interval: int = 1
    recurring_end_date: Optional[datetime] = None
    parent_task_id: Optional[int] = Field(default=None, index=True)

    # Due date and reminders (Feature 010)
    due_date: Optional[datetime] = None
    remind_at: Optional[datetime] = None
    reminded: bool = False

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
