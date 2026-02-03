-- Rollback Migration: Remove priority and tags from tasks table
-- Date: 2026-01-07
-- Feature: 009-intermediate-features
-- Description: Safely removes priority and tags columns added in 002_add_priority_tags.sql

BEGIN;

-- Step 1: Drop the priority index (must be done before dropping column)
DROP INDEX IF EXISTS idx_tasks_priority;

-- Step 2: Drop priority column
-- This also removes the CHECK constraint automatically
ALTER TABLE tasks DROP COLUMN IF EXISTS priority;

-- Step 3: Drop tags column
ALTER TABLE tasks DROP COLUMN IF EXISTS tags;

-- Step 4: Verify rollback success
DO $$
BEGIN
  -- Verify priority column is removed
  ASSERT (SELECT COUNT(*) FROM information_schema.columns
          WHERE table_name = 'tasks' AND column_name = 'priority') = 0,
         'Priority column was not removed';

  -- Verify tags column is removed
  ASSERT (SELECT COUNT(*) FROM information_schema.columns
          WHERE table_name = 'tasks' AND column_name = 'tags') = 0,
         'Tags column was not removed';

  -- Verify priority index is removed
  ASSERT (SELECT COUNT(*) FROM pg_indexes
          WHERE tablename = 'tasks' AND indexname = 'idx_tasks_priority') = 0,
         'Priority index was not removed';

  RAISE NOTICE 'Rollback 002_add_priority_tags completed successfully';
  RAISE NOTICE '  - priority column removed';
  RAISE NOTICE '  - tags column removed';
  RAISE NOTICE '  - Priority index removed';
  RAISE NOTICE '  - CHECK constraint removed';
END $$;

COMMIT;

-- Verification queries (run separately after rollback)
-- SELECT column_name
-- FROM information_schema.columns
-- WHERE table_name = 'tasks' AND column_name IN ('priority', 'tags');
-- (Should return 0 rows)
