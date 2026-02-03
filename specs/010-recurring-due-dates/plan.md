# Implementation Plan: Recurring Tasks and Due Dates with Reminders

**Branch**: `010-recurring-due-dates` | **Date**: 2026-01-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/010-recurring-due-dates/spec.md`

## Summary

Feature 010 adds recurring tasks and due dates with time-based browser notifications to the task management system. This feature enables users to:
- Set due dates and times on tasks with timezone awareness
- Receive browser notifications at configurable times before deadlines
- Create recurring tasks that automatically generate new instances (daily/weekly/monthly/custom patterns)
- Manage complex recurrence patterns with specific intervals, days, and end dates
- Backfill missed recurrences for up to 7 days when users return from absence

**Technical Approach**: Extend Task model with due_date, recurring_pattern, and reminder fields; implement APScheduler for background job scheduling; add browser notification support via Service Worker; use PostgreSQL TIMESTAMPTZ for timezone-aware storage; implement dateutil.rrule for recurrence pattern generation; add Kafka event architecture (optional for Phase V) for microservices-based reminder delivery.

**Scale**: Supports 10k+ users, millions of tasks, thousands of scheduled reminders per user, with <5s notification delivery time and 99% reliability.

## Technical Context

**Language/Version**: Python 3.13+ (backend), TypeScript 5+ (frontend), Node.js 20+
**Primary Dependencies**:
- Backend: FastAPI, SQLModel, APScheduler 3.10+, dateutil 2.8+, pytz
- Frontend: Next.js 16+, date-fns-tz, React 18+, Tailwind CSS
- Optional: Kafka/Redpanda, Dapr (Phase V)

**Storage**: PostgreSQL (Neon) with TIMESTAMPTZ columns for all date/time fields; reminders table for scheduled notifications; notification_log table for delivery tracking

**Testing**:
- Backend: pytest with timezone mocking, job scheduler testing
- Frontend: Jest, Playwright E2E testing, service worker testing
- Database: Migration testing, timezone conversion testing

**Target Platform**:
- Backend: Linux server (Render/Railway), stateless design
- Frontend: Modern browsers (Chrome 90+, Firefox 88+, Safari 14+) with Service Worker support

**Project Type**: Full-stack web application (monorepo: backend + frontend + optional microservices)

**Performance Goals**:
- Notification delivery: <5 seconds from scheduled time
- Reminder creation: <100ms per task
- Recurring instance generation: <1 minute for 1000 tasks
- Task list filtering by due date: <1 second for 10k tasks
- Notification reliability: 99% delivery rate

**Constraints**:
- Stateless backend (no long-running processes)
- User permission required for browser notifications
- Timezone-aware calculations for all dates
- 7-day backfill limit for recurring tasks
- Notification deduplication within 5-minute window
- 24-hour window for offline notification delivery

**Scale/Scope**:
- 10k+ concurrent users
- Millions of tasks in production
- 1000+ scheduled reminders per user
- Support for tasks with complex recurring patterns
- Notification batching for high-volume scenarios

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Spec-Driven Development
- [x] Feature specified in `/specs/010-recurring-due-dates/spec.md`
- [x] Spec includes 4 user stories (P1-P4), 44 functional requirements, edge cases
- [x] No manual code writing - will use Claude Code generation

### ✅ Architecture & Technology Stack Alignment
- [x] Frontend: Next.js 16+ (App Router), TypeScript, Tailwind CSS ✓
- [x] Backend: FastAPI, SQLModel, PostgreSQL ✓
- [x] Existing authentication (JWT) leveraged
- [x] Phase 3 AI chatbot integration extended with MCP tools
- [x] Phase 4 Docker/Kubernetes deployment unchanged (APScheduler compatible)

### ✅ RESTful API Design
- [x] Extends existing `/api/{user_id}/tasks` endpoints
- [x] New endpoints: PUT/DELETE `/tasks/{id}/due-date`, POST/GET/DELETE `/tasks/{id}/reminders`
- [x] New endpoints: PUT/DELETE `/tasks/{id}/recurring`, POST `/tasks/{id}/next-occurrence`
- [x] MCP tools extended: add_task, update_task (support due_date, recurring fields)
- [x] Maintains stateless design (job scheduling via background service)

### ✅ Data Management
- [x] User data isolation: all queries filtered by user_id
- [x] PostgreSQL schema extension: due_date TIMESTAMPTZ, recurring_pattern, reminders table
- [x] Indexes on user_id, due_date, remind_at for performance
- [x] No cross-user data access

### ✅ Security & Authentication
- [x] JWT verification on all endpoints
- [x] User ID validation matches existing patterns
- [x] Notification permissions per-user and per-task
- [x] Service Worker operates within same origin

### ✅ Testing & Quality Assurance
- [x] Backend tests for due dates, reminders, recurring patterns
- [x] Frontend tests for date pickers, notification UI
- [x] Service Worker tests for background notification delivery
- [x] Timezone conversion tests (DST edge cases)
- [x] Manual E2E testing checklist

### ⚠️ Complexity Justifications (Phase V Features)

| Component | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| APScheduler | Background job scheduling for recurring instances and reminders | Cron jobs would require sysadmin access, cloud functions lack state persistence |
| Service Worker | Browser notifications while tab inactive | Foreground polling wastes battery and server resources |
| Kafka (optional) | Event-driven reminder delivery to scale microservices | Single-service polling becomes bottleneck at 10k users, 1000+ reminders/user |
| Dapr Jobs API | Cloud-native job scheduling alternative to APScheduler | Requires Kubernetes/cloud, adds complexity for MVP |

**Gate Status**: ✅ PASSED - All constitution requirements met, Phase V extensions justified for scale

## Project Structure

### Documentation (this feature)

```text
specs/010-recurring-due-dates/
├── spec.md                      # Feature specification (completed)
├── plan.md                      # This file (implementation plan)
├── research.md                  # Phase 0: Technology decisions (to be created)
├── data-model.md               # Phase 1: Database schema design (to be created)
├── quickstart.md               # Phase 1: Quick implementation guide (to be created)
├── contracts/                  # Phase 1: API contracts (to be created)
│   ├── due-dates-api.md        # Due date endpoints
│   ├── reminders-api.md        # Reminder endpoints
│   └── recurring-api.md        # Recurring pattern endpoints
└── tasks.md                    # Phase 2: Task breakdown (created by /sp.tasks command)
```

### Source Code (repository root)

**Backend Changes**:
```text
backend/
├── app/
│   ├── models/
│   │   ├── task.py                      # UPDATE: Add due_date, recurring_pattern, recurring_interval, recurring_days, recurring_end_date, parent_task_id, next_occurrence
│   │   └── reminder.py                  # NEW: Reminder model with remind_at, delivered, delivery_status
│   ├── routes/
│   │   ├── tasks.py                     # UPDATE: Extend to handle new fields
│   │   ├── due_dates.py                 # NEW: PUT/DELETE /tasks/{id}/due-date, GET filtering
│   │   ├── reminders.py                 # NEW: POST/GET/DELETE /tasks/{id}/reminders, PATCH snooze
│   │   └── recurring.py                 # NEW: PUT/DELETE /tasks/{id}/recurring, POST next-occurrence
│   ├── services/
│   │   ├── task_service.py              # UPDATE: Add due date logic
│   │   ├── reminder_service.py          # NEW: Reminder scheduling and delivery
│   │   └── recurring_service.py         # NEW: Recurring task generation and backfill
│   ├── jobs/
│   │   ├── __init__.py                  # Job scheduling setup
│   │   ├── recurring_generator.py       # NEW: Generate recurring instances
│   │   ├── reminder_processor.py        # NEW: Process and trigger reminders
│   │   └── scheduler.py                 # NEW: APScheduler configuration
│   ├── mcp_server/
│   │   └── tools/
│   │       ├── add_task.py              # UPDATE: Support due_date, recurring_pattern
│   │       ├── update_task.py           # UPDATE: Support updating due dates
│   │       ├── add_reminder.py          # NEW: MCP tool for adding reminders
│   │       └── list_reminders.py        # NEW: MCP tool for listing reminders
│   ├── utils/
│   │   ├── timezone.py                  # NEW: Timezone conversion utilities
│   │   ├── rrule.py                     # NEW: Recurrence pattern generation (dateutil.rrule wrapper)
│   │   └── notification.py              # NEW: Notification batching and deduplication
│   └── migrations/
│       └── 003_add_due_dates_reminders.sql  # NEW: Database migration
├── requirements.txt             # UPDATE: Add APScheduler, dateutil, pytz
└── tests/
    ├── test_due_dates.py        # NEW: Due date endpoint tests
    ├── test_reminders.py        # NEW: Reminder scheduling tests
    ├── test_recurring.py        # NEW: Recurring pattern tests
    └── test_timezone.py         # NEW: Timezone conversion tests
```

**Frontend Changes**:
```text
frontend/
├── app/
│   └── tasks/
│       └── page.tsx                     # UPDATE: Add due date filters, recurring indicators
├── components/
│   └── tasks/
│       ├── task-item.tsx                # UPDATE: Show due date, due date indicator (overdue/upcoming)
│       ├── due-date-picker.tsx          # NEW: Date/time picker with timezone support
│       ├── due-date-editor.tsx          # NEW: Edit/remove due dates
│       ├── reminder-manager.tsx         # NEW: Add/remove reminders UI
│       ├── recurring-task-form.tsx      # NEW: Create/edit recurring patterns
│       ├── recurrence-editor.tsx        # NEW: Advanced pattern editor (interval, days, end date)
│       ├── notification-display.tsx     # NEW: Show delivered notifications
│       └── task-filters.tsx             # UPDATE: Add due date range filters
├── services/
│   ├── notification-service.ts          # NEW: Service Worker registration, notification handling
│   ├── reminder-service.ts              # NEW: Reminder API client
│   └── recurring-service.ts             # NEW: Recurring task API client
├── hooks/
│   ├── useDueDate.ts                    # NEW: Due date state management
│   ├── useReminders.ts                  # NEW: Reminder state management
│   └── useRecurring.ts                  # NEW: Recurring task state management
├── lib/
│   ├── api/
│   │   ├── due-dates.ts                 # NEW: Due date API calls
│   │   ├── reminders.ts                 # NEW: Reminder API calls
│   │   └── recurring.ts                 # NEW: Recurring task API calls
│   ├── date-utils.ts                    # NEW: Date/time formatting, timezone conversion
│   └── notification-permissions.ts      # NEW: Request/check notification permissions
├── types/
│   ├── task.ts                          # UPDATE: Add due_date, reminder, recurring fields
│   ├── reminder.ts                      # NEW: Reminder types
│   └── recurring.ts                     # NEW: Recurring pattern types
├── public/
│   └── service-worker.ts                # NEW: Service Worker for background notifications
└── tests/
    ├── components/
    │   ├── due-date-picker.test.tsx    # NEW: Due date picker tests
    │   ├── reminder-manager.test.tsx   # NEW: Reminder UI tests
    │   └── recurring-task-form.test.tsx # NEW: Recurring form tests
    └── services/
        ├── notification-service.test.ts # NEW: Service Worker tests
        └── reminder-service.test.ts     # NEW: Reminder client tests
```

**Optional Microservices (Phase V)**:
```text
services/
├── reminder-service/                    # NEW: Dedicated reminder processing
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── recurring-generator/                 # NEW: Dedicated recurring instance generation
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
└── notification-dispatcher/             # NEW: Kafka consumer for notifications
    ├── app.py
    ├── requirements.txt
    └── Dockerfile

dapr-components/
├── pubsub.yaml                          # Kafka pub/sub configuration
├── statestore.yaml                      # PostgreSQL state store
├── jobs.yaml                            # Dapr Jobs API configuration
└── secrets.yaml                         # Kubernetes secrets reference
```

**Structure Decision**: Full-stack monorepo with separate backend and frontend directories. Backend services extend main FastAPI app initially; microservices option available for Phase V cloud deployment. Dapr components added to support cloud-native job scheduling and event-driven architecture.

## Phase 0: Research & Technical Decisions

### 0.1 Timezone Management

**Technology Choice**: PostgreSQL TIMESTAMPTZ + pytz + date-fns-tz

**Rationale**:
- TIMESTAMPTZ stores absolute UTC time, preserving accurate moment regardless of device timezone
- pytz handles Python timezone conversions with DST support
- date-fns-tz provides JavaScript timezone formatting
- Combined approach: store UTC, convert to user's local timezone for display/input

**Implementation Pattern**:
```python
# Backend: Store in UTC, convert from user timezone
from datetime import datetime
import pytz

user_tz = pytz.timezone(user.timezone)  # e.g., 'America/New_York'
local_dt = user_tz.localize(datetime(2026, 2, 15, 9, 0))  # 9 AM EST
utc_dt = local_dt.astimezone(pytz.UTC)  # Convert to UTC for storage
task.due_date = utc_dt  # Store TIMESTAMPTZ in PostgreSQL

# Retrieve and display
display_dt = task.due_date.astimezone(user_tz)  # Convert back to user timezone
```

**Edge Cases Handled**:
- DST transitions: pytz handles automatic offset changes
- Timezone changes: User's timezone fetched on each request
- Past due dates: Marked as "Overdue" based on user's current time

### 0.2 Browser Notifications Architecture

**Technology Choice**: Service Worker + Notification API + Background Sync

**Rationale**:
- Service Worker enables notifications when tab is inactive/closed
- Notification API provides system-level desktop alerts
- Background Sync queues notifications for offline scenarios
- Combined approach: foreground notifications + Service Worker for background delivery

**Implementation Pattern**:
```typescript
// Frontend: Request permission and register Service Worker
if ('serviceWorker' in navigator && 'Notification' in window) {
  Notification.requestPermission().then(permission => {
    if (permission === 'granted') {
      navigator.serviceWorker.register('/service-worker.ts');
    }
  });
}

// Service Worker: Listen for reminder messages
self.addEventListener('push', event => {
  const data = event.data.json();
  self.registration.showNotification(data.title, {
    body: data.body,
    tag: `reminder-${data.task_id}`,  // Deduplication
    requireInteraction: true
  });
});
```

**Offline Handling**:
- Backend queues notifications for up to 24 hours
- On app reopening, fetch queued notifications and display as alerts
- Service Worker syncs with backend on reconnection

### 0.3 Job Scheduling Architecture

**MVP: APScheduler** → **Phase V: Dapr Jobs API**

**APScheduler (Development/MVP)**:
- Lightweight Python library, no external dependencies
- Runs in-process with FastAPI application
- Job storage via PostgreSQL for persistence
- Suitable for single-server deployment

**Dapr Jobs API (Cloud/Phase V)**:
- Cloud-native job scheduling for Kubernetes
- Decoupled from application lifecycle
- Supports distributed scheduling across replicas
- Better for horizontally-scaled deployments

**Initial Implementation** (APScheduler):
```python
# app/jobs/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio_executor import AsyncIOExecutor

# Configure job store with PostgreSQL
jobstores = {
    'default': SQLAlchemyJobStore(
        engine=engine,
        tablename='apscheduler_jobs'
    )
}

executors = {
    'default': AsyncIOExecutor()
}

job_defaults = {
    'coalesce': True,
    'max_instances': 1
}

scheduler = AsyncIOScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults
)

# Start scheduler on app startup
async def startup():
    scheduler.start()
    schedule_recurring_task_generation()
    schedule_reminder_processing()
```

### 0.4 Recurrence Pattern Generation

**Technology Choice**: dateutil.rrule wrapper

**Rationale**:
- dateutil.rrule implements RFC 5545 RRULE standard
- Handles complex patterns: daily, weekly, monthly, custom intervals
- Supports: FREQ, BYDAY, BYMONTHDAY, COUNT, UNTIL, INTERVAL
- Edge case handling: month-end dates, leap years, timezone-aware calculations

**Implementation Pattern**:
```python
# app/utils/rrule.py
from dateutil import rrule
from datetime import datetime
import pytz

def generate_next_occurrences(
    start_date: datetime,
    pattern: str,  # e.g., 'FREQ=DAILY;INTERVAL=1'
    user_tz: str,
    count: int = 10
) -> List[datetime]:
    """Generate next occurrences based on RRULE pattern"""
    rrule_obj = rrule.rrulestr(
        pattern,
        dtstart=start_date,
        tzinfo=pytz.timezone(user_tz)
    )
    return list(rrule_obj.between(start_date, None, inc=True, count=count))

# Usage: Create "Daily at 9 AM" pattern
pattern = 'FREQ=DAILY;BYHOUR=9;BYMINUTE=0'
occurrences = generate_next_occurrences(
    start_date=datetime(2026, 1, 9, 9, 0),
    pattern=pattern,
    user_tz='America/New_York',
    count=30
)
```

**Stored Pattern Format**:
```sql
-- Stored as RFC 5545 RRULE string
due_date: 2026-01-09 14:00:00+00:00  -- First occurrence (UTC)
recurring_pattern: 'FREQ=DAILY;BYHOUR=9;BYMINUTE=0;UNTIL=20260501'
recurring_end_date: 2026-05-01
```

### 0.5 Notification Batching and Deduplication

**Batching Strategy**: Group reminders within 2-minute window

**Deduplication**:
- Track `(task_id, user_id, reminder_time)` tuples
- Prevent duplicate notifications within 5-minute window
- Use notification tag in browser: `tag: 'reminder-${task_id}'`

**Implementation**:
```python
# app/utils/notification.py
def batch_reminders(
    reminders: List[Reminder],
    window_minutes: int = 2
) -> List[List[Reminder]]:
    """Group reminders by time window"""
    if not reminders:
        return []

    batches = []
    current_batch = [reminders[0]]

    for reminder in reminders[1:]:
        time_diff = (reminder.remind_at - current_batch[0].remind_at).total_seconds() / 60
        if time_diff <= window_minutes:
            current_batch.append(reminder)
        else:
            batches.append(current_batch)
            current_batch = [reminder]

    batches.append(current_batch)
    return batches

def create_batched_notification(reminders: List[Reminder]) -> NotificationPayload:
    """Create single notification for multiple tasks"""
    if len(reminders) == 1:
        return NotificationPayload(
            title=f"Task Due: {reminders[0].task.title}",
            body=f"Due at {reminders[0].remind_at.strftime('%I:%M %p')}"
        )
    else:
        task_list = '\n'.join([f"• {r.task.title}" for r in reminders])
        return NotificationPayload(
            title=f"{len(reminders)} Tasks Due",
            body=f"View all tasks due in the next 2 minutes:\n{task_list}"
        )
```

### 0.6 Backfill Logic for Missed Recurrences

**Strategy**: When user returns after absence, generate up to 7 days of missed instances

**Rationale**:
- 7-day window prevents overwhelming users with months of backlog
- Generates completed instances for past missed dates (user can mark as done)
- Excludes future instances (user controls schedule)
- Executed asynchronously to avoid blocking list request

**Implementation**:
```python
# app/services/recurring_service.py
async def backfill_missed_instances(
    task: Task,
    current_time: datetime,
    user_tz: str
) -> int:
    """Backfill up to 7 days of missed recurring instances"""
    if not task.recurring_pattern or not task.next_occurrence:
        return 0

    # Calculate backfill window: up to 7 days ago
    backfill_start = current_time - timedelta(days=7)

    # Generate instances from last_occurrence to current time
    generated_instances = 0
    next_dt = task.next_occurrence

    while next_dt <= current_time:
        if next_dt >= backfill_start:
            # Create new instance
            new_task = Task(
                user_id=task.user_id,
                title=task.title,
                description=task.description,
                priority=task.priority,
                tags=task.tags,
                due_date=next_dt,
                parent_task_id=task.id,
                created_at=current_time
            )
            db.add(new_task)
            generated_instances += 1

        # Calculate next occurrence
        next_dt = get_next_occurrence(
            task.recurring_pattern,
            next_dt,
            user_tz
        )

    db.commit()
    return generated_instances
```

## Database Schema

### Schema Extensions

**ALTER TABLE tasks**:
```sql
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS
  due_date TIMESTAMP WITH TIME ZONE DEFAULT NULL;

ALTER TABLE tasks ADD COLUMN IF NOT EXISTS
  recurring_pattern VARCHAR(500) DEFAULT NULL;  -- RFC 5545 RRULE

ALTER TABLE tasks ADD COLUMN IF NOT EXISTS
  recurring_interval INTEGER DEFAULT NULL;  -- Deprecated, use recurring_pattern

ALTER TABLE tasks ADD COLUMN IF NOT EXISTS
  recurring_days TEXT[] DEFAULT NULL;  -- Deprecated, use recurring_pattern

ALTER TABLE tasks ADD COLUMN IF NOT EXISTS
  recurring_end_date TIMESTAMP WITH TIME ZONE DEFAULT NULL;

ALTER TABLE tasks ADD COLUMN IF NOT EXISTS
  parent_task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE DEFAULT NULL;

ALTER TABLE tasks ADD COLUMN IF NOT EXISTS
  next_occurrence TIMESTAMP WITH TIME ZONE DEFAULT NULL;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_parent_id ON tasks(parent_task_id);
CREATE INDEX IF NOT EXISTS idx_tasks_recurring ON tasks(recurring_pattern)
  WHERE recurring_pattern IS NOT NULL;
```

**CREATE TABLE reminders**:
```sql
CREATE TABLE IF NOT EXISTS reminders (
  id SERIAL PRIMARY KEY,
  task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  remind_at TIMESTAMP WITH TIME ZONE NOT NULL,
  offset_minutes INTEGER NOT NULL,  -- Minutes before due_date
  delivered BOOLEAN DEFAULT FALSE,
  delivery_status VARCHAR(50) DEFAULT 'pending',  -- pending, sent, failed, dismissed
  delivery_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NULL,
  notification_id VARCHAR(255) DEFAULT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  UNIQUE(task_id, offset_minutes)
);

CREATE INDEX idx_reminders_user_id ON reminders(user_id);
CREATE INDEX idx_reminders_remind_at ON reminders(remind_at);
CREATE INDEX idx_reminders_task_id ON reminders(task_id);
CREATE INDEX idx_reminders_delivered ON reminders(delivered)
  WHERE delivered = FALSE;
```

**CREATE TABLE notification_log** (optional, for analytics):
```sql
CREATE TABLE IF NOT EXISTS notification_log (
  id SERIAL PRIMARY KEY,
  reminder_id INTEGER REFERENCES reminders(id) ON DELETE SET NULL,
  task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  user_id VARCHAR(255) NOT NULL,
  notification_title VARCHAR(500),
  notification_body TEXT,
  sent_at TIMESTAMP WITH TIME ZONE NOT NULL,
  clicked_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
  dismissed_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
  delivery_method VARCHAR(50),  -- browser, in-app, email
  delivery_status VARCHAR(50),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_notification_log_user ON notification_log(user_id);
CREATE INDEX idx_notification_log_task ON notification_log(task_id);
CREATE INDEX idx_notification_log_sent_at ON notification_log(sent_at);
```

### SQLModel Definitions

**Task Model Extensions**:
```python
# backend/app/models/task.py
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import ARRAY, String, TIMESTAMP
from datetime import datetime
from typing import Optional, List
import pytz

class TaskBase(SQLModel):
    """Base task fields"""
    title: str
    description: Optional[str] = None
    completed: bool = False
    priority: str = Field(default="medium", regex="^(high|medium|low)$")
    tags: List[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))

    # Due date and reminder fields
    due_date: Optional[datetime] = None

    # Recurring fields
    recurring_pattern: Optional[str] = None  # RFC 5545 RRULE
    recurring_interval: Optional[int] = None  # Deprecated
    recurring_days: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(ARRAY(String))
    )  # Deprecated: ['Monday', 'Wednesday', 'Friday']
    recurring_end_date: Optional[datetime] = None
    parent_task_id: Optional[int] = None
    next_occurrence: Optional[datetime] = None

class Task(TaskBase, table=True):
    """Task database model"""
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TaskCreate(TaskBase):
    pass

class TaskUpdate(SQLModel):
    """Schema for updating a task (all fields optional)"""
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[str] = Field(None, regex="^(high|medium|low)$")
    tags: Optional[List[str]] = None
    due_date: Optional[datetime] = None
    recurring_pattern: Optional[str] = None
    recurring_end_date: Optional[datetime] = None

class TaskRead(TaskBase):
    """Schema for reading a task"""
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
```

**Reminder Model**:
```python
# backend/app/models/reminder.py
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class ReminderBase(SQLModel):
    task_id: int
    offset_minutes: int  # Minutes before due_date (e.g., 15 for 15 min before)
    delivered: bool = False
    delivery_status: str = Field(default="pending", regex="^(pending|sent|failed|dismissed)$")

class Reminder(ReminderBase, table=True):
    __tablename__ = "reminders"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    task_id: int = Field(foreign_key="tasks.id")
    remind_at: datetime  # Absolute UTC time when reminder should trigger
    delivery_timestamp: Optional[datetime] = None
    notification_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ReminderCreate(ReminderBase):
    pass

class ReminderUpdate(SQLModel):
    delivered: Optional[bool] = None
    delivery_status: Optional[str] = Field(None, regex="^(pending|sent|failed|dismissed)$")

class ReminderRead(ReminderBase):
    id: int
    user_id: str
    remind_at: datetime
    delivery_timestamp: Optional[datetime]
    created_at: datetime
    updated_at: datetime
```

## API Contracts

### Due Dates API

**PUT /api/{user_id}/tasks/{task_id}/due-date** - Set/Update Due Date
```json
Request:
{
  "due_date": "2026-02-15T09:00:00",
  "user_timezone": "America/New_York"
}

Response (200 OK):
{
  "id": 1,
  "title": "Complete project proposal",
  "due_date": "2026-02-15T14:00:00Z",
  "overdue": false,
  "due_in_text": "in 5 days"
}

Error Responses:
- 400: Invalid date format or timezone
- 403: Unauthorized
- 404: Task not found
```

**DELETE /api/{user_id}/tasks/{task_id}/due-date** - Remove Due Date
```json
Response (204 No Content)

Error Responses:
- 403: Unauthorized
- 404: Task not found
```

**GET /api/{user_id}/tasks?due_date_from=...&due_date_to=...** - Filter by Due Date Range
```json
Query Parameters:
- due_date_from: ISO 8601 date (e.g., 2026-01-10)
- due_date_to: ISO 8601 date (e.g., 2026-01-17)
- relative_range: today|this_week|this_month|overdue

Response (200 OK):
{
  "tasks": [
    {
      "id": 1,
      "title": "Task 1",
      "due_date": "2026-01-15T14:00:00Z",
      "overdue": false
    }
  ],
  "count": 1
}
```

### Reminders API

**POST /api/{user_id}/tasks/{task_id}/reminders** - Create Reminder
```json
Request:
{
  "offset_minutes": 15,
  "notification_method": "browser"
}

Response (201 Created):
{
  "id": 1,
  "task_id": 1,
  "offset_minutes": 15,
  "remind_at": "2026-02-15T08:45:00Z",
  "delivered": false,
  "delivery_status": "pending"
}

Error Responses:
- 400: Invalid offset or duplicate reminder for same time
- 403: Unauthorized or notifications not permitted
- 404: Task not found
```

**GET /api/{user_id}/tasks/{task_id}/reminders** - List Reminders for Task
```json
Response (200 OK):
{
  "reminders": [
    {
      "id": 1,
      "offset_minutes": 15,
      "remind_at": "2026-02-15T08:45:00Z",
      "delivered": false,
      "delivery_status": "pending"
    },
    {
      "id": 2,
      "offset_minutes": 1440,  -- 1 day before
      "remind_at": "2026-02-14T09:00:00Z",
      "delivered": false,
      "delivery_status": "pending"
    }
  ],
  "count": 2
}
```

**DELETE /api/{user_id}/tasks/{task_id}/reminders/{reminder_id}** - Delete Reminder
```json
Response (204 No Content)

Error Responses:
- 403: Unauthorized
- 404: Reminder not found
```

**PATCH /api/{user_id}/tasks/{task_id}/reminders/{reminder_id}/snooze** - Snooze Reminder
```json
Request:
{
  "snooze_minutes": 15
}

Response (200 OK):
{
  "id": 1,
  "remind_at": "2026-02-15T09:00:00Z",  -- New time
  "delivery_status": "snoozed"
}

Error Responses:
- 400: Invalid snooze duration
- 403: Unauthorized
- 404: Reminder not found
```

### Recurring Tasks API

**PUT /api/{user_id}/tasks/{task_id}/recurring** - Create/Update Recurring Pattern
```json
Request:
{
  "recurring_pattern": "FREQ=DAILY;BYHOUR=9;BYMINUTE=0",
  "recurring_end_date": "2026-12-31T23:59:59Z",
  "user_timezone": "America/New_York"
}

Response (200 OK):
{
  "id": 1,
  "title": "Daily standup",
  "recurring_pattern": "FREQ=DAILY;BYHOUR=9;BYMINUTE=0",
  "recurring_end_date": "2026-12-31T23:59:59Z",
  "next_occurrence": "2026-01-10T14:00:00Z",
  "is_recurring": true,
  "recurring_display": "Daily at 9:00 AM"
}

Error Responses:
- 400: Invalid RRULE pattern or end date
- 403: Unauthorized
- 404: Task not found
```

**DELETE /api/{user_id}/tasks/{task_id}/recurring** - Remove Recurring Pattern
```json
Request:
{
  "delete_type": "future_only" | "all_instances"
}

Response (204 No Content)
- future_only: Deletes template, keeps existing instances
- all_instances: Deletes template and all instances (with confirmation)

Error Responses:
- 403: Unauthorized
- 404: Task not found
```

**POST /api/{user_id}/tasks/{task_id}/next-occurrence** - Get Next Occurrence
```json
Response (200 OK):
{
  "next_occurrence": "2026-01-10T14:00:00Z",
  "occurrence_number": 2,
  "total_planned": null  -- null if no end_date
}

Error Responses:
- 403: Unauthorized
- 404: Task not found or not recurring
```

## Quickstart Guide

### Prerequisites

**Backend**:
- Python 3.13+
- pip package manager
- PostgreSQL database (Neon recommended)
- `.env` file with DATABASE_URL

**Frontend**:
- Node.js 20+
- npm or yarn
- Modern browser with Service Worker support (Chrome 90+, Firefox 88+, Safari 14+)

### Backend Setup

**1. Install Dependencies**:
```bash
cd backend
pip install -r requirements.txt

# Key packages added for this feature:
# - apscheduler>=3.10.0
# - python-dateutil>=2.8.2
# - pytz>=2024.1
```

**2. Database Migration**:
```bash
# Create migration file
alembic revision --autogenerate -m "Add due dates and reminders"

# Apply migration
alembic upgrade head

# Alternatively, run SQL directly
psql $DATABASE_URL -f migrations/003_add_due_dates_reminders.sql
```

**3. Start Job Scheduler**:
```bash
# The scheduler starts automatically with the app
# Verify in logs: "Starting APScheduler background job processor"

uvicorn app.main:app --reload
```

**Jobs Running** (visible in logs):
```
2026-01-09 10:00:00 - Scheduled job: recurring_task_generator (every 1 minute)
2026-01-09 10:00:00 - Scheduled job: reminder_processor (every 30 seconds)
2026-01-09 10:00:00 - Scheduled job: backfill_checker (every 5 minutes)
```

### Frontend Setup

**1. Install Dependencies**:
```bash
cd frontend
npm install
# Installs date-fns-tz for timezone support
```

**2. Register Service Worker**:
Service Worker is automatically registered on app load (see `app/tasks/page.tsx`):
```typescript
useEffect(() => {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.ts');
    Notification.requestPermission();
  }
}, []);
```

**3. Grant Notification Permissions**:
Browser will prompt when user adds first reminder. Grant permission to enable desktop notifications.

**4. Test Locally**:
```bash
npm run dev
# Open http://localhost:3000
# Create task with due date
# Add reminder 1 minute before due time
# Wait for notification to appear
```

### Testing Instructions

**Backend Tests**:
```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/test_due_dates.py -v

# Run with timezone mocking
pytest tests/test_timezone.py -v

# Check coverage
pytest --cov=app --cov-report=html
```

**Frontend Tests**:
```bash
cd frontend

# Run Jest tests
npm test

# Run E2E tests with Playwright
npm run test:e2e

# Watch mode
npm test -- --watch
```

**Manual E2E Testing Checklist**:
- [ ] Create task, set due date for tomorrow at 9 AM
- [ ] Add reminder for 15 minutes before
- [ ] Wait for notification (or advance system clock for testing)
- [ ] Click notification, verify task opens
- [ ] Create recurring task (daily at 9 AM, 5 occurrences)
- [ ] Verify new instances appear each day
- [ ] Complete one instance, verify template still generates new ones
- [ ] Edit due date, verify reminder time updates
- [ ] Change device timezone, verify due date adjusts correctly
- [ ] Close browser, set reminder, reopen browser, verify notification still triggers
- [ ] Test offline: disable network, come back online, verify queued notifications

### Environment Variables

**Backend** (`.env`):
```env
DATABASE_URL=postgresql://user:pass@host.neon.tech/dbname
BETTER_AUTH_SECRET=your-secret-key-min-32-chars
OPENAI_API_KEY=sk-your-openai-api-key

# New for Feature 010
APSCHEDULER_TIMEZONE=UTC  # UTC for server, user conversions handled per-user
NOTIFICATION_QUEUE_TTL=86400  # 24 hours in seconds
REMINDER_BATCH_WINDOW_MINUTES=2
RECURRING_BACKFILL_DAYS=7
```

**Frontend** (`.env.local`):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_NOTIFICATION_ENABLED=true
```

### Troubleshooting

**Issue**: Reminders not firing
- **Check**: APScheduler is running (logs show "Starting APScheduler")
- **Check**: Due date is correctly set and in future
- **Check**: Reminder offset is positive and less than 24 hours
- **Check**: Task user_id matches authenticated user

**Issue**: Service Worker not delivering notifications
- **Check**: Browser notification permissions granted
- **Check**: Service Worker registered (check DevTools → Application → Service Workers)
- **Check**: HTTPS in production (Service Workers require secure context)

**Issue**: Timezone offset incorrect
- **Check**: User's timezone stored correctly in database
- **Check**: Device timezone matches user's configured timezone
- **Check**: Browser sending correct timezone in requests

**Issue**: Recurring instances not generating
- **Check**: APScheduler job is running (grep logs for "recurring_task_generator")
- **Check**: Recurring pattern is valid RRULE format
- **Check**: Task's next_occurrence is not NULL
- **Check**: Task's due_date is not NULL (required for recurring)

## Implementation Phases

### Phase 0: Research & Planning (1-2 days)
- [x] Technology decisions finalized (timezone, job scheduling, notifications)
- [x] Database schema designed (task fields, reminders table, indexes)
- [x] API contracts defined (OpenAPI 3.0 specs)
- [x] Risk assessment and edge case identification
- [ ] Research phase output: research.md, data-model.md, API contracts

### Phase 1: Database & Backend Foundation (2-3 days)
- [ ] Add due_date, recurring_pattern fields to Task model
- [ ] Create Reminder model and reminders table
- [ ] Implement timezone utility functions (pytz integration)
- [ ] Implement dateutil.rrule wrapper for recurrence patterns
- [ ] Set up APScheduler configuration and job registry
- [ ] Write unit tests for timezone and recurrence logic
- [ ] Output: Updated Task model, Reminder model, timezone tests passing

### Phase 2: Due Date API Endpoints (1-2 days)
- [ ] POST/PUT `/tasks/{id}/due-date` - Set/update due date
- [ ] DELETE `/tasks/{id}/due-date` - Remove due date
- [ ] GET `/tasks?due_date_from=...&due_date_to=...` - Filter by date range
- [ ] GET `/tasks?relative_range=today|this_week|this_month|overdue` - Relative filtering
- [ ] Tests for all endpoints with timezone conversion
- [ ] Output: Due date endpoints tested and documented

### Phase 3: Reminder Scheduling Backend (2-3 days)
- [ ] POST `/tasks/{id}/reminders` - Create reminder
- [ ] GET `/tasks/{id}/reminders` - List reminders
- [ ] DELETE `/tasks/{id}/reminders/{id}` - Delete reminder
- [ ] PATCH `/tasks/{id}/reminders/{id}/snooze` - Snooze reminder
- [ ] Implement reminder_service.py with APScheduler integration
- [ ] Implement notification batching and deduplication
- [ ] Tests for reminder creation, scheduling, delivery
- [ ] Output: Reminder endpoints tested, APScheduler jobs configured

### Phase 4: Frontend Due Date UI (2 days)
- [ ] Build DueDatePicker component (date + time selector)
- [ ] Build DueDateEditor component (edit/remove UI)
- [ ] Add due date display to TaskItem component (with overdue indicator)
- [ ] Add due date filters to TaskFilters component
- [ ] Implement useD ateUtils hook for timezone formatting
- [ ] Tests for date picker, timezone conversion
- [ ] Output: Due date UI components completed, filters working

### Phase 5: Browser Notification Frontend (1-2 days)
- [ ] Create Service Worker (public/service-worker.ts)
- [ ] Build ReminderManager component (add/remove reminders UI)
- [ ] Implement NotificationService (permission requests, registration)
- [ ] Build NotificationDisplay component (show delivered notifications)
- [ ] Handle offline queuing and retry logic
- [ ] Tests for Service Worker, notification handling
- [ ] Output: Service Worker deployed, notifications functional

### Phase 6: Recurring Task Backend (2-3 days)
- [ ] PUT `/tasks/{id}/recurring` - Create/update recurring pattern
- [ ] DELETE `/tasks/{id}/recurring` - Remove recurring (with delete_type options)
- [ ] POST `/tasks/{id}/next-occurrence` - Calculate next occurrence
- [ ] Implement recurring_service.py with instance generation logic
- [ ] Implement backfill logic (up to 7 days of missed instances)
- [ ] Set up APScheduler job: recurring_task_generator (runs every 1 minute)
- [ ] Tests for RRULE patterns, instance generation, backfill
- [ ] Output: Recurring endpoints working, instances generating automatically

### Phase 7: Recurring Task Frontend (2 days)
- [ ] Build RecurringTaskForm component (frequency selector + advanced options)
- [ ] Build RecurrenceEditor component (pattern configuration UI)
- [ ] Add recurring indicator to TaskItem component
- [ ] Implement useRecurring hook for API calls
- [ ] Display "Repeats Daily/Weekly/etc" indicator
- [ ] Tests for form submission, pattern validation
- [ ] Output: Recurring UI functional, pattern creation working

### Phase 8: MCP Tool Extensions (1 day)
- [ ] Extend add_task tool: support due_date, recurring_pattern parameters
- [ ] Extend update_task tool: support due_date, recurring_pattern updates
- [ ] Add add_reminder MCP tool
- [ ] Add list_reminders MCP tool
- [ ] Update MCP tool schemas in OpenAI agent
- [ ] Tests for AI commands: "add task with due date", "remind me at 9 AM"
- [ ] Output: MCP tools updated, AI integration working

### Phase 9: Testing & Edge Cases (1-2 days)
- [ ] E2E tests: full workflow (create → due date → reminder → notification)
- [ ] Timezone tests: DST transitions, timezone changes, edge cases
- [ ] Recurring pattern tests: all RRULE combinations, backfill scenarios
- [ ] Notification tests: offline delivery, deduplication, batching
- [ ] Service Worker tests: permission handling, background sync
- [ ] Load tests: 1000 tasks, 100 reminders per user
- [ ] Output: All tests passing (90%+ coverage), no known issues

### Phase 10: Microservices Migration (Optional, Phase V) (3-5 days)
- [ ] Create reminder-service microservice (Python FastAPI)
- [ ] Create recurring-generator microservice (Python FastAPI)
- [ ] Set up Kafka topics: task-events, reminders, task-updates
- [ ] Implement Dapr pubsub for service communication
- [ ] Configure Dapr statestore (PostgreSQL)
- [ ] Set up Dapr Jobs API for scheduled reminder delivery
- [ ] Dockerize all microservices
- [ ] Update Kubernetes/Helm charts for multi-service deployment
- [ ] Output: Microservices deployed to Kubernetes cluster

## Risk Assessment

### Critical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Browser notification permission denied | Medium | High | Fallback to in-app alerts with badge counter, allow re-enable later |
| Timezone conversion bugs (DST) | Medium | High | Comprehensive test suite with DST transitions, use pytz.utc base |
| Job scheduler persistence lost | Low | Critical | Use PostgreSQL jobstore, add health check endpoint, alerting |
| Recurring pattern infinite loop | Low | High | RRULE validation in create endpoint, max 365 occurrences safeguard |
| Notification spam (too many alerts) | Medium | Medium | Batching within 2-min window, deduplication, per-user throttling |
| Service Worker unregistered | Medium | Medium | Auto-registration on app load, fallback to polling if unavailable |
| Database migration down time | Low | High | Test migrations on staging first, use zero-downtime alter strategy |

### Secondary Risks

| Risk | Mitigation |
|------|-----------|
| High CPU usage from recurring generation | Implement backoff logic, spread jobs over time, use async processing |
| Notification delivery latency | Monitor APScheduler queue depth, add metrics/alerting |
| Stale due date indicators | Real-time UI updates (not dependent on page refresh), use polling or WebSocket |
| Out-of-sync timezone (app vs device) | Fetch user's timezone on every request, allow manual timezone override |

### Dependency Risks

| Dependency | Risk | Mitigation |
|------------|------|-----------|
| APScheduler | Single-point-of-failure for job scheduling | Phase V: migrate to Dapr Jobs API, add fallback cron monitoring |
| Service Worker | Limited browser support on older devices | Fallback polling for browsers without Service Worker support |
| dateutil | RRULE edge cases (e.g., leap seconds) | Test with dateutil test suite, add custom validators |
| PostgreSQL TIMESTAMPTZ | Timezone database updates (DST changes) | Monitor PostgreSQL version, keep IANA timezone database updated |

## Critical Files to Create/Extend

### Priority 1: Database & Models (Blocking)
1. **`backend/app/models/task.py`** - Add due_date, recurring_pattern, parent_task_id fields to Task
2. **`backend/app/models/reminder.py`** - NEW: Reminder model with remind_at, delivery_status

### Priority 2: Backend API (Core Features)
3. **`backend/app/routes/reminders.py`** - NEW: POST/GET/DELETE/PATCH reminder endpoints
4. **`backend/app/services/reminder_service.py`** - NEW: Reminder scheduling and delivery logic

### Priority 3: Frontend UI (User Interaction)
5. **`frontend/components/tasks/due-date-picker.tsx`** - NEW: Date/time picker component
6. **`frontend/public/service-worker.ts`** - NEW: Service Worker for background notifications

### Priority 4: Job Scheduling (Background Processing)
7. **`backend/app/jobs/scheduler.py`** - NEW: APScheduler configuration and job registry

### Priority 5: Frontend State Management
8. **`frontend/hooks/useReminders.ts`** - NEW: Hook for reminder state management

---

## Next Steps

1. Create `research.md` - Detailed technology research and decisions
2. Create `data-model.md` - Complete database schema with examples
3. Create `quickstart.md` - Step-by-step implementation guide
4. Run `/sp.tasks` command to generate task breakdown (tasks.md)
5. Begin Phase 0-1: Set up database models and schema
6. Implement due date API endpoints (Phase 2)
7. Implement reminder system (Phase 3)
8. Build frontend UI components (Phases 4-5)
9. Add recurring task support (Phases 6-7)
10. Extend MCP tools (Phase 8)
11. Complete testing and validation (Phase 9)

---

**Ready for task generation with `/sp.tasks` command!**
