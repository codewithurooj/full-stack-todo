# Monitoring and Observability

**Feature 011: Event-Driven Architecture with Kafka**

Monitoring configuration for Kafka event architecture including Prometheus metrics, Grafana dashboards, and alerting rules.

## Components

### Prometheus Metrics

All microservices expose Prometheus metrics at `/metrics` endpoint:

- **Recurring Task Service:** http://localhost:8001/metrics
- **Notification Service:** http://localhost:8002/metrics
- **Audit Service:** http://localhost:8003/metrics

### Grafana Dashboards

1. **Consumer Lag Dashboard** (`consumer-lag-dashboard.json`)
   - Consumer lag by service and partition
   - Offset progression over time
   - Lag alerts and thresholds

2. **Event Throughput Dashboard** (`event-throughput-dashboard.json`)
   - Events consumed per second
   - Event processing latency (p50, p95, p99)
   - Success/failure rates

### Alerting Rules

**alerts.yaml** contains Prometheus alerting rules:

- Consumer lag > 60 seconds
- Dead letter queue depth > 10
- Service health unhealthy
- Event processing failure rate > 5%

## Setup

### 1. Install Prometheus

```bash
# Docker
docker run -d -p 9090:9090 \
  -v $(pwd)/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# Kubernetes
helm install prometheus prometheus-community/prometheus
```

### 2. Install Grafana

```bash
# Docker
docker run -d -p 3000:3000 grafana/grafana

# Kubernetes
helm install grafana grafana/grafana
```

### 3. Configure Prometheus Data Source

1. Open Grafana: http://localhost:3000
2. Go to Configuration → Data Sources
3. Add Prometheus data source: http://prometheus:9090

### 4. Import Dashboards

1. Go to Dashboards → Import
2. Upload JSON files from `monitoring/` directory:
   - `consumer-lag-dashboard.json`
   - `event-throughput-dashboard.json`

### 5. Configure Alerting

1. Copy `alerts.yaml` to Prometheus rules directory
2. Add to `prometheus.yml`:
   ```yaml
   rule_files:
     - "alerts.yaml"

   alerting:
     alertmanagers:
       - static_configs:
           - targets: ["alertmanager:9093"]
   ```

## Metrics Reference

### Recurring Task Service

- `recurring_task_events_consumed_total` - Events consumed
- `recurring_task_instances_created_total` - Instances created
- `recurring_task_consumer_lag` - Consumer lag by partition
- `recurring_task_event_processing_duration_seconds` - Processing latency

### Notification Service

- `notification_reminder_events_consumed_total` - Reminders consumed
- `notification_notifications_sent_total{status}` - Notifications sent by status
- `notification_consumer_lag` - Consumer lag by partition
- `notification_delivery_duration_seconds` - Delivery latency
- `notification_late_notifications_total` - Late notifications

### Audit Service

- `audit_events_consumed_total{event_type}` - Events consumed by type
- `audit_audit_logs_inserted_total` - Audit logs inserted
- `audit_consumer_lag` - Consumer lag by partition
- `audit_batch_size` - Batch size histogram
- `audit_pending_batch_size` - Current pending batch size

## Key Queries

### Consumer Lag

```promql
# Total lag across all partitions
sum(recurring_task_consumer_lag) by (service)

# Lag by partition
recurring_task_consumer_lag{partition="0"}
```

### Event Throughput

```promql
# Events per second (rate over 5 minutes)
rate(audit_events_consumed_total[5m])

# Total events per minute
sum(rate(audit_events_consumed_total[1m])) * 60
```

### Event Latency

```promql
# p95 processing latency
histogram_quantile(0.95, rate(audit_event_processing_duration_seconds_bucket[5m]))

# p99 processing latency
histogram_quantile(0.99, rate(audit_event_processing_duration_seconds_bucket[5m]))
```

### Success Rate

```promql
# Success rate (last 5 minutes)
sum(rate(notification_notifications_sent_total{status="success"}[5m])) /
sum(rate(notification_notifications_sent_total[5m])) * 100
```

### Batch Processing

```promql
# Average batch size
rate(audit_audit_logs_inserted_total[5m]) / rate(audit_batch_commits_total[5m])

# Batch commit rate
rate(audit_batch_commits_total[5m])
```

## Alerting Examples

### High Consumer Lag Alert

```yaml
- alert: HighConsumerLag
  expr: max(audit_consumer_lag) > 1000
  for: 5m
  annotations:
    summary: "Audit service consumer lag is high"
    description: "Consumer lag is {{ $value }} events"
```

### Low Success Rate Alert

```yaml
- alert: LowNotificationSuccessRate
  expr: |
    sum(rate(notification_notifications_sent_total{status="success"}[5m])) /
    sum(rate(notification_notifications_sent_total[5m])) < 0.90
  for: 10m
  annotations:
    summary: "Notification success rate below 90%"
```

## Troubleshooting

### No Metrics Appearing

1. Check service /metrics endpoint is accessible
2. Verify Prometheus scrape config includes service
3. Check Prometheus targets page (Status → Targets)

### Grafana Dashboard Not Loading

1. Verify Prometheus data source is configured
2. Check dashboard variables are set correctly
3. Verify metric names match exported metrics

### Alerts Not Firing

1. Check Prometheus rules are loaded (Status → Rules)
2. Verify alert expression syntax
3. Check Alertmanager is configured

## Related Documentation

- **Prometheus:** https://prometheus.io/docs/
- **Grafana:** https://grafana.com/docs/
- **Event Replay:** docs/runbooks/event-replay.md
- **Scaling Consumers:** docs/runbooks/scale-consumers.md
