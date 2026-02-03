-- Validation Queries: 004_add_kafka_event_schema
-- Feature: Event-Driven Architecture with Kafka
-- Date: 2026-01-12
-- Purpose: Comprehensive validation of migration 004 success

-- ============================================================================
-- TABLE STRUCTURE VALIDATION
-- ============================================================================

-- 1. Verify audit_logs table structure
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default,
    character_maximum_length
FROM information_schema.columns
WHERE table_name = 'audit_logs'
ORDER BY ordinal_position;

-- Expected columns:
-- id              | integer         | NO  | nextval('audit_logs_id_seq'::regclass)
-- event_id        | uuid            | NO  | NULL
-- timestamp       | timestamptz     | NO  | NULL
-- user_id         | integer         | NO  | NULL
-- task_id         | integer         | YES | NULL
-- operation_type  | varchar(50)     | NO  | NULL
-- event_payload   | jsonb           | NO  | NULL
-- system_generated| boolean         | YES | false
-- created_at      | timestamptz     | YES | now()

-- 2. Verify notification_subscriptions table structure
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'notification_subscriptions'
ORDER BY ordinal_position;

-- Expected columns:
-- id         | integer     | NO  | nextval('notification_subscriptions_id_seq'::regclass)
-- user_id    | integer     | NO  | NULL
-- endpoint   | text        | NO  | NULL
-- p256dh     | text        | NO  | NULL
-- auth       | text        | NO  | NULL
-- created_at | timestamptz | YES | now()
-- updated_at | timestamptz | YES | now()

-- ============================================================================
-- INDEX VALIDATION
-- ============================================================================

-- 3. Verify audit_logs indexes
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'audit_logs'
ORDER BY indexname;

-- Expected indexes:
-- audit_logs_pkey                  | CREATE UNIQUE INDEX ... PRIMARY KEY (id)
-- audit_logs_event_id_key          | CREATE UNIQUE INDEX ... UNIQUE (event_id)
-- idx_audit_logs_task_id          | CREATE INDEX ... (task_id) WHERE task_id IS NOT NULL
-- idx_audit_logs_user_id          | CREATE INDEX ... (user_id)
-- idx_audit_logs_timestamp        | CREATE INDEX ... (timestamp DESC)
-- idx_audit_logs_operation_type   | CREATE INDEX ... (operation_type)

-- 4. Verify notification_subscriptions indexes
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'notification_subscriptions'
ORDER BY indexname;

-- Expected indexes:
-- notification_subscriptions_pkey                      | CREATE UNIQUE INDEX ... PRIMARY KEY (id)
-- notification_subscriptions_user_id_endpoint_key     | CREATE UNIQUE INDEX ... UNIQUE (user_id, endpoint)
-- idx_notification_subs_user_id                       | CREATE INDEX ... (user_id)

-- 5. Verify idempotency constraint on tasks
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'tasks'
  AND indexname = 'idx_recurring_instance_dedup';

-- Expected:
-- idx_recurring_instance_dedup | CREATE UNIQUE INDEX ... (parent_task_id, due_date) WHERE parent_task_id IS NOT NULL

-- ============================================================================
-- CONSTRAINT VALIDATION
-- ============================================================================

-- 6. Verify foreign key constraints on audit_logs
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule,
    rc.update_rule
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints AS rc
    ON tc.constraint_name = rc.constraint_name
WHERE tc.table_name = 'audit_logs'
  AND tc.constraint_type = 'FOREIGN KEY';

-- Expected:
-- fk_audit_logs_user_id | audit_logs | user_id | users | id | CASCADE    | NO ACTION
-- fk_audit_logs_task_id | audit_logs | task_id | tasks | id | SET NULL   | NO ACTION

-- 7. Verify check constraints on audit_logs
SELECT
    tc.constraint_name,
    cc.check_clause
FROM information_schema.table_constraints AS tc
JOIN information_schema.check_constraints AS cc
    ON tc.constraint_name = cc.constraint_name
WHERE tc.table_name = 'audit_logs'
  AND tc.constraint_type = 'CHECK';

-- Expected:
-- chk_audit_logs_operation_type | (operation_type IN ('task.created', 'task.updated', 'task.deleted', 'task.completed'))
-- chk_audit_logs_timestamp      | (timestamp <= (now() + '01:00:00'::interval))

-- 8. Verify foreign key constraints on notification_subscriptions
SELECT
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints AS rc
    ON tc.constraint_name = rc.constraint_name
WHERE tc.table_name = 'notification_subscriptions'
  AND tc.constraint_type = 'FOREIGN KEY';

-- Expected:
-- fk_notification_subs_user_id | user_id | users | id | CASCADE

-- ============================================================================
-- DATA INTEGRITY TESTS
-- ============================================================================

-- 9. Test audit_logs insert (should succeed)
DO $$
DECLARE
    test_event_id UUID;
    test_user_id INTEGER;
    test_task_id INTEGER;
BEGIN
    -- Get first user ID for testing
    SELECT id INTO test_user_id FROM users LIMIT 1;

    -- Get first task ID for testing
    SELECT id INTO test_task_id FROM tasks LIMIT 1;

    -- Generate unique event ID
    test_event_id := gen_random_uuid();

    -- Insert test record
    INSERT INTO audit_logs (
        event_id,
        timestamp,
        user_id,
        task_id,
        operation_type,
        event_payload,
        system_generated
    ) VALUES (
        test_event_id,
        NOW(),
        test_user_id,
        test_task_id,
        'task.created',
        '{"test": "validation_insert"}'::jsonb,
        false
    );

    -- Delete test record
    DELETE FROM audit_logs WHERE event_id = test_event_id;

    RAISE NOTICE 'audit_logs insert test: PASSED';
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'audit_logs insert test: FAILED - %', SQLERRM;
END $$;

-- 10. Test duplicate event_id constraint (should fail)
DO $$
DECLARE
    test_event_id UUID;
    test_user_id INTEGER;
BEGIN
    -- Get first user ID
    SELECT id INTO test_user_id FROM users LIMIT 1;

    test_event_id := gen_random_uuid();

    -- Insert first record
    INSERT INTO audit_logs (event_id, timestamp, user_id, operation_type, event_payload)
    VALUES (test_event_id, NOW(), test_user_id, 'task.created', '{}'::jsonb);

    -- Try to insert duplicate (should fail)
    BEGIN
        INSERT INTO audit_logs (event_id, timestamp, user_id, operation_type, event_payload)
        VALUES (test_event_id, NOW(), test_user_id, 'task.updated', '{}'::jsonb);

        RAISE EXCEPTION 'Duplicate event_id test: FAILED - no constraint violation';
    EXCEPTION
        WHEN unique_violation THEN
            -- Expected behavior
            RAISE NOTICE 'Duplicate event_id test: PASSED';
    END;

    -- Cleanup
    DELETE FROM audit_logs WHERE event_id = test_event_id;
END $$;

-- 11. Test invalid operation_type constraint (should fail)
DO $$
DECLARE
    test_user_id INTEGER;
BEGIN
    SELECT id INTO test_user_id FROM users LIMIT 1;

    BEGIN
        INSERT INTO audit_logs (event_id, timestamp, user_id, operation_type, event_payload)
        VALUES (gen_random_uuid(), NOW(), test_user_id, 'invalid.type', '{}'::jsonb);

        RAISE EXCEPTION 'Invalid operation_type test: FAILED - no constraint violation';
    EXCEPTION
        WHEN check_violation THEN
            -- Expected behavior
            RAISE NOTICE 'Invalid operation_type test: PASSED';
    END;
END $$;

-- 12. Test notification_subscriptions insert (should succeed)
DO $$
DECLARE
    test_user_id INTEGER;
BEGIN
    SELECT id INTO test_user_id FROM users LIMIT 1;

    INSERT INTO notification_subscriptions (user_id, endpoint, p256dh, auth)
    VALUES (
        test_user_id,
        'https://fcm.googleapis.com/fcm/send/test-endpoint',
        'test-public-key-base64',
        'test-auth-secret-base64'
    );

    -- Cleanup
    DELETE FROM notification_subscriptions
    WHERE endpoint = 'https://fcm.googleapis.com/fcm/send/test-endpoint';

    RAISE NOTICE 'notification_subscriptions insert test: PASSED';
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'notification_subscriptions insert test: FAILED - %', SQLERRM;
END $$;

-- 13. Test duplicate subscription constraint (should fail)
DO $$
DECLARE
    test_user_id INTEGER;
BEGIN
    SELECT id INTO test_user_id FROM users LIMIT 1;

    -- Insert first subscription
    INSERT INTO notification_subscriptions (user_id, endpoint, p256dh, auth)
    VALUES (test_user_id, 'https://test-endpoint.com', 'key1', 'auth1');

    BEGIN
        -- Try to insert duplicate (should fail)
        INSERT INTO notification_subscriptions (user_id, endpoint, p256dh, auth)
        VALUES (test_user_id, 'https://test-endpoint.com', 'key2', 'auth2');

        RAISE EXCEPTION 'Duplicate subscription test: FAILED - no constraint violation';
    EXCEPTION
        WHEN unique_violation THEN
            -- Expected behavior
            RAISE NOTICE 'Duplicate subscription test: PASSED';
    END;

    -- Cleanup
    DELETE FROM notification_subscriptions WHERE endpoint = 'https://test-endpoint.com';
END $$;

-- ============================================================================
-- PERFORMANCE VALIDATION
-- ============================================================================

-- 14. Check table sizes
SELECT
    'audit_logs' AS table_name,
    pg_size_pretty(pg_total_relation_size('audit_logs')) AS total_size,
    pg_size_pretty(pg_relation_size('audit_logs')) AS table_size,
    pg_size_pretty(pg_total_relation_size('audit_logs') - pg_relation_size('audit_logs')) AS index_size
UNION ALL
SELECT
    'notification_subscriptions' AS table_name,
    pg_size_pretty(pg_total_relation_size('notification_subscriptions')) AS total_size,
    pg_size_pretty(pg_relation_size('notification_subscriptions')) AS table_size,
    pg_size_pretty(pg_total_relation_size('notification_subscriptions') - pg_relation_size('notification_subscriptions')) AS index_size;

-- 15. Verify index usage stats (run after some data inserted)
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan AS index_scans,
    idx_tup_read AS tuples_read
FROM pg_stat_user_indexes
WHERE tablename IN ('audit_logs', 'notification_subscriptions')
ORDER BY tablename, indexname;

-- ============================================================================
-- SUMMARY
-- ============================================================================

SELECT
    'Migration 004 Validation Complete' AS status,
    NOW() AS validated_at;

-- If all queries above complete without errors, migration is successful!
