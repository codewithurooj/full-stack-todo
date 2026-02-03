-- Rollback Migration: 004_add_kafka_event_schema
-- Feature: Event-Driven Architecture with Kafka
-- Date: 2026-01-12
-- Purpose: Revert all changes made by 004_add_kafka_event_schema.sql
-- Risk Level: Low (drops tables and indexes, does not affect existing task/user data)

BEGIN;

-- ============================================================================
-- ROLLBACK ORDER (reverse of forward migration)
-- ============================================================================
-- 1. Drop notification_subscriptions indexes
-- 2. Drop notification_subscriptions table
-- 3. Drop idempotency constraint on tasks
-- 4. Drop audit_logs indexes
-- 5. Drop audit_logs table

-- ============================================================================
-- 1. DROP NOTIFICATION_SUBSCRIPTIONS INDEXES
-- ============================================================================

DROP INDEX IF EXISTS idx_notification_subs_user_id;

-- ============================================================================
-- 2. DROP NOTIFICATION_SUBSCRIPTIONS TABLE
-- ============================================================================

DROP TABLE IF EXISTS notification_subscriptions CASCADE;

-- ============================================================================
-- 3. DROP IDEMPOTENCY CONSTRAINT ON TASKS TABLE
-- ============================================================================

DROP INDEX IF EXISTS idx_recurring_instance_dedup;

-- ============================================================================
-- 4. DROP AUDIT_LOGS INDEXES
-- ============================================================================

DROP INDEX IF EXISTS idx_audit_logs_task_id;
DROP INDEX IF EXISTS idx_audit_logs_user_id;
DROP INDEX IF EXISTS idx_audit_logs_timestamp;
DROP INDEX IF EXISTS idx_audit_logs_operation_type;

-- Optional GIN index (if it was created)
DROP INDEX IF EXISTS idx_audit_logs_payload_gin;

-- ============================================================================
-- 5. DROP AUDIT_LOGS TABLE
-- ============================================================================

DROP TABLE IF EXISTS audit_logs CASCADE;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Verify that tables and indexes have been removed

-- Verify audit_logs table is dropped
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'audit_logs'
    ) THEN
        RAISE EXCEPTION 'audit_logs table was not dropped';
    END IF;
END $$;

-- Verify notification_subscriptions table is dropped
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'notification_subscriptions'
    ) THEN
        RAISE EXCEPTION 'notification_subscriptions table was not dropped';
    END IF;
END $$;

-- Verify idempotency index on tasks is dropped
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE indexname = 'idx_recurring_instance_dedup'
    ) THEN
        RAISE EXCEPTION 'idx_recurring_instance_dedup index was not dropped';
    END IF;
END $$;

COMMIT;

-- ============================================================================
-- POST-ROLLBACK VALIDATION
-- ============================================================================
-- Run these queries manually after rollback to verify success:

/*
-- 1. Verify audit_logs table does not exist
SELECT table_name
FROM information_schema.tables
WHERE table_name = 'audit_logs';
-- Expected: 0 rows

-- 2. Verify notification_subscriptions table does not exist
SELECT table_name
FROM information_schema.tables
WHERE table_name = 'notification_subscriptions';
-- Expected: 0 rows

-- 3. Verify idempotency index does not exist
SELECT indexname
FROM pg_indexes
WHERE indexname = 'idx_recurring_instance_dedup';
-- Expected: 0 rows

-- 4. Verify existing tasks table is intact
SELECT COUNT(*) FROM tasks;
-- Expected: Count of existing tasks (unchanged)

-- 5. Verify existing users table is intact
SELECT COUNT(*) FROM users;
-- Expected: Count of existing users (unchanged)
*/

-- ============================================================================
-- NOTES
-- ============================================================================
-- This rollback is safe because:
-- 1. Only drops NEW tables (audit_logs, notification_subscriptions)
-- 2. Only drops NEW index on tasks (idx_recurring_instance_dedup)
-- 3. Does NOT modify existing task or user data
-- 4. CASCADE ensures dependent objects are cleaned up properly
-- 5. IF EXISTS prevents errors if tables/indexes were never created

-- After rollback, you can safely re-run the forward migration if needed.
