# Data Model: AI Chatbot Database Schema

**Feature**: 001-chatbot-schema
**Date**: 2025-12-27
**Status**: Design

## Overview

This document defines the data model for persistent conversation and message storage supporting the Phase III AI chatbot feature. The model consists of two new entities that integrate with the existing Phase II `users` table.

## Entity Relationship Diagram

```
┌─────────────────┐
│     users       │ (existing from Phase II)
│─────────────────│
│ id (PK)         │
│ email           │
│ password_hash   │
│ created_at      │
└─────────────────┘
        │
        │ 1:N
        │
        ▼
┌─────────────────┐
│  conversations  │
│─────────────────│
│ id (PK)         │
│ user_id (FK)    │───────► users.id
│ started_at      │
│ last_message_at │
└─────────────────┘
        │
        │ 1:N
        │
        ▼
┌─────────────────┐
│    messages     │
│─────────────────│
│ id (PK)         │
│ conversation_id │───────► conversations.id
│ role            │
│ content         │
│ created_at      │
└─────────────────┘
```

## Entities

### 1. Conversation

Represents a chat session between a user and the AI assistant.

**Purpose**: Track individual chat sessions for a user, enabling the system to maintain multiple concurrent conversations and retrieve conversation-specific history.

**Lifecycle**:
- Created when user sends first message to chatbot (or starts new conversation)
- Updated (`last_message_at`) each time a new message is added
- Persists indefinitely (no automatic cleanup in Phase III)
- Deleted when user is deleted (CASCADE)

**Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, SERIAL | Unique conversation identifier |
| `user_id` | INTEGER | NOT NULL, FOREIGN KEY → users(id) | Owner of this conversation |
| `started_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | When conversation was created |
| `last_message_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | When last message was added (updated on each message) |

**Indexes**:
- Primary key index on `id` (automatic)
- Index on `user_id` for fast "get all conversations for user" queries

**Relationships**:
- **Belongs to**: User (user_id → users.id)
- **Has many**: Messages (one conversation contains multiple messages)

**Validation Rules**:
- `user_id` must reference a valid existing user
- `last_message_at` must be >= `started_at`
- Cannot create conversation without valid user_id

**Deletion Behavior**:
- When conversation deleted → cascade delete all messages in that conversation
- When user deleted → cascade delete all conversations (and transitively all messages)

**Query Patterns**:
```sql
-- Get all conversations for a user (ordered by most recent)
SELECT * FROM conversations
WHERE user_id = ?
ORDER BY last_message_at DESC;

-- Get conversation by ID (with user check)
SELECT * FROM conversations
WHERE id = ? AND user_id = ?;

-- Update last_message_at when new message added
UPDATE conversations
SET last_message_at = NOW()
WHERE id = ?;
```

---

### 2. Message

Represents a single message in a conversation (either from user or AI assistant).

**Purpose**: Store the complete history of all messages exchanged in a conversation, enabling the chatbot to retrieve full context for stateless requests.

**Lifecycle**:
- Created when user sends message or AI generates response
- Immutable once created (no updates or deletes except cascade from conversation)
- Persists with parent conversation
- Deleted when conversation is deleted (CASCADE)

**Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, SERIAL | Unique message identifier |
| `conversation_id` | INTEGER | NOT NULL, FOREIGN KEY → conversations(id) | Conversation this message belongs to |
| `role` | VARCHAR(20) | NOT NULL, CHECK (role IN ('user', 'assistant')) | Who sent this message |
| `content` | TEXT | NOT NULL | Message text content (supports 10k+ characters) |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | When message was created |

**Indexes**:
- Primary key index on `id` (automatic)
- Index on `conversation_id` for fast "get all messages for conversation" queries

**Relationships**:
- **Belongs to**: Conversation (conversation_id → conversations.id)

**Validation Rules**:
- `conversation_id` must reference a valid existing conversation
- `role` must be exactly 'user' or 'assistant' (no other values allowed)
- `content` cannot be empty or null
- `created_at` is set automatically and cannot be modified

**Deletion Behavior**:
- When message deleted → no cascade effects (messages have no dependents)
- When conversation deleted → cascade delete all messages in that conversation

**Immutability**:
Messages are designed to be immutable. Once created:
- Content cannot be edited
- Role cannot be changed
- Timestamp cannot be modified
- Only deletion is allowed (via conversation cascade or direct delete in special cases)

**Query Patterns**:
```sql
-- Get all messages for a conversation (ordered chronologically)
SELECT * FROM messages
WHERE conversation_id = ?
ORDER BY created_at ASC;

-- Get message count for a conversation
SELECT COUNT(*) FROM messages
WHERE conversation_id = ?;

-- Get latest N messages for a conversation
SELECT * FROM messages
WHERE conversation_id = ?
ORDER BY created_at DESC
LIMIT ?;
```

---

## State Transitions

### Conversation State Machine

```
[User starts chat]
    │
    ▼
┌──────────────────┐
│ CONVERSATION     │
│ CREATED          │
│ (started_at set) │
└──────────────────┘
    │
    │ [User/AI sends message]
    ▼
┌──────────────────┐
│ CONVERSATION     │
│ UPDATED          │
│ (last_message_at │
│  updated)        │
└──────────────────┘
    │
    │ [More messages...]
    ▼
    (cycle repeats)

[User deletes account]
    │
    ▼
┌──────────────────┐
│ CONVERSATION     │
│ DELETED          │
│ (cascade)        │
└──────────────────┘
```

### Message State Machine

```
[User sends message OR AI generates response]
    │
    ▼
┌──────────────────┐
│ MESSAGE          │
│ CREATED          │
│ (immutable)      │
└──────────────────┘
    │
    │ [No state changes - messages are immutable]
    │
[Conversation deleted]
    │
    ▼
┌──────────────────┐
│ MESSAGE          │
│ DELETED          │
│ (cascade)        │
└──────────────────┘
```

---

## Data Integrity Constraints

### Foreign Key Constraints

1. **conversations.user_id → users.id**
   - ON DELETE CASCADE (when user deleted, delete all conversations)
   - Ensures every conversation belongs to a valid user

2. **messages.conversation_id → conversations.id**
   - ON DELETE CASCADE (when conversation deleted, delete all messages)
   - Ensures every message belongs to a valid conversation

### Check Constraints

1. **messages.role CHECK (role IN ('user', 'assistant'))**
   - Ensures only valid role values
   - Prevents data corruption from invalid roles

### NOT NULL Constraints

All fields are NOT NULL except where explicitly marked optional:
- conversations: all fields required
- messages: all fields required

---

## Performance Considerations

### Indexing Strategy

**conversations table**:
- `id` (PRIMARY KEY) - clustered index for direct lookups
- `user_id` - B-tree index for "get user's conversations" queries

**messages table**:
- `id` (PRIMARY KEY) - clustered index for direct lookups
- `conversation_id` - B-tree index for "get conversation's messages" queries

### Query Optimization

**Expected query patterns**:
1. Get all conversations for user (ORDER BY last_message_at DESC)
2. Get all messages for conversation (ORDER BY created_at ASC)
3. Get latest N messages for conversation (ORDER BY created_at DESC LIMIT N)

**Optimization strategies**:
- Index on `user_id` supports pattern #1
- Index on `conversation_id` supports patterns #2 and #3
- Timestamps stored as TIMESTAMP (8 bytes) for efficient sorting
- TEXT column for content is optimal for variable-length text

### Expected Data Volumes

**Per user**:
- Average: 1-10 conversations
- Peak: 50 conversations

**Per conversation**:
- Average: 10-50 messages
- Peak: 1000 messages

**Total system**:
- 10,000 users
- ~50,000 conversations
- ~500,000 messages

---

## Integration with Existing Schema

### Phase II Schema (Existing)

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Phase III Extensions (New)

```sql
-- See contracts/schema.sql for complete DDL
```

### Backward Compatibility

- No changes to existing `users` table
- No changes to existing `tasks` table
- New tables are independent and don't affect Phase II functionality
- Phase II endpoints continue working unchanged

---

## Testing Strategy

### Unit Tests

1. **Conversation Model Tests**
   - Create conversation with valid user_id
   - Reject conversation with invalid user_id
   - Update last_message_at timestamp
   - Verify cascade delete when user deleted

2. **Message Model Tests**
   - Create message with valid conversation_id
   - Reject message with invalid conversation_id
   - Reject message with invalid role
   - Verify immutability (no updates allowed)
   - Verify cascade delete when conversation deleted

### Integration Tests

1. **Foreign Key Integrity**
   - Verify CASCADE DELETE from users → conversations → messages
   - Verify foreign key constraint prevents orphaned conversations
   - Verify foreign key constraint prevents orphaned messages

2. **Performance Tests**
   - Query 100 conversations for a user (< 100ms)
   - Query 50 messages for a conversation (< 50ms)
   - Concurrent message writes to same conversation

3. **Data Validation**
   - Invalid role values rejected
   - NULL values rejected
   - Empty content rejected

---

## Migration Strategy

See `contracts/schema.sql` for complete migration DDL.

**Upgrade Path**:
1. Create `conversations` table
2. Create `messages` table
3. Add indexes
4. Verify foreign keys work with existing `users` table

**Downgrade Path**:
1. Drop `messages` table (removes FK constraint)
2. Drop `conversations` table (removes FK constraint)
3. No changes needed to `users` table

**Safety Checks**:
- Verify `users` table exists before adding foreign keys
- Test migration on staging database first
- Create backup before production migration

---

## Future Extensions (Out of Scope for Phase III)

- Message search/full-text indexing
- Conversation archival/soft-delete
- Message edit history
- Read receipts
- Typing indicators
- Message reactions
- Conversation sharing
- Export functionality
