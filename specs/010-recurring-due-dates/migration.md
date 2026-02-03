# Database Migration: Recurring Tasks and Due Dates with Reminders

## Overview

**Purpose:** Add due date tracking, recurring task generation, and reminder notification capabilities to the task management system
**Risk Level:** Medium - adds multiple columns, new table, and several indexes to existing tasks table
**Estimated Duration:** 5-10 seconds on production (with CONCURRENT index creation)
**Downtime Required:** No - migration uses backward-compatible approach with defaults

**Feature Branch:** `010-recurring-due-dates`
**Migration Version:** `003_add_due_dates_reminders`
**Created:** 2026-01-09

---

## Schema Changes

### New Columns on `tasks` Table

| Column | Type | Nullable | Default | Purpose |
|--------|------|----------|---------|---------|
| `due_date` | TIMESTAMPTZ | YES | NULL | When the task is due (timezone-aware) |
| `recurring_pattern` | VARCHAR(20) | YES | 'none' | Frequency: none, daily, weekly, monthly, custom |
| `recurring_interval` | INTEGER | YES | 1 | Interval for recurring pattern (e.g., every 2 weeks) |
| `recurring_days` | TEXT[] | YES | NULL | Days of week for weekly recurrence (Mon, Wed, Fri) |
| `recurring_end_date` | TIMESTAMPTZ | YES | NULL | When recurring series ends |
| `parent_task_id` | INTEGER | YES | NULL | Links recurring instance to template task |
| `next_occurrence` | TIMESTAMPTZ | YES | NULL | Cached next occurrence for recurring tasks |

### New Table: `reminders`

```sql
CREATE TABLE reminders (
  id SERIAL PRIMARY KEY,
  task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  user_id VARCHAR(255) NOT NULL,
  remind_at TIMESTAMPTZ NOT NULL,
  delivered BOOLEAN DEFAULT FALSE,
  delivery_status VARCHAR(20) DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT chk_delivery_status
    CHECK (delivery_status IN ('pending', 'sent', 'failed', 'dismissed'))
);
```

### New Indexes

| Index Name | Table | Columns | Type | Reason |
|------------|-------|---------|------|--------|
| `idx_tasks_due_date` | tasks | due_date | BTREE (partial) | Fast filtering by due date, only where due_date IS NOT NULL |
| `idx_tasks_parent_task_id` | tasks | parent_task_id | BTREE (partial) | Find recurring instances by parent, only where parent_task_id IS NOT NULL |
| `idx_tasks_recurring_pattern` | tasks | recurring_pattern | BTREE (partial) | Find recurring templates, only where recurring_pattern != 'none' |
| `idx_tasks_next_occurrence` | tasks | next_occurrence | BTREE (partial) | Job scheduler queries for tasks to generate, only where next_occurrence IS NOT NULL |
| `idx_reminders_task_id` | reminders | task_id | BTREE | Fast lookup of reminders for a task |
| `idx_reminders_user_id` | reminders | user_id | BTREE | User-specific reminder queries |
| `idx_reminders_remind_at` | reminders | remind_at | BTREE (partial) | Job scheduler queries for pending reminders, only where delivered = FALSE |

### Check Constraints

| Constraint Name | Table | Rule | Purpose |
|-----------------|-------|------|---------|
| `chk_recurring_pattern` | tasks | recurring_pattern IN ('none', 'daily', 'weekly', 'monthly', 'custom') | Validate recurring pattern values |
| `chk_recurring_interval` | tasks | recurring_interval > 0 | Ensure positive intervals |
| `chk_delivery_status` | reminders | delivery_status IN ('pending', 'sent', 'failed', 'dismissed') | Validate delivery status |

---

## Migration Scripts

### Forward Migration

**File:** `backend/migrations/003_add_due_dates_reminders.sql`

```sql
-- Migration: Add Due Dates, Recurring Tasks, and Reminders
-- Feature: 010-recurring-due-dates
-- Risk Level: Medium
-- Estimated Duration: 5-10 seconds
-- Downtime: Zero (CONCURRENT indexes)

BEGIN;

-- ============================================================================
-- STEP 1: ADD NEW COLUMNS TO tasks TABLE
-- ============================================================================

-- Add due_date column (nullable, for task deadlines)
ALTER TABLE tasks
  ADD COLUMN IF NOT EXISTS due_date TIMESTAMPTZ DEFAULT NULL;

-- Add recurring pattern fields
ALTER TABLE tasks
  ADD COLUMN IF NOT EXISTS recurring_pattern VARCHAR(20) DEFAULT 'none',
  ADD COLUMN IF NOT EXISTS recurring_interval INTEGER DEFAULT 1,
  ADD COLUMN IF NOT EXISTS recurring_days TEXT[] DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS recurring_end_date TIMESTAMPTZ DEFAULT NULL;

-- Add parent_task_id for recurring instances (self-referential foreign key)
ALTER TABLE tasks
  ADD COLUMN IF NOT EXISTS parent_task_id INTEGER DEFAULT NULL;

-- Add next_occurrence for cached next generation time
ALTER TABLE tasks
  ADD COLUMN IF NOT EXISTS next_occurrence TIMESTAMPTZ DEFAULT NULL;

-- ============================================================================
-- STEP 2: ADD CONSTRAINTS TO tasks TABLE
-- ============================================================================

-- Validate recurring_pattern values
ALTER TABLE tasks
  ADD CONSTRAINT chk_recurring_pattern
  CHECK (recurring_pattern IN ('none', 'daily', 'weekly', 'monthly', 'custom'));

-- Validate recurring_interval is positive
ALTER TABLE tasks
  ADD CONSTRAINT chk_recurring_interval
  CHECK (recurring_interval IS NULL OR recurring_interval > 0);

-- Add foreign key for parent_task_id (self-referential)
ALTER TABLE tasks
  ADD CONSTRAINT fk_tasks_parent_task_id
  FOREIGN KEY (parent_task_id)
  REFERENCES tasks(id)
  ON DELETE CASCADE;

COMMIT;

-- ============================================================================
-- STEP 3: CREATE INDEXES ON tasks TABLE (CONCURRENTLY - NO LOCKS)
-- ============================================================================

-- Index for due date filtering (partial: only rows with due_date)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tasks_due_date
  ON tasks(due_date)
  WHERE due_date IS NOT NULL;

-- Index for finding recurring instances by parent
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tasks_parent_task_id
  ON tasks(parent_task_id)
  WHERE parent_task_id IS NOT NULL;

-- Index for finding recurring templates
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tasks_recurring_pattern
  ON tasks(recurring_pattern)
  WHERE recurring_pattern != 'none';

-- Index for job scheduler to find tasks to generate
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tasks_next_occurrence
  ON tasks(next_occurrence)
  WHERE next_occurrence IS NOT NULL;

-- ============================================================================
-- STEP 4: CREATE reminders TABLE
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS reminders (
  id SERIAL PRIMARY KEY,
  task_id INTEGER NOT NULL,
  user_id VARCHAR(255) NOT NULL,
  remind_at TIMESTAMPTZ NOT NULL,
  delivered BOOLEAN DEFAULT FALSE,
  delivery_status VARCHAR(20) DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  -- Foreign key to tasks (cascade delete)
  CONSTRAINT fk_reminders_task_id
    FOREIGN KEY (task_id)
    REFERENCES tasks(id)
    ON DELETE CASCADE,

  -- Validate delivery status
  CONSTRAINT chk_delivery_status
    CHECK (delivery_status IN ('pending', 'sent', 'failed', 'dismissed'))
);

COMMIT;

-- ============================================================================
-- STEP 5: CREATE INDEXES ON reminders TABLE (CONCURRENTLY)
-- ============================================================================

-- Index for task-specific reminder queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reminders_task_id
  ON reminders(task_id);

-- Index for user-specific reminder queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reminders_user_id
  ON reminders(user_id);

-- Index for job scheduler to find pending reminders (partial index)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reminders_remind_at
  ON reminders(remind_at)
  WHERE delivered = FALSE;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Validation: Check columns exist
SELECT
  column_name,
  data_type,
  is_nullable,
  column_default
FROM information_schema.columns
WHERE table_name = 'tasks'
  AND column_name IN (
    'due_date',
    'recurring_pattern',
    'recurring_interval',
    'recurring_days',
    'recurring_end_date',
    'parent_task_id',
    'next_occurrence'
  )
ORDER BY column_name;

-- Validation: Check reminders table exists
SELECT table_name
FROM information_schema.tables
WHERE table_name = 'reminders';

-- Validation: Check indexes exist
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('tasks', 'reminders')
  AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;
```

### Rollback Migration

**File:** `backend/migrations/003_add_due_dates_reminders_rollback.sql`

```sql
-- Rollback Migration: Remove Due Dates, Recurring Tasks, and Reminders
-- Feature: 010-recurring-due-dates
-- Risk Level: Medium
-- WARNING: This will DELETE all due dates, reminders, and recurring task data

BEGIN;

-- ============================================================================
-- STEP 1: DROP INDEXES ON reminders TABLE
-- ============================================================================

DROP INDEX IF EXISTS idx_reminders_task_id;
DROP INDEX IF EXISTS idx_reminders_user_id;
DROP INDEX IF EXISTS idx_reminders_remind_at;

-- ============================================================================
-- STEP 2: DROP reminders TABLE
-- ============================================================================

DROP TABLE IF EXISTS reminders CASCADE;

-- ============================================================================
-- STEP 3: DROP INDEXES ON tasks TABLE
-- ============================================================================

DROP INDEX IF EXISTS idx_tasks_due_date;
DROP INDEX IF EXISTS idx_tasks_parent_task_id;
DROP INDEX IF EXISTS idx_tasks_recurring_pattern;
DROP INDEX IF EXISTS idx_tasks_next_occurrence;

-- ============================================================================
-- STEP 4: DROP CONSTRAINTS ON tasks TABLE
-- ============================================================================

ALTER TABLE tasks DROP CONSTRAINT IF EXISTS fk_tasks_parent_task_id;
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS chk_recurring_pattern;
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS chk_recurring_interval;

-- ============================================================================
-- STEP 5: DROP COLUMNS FROM tasks TABLE
-- ============================================================================

ALTER TABLE tasks
  DROP COLUMN IF EXISTS next_occurrence,
  DROP COLUMN IF EXISTS parent_task_id,
  DROP COLUMN IF EXISTS recurring_end_date,
  DROP COLUMN IF EXISTS recurring_days,
  DROP COLUMN IF EXISTS recurring_interval,
  DROP COLUMN IF EXISTS recurring_pattern,
  DROP COLUMN IF EXISTS due_date;

COMMIT;

-- ============================================================================
-- ROLLBACK COMPLETE
-- ============================================================================

-- Validation: Verify columns removed
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'tasks'
  AND column_name IN (
    'due_date',
    'recurring_pattern',
    'recurring_interval',
    'recurring_days',
    'recurring_end_date',
    'parent_task_id',
    'next_occurrence'
  );
-- Expected: 0 rows

-- Validation: Verify reminders table removed
SELECT table_name
FROM information_schema.tables
WHERE table_name = 'reminders';
-- Expected: 0 rows
```

### Validation Queries

**File:** `backend/migrations/003_validate.sql`

```sql
-- Validation Queries for Migration 003

-- ============================================================================
-- CHECK 1: Verify new columns exist on tasks table
-- ============================================================================
SELECT
  column_name,
  data_type,
  is_nullable,
  column_default
FROM information_schema.columns
WHERE table_name = 'tasks'
  AND column_name IN (
    'due_date',
    'recurring_pattern',
    'recurring_interval',
    'recurring_days',
    'recurring_end_date',
    'parent_task_id',
    'next_occurrence'
  )
ORDER BY column_name;

-- Expected: 7 rows (all new columns)

-- ============================================================================
-- CHECK 2: Verify reminders table exists
-- ============================================================================
SELECT
  column_name,
  data_type,
  is_nullable
FROM information_schema.columns
WHERE table_name = 'reminders'
ORDER BY ordinal_position;

-- Expected: 8 rows (id, task_id, user_id, remind_at, delivered, delivery_status, created_at, updated_at)

-- ============================================================================
-- CHECK 3: Verify indexes exist
-- ============================================================================
SELECT
  tablename,
  indexname,
  indexdef
FROM pg_indexes
WHERE tablename IN ('tasks', 'reminders')
  AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;

-- Expected indexes on tasks:
-- - idx_tasks_due_date
-- - idx_tasks_parent_task_id
-- - idx_tasks_recurring_pattern
-- - idx_tasks_next_occurrence
--
-- Expected indexes on reminders:
-- - idx_reminders_task_id
-- - idx_reminders_user_id
-- - idx_reminders_remind_at

-- ============================================================================
-- CHECK 4: Verify constraints exist
-- ============================================================================
SELECT
  conname AS constraint_name,
  contype AS constraint_type,
  pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'tasks'::regclass
  AND conname IN ('chk_recurring_pattern', 'chk_recurring_interval', 'fk_tasks_parent_task_id')
ORDER BY conname;

-- Expected: 3 rows (recurring_pattern check, recurring_interval check, parent_task_id FK)

SELECT
  conname AS constraint_name,
  contype AS constraint_type,
  pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'reminders'::regclass
  AND conname IN ('fk_reminders_task_id', 'chk_delivery_status')
ORDER BY conname;

-- Expected: 2 rows (task_id FK, delivery_status check)

-- ============================================================================
-- CHECK 5: Verify data integrity
-- ============================================================================

-- Check: All existing tasks have default values for new columns
SELECT
  COUNT(*) AS total_tasks,
  COUNT(CASE WHEN recurring_pattern = 'none' THEN 1 END) AS non_recurring_tasks,
  COUNT(CASE WHEN recurring_interval = 1 THEN 1 END) AS default_interval_tasks,
  COUNT(CASE WHEN due_date IS NULL THEN 1 END) AS tasks_without_due_date
FROM tasks;

-- Expected: All existing tasks should have recurring_pattern = 'none', recurring_interval = 1, due_date = NULL

-- Check: No orphaned parent_task_id references
SELECT COUNT(*)
FROM tasks
WHERE parent_task_id IS NOT NULL
  AND parent_task_id NOT IN (SELECT id FROM tasks);
-- Expected: 0

-- Check: No reminders without tasks
SELECT COUNT(*)
FROM reminders r
WHERE NOT EXISTS (SELECT 1 FROM tasks t WHERE t.id = r.task_id);
-- Expected: 0

-- ============================================================================
-- CHECK 6: Performance check (index usage)
-- ============================================================================

-- Verify indexes are being used (run EXPLAIN on common queries)
EXPLAIN ANALYZE
SELECT * FROM tasks
WHERE due_date IS NOT NULL
  AND due_date < NOW()
ORDER BY due_date;
-- Should use idx_tasks_due_date

EXPLAIN ANALYZE
SELECT * FROM reminders
WHERE delivered = FALSE
  AND remind_at <= NOW()
ORDER BY remind_at;
-- Should use idx_reminders_remind_at

-- ============================================================================
-- VALIDATION COMPLETE
-- ============================================================================
```

---

## SQLModel Updates

### Updated Model: Task

**File:** `backend/app/models/task.py`

```python
"""Task model and schemas"""
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import ARRAY, String
from datetime import datetime
from typing import Optional, List


class TaskBase(SQLModel):
    """Base task fields"""
    title: str
    description: Optional[str] = None
    completed: bool = False
    priority: str = Field(default="medium", regex="^(high|medium|low)$")
    tags: List[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))

    # NEW: Due date and reminder fields
    due_date: Optional[datetime] = Field(
        default=None,
        description="Task due date with timezone"
    )

    # NEW: Recurring task fields
    recurring_pattern: str = Field(
        default="none",
        regex="^(none|daily|weekly|monthly|custom)$",
        description="Recurrence frequency"
    )
    recurring_interval: int = Field(
        default=1,
        gt=0,
        description="Interval for recurring pattern (e.g., every 2 weeks)"
    )
    recurring_days: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(ARRAY(String)),
        description="Days of week for weekly recurrence (Mon, Wed, Fri)"
    )
    recurring_end_date: Optional[datetime] = Field(
        default=None,
        description="When recurring series ends"
    )
    parent_task_id: Optional[int] = Field(
        default=None,
        foreign_key="tasks.id",
        description="Parent task for recurring instances"
    )
    next_occurrence: Optional[datetime] = Field(
        default=None,
        description="Cached next occurrence for job scheduler"
    )


class Task(TaskBase, table=True):
    """Task database model"""
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)  # JWT user ID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True


class TaskCreate(TaskBase):
    """Schema for creating a task"""
    pass


class TaskUpdate(SQLModel):
    """Schema for updating a task (all fields optional)"""
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[str] = Field(None, regex="^(high|medium|low)$")
    tags: Optional[List[str]] = None

    # NEW: Allow updating due date and recurring fields
    due_date: Optional[datetime] = None
    recurring_pattern: Optional[str] = Field(
        None,
        regex="^(none|daily|weekly|monthly|custom)$"
    )
    recurring_interval: Optional[int] = Field(None, gt=0)
    recurring_days: Optional[List[str]] = None
    recurring_end_date: Optional[datetime] = None
    next_occurrence: Optional[datetime] = None


class TaskRead(TaskBase):
    """Schema for reading a task"""
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
```

### New Model: Reminder

**File:** `backend/app/models/reminder.py`

```python
"""Reminder model and schemas"""
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class ReminderBase(SQLModel):
    """Base reminder fields"""
    task_id: int = Field(foreign_key="tasks.id")
    user_id: str = Field(description="User who owns this reminder")
    remind_at: datetime = Field(description="When to trigger reminder")
    delivered: bool = Field(default=False, description="Whether reminder was delivered")
    delivery_status: str = Field(
        default="pending",
        regex="^(pending|sent|failed|dismissed)$",
        description="Reminder delivery status"
    )


class Reminder(ReminderBase, table=True):
    """Reminder database model"""
    __tablename__ = "reminders"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True


class ReminderCreate(ReminderBase):
    """Schema for creating a reminder"""
    pass


class ReminderUpdate(SQLModel):
    """Schema for updating a reminder (all fields optional)"""
    remind_at: Optional[datetime] = None
    delivered: Optional[bool] = None
    delivery_status: Optional[str] = Field(
        None,
        regex="^(pending|sent|failed|dismissed)$"
    )


class ReminderRead(ReminderBase):
    """Schema for reading a reminder"""
    id: int
    created_at: datetime
    updated_at: datetime
```

### Schema Documentation Update

**File:** `specs/database/schema.md` (append to tasks table section)

```markdown
### tasks Table Extensions (Migration 003)

#### Due Date and Recurring Fields

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| due_date | TIMESTAMPTZ | YES | NULL | Task due date with timezone awareness |
| recurring_pattern | VARCHAR(20) | YES | 'none' | Recurrence frequency: none, daily, weekly, monthly, custom |
| recurring_interval | INTEGER | YES | 1 | Interval for recurring pattern (e.g., every 2 weeks) |
| recurring_days | TEXT[] | YES | NULL | Days of week for weekly recurrence (Mon, Wed, Fri) |
| recurring_end_date | TIMESTAMPTZ | YES | NULL | When recurring series ends |
| parent_task_id | INTEGER | YES | NULL | Parent task ID for recurring instances (FK to tasks.id) |
| next_occurrence | TIMESTAMPTZ | YES | NULL | Cached next occurrence for job scheduler |

### reminders Table (New)

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | SERIAL | NO | AUTO | Primary key |
| task_id | INTEGER | NO | - | Task this reminder belongs to (FK to tasks.id) |
| user_id | VARCHAR(255) | NO | - | User who owns this reminder |
| remind_at | TIMESTAMPTZ | NO | - | When to trigger the reminder |
| delivered | BOOLEAN | NO | FALSE | Whether reminder was delivered |
| delivery_status | VARCHAR(20) | NO | 'pending' | Status: pending, sent, failed, dismissed |
| created_at | TIMESTAMPTZ | NO | NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | NOW() | Last update timestamp |
```

---

## Migration Procedure

### Development Environment

```bash
# 1. Backup database (optional for dev)
pg_dump $DATABASE_URL > backup_dev_$(date +%Y%m%d).sql

# 2. Apply forward migration
psql $DATABASE_URL -f backend/migrations/003_add_due_dates_reminders.sql

# 3. Run validation queries
psql $DATABASE_URL -f backend/migrations/003_validate.sql

# 4. Update SQLModel models
# Edit backend/app/models/task.py (add new fields)
# Create backend/app/models/reminder.py (new model)

# 5. Restart backend to apply model changes
cd backend
uvicorn app.main:app --reload

# 6. Test endpoints
# - Create task with due_date
# - Create reminder for task
# - Create recurring task
# - List tasks with due dates

# 7. If issues: rollback
# psql $DATABASE_URL -f backend/migrations/003_add_due_dates_reminders_rollback.sql
```

### Staging Environment

```bash
# 1. Backup database (REQUIRED)
pg_dump $DATABASE_URL > backup_staging_$(date +%Y%m%d).sql

# 2. Apply migration
psql $DATABASE_URL -f backend/migrations/003_add_due_dates_reminders.sql

# 3. Validate
psql $DATABASE_URL -f backend/migrations/003_validate.sql

# 4. Deploy new code
git push staging feature/010-recurring-due-dates

# 5. Run E2E tests
npm run test:e2e

# 6. Monitor for 1 hour
# Check logs, metrics, error rates

# 7. If stable: proceed to production
# 8. If issues: rollback
# psql $DATABASE_URL -f backend/migrations/003_add_due_dates_reminders_rollback.sql
# git revert HEAD && git push staging main
```

### Production Environment

```bash
# ============================================================================
# PRE-DEPLOYMENT CHECKLIST
# ============================================================================
# [ ] Migration tested on staging
# [ ] All validation queries pass
# [ ] E2E tests pass
# [ ] Rollback script tested
# [ ] Database backup completed
# [ ] Team notified of deployment
# [ ] Off-peak time selected (low traffic)

# ============================================================================
# DEPLOYMENT STEPS
# ============================================================================

# 1. BACKUP DATABASE (CRITICAL)
pg_dump $DATABASE_URL > backup_production_$(date +%Y%m%d_%H%M%S).sql
aws s3 cp backup_production_*.sql s3://my-backups/

# 2. Apply migration (zero downtime - CONCURRENT indexes)
psql $DATABASE_URL -f backend/migrations/003_add_due_dates_reminders.sql

# Expected output:
# - ALTER TABLE (7 columns added)
# - CREATE INDEX CONCURRENTLY (4 indexes created)
# - CREATE TABLE (reminders created)
# - CREATE INDEX CONCURRENTLY (3 indexes created)
# Duration: 5-10 seconds

# 3. Validate migration success
psql $DATABASE_URL -f backend/migrations/003_validate.sql

# 4. Deploy new application code (backward compatible)
git checkout 010-recurring-due-dates
git push production 010-recurring-due-dates:main

# 5. Monitor application
# - Check /health endpoint
# - Watch error logs for 15 minutes
# - Monitor database query performance
# - Verify new endpoints work

# 6. Smoke test
curl -X GET https://api.example.com/api/user123/tasks \
  -H "Authorization: Bearer $TOKEN"

curl -X POST https://api.example.com/api/user123/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test task", "due_date": "2026-01-15T09:00:00Z"}'

# 7. If issues detected: ROLLBACK
# psql $DATABASE_URL -f backend/migrations/003_add_due_dates_reminders_rollback.sql
# git revert HEAD && git push production main
# Restore from backup if necessary

# ============================================================================
# POST-DEPLOYMENT VERIFICATION
# ============================================================================

# Check metrics after 1 hour:
# - Error rate (should be unchanged)
# - Response time (should be < 10% increase)
# - Database connection pool (should be stable)
# - New endpoints usage (should show activity)

# ============================================================================
# DEPLOYMENT COMPLETE
# ============================================================================
```

---

## Risk Assessment

### Breaking Changes

**None** - Migration is backward compatible:
- All new columns have defaults or are nullable
- Existing queries continue to work
- Old code can run during migration (graceful degradation)
- Indexes created CONCURRENTLY (no table locks)

### Performance Impact

**Index Creation:**
- CONCURRENT index creation: ~1 second per 100k rows
- No table locks during creation
- Read/write operations continue normally

**Storage:**
- New columns: ~40 bytes per task row
- New table (reminders): ~80 bytes per reminder row
- Indexes: ~24 bytes per indexed row
- **Total for 1M tasks:** ~64 MB additional storage

**Query Performance:**
- Due date filtering: O(log n) with idx_tasks_due_date
- Recurring task lookups: O(log n) with idx_tasks_recurring_pattern
- Reminder queries: O(log n) with idx_reminders_remind_at
- No performance degradation expected

### Data Integrity

**Existing Data:**
- All existing tasks receive default values:
  - `recurring_pattern = 'none'`
  - `recurring_interval = 1`
  - `due_date = NULL`
  - `parent_task_id = NULL`
- No data loss risk

**New Data:**
- Foreign key constraints prevent orphaned reminders
- Check constraints enforce valid values
- Cascade deletes maintain referential integrity

### Rollback Risk

**Risk Level:** Low

**Rollback Impact:**
- Drops all due dates (data loss)
- Drops all reminders (data loss)
- Drops all recurring task data (data loss)
- No impact on existing tasks (title, description, completed)

**Rollback Duration:** < 5 seconds

**Warning:** Rollback is destructive. Only use if migration causes critical production issues. Consider forward-fixing minor issues instead.

---

## Testing Checklist

### Pre-Production Testing

- [ ] Migration runs successfully on dev database
- [ ] All validation queries pass
- [ ] SQLModel models sync with new schema
- [ ] Backend starts without errors
- [ ] Existing API endpoints work (GET/POST/PUT/DELETE tasks)
- [ ] New functionality works:
  - [ ] Set due_date on task
  - [ ] Clear due_date from task
  - [ ] Create reminder for task
  - [ ] List reminders for task
  - [ ] Delete reminder
  - [ ] Create recurring task
  - [ ] View recurring task instances
- [ ] Rollback script tested on dev
- [ ] Migration runs successfully on staging
- [ ] E2E tests pass on staging
- [ ] Load testing completed (1000 concurrent users)

### Post-Production Testing

- [ ] Health check endpoint returns 200
- [ ] Task list endpoint responds in < 200ms
- [ ] Create task with due_date works
- [ ] Create reminder works
- [ ] Database query performance normal
- [ ] Error logs show no migration-related errors
- [ ] Frontend displays due dates correctly
- [ ] Frontend displays reminders correctly
- [ ] Recurring task generation works (if enabled)

---

## Dependencies

### Required

- PostgreSQL 12+ (for TIMESTAMPTZ, partial indexes, CONCURRENT index creation)
- Neon Serverless PostgreSQL (or compatible)
- Database user with ALTER TABLE, CREATE TABLE, CREATE INDEX privileges
- No concurrent schema migrations running

### Blocks

**This migration must complete before:**
- Due date API endpoints can be deployed
- Reminder API endpoints can be deployed
- Recurring task generation can be enabled
- Frontend due date UI can be released

### Blocked By

**Must complete before this migration:**
- None - this migration is independent

---

## Estimated Impact

| Metric | Value |
|--------|-------|
| Migration Duration | 5-10 seconds |
| Downtime | **0 seconds** (CONCURRENT indexes) |
| Disk Space Change | +64 MB per 1M tasks |
| Index Build Time | ~5 seconds total |
| Risk Level | **Medium** |
| Rollback Duration | < 5 seconds |
| Backward Compatibility | **100%** (old code works) |

---

## Troubleshooting

### Issue: Index creation fails with "already exists"

**Cause:** Migration was partially applied
**Solution:**
```sql
-- Check which indexes exist
SELECT indexname FROM pg_indexes WHERE tablename = 'tasks';

-- If needed, drop and recreate
DROP INDEX IF EXISTS idx_tasks_due_date;
CREATE INDEX CONCURRENTLY idx_tasks_due_date ON tasks(due_date) WHERE due_date IS NOT NULL;
```

### Issue: Foreign key constraint fails

**Cause:** Orphaned parent_task_id references
**Solution:**
```sql
-- Find orphaned references
SELECT id, parent_task_id
FROM tasks
WHERE parent_task_id IS NOT NULL
  AND parent_task_id NOT IN (SELECT id FROM tasks);

-- Clean up orphaned references
UPDATE tasks
SET parent_task_id = NULL
WHERE parent_task_id NOT IN (SELECT id FROM tasks);

-- Retry migration
```

### Issue: CONCURRENT index creation fails

**Cause:** Conflicting transactions
**Solution:**
```sql
-- Drop failed index
DROP INDEX IF EXISTS idx_tasks_due_date;

-- Retry with longer timeout
SET statement_timeout = '600s';
CREATE INDEX CONCURRENTLY idx_tasks_due_date ON tasks(due_date) WHERE due_date IS NOT NULL;
```

### Issue: Rollback needed immediately

**Solution:**
```bash
# Run rollback script
psql $DATABASE_URL -f backend/migrations/003_add_due_dates_reminders_rollback.sql

# Revert application code
git revert HEAD
git push production main

# Restore from backup if data loss occurred
psql $DATABASE_URL < backup_production_YYYYMMDD_HHMMSS.sql
```

---

## Success Criteria

✅ Migration is successful when:

1. All validation queries return expected results
2. Backend starts without errors
3. Existing task endpoints work (backward compatibility)
4. New due_date and reminder fields are accessible
5. Database performance remains stable (< 10% response time increase)
6. No errors in application logs
7. Frontend can read and write new fields
8. Rollback script tested and ready

---

## Additional Notes

### Timezone Handling

All TIMESTAMPTZ columns store UTC internally. Application code must:
- Convert user input from local timezone to UTC before storing
- Convert UTC to user's timezone when displaying
- Use Python `datetime.timezone.utc` or `pytz` for conversions

### Recurring Task Pattern

The `recurring_pattern` field uses simple enum values:
- `'none'` - Not recurring (default)
- `'daily'` - Every day
- `'weekly'` - Every week (specific days in `recurring_days`)
- `'monthly'` - Every month (specific day of month)
- `'custom'` - Custom interval (use `recurring_interval`)

For more complex patterns, consider migrating to RFC 5545 RRULE format in future.

### Job Scheduler Integration

The `next_occurrence` field is a cached value used by APScheduler:
- Updated by recurring task generator job
- Indexed for fast job scheduler queries
- Application code should NOT modify directly (managed by scheduler)

---

**Migration prepared by:** db-migrator agent
**Last updated:** 2026-01-09
**Status:** Ready for review and testing
