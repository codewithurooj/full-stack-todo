-- Migration: Add Due Dates, Recurring Tasks, and Reminders
-- Feature: 010-recurring-due-dates
-- Version: 003
-- Risk Level: Medium
-- Estimated Duration: 5-10 seconds
-- Downtime: Zero (CONCURRENT indexes)
-- Created: 2026-01-09

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
