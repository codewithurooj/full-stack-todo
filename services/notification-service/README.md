# Notification Service

Consumes reminder events from Kafka and sends Web Push notifications to users.

## Purpose

This microservice is part of the event-driven task reminder system. It:

1. **Consumes** reminder events from the `reminders` Kafka topic
2. **Schedules** notifications based on `remind_at` timestamps
3. **Sends** Web Push notifications to subscribed users
4. **Rate limits** notifications (10 per user per minute)
5. **Batches** notifications within a 2-minute window
6. **Marks** tasks as reminded in the database

## Architecture

- **Event Source:** Kafka topic `reminders`
- **Consumer Group:** `notification-service`
- **Database:** PostgreSQL (via Neon)
- **Push Protocol:** Web Push (RFC 8030)
- **Deployment:** Kubernetes (standalone, no Dapr)

## Event Schema

The service consumes events with this structure:

```json
{
  "event_id": "660e8400-e29b-41d4-a716-446655440001",
  "schema_version": "1.0.0",
  "timestamp": "2026-01-12T10:30:00.000Z",
  "reminder_id": "reminder-123-2026-01-19T08:00:00Z",
  "task_id": 123,
  "user_id": 456,
  "title": "Buy groceries",
  "remind_at": "2026-01-19T08:00:00.000Z",
  "due_date": "2026-01-19T09:00:00.000Z"
}
```

## Features

### 1. Scheduled Notifications
- Calculates delay until `remind_at` time
- Schedules notifications using asyncio tasks
- Handles past reminders immediately (0 delay)

### 2. Rate Limiting
- Limits to 10 notifications per user per minute
- Prevents notification spam
- Logs rate-limited notifications

### 3. Notification Batching
- Groups notifications within 2-minute window
- Reduces notification noise
- Configurable batch window

### 4. Web Push
- Standards-compliant Web Push (RFC 8030)
- VAPID authentication
- Supports multiple subscriptions per user
- Automatic cleanup of invalid subscriptions

### 5. Database Integration
- Logs all notification attempts
- Tracks push subscriptions
- Marks tasks as reminded
- Deactivates failed subscriptions

## Local Development

### Prerequisites
- Python 3.13+
- Kafka or Redpanda running locally
- PostgreSQL database
- VAPID keys (see below)

### Generate VAPID Keys

```bash
python -c "from pywebpush import generate_vapid_keys; print(generate_vapid_keys())"
```

### Setup

1. **Install dependencies:**
```bash
cd services/notification-service
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Run service:**
```bash
python -m app.main
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test
pytest tests/test_consumer.py::test_send_notification_success -v
```

## Docker

### Build Image

```bash
docker build -t notification-service:latest .
```

### Run Container

```bash
docker run \
  -e KAFKA_BOOTSTRAP_SERVERS=kafka:9092 \
  -e DATABASE_URL=postgresql://user:pass@db:5432/todo \
  -e VAPID_PRIVATE_KEY=your-key \
  notification-service:latest
```

## Kubernetes Deployment

### Deploy with Helm

```bash
# Install
helm install notification-service ./charts/notification-service

# Upgrade
helm upgrade notification-service ./charts/notification-service

# Uninstall
helm uninstall notification-service
```

### Verify Deployment

```bash
# Check pods
kubectl get pods -l app=notification-service

# View logs
kubectl logs -f deployment/notification-service

# Check consumer lag
kubectl exec -it kafka-0 -- kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group notification-service \
  --describe
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| KAFKA_BOOTSTRAP_SERVERS | Yes | localhost:9092 | Kafka bootstrap servers |
| KAFKA_TOPIC | Yes | reminders | Topic to consume from |
| CONSUMER_GROUP_ID | Yes | notification-service | Consumer group ID |
| DATABASE_URL | Yes | - | PostgreSQL connection string |
| VAPID_PUBLIC_KEY | Yes | - | VAPID public key for Web Push |
| VAPID_PRIVATE_KEY | Yes | - | VAPID private key for Web Push |
| VAPID_CLAIMS_EMAIL | Yes | - | Contact email for VAPID claims |
| BATCH_WINDOW_SECONDS | No | 120 | Notification batch window (seconds) |
| RATE_LIMIT_PER_USER | No | 10 | Max notifications per user per window |
| RATE_LIMIT_WINDOW_SECONDS | No | 60 | Rate limit window (seconds) |
| LOG_LEVEL | No | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |

## Database Tables

### notification_logs
Tracks all notification attempts:
```sql
CREATE TABLE notification_logs (
    id SERIAL PRIMARY KEY,
    reminder_id VARCHAR NOT NULL,
    task_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    sent_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR NOT NULL,
    error_message TEXT
);
```

### push_subscriptions
Stores user Web Push subscriptions:
```sql
CREATE TABLE push_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    endpoint VARCHAR UNIQUE NOT NULL,
    p256dh VARCHAR NOT NULL,
    auth VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    active BOOLEAN DEFAULT TRUE
);
```

### user_notification_stats
Tracks rate limiting per user:
```sql
CREATE TABLE user_notification_stats (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    notification_count INTEGER DEFAULT 0,
    window_start TIMESTAMP DEFAULT NOW()
);
```

## Monitoring

### Health Check

The service runs continuously. Monitor via:
- **Pod status:** `kubectl get pods`
- **Logs:** `kubectl logs -f pod/notification-service-xxx`
- **Kafka consumer lag:** Check consumer group lag
- **Database queries:** Check notification_logs table

### Key Metrics

- **Events processed:** Total reminder events consumed
- **Notifications sent:** Successful Web Push deliveries
- **Rate limited:** Count of rate-limited notifications
- **Failures:** Failed notification attempts
- **Consumer lag:** Kafka consumer group lag
- **Scheduled tasks:** Number of pending notifications

### Logging

The service uses structured logging with levels:
- **DEBUG:** Detailed execution trace
- **INFO:** Normal operations (event received, notification sent)
- **WARNING:** Rate limits, missing subscriptions
- **ERROR:** Processing failures, Kafka errors

## Troubleshooting

### Consumer not receiving messages

1. **Check Kafka connection:**
```bash
kubectl logs notification-service-xxx | grep "Kafka"
```

2. **Verify topic exists:**
```bash
kubectl exec -it kafka-0 -- kafka-topics \
  --bootstrap-server localhost:9092 \
  --list | grep reminders
```

3. **Check consumer group:**
```bash
kubectl exec -it kafka-0 -- kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group notification-service \
  --describe
```

### Notifications not sending

1. **Check VAPID keys are set:**
```bash
kubectl get secret notification-secrets -o yaml
```

2. **Verify push subscriptions exist:**
```sql
SELECT COUNT(*) FROM push_subscriptions WHERE active = true;
```

3. **Check notification logs:**
```sql
SELECT * FROM notification_logs ORDER BY sent_at DESC LIMIT 10;
```

### Rate limiting issues

1. **Check rate limit settings:**
```bash
kubectl describe deployment notification-service | grep RATE_LIMIT
```

2. **View rate-limited notifications:**
```sql
SELECT * FROM notification_logs WHERE status = 'rate_limited';
```

### Processing errors

**Check logs for error details:**
```bash
kubectl logs notification-service-xxx --tail=100 | grep ERROR
```

## Performance

### Resource Usage
- **CPU:** 250m (requests) / 500m (limits)
- **Memory:** 256Mi (requests) / 512Mi (limits)
- **Replicas:** 1 (stateless, can scale horizontally)

### Scaling Considerations
- Service is stateless and can scale horizontally
- Kafka consumer group enables parallel processing
- Rate limiting is per-instance (consider Redis for shared state)
- Scheduled tasks are in-memory (will be lost on pod restart)

### Optimization Tips
1. **Batch processing:** Increase batch window for high volume
2. **Prefetch:** Tune Kafka `max_poll_records`
3. **Connection pooling:** Use database connection pool
4. **Caching:** Cache push subscriptions in memory

## Related Services

- **Backend API:** Publishes reminder events to Kafka
- **Recurring Service:** Generates reminder events
- **Reminder Service:** Schedules reminders
- **Frontend:** Registers Web Push subscriptions

## Architecture Decisions

### Why aiokafka instead of kafka-python?
- Async/await support for better concurrency
- Non-blocking I/O for scheduling notifications
- Better performance for I/O-bound tasks

### Why no Dapr?
- Simple service doesn't need service mesh overhead
- Direct Kafka connection is more performant
- Fewer moving parts = easier debugging

### Why in-memory scheduling?
- Low latency for notification delivery
- Simple implementation with asyncio
- Trade-off: scheduled tasks lost on restart (acceptable for reminders)

## Future Enhancements

- [ ] Add support for email notifications
- [ ] Implement notification preferences per user
- [ ] Add retry logic for failed notifications
- [ ] Support notification templates
- [ ] Add metrics endpoint (Prometheus)
- [ ] Implement distributed rate limiting (Redis)
- [ ] Add notification history API
- [ ] Support notification grouping/digests
- [ ] Add A/B testing for notification content
- [ ] Implement notification analytics

---

**Generated by microservice-scaffolder agent**
**Version:** 1.0.0
**Last updated:** 2026-01-12
