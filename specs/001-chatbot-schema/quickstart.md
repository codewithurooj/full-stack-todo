# Quickstart Guide: AI Chatbot Database Schema

**Feature**: 001-chatbot-schema
**Date**: 2025-12-27
**Audience**: Developers implementing this feature

## Overview

This guide walks you through implementing and testing the database schema for the AI chatbot feature. Follow these steps sequentially to add `conversations` and `messages` tables to your existing Neon PostgreSQL database.

---

## Prerequisites

- ✅ Backend setup complete (FastAPI + SQLModel)
- ✅ Neon PostgreSQL database configured
- ✅ `users` table exists from Phase II
- ✅ Alembic initialized (or will initialize in step 1)
- ✅ Python 3.13+ environment active

---

## Step 1: Create SQLModel Models

Create two new model files in `backend/app/models/`:

### File: `backend/app/models/conversation.py`

```python
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, ForeignKey, Integer
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

    user_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True
        )
    )

    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_message_at: datetime = Field(default_factory=datetime.utcnow)
```

### File: `backend/app/models/message.py`

```python
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
```

### Register Models

Update `backend/app/models/__init__.py`:

```python
from .user import User
from .task import Task
from .conversation import Conversation  # NEW
from .message import Message  # NEW

__all__ = ["User", "Task", "Conversation", "Message"]
```

---

## Step 2: Create Alembic Migration

### Initialize Alembic (if not already done)

```bash
cd backend
alembic init alembic
```

### Configure Alembic

Edit `backend/alembic/env.py`:

```python
from app.models import SQLModel  # Import your base model
from app.config import settings

# Set database URL from environment
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Set metadata for autogenerate support
target_metadata = SQLModel.metadata
```

### Create Migration File

```bash
# Manual migration (recommended)
alembic revision -m "add_chatbot_schema"
```

This creates: `backend/alembic/versions/XXXX_add_chatbot_schema.py`

### Edit Migration File

Replace contents with:

```python
"""Add chatbot schema

Revision ID: XXXX
Revises: <previous_revision>
Create Date: 2025-12-27
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'XXXX'
down_revision = '<previous_revision>'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('last_message_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'],
                                name='fk_conversations_user_id',
                                ondelete='CASCADE'),
    )

    # Create index on user_id
    op.create_index('ix_conversations_user_id', 'conversations', ['user_id'])

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'],
                                name='fk_messages_conversation_id',
                                ondelete='CASCADE'),
        sa.CheckConstraint("role IN ('user', 'assistant')",
                          name='check_role_valid'),
    )

    # Create index on conversation_id
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])

def downgrade() -> None:
    # Drop in reverse order
    op.drop_table('messages')
    op.drop_table('conversations')
```

---

## Step 3: Run Migration

### Development (Local Database)

```bash
# Run migration
alembic upgrade head

# Verify success
alembic current
# Should show: XXXX (add_chatbot_schema) (head)
```

### Production (Neon Database)

```bash
# Set production database URL
export DATABASE_URL="postgresql://user:pass@ep-xxx.neon.tech/db"

# Run migration
alembic upgrade head

# Verify
alembic current
```

---

## Step 4: Verify Schema

### Check Tables Created

```sql
-- Connect to your database and run:

-- List tables
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Should include: conversations, messages, users, tasks

-- Describe conversations table
\d conversations

-- Describe messages table
\d messages
```

### Verify Foreign Keys

```sql
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints AS rc
  ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name IN ('conversations', 'messages');

-- Expected:
-- fk_conversations_user_id: conversations.user_id -> users.id (CASCADE)
-- fk_messages_conversation_id: messages.conversation_id -> conversations.id (CASCADE)
```

### Verify Indexes

```sql
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('conversations', 'messages')
ORDER BY tablename, indexname;

-- Expected:
-- ix_conversations_user_id
-- ix_messages_conversation_id
```

---

## Step 5: Test with Sample Data

### Insert Test Conversation

```python
# backend/test_schema.py
from sqlmodel import Session, create_engine, select
from app.models import Conversation, Message, User
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with Session(engine) as session:
    # Get first user (assumes users exist)
    user = session.exec(select(User).limit(1)).first()

    if not user:
        print("No users found. Create a user first.")
        exit(1)

    # Create conversation
    conversation = Conversation(
        user_id=user.id,
    )
    session.add(conversation)
    session.commit()
    session.refresh(conversation)

    print(f"Created conversation {conversation.id} for user {user.id}")

    # Add messages
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content="Hello, can you help me create a task?"
    )
    session.add(user_message)
    session.commit()

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content="Of course! I can help you create a task. What would you like to add?"
    )
    session.add(assistant_message)
    session.commit()

    print(f"Added 2 messages to conversation {conversation.id}")

    # Retrieve conversation with messages
    messages = session.exec(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
    ).all()

    print(f"\nConversation history ({len(messages)} messages):")
    for msg in messages:
        print(f"  [{msg.role}]: {msg.content}")
```

### Run Test

```bash
python backend/test_schema.py
```

Expected output:
```
Created conversation 1 for user 1
Added 2 messages to conversation 1

Conversation history (2 messages):
  [user]: Hello, can you help me create a task?
  [assistant]: Of course! I can help you create a task. What would you like to add?
```

---

## Step 6: Query Performance Testing

### Test Query 1: Get User's Conversations

```python
from sqlmodel import Session, create_engine, select
from app.models import Conversation
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with Session(engine) as session:
    user_id = 1  # Replace with actual user ID

    conversations = session.exec(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.last_message_at.desc())
    ).all()

    print(f"User {user_id} has {len(conversations)} conversations")
```

### Test Query 2: Get Conversation Messages

```python
from sqlmodel import Session, create_engine, select
from app.models import Message
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with Session(engine) as session:
    conversation_id = 1  # Replace with actual conversation ID

    messages = session.exec(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    ).all()

    print(f"Conversation {conversation_id} has {len(messages)} messages")
    for msg in messages:
        print(f"  [{msg.role}]: {msg.content[:50]}...")
```

### Performance Expectations

- Get user's conversations (100 conversations): < 100ms
- Get conversation messages (50 messages): < 50ms

Use `EXPLAIN ANALYZE` in PostgreSQL to verify index usage:

```sql
EXPLAIN ANALYZE
SELECT * FROM conversations WHERE user_id = 1;
-- Should show: Index Scan using ix_conversations_user_id
```

---

## Step 7: Rollback Migration (if needed)

### Development

```bash
# Rollback one migration
alembic downgrade -1

# Verify
alembic current
```

### Production

⚠️ **WARNING**: This will delete all conversation data!

```bash
# Create database backup first
pg_dump $DATABASE_URL > backup_before_rollback.sql

# Rollback
alembic downgrade -1
```

---

## Troubleshooting

### Issue: Migration fails with "relation does not exist"

**Cause**: `users` table doesn't exist

**Fix**:
```bash
# Verify users table exists
psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"

# If not, run previous migrations first
alembic upgrade head
```

### Issue: Foreign key constraint violation

**Cause**: Trying to create conversation for non-existent user

**Fix**:
```python
# Always verify user exists first
user = session.get(User, user_id)
if not user:
    raise ValueError(f"User {user_id} not found")
```

### Issue: "role must be 'user' or 'assistant'" error

**Cause**: CHECK constraint violation

**Fix**:
```python
# Ensure role is exactly 'user' or 'assistant'
message = Message(
    conversation_id=1,
    role="user",  # NOT "User" or "USER"
    content="Hello"
)
```

---

## Next Steps

After completing this quickstart:

1. ✅ Schema is ready for MCP server integration
2. ✅ Ready to implement chat endpoint
3. ✅ Can proceed with Phase III features

**Next Features to Implement**:
- MCP Server with 5 custom tools (separate feature)
- Stateless Chat API endpoint (separate feature)
- Frontend ChatKit UI (separate feature)

---

## Resources

- **Data Model**: See `data-model.md` for entity relationships
- **SQL Schema**: See `contracts/schema.sql` for complete DDL
- **Research**: See `research.md` for technical decisions
- **Plan**: See `plan.md` for overall implementation strategy

---

## Summary Checklist

- [ ] SQLModel models created (Conversation, Message)
- [ ] Alembic migration created and configured
- [ ] Migration run successfully (`alembic upgrade head`)
- [ ] Tables verified in database
- [ ] Foreign keys verified (CASCADE delete)
- [ ] Indexes verified
- [ ] Test data inserted successfully
- [ ] Queries tested and performing well
- [ ] Ready for next feature (MCP server)

🎉 **Schema implementation complete!**
