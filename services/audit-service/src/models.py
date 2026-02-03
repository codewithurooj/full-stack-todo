"""
Database Models
SQLModel definitions for audit service
"""
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID


class AuditLog(SQLModel, table=True):
    """Audit log model matching backend database schema"""
    __tablename__ = "audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: UUID = Field(unique=True, index=True)  # Idempotency key
    timestamp: datetime  # Original event timestamp (not insertion time)
    user_id: str = Field(index=True)
    task_id: Optional[int] = Field(default=None, index=True)
    operation_type: str = Field(index=True)  # task.created, task.updated, etc.
    event_payload: Dict[str, Any] = Field(sa_column=Column(JSON))  # Full event as JSONB
    system_generated: bool = False  # TRUE if from recurring-task-service
    created_at: datetime = Field(default_factory=datetime.utcnow)  # DB insertion time
