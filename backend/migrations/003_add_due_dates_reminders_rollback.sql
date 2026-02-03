-- Rollback Migration: Remove Due Dates, Recurring Tasks, and Reminders
-- Feature: 010-recurring-due-dates
-- Version: 003
-- Risk Level: Medium
-- WARNING: This will DELETE all due dates, reminders, and recurring task data
-- Created: 2026-01-09

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
