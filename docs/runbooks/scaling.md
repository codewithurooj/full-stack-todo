# Scaling Operations Guide

This guide covers how to scale the todo application to handle varying loads.

---

## Manual Scaling

### Scale Deployment Replicas

```bash
# Scale backend
kubectl scale deployment todo-backend --replicas=3 -n todo-app

# Scale frontend
kubectl scale deployment todo-frontend --replicas=3 -n todo-app

# Verify scaling
kubectl get pods -n todo-app -l app.kubernetes.io/name=todo-backend
```

### Scale Using Helm

```bash
helm upgrade todo-backend ./charts/backend \
  --set replicaCount=3 \
  -n todo-app \
  --reuse-values
```

---

## Horizontal Pod Autoscaler (HPA)

### Enable HPA

HPA is configured in the Helm values files:

```yaml
# values.yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
```

### Check HPA Status

```bash
# View HPA status
kubectl get hpa -n todo-app

# Detailed HPA info
kubectl describe hpa todo-backend -n todo-app

# Watch HPA in real-time
kubectl get hpa -n todo-app -w
```

### Manual HPA Commands

```bash
# Create HPA manually
kubectl autoscale deployment todo-backend \
  --min=2 --max=10 \
  --cpu-percent=70 \
  -n todo-app

# Update HPA
kubectl patch hpa todo-backend -n todo-app \
  -p '{"spec":{"maxReplicas":15}}'
```

---

## Resource Scaling

### Increase Resource Limits

```bash
# Update via Helm
helm upgrade todo-backend ./charts/backend \
  --set resources.limits.cpu=2000m \
  --set resources.limits.memory=2Gi \
  --set resources.requests.cpu=1000m \
  --set resources.requests.memory=1Gi \
  -n todo-app \
  --reuse-values
```

### Check Current Resources

```bash
# View resource usage
kubectl top pods -n todo-app

# View resource limits
kubectl get deployment todo-backend -n todo-app \
  -o jsonpath='{.spec.template.spec.containers[0].resources}'
```

---

## Node Scaling (Cloud Provider)

### Oracle OKE

```bash
# Scale node pool
oci ce node-pool update \
  --node-pool-id <node-pool-ocid> \
  --size 5
```

### Azure AKS

```bash
# Scale node pool
az aks scale \
  --resource-group todo-rg \
  --name todo-cluster \
  --node-count 5

# Or enable cluster autoscaler
az aks update \
  --resource-group todo-rg \
  --name todo-cluster \
  --enable-cluster-autoscaler \
  --min-count 2 \
  --max-count 10
```

### Google GKE

```bash
# Scale node pool
gcloud container clusters resize todo-cluster \
  --num-nodes 5 \
  --region us-central1

# Or enable autoscaler
gcloud container clusters update todo-cluster \
  --enable-autoscaling \
  --min-nodes 2 \
  --max-nodes 10 \
  --region us-central1
```

---

## Load Testing

### Using k6

```bash
# Install k6
brew install k6  # macOS
# or
docker pull grafana/k6

# Run load test
k6 run scripts/load_test.js
```

### Using hey

```bash
# Install hey
go install github.com/rakyll/hey@latest

# Run load test
hey -n 1000 -c 50 https://todo.example.com/api/health
```

### Using Apache Bench

```bash
# 1000 requests, 50 concurrent
ab -n 1000 -c 50 https://todo.example.com/api/health
```

---

## Scaling Recommendations

### Development/Staging

| Component | Replicas | CPU | Memory |
|-----------|----------|-----|--------|
| Backend | 1 | 200m | 256Mi |
| Frontend | 1 | 100m | 128Mi |

### Production (Small)

| Component | Replicas | CPU | Memory |
|-----------|----------|-----|--------|
| Backend | 2 | 500m | 512Mi |
| Frontend | 2 | 200m | 256Mi |

### Production (Large)

| Component | Replicas | CPU | Memory |
|-----------|----------|-----|--------|
| Backend | 3-5 | 1000m | 1Gi |
| Frontend | 3-5 | 500m | 512Mi |

---

## Database Scaling

### Neon PostgreSQL

Neon handles scaling automatically. For high-load scenarios:

1. Check compute size in Neon dashboard
2. Upgrade to larger compute if needed
3. Consider connection pooling with PgBouncer

### Connection Pool Settings

```python
# backend/app/db.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800
)
```

---

## Monitoring Scale Events

### Check Scaling Events

```bash
# View HPA events
kubectl describe hpa todo-backend -n todo-app | grep -A 20 "Events"

# View all scaling events
kubectl get events -n todo-app | grep -i scale
```

### Prometheus Metrics

Key metrics to monitor:

- `container_cpu_usage_seconds_total`
- `container_memory_usage_bytes`
- `kube_deployment_status_replicas`
- `kube_hpa_status_current_replicas`

---

## Quick Reference

| Action | Command |
|--------|---------|
| Scale replicas | `kubectl scale deployment todo-backend --replicas=3 -n todo-app` |
| Check HPA | `kubectl get hpa -n todo-app` |
| Check resource usage | `kubectl top pods -n todo-app` |
| Check node usage | `kubectl top nodes` |
| Watch pods | `kubectl get pods -n todo-app -w` |
