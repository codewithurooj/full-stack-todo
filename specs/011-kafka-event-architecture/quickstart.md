# Quickstart: Event-Driven Architecture with Kafka

**Feature**: 011-kafka-event-architecture
**Date**: 2026-01-12

## Prerequisites

- Docker Desktop 4.53+ with Docker Compose
- Python 3.13+
- Node.js 20+ (optional, for WebSocket service)
- PostgreSQL (Neon or local)
- Git

## Local Development Setup

### 1. Start Kafka Locally (Redpanda)

```bash
# Create docker-compose-kafka.yml
cat > docker-compose-kafka.yml <<EOF
version: '3.8'
services:
  redpanda:
    image: docker.redpanda.com/vectorized/redpanda:latest
    command:
      - redpanda start
      - --smp 1
      - --overprovisioned
      - --kafka-addr internal://0.0.0.0:9092,external://0.0.0.0:19092
      - --advertise-kafka-addr internal://redpanda:9092,external://localhost:19092
    ports:
      - 19092:19092  # Kafka API
      - 9644:9644    # Admin API
    networks:
      - kafka-net

networks:
  kafka-net:
    driver: bridge
EOF

# Start Redpanda
docker-compose -f docker-compose-kafka.yml up -d

# Verify Kafka is running
docker-compose -f docker-compose-kafka.yml ps

# Check Kafka topics (initially empty)
docker exec -it <container-id> rpk topic list
```

### 2. Create Kafka Topics

```bash
# Create task-events topic (12 partitions)
docker exec -it <redpanda-container-id> rpk topic create task-events --partitions 12 --replicas 1

# Create reminders topic (12 partitions)
docker exec -it <redpanda-container-id> rpk topic create reminders --partitions 12 --replicas 1

# Create task-updates topic (12 partitions, optional)
docker exec -it <redpanda-container-id> rpk topic create task-updates --partitions 12 --replicas 1

# Verify topics created
docker exec -it <redpanda-container-id> rpk topic list
```

### 3. Setup Recurring Task Service

```bash
# Create service directory
mkdir -p services/recurring-task-service/src
cd services/recurring-task-service

# Create requirements.txt
cat > requirements.txt <<EOF
aiokafka==0.10.0
sqlmodel==0.0.14
asyncpg==0.29.0
pydantic==2.5.0
python-dotenv==1.0.0
EOF

# Install dependencies
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
cat > .env <<EOF
KAFKA_BOOTSTRAP_SERVERS=localhost:19092
DATABASE_URL=postgresql://user:pass@host.neon.tech/dbname
CONSUMER_GROUP=recurring-task-service
EOF

# Create main.py (consumer skeleton)
cat > src/main.py <<'EOF'
import asyncio
from aiokafka import AIOKafkaConsumer
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def consume():
    consumer = AIOKafkaConsumer(
        'task-events',
        bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
        group_id=os.getenv('CONSUMER_GROUP'),
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    await consumer.start()
    try:
        async for msg in consumer:
            event = msg.value
            if event['event_type'] == 'task.completed':
                await handle_completed_task(event)
    finally:
        await consumer.stop()

async def handle_completed_task(event):
    task_data = event['task_data']
    if task_data.get('recurring') and task_data['recurring'] != 'none':
        print(f"Creating next occurrence for task {task_data['id']}")
        # TODO: Calculate next due_date and create new task instance

if __name__ == '__main__':
    asyncio.run(consume())
EOF

# Run the service
python src/main.py
```

### 4. Setup Notification Service

```bash
# Create service directory
mkdir -p services/notification-service/src
cd services/notification-service

# Create requirements.txt
cat > requirements.txt <<EOF
aiokafka==0.10.0
pywebpush==1.14.0
sqlmodel==0.0.14
asyncpg==0.29.0
python-dotenv==1.0.0
EOF

# Install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file
cat > .env <<EOF
KAFKA_BOOTSTRAP_SERVERS=localhost:19092
DATABASE_URL=postgresql://user:pass@host.neon.tech/dbname
CONSUMER_GROUP=notification-service
VAPID_PRIVATE_KEY=your-vapid-private-key
VAPID_PUBLIC_KEY=your-vapid-public-key
EOF

# Create main.py (consumer skeleton)
cat > src/main.py <<'EOF'
import asyncio
from aiokafka import AIOKafkaConsumer
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def consume():
    consumer = AIOKafkaConsumer(
        'reminders',
        bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
        group_id=os.getenv('CONSUMER_GROUP'),
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    await consumer.start()
    try:
        async for msg in consumer:
            event = msg.value
            await schedule_notification(event)
    finally:
        await consumer.stop()

async def schedule_notification(event):
    print(f"Scheduling notification for task {event['task_id']} at {event['remind_at']}")
    # TODO: Schedule Web Push notification

if __name__ == '__main__':
    asyncio.run(consume())
EOF

# Run the service
python src/main.py
```

### 5. Setup Audit Service

```bash
# Create service directory
mkdir -p services/audit-service/src
cd services/audit-service

# Create requirements.txt (same as recurring-task-service)
cat > requirements.txt <<EOF
aiokafka==0.10.0
sqlmodel==0.0.14
asyncpg==0.29.0
python-dotenv==1.0.0
EOF

# Install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file
cat > .env <<EOF
KAFKA_BOOTSTRAP_SERVERS=localhost:19092
DATABASE_URL=postgresql://user:pass@host.neon.tech/dbname
CONSUMER_GROUP=audit-service
EOF

# Create main.py (consumer skeleton)
cat > src/main.py <<'EOF'
import asyncio
from aiokafka import AIOKafkaConsumer
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def consume():
    consumer = AIOKafkaConsumer(
        'task-events',
        bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
        group_id=os.getenv('CONSUMER_GROUP'),
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    await consumer.start()
    try:
        async for msg in consumer:
            event = msg.value
            await log_event(event)
    finally:
        await consumer.stop()

async def log_event(event):
    print(f"Logging event: {event['event_type']} for task {event['task_id']}")
    # TODO: Insert into audit_logs table

if __name__ == '__main__':
    asyncio.run(consume())
EOF

# Run the service
python src/main.py
```

### 6. Update Backend API (Event Publishing)

```bash
cd backend

# Add Kafka producer to requirements.txt
echo "aiokafka==0.10.0" >> requirements.txt
pip install aiokafka

# Create kafka producer service
cat > app/services/kafka_producer.py <<'EOF'
from aiokafka import AIOKafkaProducer
import json
import os

producer = None

async def start_producer():
    global producer
    producer = AIOKafkaProducer(
        bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:19092'),
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None
    )
    await producer.start()

async def stop_producer():
    if producer:
        await producer.stop()

async def publish_event(topic: str, event: dict, key: str = None):
    await producer.send_and_wait(topic, value=event, key=key)
EOF

# Update main.py to initialize producer
# Add to startup event:
@app.on_event("startup")
async def startup():
    await kafka_producer.start_producer()

@app.on_event("shutdown")
async def shutdown():
    await kafka_producer.stop_producer()
```

### 7. Test End-to-End Flow

```bash
# Terminal 1: Start Kafka
docker-compose -f docker-compose-kafka.yml up

# Terminal 2: Start Recurring Task Service
cd services/recurring-task-service
python src/main.py

# Terminal 3: Start Notification Service
cd services/notification-service
python src/main.py

# Terminal 4: Start Audit Service
cd services/audit-service
python src/main.py

# Terminal 5: Start Backend API
cd backend
uvicorn app.main:app --reload

# Terminal 6: Test with curl
# Create a recurring task
curl -X POST http://localhost:8000/api/1/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Weekly report", "recurring": "weekly", "due_date": "2026-01-19T09:00:00Z"}'

# Complete the task (should trigger recurring instance creation)
curl -X PATCH http://localhost:8000/api/1/tasks/123/complete

# Check consumer logs for event processing
# Check database for new task instance
```

## Monitoring

### Check Kafka Topics

```bash
# List topics
docker exec -it <redpanda-container-id> rpk topic list

# Describe topic
docker exec -it <redpanda-container-id> rpk topic describe task-events

# Check consumer groups
docker exec -it <redpanda-container-id> rpk group list

# Check consumer lag
docker exec -it <redpanda-container-id> rpk group describe recurring-task-service
```

### Check Consumer Logs

```bash
# Follow logs for each service
tail -f services/recurring-task-service/logs/consumer.log
tail -f services/notification-service/logs/consumer.log
tail -f services/audit-service/logs/consumer.log
```

## Cloud Deployment (Redpanda Cloud)

### 1. Create Redpanda Cloud Account

1. Go to https://redpanda.com/cloud
2. Sign up for free account
3. Create Serverless cluster
4. Note bootstrap servers URL and credentials

### 2. Create Topics

```bash
# Install rpk CLI
brew install redpanda-data/tap/redpanda  # macOS
# or download from https://github.com/redpanda-data/redpanda/releases

# Configure connection
rpk cloud login

# Create topics
rpk topic create task-events --partitions 12
rpk topic create reminders --partitions 12
rpk topic create task-updates --partitions 12
```

### 3. Update Environment Variables

```bash
# Update .env files for all services
KAFKA_BOOTSTRAP_SERVERS=<bootstrap-url-from-redpanda-cloud>
KAFKA_SASL_USERNAME=<username-from-redpanda-cloud>
KAFKA_SASL_PASSWORD=<password-from-redpanda-cloud>
KAFKA_SECURITY_PROTOCOL=SASL_SSL
KAFKA_SASL_MECHANISM=SCRAM-SHA-256
```

### 4. Deploy to Kubernetes

```bash
# Build Docker images
docker build -t recurring-task-service:latest ./services/recurring-task-service
docker build -t notification-service:latest ./services/notification-service
docker build -t audit-service:latest ./services/audit-service

# Push to registry
docker tag recurring-task-service:latest your-registry/recurring-task-service:latest
docker push your-registry/recurring-task-service:latest
# Repeat for other services

# Deploy with Helm
helm install recurring-task-service ./charts/recurring-task-service \
  --set kafka.bootstrapServers=$KAFKA_BOOTSTRAP_SERVERS \
  --set kafka.username=$KAFKA_SASL_USERNAME \
  --set kafka.password=$KAFKA_SASL_PASSWORD

# Verify deployment
kubectl get pods
kubectl logs -f deployment/recurring-task-service
```

## Troubleshooting

### Kafka Connection Issues

```bash
# Test Kafka connectivity
docker exec -it <redpanda-container-id> rpk cluster info

# Check if topics exist
docker exec -it <redpanda-container-id> rpk topic list

# Check consumer group status
docker exec -it <redpanda-container-id> rpk group describe recurring-task-service
```

### Consumer Lag

```bash
# Monitor consumer lag
docker exec -it <redpanda-container-id> rpk group describe recurring-task-service

# If lag is high, scale consumers
kubectl scale deployment recurring-task-service --replicas=3
```

### Event Not Consumed

1. Check consumer is running: `ps aux | grep python`
2. Check consumer logs for errors
3. Verify topic exists and has messages
4. Check consumer group assignment

## Next Steps

1. Implement full business logic in each service
2. Add error handling and retry logic
3. Add monitoring (Prometheus metrics)
4. Add health check endpoints
5. Write integration tests
6. Deploy to Kubernetes

## References

- Redpanda Quickstart: https://docs.redpanda.com/docs/get-started/quick-start/
- aiokafka Documentation: https://aiokafka.readthedocs.io/
- Web Push Protocol: https://developer.mozilla.org/en-US/docs/Web/API/Push_API
- Kafka Best Practices: https://kafka.apache.org/documentation/#bestpractices
