# Notification Service - Deployment Checklist

Use this checklist to ensure successful deployment of the notification service.

## Pre-Deployment Checklist

### 1. Infrastructure ✓

- [ ] **Kafka/Redpanda running**
  ```bash
  kubectl get pods -l app=kafka
  ```

- [ ] **PostgreSQL database accessible**
  ```bash
  psql $DATABASE_URL -c "SELECT 1"
  ```

- [ ] **Kafka topic `reminders` created**
  ```bash
  kafka-topics --bootstrap-server kafka:9092 --list | grep reminders
  ```

### 2. VAPID Keys ✓

- [ ] **Keys generated**
  ```bash
  python -c "from pywebpush import generate_vapid_keys; print(generate_vapid_keys())"
  ```

- [ ] **Public key saved**
  - Backend .env
  - Frontend .env.local
  - Notification service .env

- [ ] **Private key saved**
  - Backend .env
  - Notification service .env

- [ ] **Same keys across all services** ⚠️ CRITICAL

### 3. Database Migration ✓

- [ ] **Migration file reviewed**
  ```bash
  cat migrations/001_create_tables.sql
  ```

- [ ] **Migration executed**
  ```bash
  psql $DATABASE_URL -f migrations/001_create_tables.sql
  ```

- [ ] **Tables created**
  ```bash
  psql $DATABASE_URL -c "\dt notification_logs push_subscriptions user_notification_stats"
  ```

- [ ] **Tasks table has reminded column**
  ```bash
  psql $DATABASE_URL -c "\d tasks" | grep reminded
  ```

### 4. Configuration ✓

- [ ] **Environment variables set**
  - KAFKA_BOOTSTRAP_SERVERS
  - DATABASE_URL
  - VAPID_PUBLIC_KEY
  - VAPID_PRIVATE_KEY
  - VAPID_CLAIMS_EMAIL

- [ ] **.env file created** (local)
  ```bash
  cp .env.example .env
  ```

- [ ] **Kubernetes secrets created** (production)
  ```bash
  kubectl create secret generic db-secret --from-literal=DATABASE_URL=...
  kubectl create secret generic vapid-secret \
    --from-literal=VAPID_PUBLIC_KEY=... \
    --from-literal=VAPID_PRIVATE_KEY=...
  ```

### 5. Testing ✓

- [ ] **Dependencies installed**
  ```bash
  pip install -r requirements.txt
  ```

- [ ] **Verification script passed**
  ```bash
  python verify_service.py
  ```

- [ ] **Unit tests passed**
  ```bash
  pytest tests/ -v
  ```

- [ ] **Coverage acceptable (>80%)**
  ```bash
  pytest tests/ --cov=app --cov-report=term
  ```

## Deployment Steps

### Local Deployment

#### Step 1: Install
```bash
cd services/notification-service
pip install -r requirements.txt
```

#### Step 2: Configure
```bash
make setup
# Or manually:
cp .env.example .env
# Edit .env with your values
```

#### Step 3: Verify
```bash
python verify_service.py
```

#### Step 4: Run
```bash
make run
```

#### Step 5: Test
Publish test event to Kafka and verify notification.

### Docker Deployment

#### Step 1: Build Image
```bash
docker build -t notification-service:latest .
```

#### Step 2: Test Locally
```bash
docker run --env-file .env notification-service:latest
```

#### Step 3: Push to Registry
```bash
docker tag notification-service:latest your-registry/notification-service:1.0.0
docker push your-registry/notification-service:1.0.0
```

### Kubernetes Deployment

#### Step 1: Create Namespace (if needed)
```bash
kubectl create namespace todo-app
kubectl config set-context --current --namespace=todo-app
```

#### Step 2: Create Secrets
```bash
# Database secret
kubectl create secret generic db-secret \
  --from-literal=DATABASE_URL=postgresql://user:pass@host:5432/db

# VAPID secret
kubectl create secret generic vapid-secret \
  --from-literal=VAPID_PUBLIC_KEY=... \
  --from-literal=VAPID_PRIVATE_KEY=...
```

#### Step 3: Update Helm Values (if needed)
```bash
# Edit charts/notification-service/values.yaml
# Update image repository, Kafka servers, etc.
```

#### Step 4: Install with Helm
```bash
helm install notification-service ./charts/notification-service
```

#### Step 5: Verify Deployment
```bash
# Check pods
kubectl get pods -l app=notification-service

# Check logs
kubectl logs -f deployment/notification-service

# Check events
kubectl get events --sort-by=.metadata.creationTimestamp
```

## Post-Deployment Verification

### 1. Service Health ✓

- [ ] **Pod is running**
  ```bash
  kubectl get pods -l app=notification-service
  ```

- [ ] **No errors in logs**
  ```bash
  kubectl logs -f deployment/notification-service | grep ERROR
  ```

- [ ] **Consumer connected to Kafka**
  ```bash
  kubectl logs deployment/notification-service | grep "Consumer started"
  ```

### 2. Kafka Integration ✓

- [ ] **Consumer group exists**
  ```bash
  kafka-consumer-groups --bootstrap-server kafka:9092 \
    --group notification-service \
    --describe
  ```

- [ ] **No consumer lag** (should be 0 initially)

- [ ] **Topic has partition assignments**

### 3. Database Integration ✓

- [ ] **Can connect to database**
  ```bash
  kubectl logs deployment/notification-service | grep "database"
  ```

- [ ] **Tables accessible**
  ```sql
  SELECT COUNT(*) FROM notification_logs;
  SELECT COUNT(*) FROM push_subscriptions;
  ```

### 4. End-to-End Test ✓

- [ ] **Publish test event**
  ```bash
  kafka-console-producer --bootstrap-server kafka:9092 --topic reminders
  # Paste test event JSON
  ```

- [ ] **Service logs event received**
  ```bash
  kubectl logs -f deployment/notification-service | grep "Received reminder event"
  ```

- [ ] **Notification scheduled**
  ```bash
  kubectl logs -f deployment/notification-service | grep "Scheduling notification"
  ```

- [ ] **Check database logs**
  ```sql
  SELECT * FROM notification_logs ORDER BY sent_at DESC LIMIT 5;
  ```

### 5. Integration Tests ✓

- [ ] **Backend publishes events**
  - Create task with reminder via API
  - Check Kafka topic for event

- [ ] **Frontend receives notifications**
  - Register push subscription
  - Create task with reminder
  - Verify notification appears

- [ ] **Database consistency**
  - Check task.reminded = true
  - Check notification_logs entry

## Monitoring Setup

### 1. Logging ✓

- [ ] **Logs are structured**
  ```bash
  kubectl logs deployment/notification-service | jq
  ```

- [ ] **Log level appropriate** (INFO for production)

- [ ] **Errors are captured**
  ```bash
  kubectl logs deployment/notification-service | grep ERROR
  ```

### 2. Metrics ✓

- [ ] **Consumer lag monitored**
  ```bash
  # Check periodically
  kafka-consumer-groups --bootstrap-server kafka:9092 \
    --group notification-service \
    --describe
  ```

- [ ] **Resource usage tracked**
  ```bash
  kubectl top pod -l app=notification-service
  ```

### 3. Alerts ✓

- [ ] **Alert on pod restart**
- [ ] **Alert on high consumer lag**
- [ ] **Alert on error rate spike**
- [ ] **Alert on resource limits reached**

## Troubleshooting Guide

### Issue: Pod not starting

**Check:**
```bash
# Pod status
kubectl get pods -l app=notification-service

# Events
kubectl describe pod <pod-name>

# Logs
kubectl logs <pod-name>
```

**Common causes:**
- Image pull error
- Secret not found
- Configuration error
- Resource limits too low

### Issue: Consumer not receiving messages

**Check:**
```bash
# Consumer group
kafka-consumer-groups --bootstrap-server kafka:9092 \
  --group notification-service \
  --describe

# Topic exists
kafka-topics --bootstrap-server kafka:9092 --list

# Service logs
kubectl logs -f deployment/notification-service
```

**Common causes:**
- Wrong topic name
- Kafka not accessible
- Consumer group offset at end
- Network policy blocking

### Issue: Notifications not sending

**Check:**
```bash
# Service logs
kubectl logs -f deployment/notification-service | grep "notification"

# Database subscriptions
psql $DATABASE_URL -c "SELECT COUNT(*) FROM push_subscriptions WHERE active = true"

# VAPID keys match
kubectl get secret vapid-secret -o yaml
```

**Common causes:**
- VAPID keys mismatch
- No push subscriptions
- Invalid subscription endpoints
- Rate limiting active

### Issue: Database errors

**Check:**
```bash
# Connection string
kubectl get secret db-secret -o yaml

# Database accessible
kubectl run -it --rm psql --image=postgres:13 -- \
  psql $DATABASE_URL -c "SELECT 1"

# Tables exist
psql $DATABASE_URL -c "\dt"
```

**Common causes:**
- Wrong DATABASE_URL
- Migration not run
- Database not accessible
- Connection pool exhausted

## Rollback Procedure

If deployment fails:

### 1. Immediate Rollback
```bash
# Rollback to previous release
helm rollback notification-service

# Or delete deployment
helm uninstall notification-service
```

### 2. Fix Issues
- Review logs for errors
- Check configuration
- Verify secrets
- Test locally

### 3. Redeploy
```bash
# Fix issues, then redeploy
helm upgrade notification-service ./charts/notification-service
```

## Scaling Guide

### Horizontal Scaling

```bash
# Scale to 3 replicas
kubectl scale deployment notification-service --replicas=3

# Or update Helm values
helm upgrade notification-service ./charts/notification-service \
  --set replicaCount=3
```

**Note:** Consumer group enables parallel processing across replicas.

### Vertical Scaling

```bash
# Update resource limits
helm upgrade notification-service ./charts/notification-service \
  --set resources.requests.cpu=500m \
  --set resources.requests.memory=512Mi
```

## Maintenance

### Regular Tasks

- **Weekly:** Check consumer lag
- **Weekly:** Review error logs
- **Monthly:** Clean old notification_logs
- **Monthly:** Review inactive subscriptions
- **Quarterly:** Rotate VAPID keys

### Log Cleanup

```sql
-- Delete logs older than 30 days
DELETE FROM notification_logs
WHERE sent_at < NOW() - INTERVAL '30 days';

-- Deactivate old inactive subscriptions
UPDATE push_subscriptions
SET active = false
WHERE active = true
  AND created_at < NOW() - INTERVAL '90 days'
  AND id NOT IN (
    SELECT subscription_id FROM notification_logs
    WHERE sent_at > NOW() - INTERVAL '90 days'
  );
```

## Success Criteria

Deployment is successful when:

- ✅ Pod is running and healthy
- ✅ Consumer connected to Kafka
- ✅ Consumer lag is 0 or low
- ✅ No errors in logs
- ✅ End-to-end test passes
- ✅ Monitoring is active
- ✅ Alerts are configured

## Resources

- [README.md](README.md) - Complete documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick setup guide
- [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) - Integration details
- [SERVICE_SUMMARY.md](SERVICE_SUMMARY.md) - Implementation overview

## Support Contacts

- **Service owner:** [Team/Person]
- **Infrastructure:** [Team/Person]
- **On-call:** [Rotation/Schedule]

---

**Last updated:** 2026-01-12
**Version:** 1.0.0
