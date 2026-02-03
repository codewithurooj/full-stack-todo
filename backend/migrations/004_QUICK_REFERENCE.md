# Migration 004 Quick Reference Card

## TL;DR

**What:** Add Kafka event-driven architecture support (audit logs + notifications)
**Risk:** Low (backward compatible, no data changes)
**Time:** 5-10 seconds
**Downtime:** None

---

## Files

| File | Purpose |
|------|---------|
| `004_add_kafka_event_schema.sql` | Apply migration |
| `004_add_kafka_event_schema_rollback.sql` | Undo migration |
| `004_validate.sql` | Verify success |
| `004_MIGRATION_GUIDE.md` | Full documentation |
| `004_TESTING_CHECKLIST.md` | Testing steps |

---

## Apply Migration (3 Steps)

```bash
# 1. Backup (CRITICAL)
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# 2. Apply
psql $DATABASE_URL -f 004_add_kafka_event_schema.sql

# 3. Validate
psql $DATABASE_URL -f 004_validate.sql
```

Expected output: "All tests PASSED"

---

## What Gets Created

### Tables (2)
1. **audit_logs** - Event audit trail from Kafka
   - 9 columns (id, event_id, timestamp, user_id, task_id, operation_type, event_payload, system_generated, created_at)
   - 6 indexes (including unique constraint on event_id)

2. **notification_subscriptions** - Web Push subscriptions
   - 7 columns (id, user_id, endpoint, p256dh, auth, created_at, updated_at)
   - 2 indexes (including unique constraint on user_id + endpoint)

### Indexes (8 total)
- `audit_logs_event_id_key` (UNIQUE)
- `idx_audit_logs_task_id` (partial: WHERE task_id IS NOT NULL)
- `idx_audit_logs_user_id`
- `idx_audit_logs_timestamp` (DESC)
- `idx_audit_logs_operation_type`
- `notification_subscriptions_user_id_endpoint_key` (UNIQUE)
- `idx_notification_subs_user_id`
- `idx_recurring_instance_dedup` on tasks table (UNIQUE partial)

---

## Using New Models

### Import Models
```python
from app.models import AuditLog, AuditLogCreate, AuditLogRead
from app.models import NotificationSubscription, NotificationSubscriptionCreate
```

### Create Audit Log
```python
from app.models import AuditLog
from uuid import uuid4
from datetime import datetime

audit_log = AuditLog(
    event_id=uuid4(),
    timestamp=datetime.utcnow(),
    user_id=1,
    task_id=123,
    operation_type="task.created",
    event_payload={"title": "Buy groceries"},
    system_generated=False
)
session.add(audit_log)
session.commit()
```

### Create Notification Subscription
```python
from app.models import NotificationSubscription

subscription = NotificationSubscription(
    user_id=1,
    endpoint="https://fcm.googleapis.com/...",
    p256dh="public-key-base64",
    auth="auth-secret-base64"
)
session.add(subscription)
session.commit()
```

---

## Query Examples

### Get Audit Logs for Task
```sql
SELECT * FROM audit_logs
WHERE task_id = 123
ORDER BY timestamp DESC;
```

### Get Audit Logs for User
```sql
SELECT * FROM audit_logs
WHERE user_id = 1
ORDER BY timestamp DESC
LIMIT 100;
```

### Get User's Notification Subscriptions
```sql
SELECT * FROM notification_subscriptions
WHERE user_id = 1;
```

---

## Rollback (if needed)

```bash
# 1. Stop event producers (if live)
kubectl scale deployment kafka-producer --replicas=0

# 2. Run rollback
psql $DATABASE_URL -f 004_add_kafka_event_schema_rollback.sql

# 3. Verify rollback
psql $DATABASE_URL -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name IN ('audit_logs', 'notification_subscriptions');"
# Expected: 0

# 4. Restart event producers
kubectl scale deployment kafka-producer --replicas=3
```

---

## Validation Queries

### Check Tables Exist
```sql
SELECT table_name FROM information_schema.tables
WHERE table_name IN ('audit_logs', 'notification_subscriptions');
-- Expected: 2 rows
```

### Check Indexes
```sql
SELECT COUNT(*) FROM pg_indexes
WHERE tablename IN ('audit_logs', 'notification_subscriptions')
   OR (tablename = 'tasks' AND indexname = 'idx_recurring_instance_dedup');
-- Expected: 9 indexes
```

### Test Insert
```sql
INSERT INTO audit_logs (event_id, timestamp, user_id, operation_type, event_payload)
VALUES (gen_random_uuid(), NOW(), 1, 'task.created', '{}'::jsonb);
-- Expected: INSERT successful
```

---

## Troubleshooting

### "relation audit_logs does not exist"
**Cause:** Migration not applied
**Fix:** Run `004_add_kafka_event_schema.sql`

### "duplicate key value violates unique constraint"
**Cause:** Trying to insert duplicate event_id or subscription
**Fix:** Use `gen_random_uuid()` for event_id, ensure unique subscriptions

### "violates check constraint chk_audit_logs_operation_type"
**Cause:** Invalid operation_type value
**Fix:** Use only: task.created, task.updated, task.deleted, task.completed

### Backend won't start after migration
**Cause:** SQLModel models not updated
**Fix:** Ensure `audit_log.py` and `notification_subscription.py` exist in `backend/app/models/`

---

## Important Notes

### Idempotency
- **audit_logs:** Unique constraint on `event_id` prevents duplicate events
- **tasks:** Unique constraint on `(parent_task_id, due_date)` prevents duplicate recurring instances
- **notification_subscriptions:** Unique constraint on `(user_id, endpoint)` prevents duplicate subscriptions

### Data Retention
Set up cron job to clean up old audit logs:
```sql
DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '90 days';
```

### Performance
- Partial index on `task_id` saves space (only indexes non-NULL values)
- All queries use indexes (verify with EXPLAIN ANALYZE)
- Zero downtime migration (no table locks)

---

## Health Checks

### Application Health
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

### Database Health
```sql
SELECT pg_database_size(current_database()) AS db_size;
SELECT COUNT(*) FROM audit_logs;
SELECT COUNT(*) FROM notification_subscriptions;
```

---

## Success Criteria

✅ Migration completes in < 10 seconds
✅ All validation queries pass
✅ Backend server starts without errors
✅ Existing API endpoints work
✅ No errors in application logs
✅ Database metrics normal

---

## Support

- Full docs: `004_MIGRATION_GUIDE.md`
- Testing: `004_TESTING_CHECKLIST.md`
- Validation: `004_validate.sql`
- Spec: `specs/011-kafka-event-architecture/data-model.md`

---

**Migration:** 004
**Feature:** Kafka Event-Driven Architecture
**Status:** Ready for Production
**Date:** 2026-01-12
