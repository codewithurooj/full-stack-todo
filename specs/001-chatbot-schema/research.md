# Research: AI Chatbot Database Schema

**Feature**: 001-chatbot-schema
**Date**: 2025-12-27
**Status**: Completed

## Research Objectives

This document consolidates research findings for implementing the database schema for AI chatbot functionality. All technical decisions have been researched and documented below.

---

## 1. Alembic Migration Strategy

### Decision: Use Manual Migrations

**Rationale**:
- Need explicit control over CASCADE DELETE behavior
- Want to optimize indexes for specific query patterns
- Need PostgreSQL-specific features (composite indexes, CHECK constraints)
- Better documentation and version control

### Implementation Approach

**Migration File Structure**:
```python
# alembic/versions/001_add_chatbot_schema.py

def upgrade() -> None:
    # 1. Create conversations table with CASCADE foreign key
    # 2. Create messages table with CASCADE foreign key
    # 3. Add indexes optimized for read patterns
    # 4. Add CHECK constraints for data integrity

def downgrade() -> None:
    # Drop in reverse order (messages first, then conversations)
```

**Key Findings**:
- Alembic supports `ondelete='CASCADE'` in `ForeignKeyConstraint`
- Manual migrations provide better control than autogenerate
- Use `op.create_index()` with PostgreSQL-specific options
- Always test both upgrade and downgrade paths

**Best Practices**:
1. Validate data before applying constraints
2. Use `server_default=sa.func.now()` for database-level timestamps
3. Create indexes after tables for better performance
4. Document what each migration does in docstrings

---

## 2. SQLModel Foreign Key Configuration

### Decision: Simple FK without Relationship Fields

**Rationale**:
- Stateless API design doesn't need ORM relationship loading
- Prevents N+1 query problems
- Lightweight models suitable for REST API responses
- Easier to understand explicit queries

### Implementation Pattern

```python
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import INTEGER

class Conversation(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)

    # Simple FK definition without Relationship
    user_id: int = Field(
        sa_column=Column(
            INTEGER,
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True
        )
    )
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_message_at: datetime = Field(default_factory=datetime.utcnow)

class Message(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)

    # Simple FK definition
    conversation_id: int = Field(
        sa_column=Column(
            INTEGER,
            ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
            index=True
        )
    )
    role: str = Field(max_length=20)
    content: str = Field(sa_column=Column(sa.Text()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

**Cascade Delete Options**:
- `ondelete="CASCADE"` - Delete children when parent deleted
- `onupdate="CASCADE"` - Update children when parent ID changes

**Why Database-Level Cascade**:
- Enforced by PostgreSQL (always works, even outside ORM)
- Faster than ORM-level cascade
- Prevents orphaned records
- Works with manual SQL queries

---

## 3. Index Strategy

### Decision: Composite B-tree Indexes with INCLUDE Columns

**Rationale**:
- Read-heavy workload (fetching conversation history)
- Common query patterns: filter + sort
- Enable index-only scans (no table lookups needed)

### Index Design

**1. Conversations Table**:
```sql
-- Primary access: "get user's conversations"
CREATE INDEX idx_conversations_user_id
  ON conversations(user_id);

-- For sorting by recency
CREATE INDEX idx_conversations_last_message
  ON conversations(last_message_at DESC);
```

**2. Messages Table**:
```sql
-- Primary access: "get conversation's messages"
CREATE INDEX idx_messages_conversation_id
  ON messages(conversation_id);

-- Composite for filter + sort (CRITICAL for performance)
CREATE INDEX idx_messages_conversation_created
  ON messages(conversation_id, created_at);
```

**Performance Expectations**:
- Query 100 conversations for user: < 100ms (spec requirement: SC-002)
- Query 50 messages for conversation: < 50ms (spec requirement: SC-003)
- Uses B-tree indexes (default, best for range queries)

**When to Use Index Types**:
| Type | Use Case | This Project |
|------|----------|--------------|
| B-tree | Equality + range queries | ✅ Primary choice |
| Hash | Equality only | ❌ Not needed |
| GIN | Full-text search | ❌ Not in Phase III |
| BRIN | Very large tables | ❌ Not at this scale |

---

## 4. Timestamp Data Type

### Decision: Use TIMESTAMP (not TIMESTAMPTZ)

**Rationale**:
- Application handles timezone conversion (UTC)
- Identical storage (8 bytes) and performance
- Simpler for chronological ordering

**Implementation**:
```sql
CREATE TABLE conversations (
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE messages (
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**Ordering Guarantee**:
- All timestamps stored as UTC
- `ORDER BY created_at` gives correct chronological order
- Millisecond precision for uniqueness

**Alternative Considered**:
- TIMESTAMPTZ: Automatic timezone conversion
- **Rejected**: Application already handles UTC conversion
- No performance benefit, adds complexity

---

## 5. TEXT Column Performance

### Decision: Use TEXT with Default Storage

**Rationale**:
- No performance difference vs VARCHAR
- PostgreSQL TOAST automatically handles large content
- Supports 10,000+ character messages (requirement: FR-009)

**Storage Characteristics**:
```
Message content: 10,000 characters
Storage overhead: 4 bytes (TOAST header)
Total per message: ~10 KB

With compression (automatic):
- Typical compression: 2:1 ratio
- Actual storage: ~5 KB per message
- 100k messages: ~500 MB (vs 1 GB uncompressed)
```

**TOAST Behavior**:
- Automatic compression for text > 2KB
- Stored out-of-line (separate TOAST table)
- Transparent to application
- Decompressed automatically on SELECT

**Query Performance**:
- Full text fetch: 1-5ms (no additional cost)
- Substring operations: Supported
- No degradation vs VARCHAR

---

## 6. Neon PostgreSQL Considerations

### Platform-Specific Optimizations

**Connection Pooling**:
```python
# Use NullPool for Neon Serverless
from sqlalchemy.pool import NullPool

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=NullPool  # Critical for serverless
)
```

**Performance Characteristics**:
- Serverless compute may auto-suspend
- Connection timeout: 30 seconds
- Max connections: 100-200
- Recommended pool size: 20-30

**Storage Implications**:
- Conversations: ~50 KB (at 1000 conversations)
- Messages: ~500 MB (at 100k messages with compression)
- Indexes: ~150 MB
- Total: ~650 MB (well within limits)

---

## 7. Query Optimization Patterns

### Pattern 1: Get User's Conversations

```python
# Optimized query
from sqlmodel import select

stmt = select(Conversation).where(
    Conversation.user_id == user_id
).order_by(Conversation.last_message_at.desc())

conversations = session.exec(stmt).all()
```

**Index Used**: `idx_conversations_user_id`
**Expected Performance**: < 100ms for 100 conversations

### Pattern 2: Get Conversation Messages

```python
stmt = select(Message).where(
    Message.conversation_id == conversation_id
).order_by(Message.created_at.asc())

messages = session.exec(stmt).all()
```

**Index Used**: `idx_messages_conversation_created`
**Expected Performance**: < 50ms for 50 messages

### Pattern 3: Pagination (Avoid OFFSET)

```python
# GOOD: Cursor-based pagination
stmt = select(Message).where(
    Message.conversation_id == conversation_id,
    Message.created_at > last_seen_timestamp
).order_by(Message.created_at.asc()).limit(50)

# BAD: Offset-based pagination
stmt = select(Message).where(
    Message.conversation_id == conversation_id
).order_by(Message.created_at.asc()).offset(50).limit(50)
```

**Rationale**: OFFSET rescans all skipped rows; cursor-based uses index directly

---

## 8. Testing Strategy

### Migration Testing

1. **Validate Data Before Migration**:
```python
# Check users table exists
SELECT COUNT(*) FROM users;

# Verify no orphaned data (in future migrations)
SELECT COUNT(*) FROM conversations c
LEFT JOIN users u ON c.user_id = u.id
WHERE u.id IS NULL;
```

2. **Test Upgrade Path**:
```bash
alembic upgrade head
```

3. **Test Downgrade Path**:
```bash
alembic downgrade -1
alembic upgrade head
```

### Performance Testing

```sql
-- Verify index usage
EXPLAIN ANALYZE
SELECT * FROM conversations WHERE user_id = 1;

-- Should show: Index Scan using idx_conversations_user_id
```

---

## 9. Database Initialization

### Development Setup

```python
# Option 1: Alembic migrations (production-ready)
from alembic.config import Config
from alembic import command

alembic_cfg = Config("alembic.ini")
command.upgrade(alembic_cfg, "head")

# Option 2: SQLModel create_all (development only)
from sqlmodel import SQLModel, create_engine

engine = create_engine(DATABASE_URL)
SQLModel.metadata.create_all(engine)
```

**Recommendation**: Use Alembic for all environments (consistency)

---

## 10. Migration Rollback Strategy

### Downgrade Function

```python
def downgrade() -> None:
    """
    Rollback: Drop messages and conversations tables.

    WARNING: This will delete all conversation history!
    Only run in development or with database backup.
    """
    # Drop in reverse dependency order
    op.drop_table('messages')
    op.drop_table('conversations')
```

### Safety Checks

Before production rollback:
1. Create database backup
2. Verify downgrade script in staging
3. Document data loss implications
4. Get approval from stakeholders

---

## Summary of Decisions

| Decision Point | Choice | Rationale |
|----------------|--------|-----------|
| **Migration Approach** | Manual migrations | Explicit control, better docs |
| **Foreign Keys** | Simple FK, no Relationship | Stateless API, prevents N+1 |
| **Cascade Delete** | Database-level CASCADE | Reliable, enforced by PostgreSQL |
| **Indexes** | Composite B-tree | Read-heavy workload |
| **Timestamp Type** | TIMESTAMP | UTC in application, simpler |
| **Text Storage** | TEXT | No performance cost, auto-compression |
| **Connection Pool** | NullPool | Neon serverless requirement |

---

## References

- Alembic Documentation: https://alembic.sqlalchemy.org/
- SQLModel Documentation: https://sqlmodel.tiangolo.com/
- PostgreSQL Index Documentation: https://www.postgresql.org/docs/current/indexes.html
- Neon PostgreSQL: https://neon.tech/docs/

---

## Next Steps

1. Create SQLModel models (Conversation, Message)
2. Create Alembic migration script
3. Write unit tests for models
4. Write integration tests for schema
5. Document migration runbook

All research tasks completed. Ready to proceed to Phase 1: Design & Data Modeling.
