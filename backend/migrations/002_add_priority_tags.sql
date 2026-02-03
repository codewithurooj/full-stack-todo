-- Migration: Add priority and tags to tasks table
-- Date: 2026-01-07
-- Feature: 009-intermediate-features
-- Description: Adds priority (VARCHAR with CHECK constraint) and tags (TEXT[] array) columns to tasks table

BEGIN;

-- Step 1: Add priority column with default value 'medium'
-- Using default ensures zero-downtime - existing rows get 'medium' automatically
ALTER TABLE tasks
  ADD COLUMN priority VARCHAR(20) DEFAULT 'medium';

-- Step 2: Add tags column with default empty array
-- Using default empty array ensures all existing rows have valid values
ALTER TABLE tasks
  ADD COLUMN tags TEXT[] DEFAULT '{}';

-- Step 3: Add CHECK constraint for priority values
-- Ensures data integrity - only 'high', 'medium', 'low' are allowed
ALTER TABLE tasks
  ADD CONSTRAINT chk_tasks_priority
  CHECK (priority IN ('high', 'medium', 'low'));

-- Step 4: Create index on priority column for filtering performance
-- Improves query performance when filtering tasks by priority
CREATE INDEX idx_tasks_priority ON tasks(priority);

-- Step 5: Verify migration success
-- Validates that all columns and indexes were created correctly
DO $$
BEGIN
  -- Verify priority column exists
  ASSERT (SELECT COUNT(*) FROM information_schema.columns
          WHERE table_name = 'tasks' AND column_name = 'priority') = 1,
         'Priority column was not created';

  -- Verify tags column exists
  ASSERT (SELECT COUNT(*) FROM information_schema.columns
          WHERE table_name = 'tasks' AND column_name = 'tags') = 1,
         'Tags column was not created';

  -- Verify priority index exists
  ASSERT (SELECT COUNT(*) FROM pg_indexes
          WHERE tablename = 'tasks' AND indexname = 'idx_tasks_priority') = 1,
         'Priority index was not created';

  -- Verify priority constraint exists
  ASSERT (SELECT COUNT(*) FROM information_schema.constraint_column_usage
          WHERE table_name = 'tasks' AND constraint_name = 'chk_tasks_priority') = 1,
         'Priority CHECK constraint was not created';

  RAISE NOTICE 'Migration 002_add_priority_tags verified successfully';
  RAISE NOTICE '  - priority column added (VARCHAR(20), default: medium)';
  RAISE NOTICE '  - tags column added (TEXT[], default: {})';
  RAISE NOTICE '  - CHECK constraint added for priority values';
  RAISE NOTICE '  - Index created on priority column';
END $$;

COMMIT;

-- Verification queries (run separately after migration)
-- SELECT column_name, data_type, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'tasks' AND column_name IN ('priority', 'tags');
--
-- SELECT indexname, indexdef
-- FROM pg_indexes
-- WHERE tablename = 'tasks' AND indexname = 'idx_tasks_priority';
