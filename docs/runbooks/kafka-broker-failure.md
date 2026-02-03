# Kafka Broker Failure Runbook

**Feature 011: Event-Driven Architecture with Kafka**

Procedures for handling Kafka broker failures in production.

## Incident Detection

### Symptoms

- Consumer lag increasing rapidly
- Services reporting Kafka connection errors
- Alert: `KafkaConnectionLost` firing
- Consumer offset not advancing

### Verification

```bash
# Check Kafka broker status
rpk cluster info

# Check topic health
rpk topic describe task-events

# Check consumer groups
rpk group list
rpk group describe recurring-task-service-group
```

## Response Procedures

### Scenario 1: Single Broker Down (Multi-Broker Cluster)

**Impact:** Low - Kafka automatically fails over to other brokers

**Actions:**

1. **Verify Cluster Status**
   ```bash
   rpk cluster info
   # Check for healthy brokers
   ```

2. **Check Topic Replication**
   ```bash
   rpk topic describe task-events
   # Verify replicas are in-sync (ISR)
   ```

3. **Monitor Consumer Lag**
   ```bash
   rpk group describe audit-service-group
   # Should continue processing normally
   ```

4. **Investigate Failed Broker**
   ```bash
   kubectl logs broker-2  # Kubernetes
   docker logs kafka-2    # Docker
   ```

5. **Restart Failed Broker**
   ```bash
   kubectl delete pod broker-2  # K8s will recreate
   ```

**Expected Recovery Time:** <5 minutes (automatic)

###  Scenario 2: All Brokers Down

**Impact:** Critical - All event processing stops

**Actions:**

1. **Declare Incident**
   - Alert on-call team
   - Create incident ticket
   - Post to #incidents Slack channel

2. **Check Broker Logs**
   ```bash
   kubectl logs -l app=kafka --tail=100
   ```

3. **Common Causes:**
   - Disk full
   - OOM killer
   - Network partition
   - Configuration error after deployment

4. **Restart Brokers**
   ```bash
   # Kubernetes
   kubectl rollout restart statefulset kafka

   # Docker Compose
   docker-compose -f docker-compose-kafka.yml restart redpanda
   ```

5. **Verify Cluster Recovery**
   ```bash
   rpk cluster info
   rpk cluster health
   ```

6. **Check Topic Status**
   ```bash
   rpk topic describe task-events
   rpk topic describe reminders
   ```

7. **Verify Consumer Resume**
   ```bash
   # Check all three consumer groups
   rpk group describe recurring-task-service-group
   rpk group describe notification-service-group
   rpk group describe audit-service-group
   ```

8. **Monitor Consumer Lag Catch-Up**
   ```bash
   watch 'rpk group describe audit-service-group | grep LAG'
   ```

**Expected Recovery Time:** 5-15 minutes

### Scenario 3: Kafka Cluster Unavailable (Cloud Provider Issue)

**Impact:** Critical - Cannot restore immediately

**Actions:**

1. **Check Cloud Provider Status**
   - Redpanda Cloud: https://status.redpanda.com
   - AWS MSK: AWS Health Dashboard
   - Confluent Cloud: https://status.confluent.io

2. **Enable Maintenance Mode**
   ```bash
   # Scale down consumers to prevent errors
   kubectl scale deployment recurring-task-service --replicas=0
   kubectl scale deployment notification-service --replicas=0
   kubectl scale deployment audit-service --replicas=0
   ```

3. **Notify Stakeholders**
   - Post to status page
   - Email affected users
   - Update incident ticket

4. **Wait for Cloud Provider Recovery**
   - Monitor provider status page
   - Check for ETR (Estimated Time to Recovery)

5. **Once Cluster Returns**
   ```bash
   # Verify cluster health
   rpk cluster health

   # Scale up consumers
   kubectl scale deployment recurring-task-service --replicas=3
   kubectl scale deployment notification-service --replicas=2
   kubectl scale deployment audit-service --replicas=2
   ```

6. **Monitor Recovery**
   - Check consumer lag catch-up
   - Verify no data loss
   - Check audit logs for gaps

**Expected Recovery Time:** Depends on cloud provider (1-4 hours typical)

## Data Loss Prevention

### Kafka Guarantees

✅ **No Data Loss Scenarios:**
- Single broker failure (with replication)
- Consumer service restart
- Consumer crash before offset commit

**Why:** Kafka persists events to disk with replication. Consumers commit offsets after successful processing.

❌ **Data Loss Risk Scenarios:**
- All brokers fail AND disk data lost
- Topic retention period exceeded
- Manual topic deletion

### Verification After Recovery

```bash
# Check for event gaps in audit logs
psql $DATABASE_URL << EOF
SELECT
  MIN(timestamp) as earliest_event,
  MAX(timestamp) as latest_event,
  COUNT(*) as total_events
FROM audit_logs
WHERE created_at > NOW() - INTERVAL '1 hour';
EOF

# Check for missing recurring instances
psql $DATABASE_URL << EOF
SELECT
  COUNT(*) as completed_recurring_tasks,
  COUNT(DISTINCT parent_task_id) as unique_patterns
FROM tasks
WHERE completed = true
  AND recurring_pattern != 'none'
  AND completed_at > NOW() - INTERVAL '1 hour';
EOF
```

## Prevention

### Monitoring

```yaml
# Add alerts for broker health
- alert: KafkaBrokerDown
  expr: up{job="kafka"} == 0
  for: 1m
  severity: critical

- alert: KafkaUnderReplicatedPartitions
  expr: kafka_cluster_partition_under_replicated > 0
  for: 5m
  severity: warning
```

### Best Practices

1. **Use Multi-Broker Clusters**
   - Minimum 3 brokers in production
   - Replication factor: 3

2. **Configure Topic Retention**
   - Minimum 7 days retention
   - Allows time to recover from extended outages

3. **Monitor Disk Usage**
   - Alert at 70% disk usage
   - Auto-expand storage if possible

4. **Regular Backups**
   - Snapshot broker volumes daily
   - Test restore procedures quarterly

5. **Consumer Idempotency**
   - Already implemented via unique constraints
   - Allows safe event replay

## Escalation

### When to Escalate

- Broker down >15 minutes
- Data loss detected
- Cannot restart brokers
- Cloud provider outage >2 hours

### Escalation Path

1. **On-Call Engineer** → Investigate (0-15 minutes)
2. **Platform Lead** → Coordinate recovery (15-30 minutes)
3. **CTO** → Executive decision if extended outage (>1 hour)
4. **Cloud Provider Support** → Engage for provider issues

## Post-Incident

### Required Actions

1. **Verify SLAs Met**
   - 99.9% recurring reliability
   - 99% notification delivery
   - <500ms event latency

2. **Write Incident Report**
   - Timeline of events
   - Root cause analysis
   - Action items

3. **Update Runbook**
   - Add new scenarios encountered
   - Improve procedures
   - Update timelines

## Related Runbooks

- **Event Replay:** docs/runbooks/event-replay.md
- **Scaling Consumers:** docs/runbooks/scale-consumers.md
- **DLQ Investigation:** docs/runbooks/dlq-investigation.md

---

**Last Updated:** 2026-01-13
**Maintained By:** Platform Team
**Incident Hotline:** +1-555-ON-CALL-0
