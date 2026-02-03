# Notification Service - Quick Start Guide

Get the notification service running in 5 minutes.

## Prerequisites

- Python 3.13+
- PostgreSQL database
- Kafka or Redpanda running

## Step 1: Install Dependencies

```bash
cd services/notification-service
pip install -r requirements.txt
```

## Step 2: Generate VAPID Keys

```bash
python -c "from pywebpush import generate_vapid_keys; print(generate_vapid_keys())"
```

Save the output - you'll need both keys.

## Step 3: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set:
```env
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
DATABASE_URL=postgresql://user:password@localhost:5432/todo_db
VAPID_PUBLIC_KEY=<your-public-key>
VAPID_PRIVATE_KEY=<your-private-key>
```

## Step 4: Run Database Migration

```bash
# Using psql
psql $DATABASE_URL -f migrations/001_create_tables.sql

# Or using Python
python -c "
from sqlmodel import create_engine
import os
engine = create_engine(os.getenv('DATABASE_URL'))
with open('migrations/001_create_tables.sql') as f:
    engine.execute(f.read())
"
```

## Step 5: Run Service

```bash
python -m app.main
```

You should see:
```
2026-01-12 10:00:00 - __main__ - INFO - Starting notification-service
2026-01-12 10:00:00 - __main__ - INFO - Kafka bootstrap servers: localhost:9092
2026-01-12 10:00:00 - __main__ - INFO - Consumer group: notification-service
2026-01-12 10:00:00 - app.consumer - INFO - Consumer started, waiting for messages...
```

## Step 6: Test with Sample Event

In another terminal, publish a test reminder event to Kafka:

```bash
# Using kafka-console-producer
echo '{
  "event_id": "test-001",
  "schema_version": "1.0.0",
  "timestamp": "2026-01-12T10:30:00.000Z",
  "reminder_id": "test-reminder-001",
  "task_id": 1,
  "user_id": 1,
  "title": "Test notification",
  "remind_at": "2026-01-12T10:30:30.000Z",
  "due_date": "2026-01-12T11:00:00.000Z"
}' | kafka-console-producer \
  --bootstrap-server localhost:9092 \
  --topic reminders
```

The service should log:
```
2026-01-12 10:30:00 - app.consumer - INFO - Received reminder event: test-reminder-001
2026-01-12 10:30:00 - app.consumer - INFO - Scheduling notification for reminder test-reminder-001
```

## Docker Quickstart

```bash
# Build
docker build -t notification-service:latest .

# Run
docker run \
  -e KAFKA_BOOTSTRAP_SERVERS=host.docker.internal:9092 \
  -e DATABASE_URL=postgresql://user:pass@host.docker.internal:5432/todo \
  -e VAPID_PRIVATE_KEY=your-key \
  notification-service:latest
```

## Kubernetes Quickstart

```bash
# Create secrets first
kubectl create secret generic db-secret \
  --from-literal=DATABASE_URL=postgresql://user:pass@db:5432/todo

kubectl create secret generic vapid-secret \
  --from-literal=VAPID_PUBLIC_KEY=your-public-key \
  --from-literal=VAPID_PRIVATE_KEY=your-private-key

# Deploy with Helm
helm install notification-service ./charts/notification-service

# Verify
kubectl get pods -l app=notification-service
kubectl logs -f deployment/notification-service
```

## Troubleshooting

### "No module named 'app'"
- Make sure you're in the `services/notification-service` directory
- Check that `PYTHONPATH` includes current directory

### "Failed to connect to Kafka"
- Verify Kafka is running: `telnet localhost 9092`
- Check `KAFKA_BOOTSTRAP_SERVERS` is correct

### "Database connection error"
- Verify PostgreSQL is running
- Check `DATABASE_URL` format
- Run migration script

### "VAPID_PRIVATE_KEY not set"
- Generate VAPID keys (see Step 2)
- Set in `.env` file

## Next Steps

1. **Register push subscription:** Create endpoint in backend API
2. **Test end-to-end:** Create task with reminder
3. **Monitor logs:** Watch for notification events
4. **Check database:** Query `notification_logs` table
5. **Scale:** Deploy multiple replicas for high availability

## Resources

- [README.md](README.md) - Full documentation
- [tests/](tests/) - Test examples
- [Web Push Protocol](https://tools.ietf.org/html/rfc8030)
- [VAPID Spec](https://tools.ietf.org/html/rfc8292)

---

**Need help?** Check the [Troubleshooting section](README.md#troubleshooting) in the main README.
