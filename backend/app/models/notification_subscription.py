"""Notification subscription model for Web Push notifications"""
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class NotificationSubscriptionBase(SQLModel):
    """Base notification subscription fields"""
    user_id: int = Field(foreign_key="users.id", nullable=False, description="User who granted notification permission")
    endpoint: str = Field(nullable=False, description="Push service endpoint (e.g., FCM URL)")
    p256dh: str = Field(nullable=False, description="Client public key for message encryption (VAPID)")
    auth: str = Field(nullable=False, description="Authentication secret for message verification")


class NotificationSubscription(NotificationSubscriptionBase, table=True):
    """Notification subscription database model"""
    __tablename__ = "notification_subscriptions"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Subscription creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last subscription update")

    class Config:
        arbitrary_types_allowed = True


class NotificationSubscriptionCreate(NotificationSubscriptionBase):
    """Schema for creating a notification subscription"""
    pass


class NotificationSubscriptionUpdate(SQLModel):
    """Schema for updating a notification subscription (all fields optional)"""
    endpoint: Optional[str] = None
    p256dh: Optional[str] = None
    auth: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationSubscriptionRead(NotificationSubscriptionBase):
    """Schema for reading a notification subscription"""
    id: int
    created_at: datetime
    updated_at: datetime
