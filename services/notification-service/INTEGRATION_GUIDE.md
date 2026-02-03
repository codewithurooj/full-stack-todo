# Notification Service - Integration Guide

This guide explains how the Notification Service integrates with the rest of the todo application system.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                       │
│  - Register Web Push subscriptions                          │
│  - Display notifications                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ HTTPS
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend API (FastAPI)                      │
│  - Create/update tasks                                       │
│  - Manage push subscriptions                                │
│  - Publish reminder events to Kafka                         │
└──────────────┬──────────────────┬───────────────────────────┘
               │                  │
               │ PostgreSQL       │ Kafka
               ▼                  ▼
┌─────────────────┐    ┌──────────────────┐
│   PostgreSQL    │    │      Kafka       │
│   - Tasks       │    │  Topic: reminders│
│   - Users       │    └────────┬─────────┘
│   - Subscr.     │             │
└─────────────────┘             │ Consume
                                ▼
                     ┌──────────────────────┐
                     │ Notification Service │
                     │  - Schedule notifs   │
                     │  - Rate limiting     │
                     │  - Send Web Push     │
                     └──────────┬───────────┘
                                │
                                │ Web Push
                                ▼
                     ┌──────────────────────┐
                     │   User Browsers      │
                     │  - Service Workers   │
                     │  - Push Notifications│
                     └──────────────────────┘
```

## Integration Points

### 1. Backend API → Kafka

**When:** User creates/updates a task with a reminder

**Backend publishes event:**
```python
# backend/app/routes/tasks.py
from kafka import KafkaProducer
import json
from datetime import datetime

producer = KafkaProducer(
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def publish_reminder_event(task, reminder_time):
    """Publish reminder event to Kafka"""
    event = {
        "event_id": str(uuid.uuid4()),
        "schema_version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "reminder_id": f"reminder-{task.id}-{reminder_time.isoformat()}",
        "task_id": task.id,
        "user_id": task.user_id,
        "title": task.title,
        "remind_at": reminder_time.isoformat() + "Z",
        "due_date": task.due_date.isoformat() + "Z" if task.due_date else None
    }

    producer.send('reminders', value=event)
    producer.flush()
```

**Example usage:**
```python
@router.post("/tasks")
def create_task(task: TaskCreate, user_id: int):
    # Create task in database
    new_task = Task(**task.dict(), user_id=user_id)
    db.add(new_task)
    db.commit()

    # If task has reminder, publish event
    if task.reminder_time:
        publish_reminder_event(new_task, task.reminder_time)

    return new_task
```

### 2. Backend API → PostgreSQL

**Push Subscription Management:**

```python
# backend/app/routes/push.py
from fastapi import APIRouter, Depends
from app.models import PushSubscription

router = APIRouter()

@router.post("/push/subscribe")
def subscribe_push(
    subscription: dict,
    user_id: int = Depends(get_current_user)
):
    """Register Web Push subscription for user"""
    sub = PushSubscription(
        user_id=user_id,
        endpoint=subscription['endpoint'],
        p256dh=subscription['keys']['p256dh'],
        auth=subscription['keys']['auth']
    )
    db.add(sub)
    db.commit()
    return {"message": "Subscribed to push notifications"}

@router.delete("/push/unsubscribe")
def unsubscribe_push(endpoint: str, user_id: int = Depends(get_current_user)):
    """Unsubscribe from Web Push"""
    sub = db.query(PushSubscription).filter(
        PushSubscription.user_id == user_id,
        PushSubscription.endpoint == endpoint
    ).first()

    if sub:
        sub.active = False
        db.commit()

    return {"message": "Unsubscribed"}
```

### 3. Frontend → Backend API

**Register Service Worker and Subscribe:**

```typescript
// frontend/lib/push-notifications.ts
export async function subscribeUserToPush() {
  // Register service worker
  const registration = await navigator.serviceWorker.register('/service-worker.js');

  // Request notification permission
  const permission = await Notification.requestPermission();
  if (permission !== 'granted') {
    throw new Error('Notification permission denied');
  }

  // Subscribe to push
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY!)
  });

  // Send subscription to backend
  await fetch('/api/push/subscribe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(subscription.toJSON())
  });

  return subscription;
}
```

**Service Worker:**
```javascript
// frontend/public/service-worker.js
self.addEventListener('push', function(event) {
  const data = event.data.json();

  const options = {
    body: data.body,
    icon: '/icon-192.png',
    badge: '/badge-72.png',
    data: data.data,
    actions: [
      { action: 'view', title: 'View Task' },
      { action: 'dismiss', title: 'Dismiss' }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();

  if (event.action === 'view') {
    const taskId = event.notification.data.task_id;
    event.waitUntil(
      clients.openWindow(`/tasks/${taskId}`)
    );
  }
});
```

### 4. Notification Service → PostgreSQL

**The service uses database for:**

1. **Read push subscriptions:**
```python
subscriptions = db.query(PushSubscription).filter(
    PushSubscription.user_id == user_id,
    PushSubscription.active == True
).all()
```

2. **Log notifications:**
```python
log = NotificationLog(
    reminder_id=reminder_id,
    task_id=task_id,
    user_id=user_id,
    status='sent'
)
db.add(log)
db.commit()
```

3. **Mark task reminded:**
```python
task = db.query(Task).get(task_id)
task.reminded = True
db.commit()
```

## Database Setup

### Required Tables

Run this SQL migration:

```sql
-- Add reminded column to tasks table
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS reminded BOOLEAN DEFAULT FALSE;

-- Create notification tables
CREATE TABLE notification_logs (...);
CREATE TABLE push_subscriptions (...);
CREATE TABLE user_notification_stats (...);
```

See `migrations/001_create_tables.sql` for complete schema.

### Backend Models Update

Add to your backend models:

```python
# backend/app/models/task.py
from sqlmodel import Field, SQLModel

class Task(SQLModel, table=True):
    id: int = Field(primary_key=True)
    user_id: int
    title: str
    # ... other fields ...
    reminded: bool = Field(default=False)  # Add this field
```

## Kafka Setup

### Topic Creation

Create the `reminders` topic:

```bash
# Using kafka-topics
kafka-topics --bootstrap-server localhost:9092 \
  --create \
  --topic reminders \
  --partitions 3 \
  --replication-factor 1

# Or using Redpanda
rpk topic create reminders --partitions 3
```

### Producer Configuration

In your backend:

```python
# backend/app/config.py
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# backend/app/main.py
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Make producer available in routes
app.state.kafka_producer = producer
```

## VAPID Keys Setup

### 1. Generate Keys

```bash
cd services/notification-service
python -c "from pywebpush import generate_vapid_keys; print(generate_vapid_keys())"
```

### 2. Configure Backend

Add to backend `.env`:
```env
VAPID_PUBLIC_KEY=your-public-key
VAPID_PRIVATE_KEY=your-private-key
```

### 3. Configure Frontend

Add to frontend `.env.local`:
```env
NEXT_PUBLIC_VAPID_PUBLIC_KEY=your-public-key
```

### 4. Configure Notification Service

Add to notification service `.env`:
```env
VAPID_PUBLIC_KEY=your-public-key
VAPID_PRIVATE_KEY=your-private-key
VAPID_CLAIMS_EMAIL=mailto:admin@yourdomain.com
```

**Important:** Use the SAME VAPID keys across all services!

## Deployment Order

### 1. Infrastructure
```bash
# PostgreSQL (already running)
# Kafka
helm install kafka bitnami/kafka

# Or Redpanda
helm install redpanda redpanda/redpanda
```

### 2. Create Kafka Topic
```bash
kubectl exec -it kafka-0 -- kafka-topics \
  --bootstrap-server localhost:9092 \
  --create --topic reminders \
  --partitions 3 --replication-factor 1
```

### 3. Database Migration
```bash
# From backend
kubectl exec -it backend-pod -- \
  psql $DATABASE_URL -f /app/migrations/add_reminded_column.sql

# From notification service
kubectl exec -it backend-pod -- \
  psql $DATABASE_URL -f services/notification-service/migrations/001_create_tables.sql
```

### 4. Backend API
```bash
# Deploy backend with Kafka producer
helm upgrade backend ./charts/backend
```

### 5. Notification Service
```bash
# Create secrets
kubectl create secret generic vapid-secret \
  --from-literal=VAPID_PUBLIC_KEY=... \
  --from-literal=VAPID_PRIVATE_KEY=...

# Deploy service
helm install notification-service ./charts/notification-service
```

### 6. Frontend
```bash
# Build with VAPID public key
NEXT_PUBLIC_VAPID_PUBLIC_KEY=... npm run build

# Deploy
vercel deploy --prod
```

## Testing Integration

### 1. Test Push Subscription

```bash
# Frontend console
await subscribeUserToPush();
```

Check backend logs for subscription creation.

### 2. Test Reminder Event

Create task with reminder via frontend or API:

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test task",
    "reminder_time": "2026-01-12T12:00:00Z"
  }'
```

### 3. Verify Kafka Event

```bash
# Check topic
kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic reminders \
  --from-beginning
```

### 4. Check Service Logs

```bash
kubectl logs -f deployment/notification-service
```

Should see:
```
INFO - Received reminder event: reminder-123-...
INFO - Scheduling notification for reminder reminder-123-...
INFO - Sending notification for reminder reminder-123-...
INFO - Notification sent successfully
```

### 5. Verify Notification

- Check browser for notification
- Check `notification_logs` table
- Check `tasks` table for `reminded=true`

## Monitoring Integration

### Metrics to Track

1. **Backend:**
   - Reminder events published
   - Push subscription registrations
   - API latency for task creation

2. **Notification Service:**
   - Events consumed
   - Notifications sent
   - Rate-limited notifications
   - Consumer lag

3. **Frontend:**
   - Subscription success rate
   - Notification click-through rate

### Logging Correlation

Use correlation IDs across services:

```python
# Backend
event_id = str(uuid.uuid4())
logger.info(f"Publishing reminder event {event_id}")

# Notification Service
logger.info(f"Processing event {event['event_id']}")
```

## Troubleshooting Integration

### Issue: Notifications not received

**Check:**
1. Push subscription exists in database
2. Reminder event published to Kafka
3. Notification service consuming events
4. VAPID keys match across services
5. Service worker registered in browser

### Issue: Events not consumed

**Check:**
1. Kafka topic exists and has messages
2. Consumer group is correct
3. Network connectivity to Kafka
4. Consumer not lagging

### Issue: Database errors

**Check:**
1. Migration ran successfully
2. Database connection string correct
3. Tables exist: `notification_logs`, `push_subscriptions`
4. `tasks` table has `reminded` column

### Issue: VAPID errors

**Check:**
1. Same VAPID keys in all services
2. Keys properly base64 encoded
3. Claims email set correctly

## Security Considerations

### 1. VAPID Keys
- Store as Kubernetes secrets
- Never commit to git
- Rotate periodically

### 2. Push Subscriptions
- Validate user owns subscription
- Clean up inactive subscriptions
- Rate limit subscription creation

### 3. Kafka
- Use authentication in production
- Enable SSL/TLS
- Restrict topic access

### 4. Database
- Use connection pooling
- Prepared statements (SQLModel handles this)
- Encrypt sensitive data

## Performance Optimization

### 1. Backend
- Batch Kafka publishes
- Async event publishing
- Cache user preferences

### 2. Notification Service
- Tune batch window
- Adjust rate limits
- Scale replicas

### 3. Database
- Index user_id in push_subscriptions
- Partition notification_logs by date
- Clean old logs periodically

## Next Steps

After integration:

1. **Test end-to-end flow**
2. **Monitor metrics**
3. **Set up alerts**
4. **Load test**
5. **Document runbooks**

## Resources

- [Web Push Protocol](https://tools.ietf.org/html/rfc8030)
- [VAPID Spec](https://tools.ietf.org/html/rfc8292)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [Push API](https://developer.mozilla.org/en-US/docs/Web/API/Push_API)
- [Kafka Documentation](https://kafka.apache.org/documentation/)

---

**Need help?** Review the main [README.md](README.md) or [QUICKSTART.md](QUICKSTART.md)
