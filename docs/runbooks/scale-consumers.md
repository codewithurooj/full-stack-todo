# Scaling Consumer Groups Runbook

**Feature 011: Event-Driven Architecture with Kafka**

Procedures for scaling Kafka consumer groups up or down based on load.

## When to Scale

### Scale UP Indicators

✅ Scale up when:
- Consumer lag > 1000 events for >5 minutes
- Event throughput > 5000 events/minute
- p95 processing latency > 500ms
- CPU utilization > 70%
- Memory utilization > 80%

### Scale DOWN Indicators

✅ Scale down when:
- Consumer lag consistently <100 events
- Event throughput < 1000 events/minute
- CPU utilization < 20%
- Cost optimization needed

## Scaling Procedures

### Manual Scaling

#### Scale UP

```bash
# Increase replicas to 5
kubectl scale deployment recurring-task-service --replicas=5

# Verify scaling
kubectl get pods -l app=recurring-task-service
kubectl get hpa recurring-task-service
```

#### Scale DOWN

```bash
# Decrease replicas to 2
kubectl scale deployment recurring-task-service --replicas=2

# Verify scaling
kubectl get pods -l app=recurring-task-service
```

### Automatic Scaling (HPA)

Already configured via Helm charts:

```yaml
autoscaling:
  enabled: true
  minReplicas: 1
  maxReplicas: 10
  metrics:
    - type: External
      external:
        metric:
          name: kafka_consumer_lag
        target:
          type: Value
          value: "100"
```

**How it works:**
- HPA monitors consumer lag metric
- Scales up when lag > 100 events
- Scales down when lag < 100 events
- Respects min/max replica limits

### Verify HPA Status

```bash
# Check HPA
kubectl get hpa

# Describe HPA
kubectl describe hpa recurring-task-service

# Watch HPA decisions
kubectl get hpa recurring-task-service -w
```

## Partition-Based Scaling

### Understanding Partition Limits

**Rule:** Max consumers = Number of topic partitions

**Example:**
- Topic `task-events` has 10 partitions
- Max useful replicas: 10
- More than 10 replicas = idle consumers

### Check Partition Count

```bash
rpk topic describe task-events
```

Output:
```
PARTITION  LEADER  REPLICAS  ISR
0          1       [1 2 3]   [1 2 3]
1          2       [2 3 1]   [2 3 1]
...
9          1       [1 2 3]   [1 2 3]
```

Total partitions: 10

### Increase Partitions

```bash
# Increase to 20 partitions
rpk topic alter-config task-events --set partition_count=20

# Verify
rpk topic describe task-events
```

**Warning:** Cannot decrease partition count. Only increase.

### Best Practice

Set partitions based on expected max replicas:
- **Development:** 3 partitions (low traffic)
- **Staging:** 10 partitions (moderate traffic)
- **Production:** 30 partitions (high traffic, room to scale)

## Service-Specific Scaling

### Recurring Task Service

**Typical Scale:**
- Dev: 1 replica
- Prod: 3-5 replicas

**Scale when:**
- Many recurring tasks being completed
- Consumer lag > 500
- Creating 100+ instances/minute

```bash
kubectl scale deployment recurring-task-service --replicas=5
```

### Notification Service

**Typical Scale:**
- Dev: 1 replica
- Prod: 2-3 replicas

**Scale when:**
- Many reminders due
- Notification send rate > 50/second
- Consumer lag > 200

```bash
kubectl scale deployment notification-service --replicas=3
```

### Audit Service

**Typical Scale:**
- Dev: 1 replica
- Prod: 2-4 replicas

**Scale when:**
- High event volume (all event types)
- Batch commits taking > 5 seconds
- Consumer lag > 1000

```bash
kubectl scale deployment audit-service --replicas=4
```

## Monitoring Scaling Impact

### Before Scaling

```bash
# Record current lag
rpk group describe recurring-task-service-group > before-scale.txt

# Record current throughput
kubectl top pods -l app=recurring-task-service
```

### During Scaling

```bash
# Watch pods come online
kubectl get pods -l app=recurring-task-service -w

# Monitor lag reduction
watch 'rpk group describe recurring-task-service-group | grep LAG'
```

### After Scaling

```bash
# Verify lag decreased
rpk group describe recurring-task-service-group

# Check resource usage
kubectl top pods -l app=recurring-task-service

# Compare metrics
diff before-scale.txt <(rpk group describe recurring-task-service-group)
```

### Expected Impact

**Scale 1 → 3 replicas:**
- Lag catchup: 3x faster
- Throughput: 3x higher
- Latency: Similar or better

**Scale 5 → 10 replicas:**
- Lag catchup: 2x faster (diminishing returns)
- May hit partition limit

## Cost Optimization

### Right-Sizing

```bash
# Check actual resource usage
kubectl top pods --sort-by=cpu
kubectl top pods --sort-by=memory

# Compare to resource limits
kubectl describe deployment recurring-task-service | grep -A 5 "Limits"
```

### Reduce Over-Provisioned Resources

```yaml
# Update Helm values
resources:
  limits:
    cpu: 500m      # Was 1000m
    memory: 512Mi  # Was 1Gi
  requests:
    cpu: 100m      # Was 200m
    memory: 128Mi  # Was 256Mi
```

```bash
# Apply changes
helm upgrade recurring-task-service ./charts/recurring-task-service \
  -f values-optimized.yaml
```

### Use Spot Instances

For non-critical consumers (e.g., audit-service):

```yaml
# Add node selector for spot instances
nodeSelector:
  node-type: spot
tolerations:
  - key: "spot"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"
```

## Troubleshooting

### Issue: Scaled up but lag still high

**Possible Causes:**
1. Hit partition limit (consumers > partitions)
2. Database bottleneck (slow inserts)
3. Network issues

**Debug:**
```bash
# Check partition distribution
kubectl exec -it deploy/recurring-task-service -- \
  python -c "from src.consumer import consumer; print(consumer.assignment())"

# Check database connection
kubectl exec -it deploy/recurring-task-service -- \
  psql $DATABASE_URL -c "SELECT COUNT(*) FROM tasks;"
```

### Issue: HPA not scaling

**Possible Causes:**
1. Metrics not available
2. HPA misconfigured
3. Reached max replicas

**Debug:**
```bash
# Check HPA events
kubectl describe hpa recurring-task-service

# Check metrics server
kubectl get apiservice v1beta1.metrics.k8s.io -o yaml

# Check custom metrics
kubectl get --raw /apis/external.metrics.k8s.io/v1beta1
```

### Issue: Uneven partition distribution

**Symptoms:** Some consumers idle, others overloaded

**Solution:** Kafka rebalances automatically, but you can trigger:

```bash
# Restart all consumers to force rebalance
kubectl rollout restart deployment recurring-task-service
```

## Best Practices

1. **Start Small, Scale Up**
   - Begin with minReplicas=1
   - Let HPA scale based on actual load

2. **Monitor Before Scaling**
   - Understand current bottleneck
   - Check CPU, memory, lag, latency

3. **Scale Gradually**
   - Increase 2-3 replicas at a time
   - Observe impact before adding more

4. **Test Scaling in Staging**
   - Simulate production load
   - Verify HPA thresholds

5. **Set Appropriate Limits**
   - maxReplicas = Topic partitions
   - Avoid over-provisioning

## Emergency Scale-Up

For sudden traffic spikes:

```bash
# Immediate scale to max
kubectl scale deployment recurring-task-service --replicas=10
kubectl scale deployment notification-service --replicas=5
kubectl scale deployment audit-service --replicas=8

# Monitor catch-up
watch 'rpk group list | xargs -I {} rpk group describe {}'
```

## Related Runbooks

- **Kafka Broker Failure:** docs/runbooks/kafka-broker-failure.md
- **Event Replay:** docs/runbooks/event-replay.md

---

**Last Updated:** 2026-01-13
**Maintained By:** Platform Team
