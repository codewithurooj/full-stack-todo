"""Conversation model for AI chatbot feature"""
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, ForeignKey, String
from datetime import datetime
from typing import Optional


class Conversation(SQLModel, table=True):
    """
    Represents a chat session between a user and the AI assistant.

    Relationships:
    - Belongs to User (user_id -> users.id)
    - Has many Messages

    Lifecycle:
    - Created on first chat message
    - Updated (last_message_at) on each new message
    - Deleted when user deleted (CASCADE)
    """
    __tablename__ = "conversations"

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: str = Field(
        sa_column=Column(
            String,
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True
        )
    )

    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_message_at: datetime = Field(default_factory=datetime.utcnow)
