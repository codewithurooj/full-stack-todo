# Phase 1: Data Model & Event Schemas
**Feature**: Event-Driven Architecture with Kafka
**Date**: 2026-01-12

## Overview

This document defines the data models, event schemas, and database schema extensions required for the event-driven architecture with Kafka.

## Event Schemas

### 1. Task Event Schema

**Topic**: `task-events`
**Purpose**: Published by Backend API on all task operations; consumed by Recurring Task Service and Audit Service

**Schema** (JSON):
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "task.created | task.updated | task.deleted | task.completed",
  "schema_version": "1.0.0",
  "timestamp": "2026-01-12T10:30:00.000Z",
  "user_id": 456,
  "task_id": 123,
  "task_data": {
    "id": 123,
    "user_id": 456,
    "title": "Buy groceries",
    "description": "Milk, eggs, bread",
    "completed": false,
    "priority": "high",
    "tags": ["shopping", "urgent"],
    "recurring": "weekly",
    "recurring_interval": 1,
    "parent_task_id": null,
    "due_date": "2026-01-19T09:00:00.000Z",
    "remind_at": "2026-01-19T08:00:00.000Z",
    "reminded": false,
    "created_at": "2026-01-12T10:30:00.000Z",
    "updated_at": "2026-01-12T10:30:00.000Z"
  }
}
```

**Field Descriptions**:
- `event_id` (UUID, required): Unique identifier for this event; used for idempotency
- `event_type` (string, required): Type of task operation (task.created, task.updated, task.deleted, task.completed)
- `schema_version` (string, required): Event schema version for backward compatibility
- `timestamp` (ISO 8601, required): Event generation time in UTC
- `user_id` (integer, required): User who owns the task
- `task_id` (integer, required): Task identifier
- `task_data` (object, required): Full task object at time of event

**Event Types**:
- `task.created`: New task created
- `task.updated`: Task fields modified (title, description, priority, tags, etc.)
- `task.deleted`: Task removed
- `task.completed`: Task marked complete/incomplete

**Partitioning**: By `user_id` to maintain per-user event ordering

**Retention**: 7 days

### 2. Reminder Event Schema

**Topic**: `reminders`
**Purpose**: Published by Backend API when task created/updated with remind_at; consumed by Notification Service

**Schema** (JSON):
```json
{
  "event_id": "660e8400-e29b-41d4-a716-446655440001",
  "schema_version": "1.0.0",
  "timestamp": "2026-01-12T10:30:00.000Z",
  "reminder_id": "reminder-123-2026-01-19T08:00:00Z",
  "task_id": 123,
  "user_id": 456,
  "title": "Buy groceries",
  "remind_at": "2026-01-19T08:00:00.000Z",
  "due_date": "2026-01-19T09:00:00.000Z"
}
```

**Field Descriptions**:
- `event_id` (UUID, required): Unique identifier for this event
- `schema_version` (string, required): Event schema version
- `timestamp` (ISO 8601, required): Event generation time in UTC
- `reminder_id` (string, required): Unique identifier for idempotency (format: `reminder-{task_id}-{remind_at}`)
- `task_id` (integer, required): Task to remind about
- `user_id` (integer, required): User to notify
- `title` (string, required): Task title for notification body
- `remind_at` (ISO 8601, required): When to send notification
- `due_date` (ISO 8601, optional): Task due date for context

**Partitioning**: By `user_id`

**Retention**: 7 days

### 3. Task Update Event Schema (Optional)

**Topic**: `task-updates`
**Purpose**: Real-time sync for connected clients via WebSocket Service (optional feature)

**Schema** (JSON):
```json
{
  "event_id": "770e8400-e29b-41d4-a716-446655440002",
  "event_type": "task.created | task.updated | task.deleted | task.completed",
  "schema_version": "1.0.0",
  "timestamp": "2026-01-12T10:35:00.000Z",
  "user_id": 456,
  "task_id": 123,
  "changes": {
    "title": "Buy groceries (updated)",
    "completed": true
  }
}
```

**Field Descriptions**:
- `event_id` (UUID, required): Unique identifier for this event
- `event_type` (string, required): Type of task operation
- `schema_version` (string, required): Event schema version
- `timestamp` (ISO 8601, required): Event generation time in UTC
- `user_id` (integer, required): User who owns the task
- `task_id` (integer, required): Task identifier
- `changes` (object, required): Fields that changed (for updates) or full object (for creates)

**Partitioning**: By `user_id`

**Retention**: 1 day (shorter retention for real-time sync)

## Database Schema Extensions

### 1. Audit Logs Table

**Purpose**: Store comprehensive audit trail of all task operations

```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    event_id UUID UNIQUE NOT NULL,              -- Idempotency key from event
    timestamp TIMESTAMPTZ NOT NULL,             -- Event timestamp
    user_id INTEGER NOT NULL REFERENCES users(id),
    task_id INTEGER REFERENCES tasks(id),       -- NULL for user-level events
    operation_type VARCHAR(50) NOT NULL,        -- task.created, task.updated, etc.
    event_payload JSONB NOT NULL,               -- Full event for forensic analysis
    system_generated BOOLEAN DEFAULT FALSE,     -- True if auto-generated (recurring)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX idx_audit_logs_task_id ON audit_logs(task_id) WHERE task_id IS NOT NULL;
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_operation_type ON audit_logs(operation_type);

-- Full-text search on event payload (optional)
CREATE INDEX idx_audit_logs_payload_gin ON audit_logs USING gin(event_payload);
```

**Field Descriptions**:
- `event_id`: UUID from Kafka event (enforces idempotency)
- `timestamp`: Original event timestamp (not database insertion time)
- `user_id`: User who performed the operation
- `task_id`: Task affected (NULL for non-task events)
- `operation_type`: Event type (task.created, task.updated, etc.)
- `event_payload`: Full event JSON for debugging/forensics
- `system_generated`: TRUE if event was generated by Recurring Task Service
- `created_at`: Database insertion timestamp

**Retention Policy**:
```sql
-- Clean up old audit logs (run daily via cron job)
DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '90 days';
```

### 2. Notification Subscriptions Table (Optional)

**Purpose**: Store Web Push subscriptions for browser notifications

```sql
CREATE TABLE notification_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    endpoint TEXT NOT NULL,                     -- Push service endpoint
    p256dh TEXT NOT NULL,                       -- Public key for encryption
    auth TEXT NOT NULL,                         -- Auth secret for encryption
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, endpoint)
);

CREATE INDEX idx_notification_subs_user_id ON notification_subscriptions(user_id);
```

**Field Descriptions**:
- `user_id`: User who granted notification permission
- `endpoint`: Push service URL (e.g., FCM endpoint)
- `p256dh`: Client public key for encryption
- `auth`: Authentication secret
- `created_at`/`updated_at`: Subscription lifecycle

**Note**: Alternative approach is to store subscriptions in frontend localStorage and pass on demand (simpler for MVP).

### 3. Idempotency Keys (Existing Table Modifications)

**Purpose**: Enforce idempotency for recurring instance creation

**Option A**: Add unique constraint to tasks table
```sql
-- Prevent duplicate recurring instances
CREATE UNIQUE INDEX idx_recurring_instance_dedup
ON tasks(parent_task_id, due_date)
WHERE parent_task_id IS NOT NULL;
```

**Option B**: Separate idempotency table (if more flexibility needed)
```sql
CREATE TABLE idempotency_keys (
    key VARCHAR(255) PRIMARY KEY,               -- Composite key (e.g., "recurring-123-2026-01-19")
    task_id INTEGER REFERENCES tasks(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_idempotency_task_id ON idempotency_keys(task_id);

-- Clean up old keys (run daily)
DELETE FROM idempotency_keys WHERE created_at < NOW() - INTERVAL '7 days';
```

**Recommendation**: Use Option A (unique constraint on tasks table) for simplicity.

## Data Flow Diagrams

### Recurring Task Flow

```
User completes task (Frontend)
  ↓
Backend API: PATCH /api/{user_id}/tasks/{task_id}/complete
  ↓
Update task.completed = true in database
  ↓
Publish event to task-events topic:
  {
    event_type: "task.completed",
    task_id: 123,
    user_id: 456,
    task_data: {...}
  }
  ↓
Recurring Task Service consumes event
  ↓
Check: task_data.recurring != "none"?
  ↓ YES
Calculate next due_date (daily/weekly/monthly)
  ↓
Create new task instance:
  - Same title, description, priority, tags
  - New due_date
  - parent_task_id = original task ID
  - completed = false
  ↓
Insert into database (idempotency key: parent_task_id + due_date)
  ↓
Publish task.created event to task-events
  ↓
Frontend receives new task (via polling or WebSocket)
```

### Notification Flow

```
User creates task with remind_at (Frontend)
  ↓
Backend API: POST /api/{user_id}/tasks
  ↓
Create task in database
  ↓
Publish event to task-events topic (task.created)
  AND
Publish event to reminders topic:
  {
    reminder_id: "reminder-123-2026-01-19T08:00:00Z",
    task_id: 123,
    user_id: 456,
    title: "Buy groceries",
    remind_at: "2026-01-19T08:00:00Z"
  }
  ↓
Notification Service consumes event
  ↓
Schedule notification for remind_at time
  (using Dapr Jobs API or internal scheduler)
  ↓
At remind_at time:
  - Retrieve user's Web Push subscription from database/localStorage
  - Send Web Push notification with task title and due time
  - Update task.reminded = true in database
  ↓
User clicks notification
  ↓
Browser opens task in app
```

### Audit Logging Flow

```
Any task operation (create/update/delete/complete)
  ↓
Backend API publishes event to task-events topic
  ↓
Audit Service consumes event (no filtering)
  ↓
Parse event:
  - event_id (idempotency key)
  - timestamp
  - user_id
  - task_id
  - operation_type
  - event_payload (full JSON)
  ↓
Insert into audit_logs table
  (idempotency: ON CONFLICT DO NOTHING on event_id)
  ↓
Commit consumer offset after successful insert
  ↓
Audit log available for queries:
  - GET /api/audit/task/{task_id}
  - GET /api/audit/user/{user_id}
```

## Event Schema Evolution

### Adding New Fields (Backward Compatible)

**Example**: Add `priority_changed` field to task.updated events

1. **Update event schema** (v1.1.0):
```json
{
  "event_type": "task.updated",
  "schema_version": "1.1.0",
  ...
  "task_data": {
    ...
    "priority": "high",
    "priority_changed": true  // New optional field
  }
}
```

2. **Old consumers** (v1.0.0): Ignore new field (graceful degradation)
3. **New consumers** (v1.1.0): Utilize new field if present

**Rule**: Always add new fields as optional, never remove existing fields.

### Breaking Changes (Major Version)

**Example**: Change `recurring` from string to object

1. **Create new event type** (`task.created.v2`):
```json
{
  "event_type": "task.created.v2",
  "schema_version": "2.0.0",
  ...
  "task_data": {
    ...
    "recurring": {
      "frequency": "weekly",
      "interval": 1,
      "days_of_week": ["monday"]
    }
  }
}
```

2. **Dual publishing period**:
   - Backend API publishes both v1 and v2 events
   - Consumers migrate to v2 gradually
   - Deprecate v1 after 90 days

3. **Version negotiation**:
   - Consumers advertise supported versions
   - Producers send highest supported version

## Validation Rules

### Event Validation (Producer)

```python
from pydantic import BaseModel, UUID4, Field
from datetime import datetime
from typing import Literal

class TaskEventSchema(BaseModel):
    event_id: UUID4
    event_type: Literal["task.created", "task.updated", "task.deleted", "task.completed"]
    schema_version: str = "1.0.0"
    timestamp: datetime
    user_id: int = Field(gt=0)
    task_id: int = Field(gt=0)
    task_data: dict

# Validate before publishing
event = TaskEventSchema(
    event_id=uuid.uuid4(),
    event_type="task.created",
    timestamp=datetime.utcnow(),
    user_id=456,
    task_id=123,
    task_data=task.dict()
)
await producer.send('task-events', value=event.dict())
```

### Database Constraints

```sql
-- Audit logs
ALTER TABLE audit_logs
  ADD CONSTRAINT audit_logs_operation_type_check
  CHECK (operation_type IN ('task.created', 'task.updated', 'task.deleted', 'task.completed'));

ALTER TABLE audit_logs
  ADD CONSTRAINT audit_logs_timestamp_check
  CHECK (timestamp <= NOW() + INTERVAL '1 hour');  -- Prevent future timestamps

-- Ensure event_id is valid UUID
ALTER TABLE audit_logs
  ADD CONSTRAINT audit_logs_event_id_check
  CHECK (event_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$');
```

## Summary

All data models and event schemas defined. Database schema extensions specified with idempotency enforcement. Ready to proceed to contract generation and quickstart documentation.

**Key Artifacts**:
- 3 event schemas: task-events, reminders, task-updates
- Audit logs table with indexes
- Idempotency strategies with database constraints
- Data flow diagrams for recurring tasks, notifications, and audit logging
- Validation rules for event schemas

**Next Steps**:
1. Generate event schema contracts (JSON Schema format) in /contracts directory
2. Create quickstart.md for local development setup
3. Run /sp.tasks to break down implementation
