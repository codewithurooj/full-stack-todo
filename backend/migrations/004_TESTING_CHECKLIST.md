# Migration 004 Testing Checklist

## Feature: Kafka Event-Driven Architecture
## Migration: 004_add_kafka_event_schema
## Date: 2026-01-12

---

## Pre-Migration Testing (Development)

### 1. Migration Script Validation

- [ ] **Forward migration runs without errors**
  ```bash
  psql $DEV_DATABASE_URL -f backend/migrations/004_add_kafka_event_schema.sql
  # Expected: No errors, completes in < 10 seconds
  ```

- [ ] **Validation queries pass all checks**
  ```bash
  psql $DEV_DATABASE_URL -f backend/migrations/004_validate.sql
  # Expected: All tests PASSED
  ```

- [ ] **Rollback migration runs without errors**
  ```bash
  psql $DEV_DATABASE_URL -f backend/migrations/004_add_kafka_event_schema_rollback.sql
  # Expected: Tables/indexes removed, no errors
  ```

- [ ] **Can re-apply forward migration after rollback**
  ```bash
  psql $DEV_DATABASE_URL -f backend/migrations/004_add_kafka_event_schema.sql
  # Expected: Migration succeeds again
  ```

### 2. Database Schema Verification

- [ ] **audit_logs table exists with correct structure**
  ```sql
  SELECT column_name, data_type, is_nullable
  FROM information_schema.columns
  WHERE table_name = 'audit_logs'
  ORDER BY ordinal_position;
  -- Expected: 9 columns (id, event_id, timestamp, user_id, task_id, operation_type, event_payload, system_generated, created_at)
  ```

- [ ] **notification_subscriptions table exists with correct structure**
  ```sql
  SELECT column_name, data_type, is_nullable
  FROM information_schema.columns
  WHERE table_name = 'notification_subscriptions'
  ORDER BY ordinal_position;
  -- Expected: 7 columns (id, user_id, endpoint, p256dh, auth, created_at, updated_at)
  ```

- [ ] **All indexes created successfully**
  ```sql
  SELECT tablename, indexname FROM pg_indexes
  WHERE tablename IN ('audit_logs', 'notification_subscriptions', 'tasks')
    AND indexname LIKE 'idx_%'
  ORDER BY tablename, indexname;
  -- Expected: 9 indexes total
  ```

- [ ] **Foreign key constraints exist**
  ```sql
  SELECT tc.table_name, tc.constraint_name, kcu.column_name, ccu.table_name AS foreign_table
  FROM information_schema.table_constraints AS tc
  JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name
  JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
  WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_name IN ('audit_logs', 'notification_subscriptions')
  ORDER BY tc.table_name;
  -- Expected: 3 foreign keys
  ```

- [ ] **Check constraints exist**
  ```sql
  SELECT tc.table_name, tc.constraint_name, cc.check_clause
  FROM information_schema.table_constraints AS tc
  JOIN information_schema.check_constraints AS cc ON tc.constraint_name = cc.constraint_name
  WHERE tc.table_name = 'audit_logs'
  ORDER BY tc.constraint_name;
  -- Expected: 2 check constraints
  ```

### 3. SQLModel Integration

- [ ] **New models can be imported**
  ```bash
  cd backend
  python -c "from app.models import AuditLog, AuditLogCreate, AuditLogRead; print('AuditLog models imported')"
  python -c "from app.models import NotificationSubscription, NotificationSubscriptionCreate; print('NotificationSubscription models imported')"
  # Expected: No import errors
  ```

- [ ] **Backend server starts without errors**
  ```bash
  cd backend
  uvicorn app.main:app --reload
  # Expected: Server starts, no schema errors
  ```

- [ ] **SQLModel can create tables (no-op if tables exist)**
  ```python
  from sqlmodel import create_engine, SQLModel
  from app.models import AuditLog, NotificationSubscription
  engine = create_engine("postgresql://...")
  SQLModel.metadata.create_all(engine)
  # Expected: No errors
  ```

### 4. Data Integrity Tests

#### audit_logs Table Tests

- [ ] **Can insert valid audit log entry**
  ```sql
  INSERT INTO audit_logs (event_id, timestamp, user_id, task_id, operation_type, event_payload)
  VALUES (gen_random_uuid(), NOW(), 1, 1, 'task.created', '{"title": "Test task"}'::jsonb)
  RETURNING id;
  -- Expected: INSERT successful, returns id
  ```

- [ ] **Cannot insert duplicate event_id**
  ```sql
  -- Insert first entry
  INSERT INTO audit_logs (event_id, timestamp, user_id, operation_type, event_payload)
  VALUES ('550e8400-e29b-41d4-a716-446655440000'::uuid, NOW(), 1, 'task.created', '{}'::jsonb);

  -- Try to insert duplicate (should fail)
  INSERT INTO audit_logs (event_id, timestamp, user_id, operation_type, event_payload)
  VALUES ('550e8400-e29b-41d4-a716-446655440000'::uuid, NOW(), 1, 'task.updated', '{}'::jsonb);
  -- Expected: ERROR - duplicate key value violates unique constraint
  ```

- [ ] **Cannot insert invalid operation_type**
  ```sql
  INSERT INTO audit_logs (event_id, timestamp, user_id, operation_type, event_payload)
  VALUES (gen_random_uuid(), NOW(), 1, 'invalid.operation', '{}'::jsonb);
  -- Expected: ERROR - check constraint "chk_audit_logs_operation_type"
  ```

- [ ] **Cannot insert far-future timestamp**
  ```sql
  INSERT INTO audit_logs (event_id, timestamp, user_id, operation_type, event_payload)
  VALUES (gen_random_uuid(), NOW() + INTERVAL '2 hours', 1, 'task.created', '{}'::jsonb);
  -- Expected: ERROR - check constraint "chk_audit_logs_timestamp"
  ```

- [ ] **Foreign key to users table enforced**
  ```sql
  INSERT INTO audit_logs (event_id, timestamp, user_id, operation_type, event_payload)
  VALUES (gen_random_uuid(), NOW(), 999999, 'task.created', '{}'::jsonb);
  -- Expected: ERROR - foreign key constraint (if user 999999 doesn't exist)
  ```

- [ ] **Deleting task sets task_id to NULL**
  ```sql
  -- Create task and audit log referencing it
  INSERT INTO tasks (user_id, title) VALUES (1, 'Test task') RETURNING id;
  INSERT INTO audit_logs (event_id, timestamp, user_id, task_id, operation_type, event_payload)
  VALUES (gen_random_uuid(), NOW(), 1, <task_id>, 'task.created', '{}'::jsonb);

  -- Delete task
  DELETE FROM tasks WHERE id = <task_id>;

  -- Verify audit log still exists with task_id = NULL
  SELECT task_id FROM audit_logs WHERE task_id IS NULL;
  -- Expected: 1 row with task_id = NULL
  ```

#### notification_subscriptions Table Tests

- [ ] **Can insert valid subscription**
  ```sql
  INSERT INTO notification_subscriptions (user_id, endpoint, p256dh, auth)
  VALUES (1, 'https://fcm.googleapis.com/test', 'test-key', 'test-auth')
  RETURNING id;
  -- Expected: INSERT successful
  ```

- [ ] **Cannot insert duplicate subscription (same user + endpoint)**
  ```sql
  INSERT INTO notification_subscriptions (user_id, endpoint, p256dh, auth)
  VALUES (1, 'https://fcm.googleapis.com/test', 'key1', 'auth1');

  INSERT INTO notification_subscriptions (user_id, endpoint, p256dh, auth)
  VALUES (1, 'https://fcm.googleapis.com/test', 'key2', 'auth2');
  -- Expected: ERROR - duplicate key value violates unique constraint
  ```

- [ ] **Can insert same endpoint for different users**
  ```sql
  INSERT INTO notification_subscriptions (user_id, endpoint, p256dh, auth)
  VALUES (1, 'https://fcm.googleapis.com/endpoint1', 'key1', 'auth1');

  INSERT INTO notification_subscriptions (user_id, endpoint, p256dh, auth)
  VALUES (2, 'https://fcm.googleapis.com/endpoint1', 'key2', 'auth2');
  -- Expected: Both inserts successful
  ```

- [ ] **Foreign key to users table enforced**
  ```sql
  INSERT INTO notification_subscriptions (user_id, endpoint, p256dh, auth)
  VALUES (999999, 'https://test.com', 'key', 'auth');
  -- Expected: ERROR - foreign key constraint (if user 999999 doesn't exist)
  ```

- [ ] **Deleting user cascades to subscriptions**
  ```sql
  -- Create test user and subscription
  INSERT INTO users (email, hashed_password) VALUES ('test@example.com', 'hash') RETURNING id;
  INSERT INTO notification_subscriptions (user_id, endpoint, p256dh, auth)
  VALUES (<user_id>, 'https://test.com', 'key', 'auth');

  -- Delete user
  DELETE FROM users WHERE id = <user_id>;

  -- Verify subscription deleted
  SELECT COUNT(*) FROM notification_subscriptions WHERE user_id = <user_id>;
  -- Expected: 0 rows
  ```

#### tasks Table Idempotency Tests

- [ ] **Can insert recurring task instance**
  ```sql
  -- Create parent task
  INSERT INTO tasks (user_id, title, recurring_pattern) VALUES (1, 'Daily standup', 'daily') RETURNING id;

  -- Create recurring instance
  INSERT INTO tasks (user_id, title, parent_task_id, due_date)
  VALUES (1, 'Daily standup', <parent_id>, '2026-01-13T09:00:00Z');
  -- Expected: INSERT successful
  ```

- [ ] **Cannot insert duplicate recurring instance (same parent + due_date)**
  ```sql
  INSERT INTO tasks (user_id, title, parent_task_id, due_date)
  VALUES (1, 'Daily standup', <parent_id>, '2026-01-13T09:00:00Z');

  INSERT INTO tasks (user_id, title, parent_task_id, due_date)
  VALUES (1, 'Daily standup', <parent_id>, '2026-01-13T09:00:00Z');
  -- Expected: ERROR - duplicate key value violates unique constraint
  ```

- [ ] **Can insert same due_date for different parent tasks**
  ```sql
  INSERT INTO tasks (user_id, title, parent_task_id, due_date)
  VALUES (1, 'Task A', 1, '2026-01-13T09:00:00Z');

  INSERT INTO tasks (user_id, title, parent_task_id, due_date)
  VALUES (1, 'Task B', 2, '2026-01-13T09:00:00Z');
  -- Expected: Both inserts successful
  ```

### 5. Index Performance Tests

- [ ] **Query audit logs by task_id uses index**
  ```sql
  EXPLAIN ANALYZE SELECT * FROM audit_logs WHERE task_id = 1;
  -- Expected: Index Scan using idx_audit_logs_task_id
  ```

- [ ] **Query audit logs by user_id uses index**
  ```sql
  EXPLAIN ANALYZE SELECT * FROM audit_logs WHERE user_id = 1;
  -- Expected: Index Scan using idx_audit_logs_user_id
  ```

- [ ] **Query audit logs by timestamp uses index**
  ```sql
  EXPLAIN ANALYZE SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 10;
  -- Expected: Index Scan using idx_audit_logs_timestamp
  ```

- [ ] **Query subscriptions by user_id uses index**
  ```sql
  EXPLAIN ANALYZE SELECT * FROM notification_subscriptions WHERE user_id = 1;
  -- Expected: Index Scan using idx_notification_subs_user_id
  ```

### 6. Backward Compatibility Tests

- [ ] **Existing tasks API endpoints work**
  ```bash
  # GET /api/{user_id}/tasks
  curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/1/tasks
  # Expected: 200 OK, returns tasks
  ```

- [ ] **Can create new task**
  ```bash
  curl -X POST -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"title": "Test task"}' \
    http://localhost:8000/api/1/tasks
  # Expected: 201 Created
  ```

- [ ] **Can update existing task**
  ```bash
  curl -X PUT -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"title": "Updated task"}' \
    http://localhost:8000/api/1/tasks/1
  # Expected: 200 OK
  ```

- [ ] **Can delete existing task**
  ```bash
  curl -X DELETE -H "Authorization: Bearer $TOKEN" \
    http://localhost:8000/api/1/tasks/1
  # Expected: 204 No Content
  ```

---

## Staging Environment Testing

### 1. Migration Execution

- [ ] **Backup staging database**
  ```bash
  pg_dump $STAGING_DATABASE_URL > staging_backup_$(date +%Y%m%d).sql
  ```

- [ ] **Apply migration on staging**
  ```bash
  psql $STAGING_DATABASE_URL -f backend/migrations/004_add_kafka_event_schema.sql
  # Expected: Completes in < 10 seconds
  ```

- [ ] **Run validation queries**
  ```bash
  psql $STAGING_DATABASE_URL -f backend/migrations/004_validate.sql
  # Expected: All tests PASSED
  ```

### 2. Application Testing

- [ ] **Deploy new backend code to staging**
  ```bash
  git push staging 011-kafka-event-architecture
  ```

- [ ] **Backend server starts successfully**
  ```bash
  systemctl status todo-backend
  # Expected: active (running)
  ```

- [ ] **Health check passes**
  ```bash
  curl https://staging-api.example.com/health
  # Expected: {"status": "healthy"}
  ```

### 3. Load Testing (Optional)

- [ ] **Insert 1000 audit log entries**
  ```sql
  DO $$
  BEGIN
    FOR i IN 1..1000 LOOP
      INSERT INTO audit_logs (event_id, timestamp, user_id, operation_type, event_payload)
      VALUES (gen_random_uuid(), NOW(), 1, 'task.created', '{}'::jsonb);
    END LOOP;
  END $$;
  -- Expected: Completes in < 5 seconds
  ```

- [ ] **Query performance acceptable**
  ```sql
  EXPLAIN ANALYZE SELECT * FROM audit_logs WHERE user_id = 1 ORDER BY timestamp DESC LIMIT 100;
  -- Expected: Execution time < 50ms
  ```

---

## Production Readiness Checklist

### 1. Pre-Migration Checks

- [ ] **All development tests passed**
- [ ] **All staging tests passed**
- [ ] **Rollback script tested on staging**
- [ ] **Database backup scheduled/completed**
- [ ] **Migration window scheduled (if needed)**
- [ ] **Team notified of deployment**
- [ ] **Monitoring alerts configured**

### 2. Migration Prerequisites

- [ ] **PostgreSQL version >= 12**
  ```sql
  SELECT version();
  ```

- [ ] **Required extensions enabled**
  ```sql
  SELECT * FROM pg_extension WHERE extname IN ('uuid-ossp', 'btree_gin');
  ```

- [ ] **Sufficient disk space available**
  ```sql
  SELECT pg_size_pretty(pg_database_size(current_database()));
  -- Ensure at least 10 GB free
  ```

- [ ] **No long-running transactions**
  ```sql
  SELECT pid, now() - pg_stat_activity.query_start AS duration, query
  FROM pg_stat_activity
  WHERE state != 'idle'
  ORDER BY duration DESC
  LIMIT 10;
  -- Ensure no queries running > 5 minutes
  ```

### 3. Post-Migration Validation

- [ ] **All tables created**
  ```sql
  SELECT table_name FROM information_schema.tables
  WHERE table_name IN ('audit_logs', 'notification_subscriptions');
  -- Expected: 2 rows
  ```

- [ ] **All indexes created**
  ```sql
  SELECT COUNT(*) FROM pg_indexes
  WHERE tablename IN ('audit_logs', 'notification_subscriptions')
    OR (tablename = 'tasks' AND indexname = 'idx_recurring_instance_dedup');
  -- Expected: 9 indexes
  ```

- [ ] **Application health check passes**
  ```bash
  curl https://api.example.com/health
  # Expected: {"status": "healthy"}
  ```

- [ ] **No errors in application logs**
  ```bash
  tail -n 100 /var/log/todo-backend.log | grep ERROR
  # Expected: No errors related to schema
  ```

### 4. Monitoring (First 24 Hours)

- [ ] **Database CPU usage normal (< 50%)**
- [ ] **Database memory usage normal (< 80%)**
- [ ] **No lock waits or deadlocks**
- [ ] **API response times normal (< 200ms p95)**
- [ ] **No increase in error rate**
- [ ] **Disk space not growing abnormally**

---

## Rollback Checklist

### Trigger Conditions for Rollback

Rollback if any of the following occur:
- [ ] Migration fails to complete
- [ ] Validation queries fail
- [ ] Backend server fails to start
- [ ] API error rate increases > 5%
- [ ] Database performance degrades > 20%
- [ ] Critical bug discovered in new schema

### Rollback Procedure

- [ ] **Stop event producers (if live)**
  ```bash
  # Prevent data loss during rollback
  kubectl scale deployment kafka-producer --replicas=0
  ```

- [ ] **Execute rollback script**
  ```bash
  psql $DATABASE_URL -f backend/migrations/004_add_kafka_event_schema_rollback.sql
  ```

- [ ] **Verify rollback success**
  ```sql
  SELECT table_name FROM information_schema.tables
  WHERE table_name IN ('audit_logs', 'notification_subscriptions');
  -- Expected: 0 rows
  ```

- [ ] **Revert application code**
  ```bash
  git revert HEAD
  systemctl restart todo-backend
  ```

- [ ] **Verify application health**
  ```bash
  curl https://api.example.com/health
  # Expected: {"status": "healthy"}
  ```

- [ ] **Restart event producers**
  ```bash
  kubectl scale deployment kafka-producer --replicas=3
  ```

---

## Sign-Off

### Development
- [ ] Developer: _________________ Date: _______
- [ ] Tests passed: ☐ Yes ☐ No
- [ ] Notes: _________________________________

### Staging
- [ ] QA Engineer: _________________ Date: _______
- [ ] Tests passed: ☐ Yes ☐ No
- [ ] Notes: _________________________________

### Production
- [ ] DevOps Engineer: _________________ Date: _______
- [ ] Migration successful: ☐ Yes ☐ No
- [ ] Rollback tested: ☐ Yes ☐ No ☐ N/A
- [ ] Notes: _________________________________

---

**Migration Number:** 004
**Feature:** Kafka Event-Driven Architecture
**Risk Level:** Low
**Estimated Duration:** 5-10 seconds
**Downtime Required:** No

**Checklist Version:** 1.0
**Last Updated:** 2026-01-12
