# Recurring Task Service Helm Chart

Kubernetes deployment for the Recurring Task Service - a Kafka consumer that automatically creates recurring task instances.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- Kafka cluster (Redpanda or Apache Kafka)
- PostgreSQL database
- Prometheus Operator (optional, for ServiceMonitor)

## Installing the Chart

```bash
# Install with default values
helm install recurring-task-service ./charts/recurring-task-service

# Install with custom values
helm install recurring-task-service ./charts/recurring-task-service \
  --set database.url="postgresql://user:pass@host/db" \
  --set kafka.bootstrapServers="kafka:9092"

# Install with values file
helm install recurring-task-service ./charts/recurring-task-service \
  -f values-production.yaml
```

## Uninstalling the Chart

```bash
helm uninstall recurring-task-service
```

## Configuration

### Required Configuration

You MUST set these values:

```yaml
database:
  url: "postgresql://user:password@host:5432/dbname"

kafka:
  bootstrapServers: "kafka:9092"
```

### Kafka SASL Authentication

For Redpanda Cloud or secured Kafka:

```yaml
kafka:
  bootstrapServers: "seed-xyz.cloud.redpanda.com:9092"
  sasl:
    enabled: true
    username: "your-username"
    password: "your-password"
  securityProtocol: "SASL_SSL"
```

### Resource Configuration

```yaml
resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 200m
    memory: 256Mi
```

### Autoscaling

```yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: External
      external:
        metric:
          name: kafka_consumer_lag
        target:
          type: Value
          value: "100"
```

## Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas | `1` |
| `image.repository` | Image repository | `recurring-task-service` |
| `image.tag` | Image tag | `latest` |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `service.type` | Service type | `ClusterIP` |
| `service.port` | Service port | `8001` |
| `service.metricsPort` | Metrics port | `8080` |
| `resources.limits.cpu` | CPU limit | `500m` |
| `resources.limits.memory` | Memory limit | `512Mi` |
| `autoscaling.enabled` | Enable HPA | `true` |
| `autoscaling.minReplicas` | Minimum replicas | `1` |
| `autoscaling.maxReplicas` | Maximum replicas | `10` |
| `kafka.bootstrapServers` | Kafka bootstrap servers | `kafka:9092` |
| `kafka.topic` | Kafka topic to consume | `task-events` |
| `kafka.consumerGroup` | Consumer group ID | `recurring-task-service-group` |
| `database.url` | Database connection URL | `""` |
| `config.logLevel` | Log level | `INFO` |
| `livenessProbe.enabled` | Enable liveness probe | `true` |
| `readinessProbe.enabled` | Enable readiness probe | `true` |
| `metrics.enabled` | Enable Prometheus metrics | `true` |
| `metrics.serviceMonitor.enabled` | Enable ServiceMonitor | `true` |

## Monitoring

### Prometheus Metrics

The service exposes Prometheus metrics at `/metrics` on port 8080.

Key metrics:
- `recurring_task_events_consumed_total` - Events consumed
- `recurring_task_instances_created_total` - Instances created
- `recurring_task_consumer_lag` - Consumer lag
- `recurring_task_event_processing_duration_seconds` - Processing latency

### ServiceMonitor

If Prometheus Operator is installed:

```yaml
metrics:
  serviceMonitor:
    enabled: true
    interval: 15s
    scrapeTimeout: 10s
```

### Health Checks

```bash
# Liveness probe
curl http://localhost:8001/health

# Readiness probe
curl http://localhost:8001/health
```

## Upgrading

```bash
# Upgrade to new version
helm upgrade recurring-task-service ./charts/recurring-task-service

# Upgrade with new values
helm upgrade recurring-task-service ./charts/recurring-task-service \
  --set image.tag=v1.1.0

# Rollback if needed
helm rollback recurring-task-service
```

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods -l app.kubernetes.io/name=recurring-task-service
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### Check Consumer Lag

```bash
kubectl exec -it deploy/recurring-task-service -- \
  python -c "from src.metrics import metrics_collector; print(metrics_collector.export_metrics())"
```

### Verify Configuration

```bash
kubectl get configmap recurring-task-service -o yaml
kubectl get secret recurring-task-service -o yaml
```

### Debug Kafka Connection

```bash
kubectl exec -it deploy/recurring-task-service -- \
  rpk cluster info --brokers $KAFKA_BOOTSTRAP_SERVERS
```

## Examples

### Development Environment

```yaml
# values-dev.yaml
replicaCount: 1
autoscaling:
  enabled: false
kafka:
  bootstrapServers: "localhost:19092"
database:
  url: "postgresql://postgres:postgres@localhost:5432/todo"
```

```bash
helm install recurring-task-service ./charts/recurring-task-service \
  -f values-dev.yaml
```

### Production Environment

```yaml
# values-prod.yaml
replicaCount: 3
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
resources:
  limits:
    cpu: 1000m
    memory: 1Gi
kafka:
  bootstrapServers: "seed-xyz.cloud.redpanda.com:9092"
  sasl:
    enabled: true
    username: "prod-user"
    password: "prod-password"
  securityProtocol: "SASL_SSL"
database:
  url: "postgresql://user:pass@prod-db:5432/todo"
```

```bash
helm install recurring-task-service ./charts/recurring-task-service \
  -f values-prod.yaml \
  --set image.tag=v1.0.0
```

## Security

### Secrets Management

Store sensitive values in Kubernetes secrets:

```bash
# Create secret manually
kubectl create secret generic recurring-task-service \
  --from-literal=DATABASE_URL="postgresql://user:pass@host/db" \
  --from-literal=KAFKA_SASL_PASSWORD="password"

# Reference existing secret
helm install recurring-task-service ./charts/recurring-task-service \
  --set existingSecret=my-secret
```

## License

Copyright © 2026 Platform Team
