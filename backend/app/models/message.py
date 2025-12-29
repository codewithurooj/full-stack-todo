"""Message model for AI chatbot feature"""
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, ForeignKey, Integer, Text, CheckConstraint
from datetime import datetime
from typing import Optional


class Message(SQLModel, table=True):
    """
    Represents a single message in a conversation.

    Relationships:
    - Belongs to Conversation (conversation_id -> conversations.id)

    Constraints:
    - Role must be 'user' or 'assistant'
    - Content cannot be empty

    Lifecycle:
    - Created when user or AI sends message
    - Immutable after creation (no updates)
    - Deleted when conversation deleted (CASCADE)
    """
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="check_role_valid"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    conversation_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
            index=True
        )
    )

    role: str = Field(max_length=20)  # 'user' or 'assistant'
    content: str = Field(sa_column=Column(Text(), nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow)
