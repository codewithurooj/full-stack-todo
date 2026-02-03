# Dapr Troubleshooting Runbook

**Feature**: 012-dapr-integration
**Last Updated**: 2026-01-18

This runbook provides solutions for common Dapr-related issues in the Todo application.

---

## Quick Diagnostics

### Check Dapr Sidecar Health

```bash
# Local development
curl http://localhost:3500/v1.0/healthz
# Expected: HTTP 204 No Content

# Kubernetes
kubectl get pods -l app=backend-service
kubectl logs <pod-name> -c daprd | tail -50
```

### Check Registered Components

```bash
curl http://localhost:3500/v1.0/metadata | jq '.components'
```

### Check Service Status

```bash
# Local multi-app mode
dapr list

# Kubernetes
dapr status -k
```

---

## Issue: Dapr Sidecar Not Starting

### Symptoms
- Application starts but Dapr features don't work
- `check_dapr_health()` returns False
- HTTP requests to localhost:3500 fail

### Diagnosis

```bash
# Check if Dapr is installed
dapr --version

# Check if Dapr is initialized
dapr init

# Check Docker containers (local mode)
docker ps | grep daprd
```

### Solutions

**Solution 1: Initialize Dapr**
```bash
dapr init
```

**Solution 2: Reinitialize Dapr**
```bash
dapr uninstall --all
dapr init
```

**Solution 3: Check port availability**
```bash
# Windows
netstat -an | findstr 3500
# Linux/Mac
lsof -i :3500
```

---

## Issue: Pub/Sub Events Not Delivered

### Symptoms
- Events published successfully but subscribers don't receive them
- Notification service doesn't process task events

### Diagnosis

```bash
# Check topic exists
docker exec -it redpanda rpk topic list

# Check consumer groups
docker exec -it redpanda rpk group list

# Check topic messages
docker exec -it redpanda rpk topic consume task-events --offset end
```

### Solutions

**Solution 1: Create missing topics**
```bash
docker exec -it redpanda rpk topic create task-events reminders task-updates
```

**Solution 2: Check subscription endpoint**
```bash
curl http://localhost:8001/dapr/subscribe
# Should return JSON array of subscriptions
```

**Solution 3: Verify component configuration**
```bash
# Check pubsub component
curl http://localhost:3500/v1.0/metadata | jq '.components[] | select(.name=="kafka-pubsub")'
```

---

## Issue: State Store Operations Failing

### Symptoms
- Conversation state not persisting
- 500 errors on state operations

### Diagnosis

```bash
# Test state store directly
curl -X POST http://localhost:3500/v1.0/state/statestore \
  -H "Content-Type: application/json" \
  -d '[{"key":"test","value":"hello"}]'

curl http://localhost:3500/v1.0/state/statestore/test
```

### Solutions

**Solution 1: Check database connection**
```bash
# Verify connection string in component
cat ~/.dapr/components/statestore.yaml

# Test database connection
psql "your-connection-string" -c "SELECT 1"
```

**Solution 2: Create state table manually**
```sql
CREATE TABLE IF NOT EXISTS dapr_state (
  key TEXT PRIMARY KEY,
  value JSONB,
  etag TEXT,
  insertdate TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updatedate TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## Issue: Service Invocation Failing

### Symptoms
- Cross-service calls return 500 or timeout
- Service discovery not working

### Diagnosis

```bash
# Test service invocation
curl http://localhost:3500/v1.0/invoke/backend-service/method/health

# Check service registration
curl http://localhost:3500/v1.0/metadata | jq '.id'
```

### Solutions

**Solution 1: Verify app-id matches**
Ensure the `--app-id` flag matches the target service name in invoke calls.

**Solution 2: Check network connectivity**
```bash
# In Kubernetes, check service DNS
kubectl exec -it <pod> -- nslookup backend-service.default.svc.cluster.local
```

---

## Issue: Secrets Not Loading

### Symptoms
- Environment variables empty
- Authentication failures
- API key errors

### Diagnosis

```bash
# Test secrets retrieval
curl http://localhost:3500/v1.0/secrets/kubernetes-secrets/app-secrets

# Check component
curl http://localhost:3500/v1.0/metadata | jq '.components[] | select(.name=="kubernetes-secrets")'
```

### Solutions

**Solution 1: Create Kubernetes secret**
```bash
kubectl create secret generic app-secrets \
  --from-literal=OPENAI_API_KEY="sk-..." \
  --from-literal=BETTER_AUTH_SECRET="..."
```

**Solution 2: Use env var fallback (local development)**
Ensure environment variables are set in .env file as fallback.

---

## Issue: Jobs API Not Working

### Symptoms
- Scheduled reminders not triggering
- Jobs not appearing in scheduler

### Diagnosis

```bash
# Check scheduler component
curl http://localhost:3500/v1.0/metadata | jq '.components[] | select(.name=="scheduler")'

# Check job status (alpha API)
curl http://localhost:3500/v1.0-alpha1/jobs/reminder-123-24h
```

### Solutions

**Solution 1: Enable scheduler component**
Ensure scheduler.yaml is in your components directory.

**Solution 2: Use fallback scheduler**
The application has an in-memory fallback scheduler when Dapr Jobs API is unavailable.

---

## Kubernetes-Specific Issues

### Dapr Sidecar Injection Not Working

**Symptoms**: Pods start without daprd container

**Solution**:
```bash
# Verify namespace has injection enabled
kubectl get namespace default -o yaml | grep dapr.io/enabled

# Enable injection
kubectl label namespace default dapr.io/enabled=true

# Verify pod has annotation
kubectl get pod <pod-name> -o yaml | grep dapr.io/enabled
```

### Component Not Available in Namespace

**Symptoms**: Component works locally but not in K8s

**Solution**:
```bash
# Check component namespace
kubectl get components -A

# Apply to correct namespace
kubectl apply -f dapr-components/ -n default
```

---

## Performance Issues

### High Latency

**Diagnosis**:
```bash
# Check Dapr metrics
curl http://localhost:9090/metrics | grep dapr
```

**Solutions**:
1. Enable gRPC instead of HTTP for internal communication
2. Increase Dapr sidecar resources
3. Check network policies

### Memory Usage

**Solution**: Adjust sidecar resources
```yaml
annotations:
  dapr.io/sidecar-memory-limit: "512Mi"
  dapr.io/sidecar-memory-request: "256Mi"
```

---

## Logs and Debugging

### Enable Verbose Logging

```yaml
# In deployment annotations
dapr.io/log-level: "debug"
dapr.io/enable-api-logging: "true"
```

### View Dapr Logs

```bash
# Local
dapr logs --app-id backend-service

# Kubernetes
kubectl logs <pod-name> -c daprd -f

# Filter errors
kubectl logs <pod-name> -c daprd | grep -i error
```

### Common Log Messages

| Message | Meaning | Action |
|---------|---------|--------|
| `component loaded` | Component initialized | Normal |
| `connection refused` | Target unavailable | Check service health |
| `context deadline exceeded` | Timeout | Check network/resources |
| `unauthenticated` | Auth failure | Check credentials |

---

## Rollback Procedures

### Disable Dapr for a Service

1. Update Helm values:
```yaml
dapr:
  enabled: false
```

2. Redeploy:
```bash
helm upgrade backend ./charts/backend -f values.yaml
```

### Revert to Kafka Direct Connection

1. Set `DAPR_ENABLED=false` in environment
2. Application will use kafka_producer.py fallback

---

## Support Resources

- [Dapr Documentation](https://docs.dapr.io/)
- [Dapr GitHub Issues](https://github.com/dapr/dapr/issues)
- [Dapr Discord](https://discord.com/invite/dapr)
- Project quickstart: `specs/012-dapr-integration/quickstart.md`
