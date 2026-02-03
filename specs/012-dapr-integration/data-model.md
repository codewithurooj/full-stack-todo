# Data Model: Dapr Integration

**Feature**: 012-dapr-integration
**Date**: 2026-01-18
**Status**: Complete

## Overview

The Dapr integration does not introduce new application database tables. Instead, it utilizes Dapr's built-in state store component backed by PostgreSQL for conversation state persistence. This document describes the data structures used by Dapr components.

---

## 1. Dapr State Store Table

Dapr automatically creates and manages a state table in PostgreSQL when using the `state.postgresql` component.

### Auto-Generated Schema

```sql
-- Created automatically by Dapr when statestore component initializes
CREATE TABLE IF NOT EXISTS dapr_state (
    key VARCHAR(256) PRIMARY KEY,
    value JSONB NOT NULL,
    etag VARCHAR(36) NOT NULL DEFAULT gen_random_uuid()::text,
    insertdate TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updatedate TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for efficient key lookups
CREATE INDEX IF NOT EXISTS idx_dapr_state_key ON dapr_state(key);
```

### Key Naming Convention

| Key Pattern | Purpose | Example |
|-------------|---------|---------|
| `statestore\|\|conversation-{id}` | Conversation state | `statestore\|\|conversation-123` |
| `statestore\|\|user-prefs-{user_id}` | User preferences (future) | `statestore\|\|user-prefs-456` |

Note: Dapr prefixes keys with the component name and delimiter.

---

## 2. Conversation State Structure

State values stored in the `dapr_state` table for conversation persistence.

### Schema

```typescript
interface ConversationState {
  user_id: string;
  messages: Message[];
  context: ConversationContext;
  created_at: string;  // ISO 8601 timestamp
  updated_at: string;  // ISO 8601 timestamp
}

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;  // ISO 8601 timestamp
  tool_calls?: ToolCall[];  // Optional, for assistant messages
}

interface ToolCall {
  tool: string;
  parameters: Record<string, any>;
  result?: any;
}

interface ConversationContext {
  last_tool_call?: string;
  preferences?: UserPreferences;
  active_task_id?: number;  // Task being discussed
}
```

### Example State Document

```json
{
  "user_id": "user_456",
  "messages": [
    {
      "role": "user",
      "content": "Add a task to buy groceries",
      "timestamp": "2026-01-18T10:00:00Z"
    },
    {
      "role": "assistant",
      "content": "I have added 'Buy groceries' to your task list.",
      "timestamp": "2026-01-18T10:00:01Z",
      "tool_calls": [
        {
          "tool": "add_task",
          "parameters": {"title": "Buy groceries", "user_id": "user_456"},
          "result": {"task_id": 789, "status": "created"}
        }
      ]
    }
  ],
  "context": {
    "last_tool_call": "add_task",
    "active_task_id": 789
  },
  "created_at": "2026-01-18T10:00:00Z",
  "updated_at": "2026-01-18T10:00:01Z"
}
```

---

## 3. Event Schemas (Kafka Topics)

Events published via Dapr pub/sub to Kafka topics. These schemas are unchanged from the existing implementation.

### Task Event Schema

**Topic**: `task-events`

```typescript
interface TaskEvent {
  event_type: "task.created" | "task.updated" | "task.completed" | "task.deleted";
  event_id: string;      // UUID v4 for idempotency
  task_id: number;
  user_id: string;
  task_data: TaskData;
  timestamp: string;     // ISO 8601
  correlation_id?: string;  // For distributed tracing
}

interface TaskData {
  title: string;
  description?: string;
  completed: boolean;
  priority?: "high" | "medium" | "low";
  tags?: string[];
  due_date?: string;
  recurring?: "none" | "daily" | "weekly" | "monthly";
  recurring_interval?: number;
}
```

### Reminder Event Schema

**Topic**: `reminders`

```typescript
interface ReminderEvent {
  event_id: string;      // UUID v4
  task_id: number;
  user_id: string;
  title: string;
  remind_at: string;     // ISO 8601 - when to send notification
  timestamp: string;     // ISO 8601 - when event was created
  notification_type?: "browser" | "email" | "push";
}
```

### Task Update Event Schema (Future)

**Topic**: `task-updates`

```typescript
interface TaskUpdateEvent {
  event_type: "task.field_changed" | "task.status_changed";
  event_id: string;
  task_id: number;
  user_id: string;
  changes: FieldChange[];
  timestamp: string;
}

interface FieldChange {
  field: string;
  old_value: any;
  new_value: any;
}
```

---

## 4. Dapr Jobs Data Structure

Jobs scheduled via Dapr Jobs API for reminders.

### Job Schedule Request

```typescript
interface DaprJobRequest {
  dueTime: string;  // ISO 8601 timestamp for job execution
  ttl?: string;     // Time-to-live (e.g., "24h")
  repeats?: number; // Number of times to repeat (1 = one-time)
  data: {
    "@type": "type.googleapis.com/google.protobuf.StringValue";
    value: string;  // JSON-encoded payload
  };
}
```

### Reminder Job Payload

```typescript
interface ReminderJobPayload {
  task_id: number;
  user_id: string;
  title: string;
  due_date?: string;
  notification_type: "browser" | "push";
}
```

### Job Naming Convention

| Job Name Pattern | Purpose |
|------------------|---------|
| `reminder-{task_id}` | Primary reminder for task |
| `reminder-{task_id}-1h` | 1-hour before reminder |
| `reminder-{task_id}-24h` | 24-hour before reminder |

---

## 5. Kubernetes Secret Structure

Secrets accessed via Dapr secrets component.

### app-secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
stringData:
  OPENAI_API_KEY: "sk-..."
  BETTER_AUTH_SECRET: "..."
  VAPID_PRIVATE_KEY: "..."
  VAPID_PUBLIC_KEY: "..."
```

### postgres-credentials

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-credentials
type: Opaque
stringData:
  connectionString: "postgresql://user:pass@host:5432/dbname?sslmode=require"
```

### kafka-credentials

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: kafka-credentials
type: Opaque
stringData:
  brokers: "kafka-broker:9092"
  username: "kafka-user"
  password: "kafka-password"
```

---

## 6. Idempotency Tracking

For event processing idempotency, services track processed event IDs.

### Processed Events Table (per service)

```sql
-- Used by notification-service, recurring-task-service, audit-service
CREATE TABLE IF NOT EXISTS processed_events (
    event_id VARCHAR(36) PRIMARY KEY,
    topic VARCHAR(100) NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    -- Auto-cleanup after 7 days
    CONSTRAINT check_event_id CHECK (event_id ~ '^[0-9a-f-]{36}$')
);

CREATE INDEX idx_processed_events_date ON processed_events(processed_at);

-- Cleanup job: DELETE FROM processed_events WHERE processed_at < NOW() - INTERVAL '7 days';
```

---

## 7. Entity Relationships

```
┌─────────────────┐     ┌──────────────────┐
│  dapr_state     │     │  processed_events│
│  (Conversation) │     │  (Idempotency)   │
├─────────────────┤     ├──────────────────┤
│ key (PK)        │     │ event_id (PK)    │
│ value (JSONB)   │     │ topic            │
│ etag            │     │ processed_at     │
│ insertdate      │     └──────────────────┘
│ updatedate      │
└─────────────────┘
        │
        │ Stores conversation history for
        │ chat endpoint state management
        ▼
┌─────────────────┐
│  conversations  │  (Existing table - still used for
│  (Existing)     │   user_id lookups, may be deprecated)
└─────────────────┘
```

---

## 8. Migration Notes

### No Breaking Changes

- Existing `tasks`, `users`, `conversations`, `messages` tables remain unchanged
- Dapr state store is additive (new `dapr_state` table)
- Event schemas are backward compatible

### Future Deprecation Candidates

Once Dapr integration is stable:
1. `conversations` table - Replaced by Dapr state store
2. `messages` table - Replaced by Dapr state store
3. Direct Kafka connection settings - Replaced by Dapr pub/sub

### Data Migration Path

If migrating existing conversations to Dapr state store:

```python
async def migrate_conversations_to_dapr():
    """One-time migration of existing conversations."""
    conversations = await get_all_conversations()
    for conv in conversations:
        messages = await get_messages_for_conversation(conv.id)
        state = {
            "user_id": str(conv.user_id),
            "messages": [
                {"role": m.role, "content": m.content, "timestamp": m.created_at.isoformat()}
                for m in messages
            ],
            "context": {},
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat()
        }
        await save_state(f"conversation-{conv.id}", state)
```

---

## Validation Rules

### Conversation State

| Field | Rule |
|-------|------|
| user_id | Required, non-empty string |
| messages | Array with 0-1000 items |
| messages[].role | Enum: user, assistant, system |
| messages[].content | Required, max 10000 chars |
| created_at | Valid ISO 8601 timestamp |
| updated_at | Must be >= created_at |

### Event Schemas

| Field | Rule |
|-------|------|
| event_id | Valid UUID v4 |
| task_id | Positive integer |
| user_id | Non-empty string |
| timestamp | Valid ISO 8601 timestamp |
| event_type | Valid enum value |
