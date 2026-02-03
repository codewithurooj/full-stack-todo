"""
Database models for notification service
"""
from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel


class NotificationLog(SQLModel, table=True):
    """Log of sent notifications"""
    __tablename__ = "notification_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    reminder_id: str = Field(index=True)
    task_id: int = Field(index=True)
    user_id: int = Field(index=True)
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    status: str  # 'sent', 'failed', 'rate_limited'
    error_message: Optional[str] = None


class PushSubscription(SQLModel, table=True):
    """Web Push subscriptions for users"""
    __tablename__ = "push_subscriptions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    endpoint: str = Field(index=True, unique=True)
    p256dh: str  # Encryption key
    auth: str  # Authentication secret
    created_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = Field(default=True)


class UserNotificationStats(SQLModel, table=True):
    """Track notification rate limiting per user"""
    __tablename__ = "user_notification_stats"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, unique=True)
    notification_count: int = Field(default=0)
    window_start: datetime = Field(default_factory=datetime.utcnow)
