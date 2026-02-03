# Event Replay Operational Runbook

**Feature 011: Event-Driven Architecture with Kafka**

This runbook documents procedures for replaying Kafka events for disaster recovery, service recovery, testing, and debugging.

## Table of Contents

1. [Overview](#overview)
2. [When to Use Event Replay](#when-to-use-event-replay)
3. [Prerequisites](#prerequisites)
4. [Replay Procedures](#replay-procedures)
5. [Recovery Scenarios](#recovery-scenarios)
6. [Troubleshooting](#troubleshooting)
7. [Safety Checklist](#safety-checklist)

## Overview

Event replay allows you to reprocess events from Kafka topics. This is useful for:

- **Disaster Recovery:** Restore service state after data loss
- **Bug Fixes:** Reprocess events after fixing a bug in consumer logic
- **Testing:** Test new consumer code against production data
- **Auditing:** Investigate historical events
- **Data Migration:** Rebuild derived data stores

### Replay Tool

Location: `services/scripts/replay_events.py`

The replay tool provides three replay modes:
1. **From Beginning:** Replay all events from topic start
2. **From Timestamp:** Replay events from specific datetime
3. **From Offset:** Replay from specific partition offset

## When to Use Event Replay

### ✅ Use Event Replay When:

- A microservice lost data due to database failure
- Consumer logic had a bug that was recently fixed
- You need to rebuild audit logs from scratch
- Testing new consumer code before deployment
- Investigating a production incident

### ❌ Don't Use Event Replay When:

- Services are running normally (let consumers process naturally)
- Topic has millions of events and you only need recent ones
- You want to modify event data (replay is read-only)

## Prerequisites

### 1. Install Dependencies

```bash
cd services/scripts
pip install -r requirements.txt
```

### 2. Verify Kafka Access

```bash
# Check topic exists
rpk topic list

# Check topic partition count
rpk topic describe task-events
```

### 3. Identify Replay Parameters

Determine:
- **Topic:** Which topic to replay (task-events, reminders, etc.)
- **Consumer Group:** Which service's consumer group to use
- **Start Position:** Timestamp, offset, or beginning
- **Target Service:** Which microservice will consume the replayed events

## Replay Procedures

### Procedure 1: Full Topic Replay (From Beginning)

**Use Case:** Rebuild entire service state from scratch

**Steps:**

1. **Stop Target Service** (prevents race conditions)
   ```bash
   # Kubernetes
   kubectl scale deployment audit-service --replicas=0

   # Docker
   docker stop audit-service
   ```

2. **Clear Service State** (optional)
   ```sql
   -- Clear audit logs table
   TRUNCATE TABLE audit_logs;

   -- Reset consumer group offset
   rpk group delete audit-service-group
   ```

3. **Start Replay in Dry-Run Mode** (verify first)
   ```bash
   python replay_events.py \
     --topic task-events \
     --from-beginning \
     --consumer-group audit-service-group \
     --dry-run \
     --max-events 100
   ```

4. **Review Output** (check for errors)
   ```
   [1] Partition=0, Offset=0, Type=task.created, ID=abc123
   [2] Partition=0, Offset=1, Type=task.updated, ID=def456
   ...
   Replay complete: 100 events replayed
   ```

5. **Start Full Replay** (without dry-run)
   ```bash
   python replay_events.py \
     --topic task-events \
     --from-beginning \
     --consumer-group audit-service-group
   ```

6. **Monitor Progress** (in separate terminal)
   ```bash
   # Check consumer lag
   rpk group describe audit-service-group

   # Check database row count
   psql $DATABASE_URL -c "SELECT COUNT(*) FROM audit_logs;"
   ```

7. **Restart Service**
   ```bash
   kubectl scale deployment audit-service --replicas=1
   ```

8. **Verify Service Health**
   ```bash
   kubectl logs -f deployment/audit-service
   ```

**Expected Duration:** 5-30 minutes depending on topic size

### Procedure 2: Timestamp-Based Replay

**Use Case:** Replay events from specific date/time (e.g., after a bug was deployed)

**Steps:**

1. **Identify Start Timestamp**
   ```bash
   # Example: Bug deployed on 2026-01-13 at 10:00 AM
   START_TIME="2026-01-13 10:00:00"
   ```

2. **Stop Target Service**
   ```bash
   kubectl scale deployment recurring-task-service --replicas=0
   ```

3. **Reset Consumer Offset to Timestamp**
   ```bash
   python replay_events.py \
     --topic task-events \
     --from-time "$START_TIME" \
     --consumer-group recurring-task-service-group \
     --dry-run \
     --max-events 10
   ```

4. **Verify Events**
   ```
   [1] Partition=0, Offset=1523, Type=task.completed, ID=...
   # Verify timestamp is >= 2026-01-13 10:00:00
   ```

5. **Run Full Replay**
   ```bash
   python replay_events.py \
     --topic task-events \
     --from-time "$START_TIME" \
     --consumer-group recurring-task-service-group
   ```

6. **Restart Service**
   ```bash
   kubectl scale deployment recurring-task-service --replicas=1
   ```

**Expected Duration:** 2-15 minutes depending on time range

### Procedure 3: Offset-Based Replay

**Use Case:** Replay from specific Kafka offset (advanced)

**Steps:**

1. **Identify Offset**
   ```bash
   # Check current consumer offset
   rpk group describe recurring-task-service-group

   # Example output:
   # Partition: 0, Offset: 5000, Lag: 0
   ```

2. **Calculate Target Offset**
   ```bash
   # Want to replay last 1000 events
   TARGET_OFFSET=$((5000 - 1000))
   echo "Target offset: $TARGET_OFFSET"
   ```

3. **Stop Service**
   ```bash
   kubectl scale deployment recurring-task-service --replicas=0
   ```

4. **Replay from Offset**
   ```bash
   python replay_events.py \
     --topic task-events \
     --offset $TARGET_OFFSET \
     --partition 0 \
     --consumer-group recurring-task-service-group
   ```

5. **Restart Service**
   ```bash
   kubectl scale deployment recurring-task-service --replicas=1
   ```

**Expected Duration:** 1-10 minutes

## Recovery Scenarios

### Scenario 1: Audit Service Lost Database

**Problem:** Database corruption, entire audit_logs table lost

**Solution:**

1. Restore database from backup (if available)
2. If no backup, replay all task-events:
   ```bash
   # Clear corrupted data
   psql $DATABASE_URL -c "TRUNCATE TABLE audit_logs;"

   # Replay all events
   kubectl scale deployment audit-service --replicas=0
   rpk group delete audit-service-group
   python replay_events.py --topic task-events --from-beginning --consumer-group audit-service-group
   kubectl scale deployment audit-service --replicas=1
   ```

3. Verify audit log count matches expected

**Recovery Time:** 10-30 minutes for 100K events

### Scenario 2: Recurring Task Service Bug Fixed

**Problem:** Bug in recurrence calculation, need to reprocess completed tasks

**Solution:**

1. Deploy fix to recurring-task-service
2. Identify when bug was introduced (e.g., 2026-01-10)
3. Delete incorrect task instances:
   ```sql
   DELETE FROM tasks
   WHERE parent_task_id IS NOT NULL
   AND created_at >= '2026-01-10';
   ```

4. Replay events from bug introduction date:
   ```bash
   kubectl scale deployment recurring-task-service --replicas=0
   python replay_events.py \
     --topic task-events \
     --from-time "2026-01-10 00:00:00" \
     --consumer-group recurring-task-service-group
   kubectl scale deployment recurring-task-service --replicas=1
   ```

5. Verify correct instances created

**Recovery Time:** 5-20 minutes

### Scenario 3: Test New Consumer Logic

**Problem:** Need to test new consumer code against production events

**Solution:**

1. Use separate consumer group (don't affect production):
   ```bash
   python replay_events.py \
     --topic task-events \
     --from-beginning \
     --consumer-group test-consumer-group \
     --dry-run \
     --max-events 1000
   ```

2. Deploy test service with new code:
   ```bash
   kubectl apply -f test-consumer-deployment.yaml
   ```

3. Point test service at test-consumer-group
4. Monitor logs for errors
5. If successful, deploy to production consumer group

**Recovery Time:** 5-15 minutes

### Scenario 4: Notification Service Missed Events

**Problem:** Notification service was down for 2 hours, missed reminder events

**Solution:**

1. Check consumer lag:
   ```bash
   rpk group describe notification-service-group
   # Lag: 523 events
   ```

2. Service will automatically catch up when restarted
3. No manual replay needed (consumer will resume from last committed offset)
4. Monitor catch-up progress:
   ```bash
   watch 'rpk group describe notification-service-group'
   ```

**Recovery Time:** Automatic, 1-5 minutes to catch up

## Troubleshooting

### Issue: "No messages available" immediately

**Cause:** Consumer offset is at end of topic

**Solution:**
```bash
# Check consumer offset
rpk group describe my-consumer-group

# If offset is at end, reset to beginning
rpk group seek my-consumer-group --to start

# Or use --from-beginning flag
python replay_events.py --topic task-events --from-beginning --consumer-group my-consumer-group
```

### Issue: "Could not parse timestamp"

**Cause:** Incorrect timestamp format

**Solution:**
```bash
# Use format: YYYY-MM-DD HH:MM:SS
python replay_events.py --from-time "2026-01-13 12:00:00"

# Or ISO format
python replay_events.py --from-time "2026-01-13T12:00:00"
```

### Issue: Replay creates duplicate database entries

**Cause:** Service is still running, processing events in parallel

**Solution:**
```bash
# Always stop service before replay
kubectl scale deployment my-service --replicas=0

# Then replay
python replay_events.py ...

# Then restart service
kubectl scale deployment my-service --replicas=1
```

### Issue: Replay is very slow

**Cause:** Network latency, large event payloads, or slow database

**Solutions:**
1. Run replay script on same network as Kafka
2. Increase batch size (not supported in basic tool)
3. Use --max-events to test smaller batches first
4. Check database connection pool settings

### Issue: Events out of chronological order

**Cause:** Multiple partitions, Kafka doesn't guarantee global ordering

**Solution:**
- This is expected behavior
- Kafka only guarantees ordering within a partition
- Events with same partition key (user_id) will be in order
- Use event timestamp field for chronological sorting in queries

## Safety Checklist

Before running event replay in production:

- [ ] **Backup database** (if clearing data)
- [ ] **Stop target service** (prevent race conditions)
- [ ] **Test with --dry-run first** (verify events)
- [ ] **Test with --max-events=100 first** (verify logic)
- [ ] **Verify consumer group** (don't affect other services)
- [ ] **Notify team** (communicate downtime)
- [ ] **Monitor logs** (watch for errors)
- [ ] **Have rollback plan** (restore from backup if needed)
- [ ] **Verify after replay** (check row counts, sample data)
- [ ] **Restart service** (return to normal operation)

## Best Practices

1. **Always use --dry-run first** to verify events and logic
2. **Stop services before replay** to prevent duplicate processing
3. **Use unique consumer group for testing** to avoid affecting production
4. **Monitor consumer lag** during replay to track progress
5. **Verify data integrity** after replay completes
6. **Document replay reason** in incident log or runbook
7. **Test replay procedures** in staging before production use

## Kafka Consumer Group Management

### List Consumer Groups

```bash
rpk group list
```

### Describe Consumer Group

```bash
rpk group describe audit-service-group
```

Output shows:
- Current offset
- Lag (events behind)
- Last commit time

### Reset Consumer Group Offset

```bash
# Reset to beginning
rpk group seek audit-service-group --to start

# Reset to end
rpk group seek audit-service-group --to end

# Reset to specific timestamp
rpk group seek audit-service-group --to "2026-01-13T12:00:00Z"
```

### Delete Consumer Group

```bash
# Only works when no members are active
rpk group delete audit-service-group
```

## Related Runbooks

- **Kafka Broker Failure:** docs/runbooks/kafka-broker-failure.md
- **Scaling Consumer Groups:** docs/runbooks/scale-consumers.md
- **DLQ Investigation:** docs/runbooks/dlq-investigation.md

## Emergency Contacts

- **On-Call Engineer:** Use PagerDuty
- **DevOps Team:** #devops Slack channel
- **Database Admin:** #database Slack channel

---

**Last Updated:** 2026-01-13
**Maintained By:** Platform Team
