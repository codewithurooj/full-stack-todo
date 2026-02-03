# Phase 0: Research & Technology Decisions
**Feature**: Event-Driven Architecture with Kafka
**Date**: 2026-01-12

## Overview

This document consolidates research findings and technology decisions for implementing the event-driven architecture with Kafka for the Full-Stack Todo application.

## Technology Decisions

### 1. Kafka Platform

**Decision**: Redpanda Cloud (Serverless Tier)

**Rationale**:
- **Kafka-compatible**: Drop-in replacement with full Kafka API compatibility
- **Serverless**: No infrastructure management required
- **Free Tier**: Generous free tier for development and testing
- **Performance**: Built in C++ for 10x better performance than Apache Kafka
- **Simple Setup**: Faster to get started than self-hosted Kafka/Strimzi
- **Cloud-native**: Designed for cloud deployments from the ground up

**Alternatives Considered**:
1. **Apache Kafka (Strimzi on Kubernetes)**:
   - Pros: Standard Kafka, full control, no vendor lock-in
   - Cons: Complex setup, resource-intensive (requires ZooKeeper), maintenance overhead
   - Rejected: Too complex for Phase V MVP; can migrate later if needed

2. **Confluent Cloud**:
   - Pros: Managed Kafka service, excellent tooling
   - Cons: No free tier, expensive for small projects
   - Rejected: Cost prohibitive for hackathon/demo project

3. **AWS MSK (Managed Streaming for Kafka)**:
   - Pros: Integrated with AWS ecosystem
   - Cons: AWS vendor lock-in, no free tier, complex IAM setup
   - Rejected: Not cloud-agnostic, adds AWS dependency

**Configuration**:
- Bootstrap servers: From Redpanda Cloud console
- Authentication: SASL/SCRAM-SHA-256
- Topics: task-events, reminders, task-updates
- Partitions: 12 per topic (for parallelism with 10+ consumers)
- Replication: 3 (Redpanda default)
- Retention: 7 days

### 2. Kafka Client Library (Python)

**Decision**: aiokafka

**Rationale**:
- **Async/Await**: Native async support matches FastAPI's async architecture
- **Production-Ready**: Widely used in production Python services
- **Active Maintenance**: Regular updates and bug fixes
- **Good Documentation**: Clear examples and API docs
- **Performance**: Efficient async I/O without blocking threads

**Alternatives Considered**:
1. **confluent-kafka-python**:
   - Pros: Official Confluent library, C-based for performance
   - Cons: No native async support, requires thread pools for FastAPI
   - Rejected: Sync API doesn't fit well with async FastAPI

2. **kafka-python**:
   - Pros: Pure Python, simple API
   - Cons: Not actively maintained, no async support, slower performance
   - Rejected: Lack of maintenance and async support

**Installation**:
```bash
pip install aiokafka
```

**Example Usage**:
```python
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

# Producer
producer = AIOKafkaProducer(bootstrap_servers='localhost:9092')
await producer.send('topic', b'message')

# Consumer
consumer = AIOKafkaConsumer('topic', bootstrap_servers='localhost:9092')
async for msg in consumer:
    process(msg.value)
```

### 3. Web Push Notification Library (Python)

**Decision**: pywebpush

**Rationale**:
- **Standard Protocol**: Implements Web Push Protocol (RFC 8030)
- **VAPID Support**: Voluntary Application Server Identification for security
- **Simple API**: Easy to integrate with existing Python services
- **Browser Compatibility**: Works with Chrome, Firefox, Edge, Safari

**Alternatives Considered**:
1. **Custom Implementation**:
   - Pros: Full control, no dependencies
   - Cons: Complex protocol, VAPID key management, error-prone
   - Rejected: Reinventing the wheel, too time-consuming

2. **Firebase Cloud Messaging (FCM)**:
   - Pros: Google-backed, reliable delivery
   - Cons: Google vendor lock-in, requires Firebase setup
   - Rejected: Adds unnecessary dependency, overkill for browser notifications

**Installation**:
```bash
pip install pywebpush
```

**Example Usage**:
```python
from pywebpush import webpush, WebPushException

subscription_info = {
    "endpoint": "https://fcm.googleapis.com/fcm/send/...",
    "keys": {
        "auth": "...",
        "p256dh": "..."
    }
}

try:
    webpush(
        subscription_info=subscription_info,
        data="Task reminder: Buy groceries",
        vapid_private_key="private_key",
        vapid_claims={"sub": "mailto:admin@example.com"}
    )
except WebPushException as ex:
    print(f"Notification failed: {ex}")
```

### 4. Testing Framework

**Decision**: pytest + testcontainers-python

**Rationale**:
- **pytest**: Standard Python testing framework, already used in backend
- **testcontainers-python**: Spin up real Kafka broker for integration tests
- **Isolation**: Each test gets a fresh Kafka instance, no shared state
- **CI/CD Friendly**: Works in GitHub Actions and other CI platforms

**Alternatives Considered**:
1. **Mocking Kafka**:
   - Pros: Fast tests, no containers
   - Cons: Doesn't test real Kafka behavior, misses edge cases
   - Rejected: Integration tests need real Kafka to validate event ordering, partitioning, consumer groups

2. **Embedded Kafka**:
   - Pros: Lightweight, fast startup
   - Cons: Not available for Python, JVM-only
   - Rejected: Not applicable for Python services

**Installation**:
```bash
pip install pytest pytest-asyncio testcontainers[kafka]
```

**Example Test**:
```python
import pytest
from testcontainers.kafka import KafkaContainer

@pytest.fixture
def kafka():
    with KafkaContainer() as kafka:
        yield kafka.get_bootstrap_server()

@pytest.mark.asyncio
async def test_event_publishing(kafka):
    producer = AIOKafkaProducer(bootstrap_servers=kafka)
    await producer.start()
    await producer.send('test-topic', b'test message')
    await producer.stop()
```

### 5. Consumer Group Strategy

**Decision**: Separate consumer groups per service

**Rationale**:
- **Independent Processing**: Each service processes events independently
- **Scalability**: Each service can scale horizontally within its consumer group
- **Fault Isolation**: One service failure doesn't affect others

**Configuration**:
- Recurring Task Service: Consumer group `recurring-task-service`
- Notification Service: Consumer group `notification-service`
- Audit Service: Consumer group `audit-service`

**Benefits**:
- Audit Service gets ALL events (full audit trail)
- Recurring Task Service filters to task.completed events only
- Each service maintains its own offset, can replay independently

### 6. Idempotency Strategy

**Decision**: Database unique constraints on idempotency keys

**Rationale**:
- **At-Least-Once Delivery**: Kafka guarantees at-least-once, so duplicates possible
- **Database Constraints**: PostgreSQL UNIQUE constraints enforce idempotency
- **Automatic Deduplication**: Duplicate inserts fail gracefully with constraint violation
- **No External State**: No Redis or separate deduplication cache needed

**Implementation**:
```sql
-- Recurring Task Service: Prevent duplicate instance creation
CREATE UNIQUE INDEX idx_recurring_instance_dedup
ON tasks(parent_task_id, due_date)
WHERE recurring != 'none';

-- Notification Service: Prevent duplicate notifications
CREATE UNIQUE INDEX idx_reminder_dedup
ON reminders(task_id, remind_at);

-- Audit Service: Prevent duplicate log entries
CREATE UNIQUE INDEX idx_audit_event_id
ON audit_logs(event_id);
```

**Error Handling**:
```python
try:
    session.add(new_task_instance)
    session.commit()
except IntegrityError:
    # Duplicate detected, idempotency working correctly
    logger.info(f"Duplicate event {event_id}, skipping")
    session.rollback()
```

### 7. Event Ordering Strategy

**Decision**: Partition by user_id

**Rationale**:
- **Per-User Ordering**: Events for the same user processed in order
- **Parallelism**: Events for different users processed in parallel
- **Scalability**: Multiple consumers process different partitions

**Configuration**:
```python
# Producer: Always use user_id as partition key
await producer.send(
    'task-events',
    key=str(user_id).encode('utf-8'),
    value=event_data
)

# Consumer: Process messages from assigned partitions in order
async for msg in consumer:
    # msg.partition, msg.offset guarantee ordering within partition
    process_event(msg.value)
```

**Tradeoffs**:
- **Hotspot Risk**: Users with high activity may overload a single partition
- **Mitigation**: 12 partitions spread load; monitor partition lag

### 8. Error Handling & Dead Letter Queue

**Decision**: Exponential backoff + DLQ topic

**Rationale**:
- **Transient Failures**: Retry with exponential backoff (1s, 2s, 4s, 8s, 16s, max 60s)
- **Persistent Failures**: After 3 retries, send to dead letter queue for manual review
- **Service Availability**: Don't block consumer on unrecoverable errors

**Implementation**:
```python
async def process_event(event):
    retries = 0
    max_retries = 3
    backoff = 1

    while retries < max_retries:
        try:
            await handle_event(event)
            return  # Success
        except TransientError as e:
            retries += 1
            logger.warn(f"Retry {retries}/{max_retries}: {e}")
            await asyncio.sleep(backoff)
            backoff *= 2
        except PersistentError as e:
            logger.error(f"Unrecoverable error: {e}")
            await send_to_dlq(event, error=str(e))
            return

    # Max retries exceeded
    await send_to_dlq(event, error="Max retries exceeded")
```

**DLQ Topic**:
- Topic name: `dlq-task-events`
- Schema: `{original_event, error_message, retry_count, timestamp}`
- Monitoring: Alert when DLQ depth > 10 messages

### 9. Monitoring Strategy

**Decision**: Prometheus metrics + Grafana dashboards

**Rationale**:
- **Industry Standard**: Prometheus is standard for Kubernetes monitoring
- **Rich Ecosystem**: Pre-built exporters and dashboards
- **Pull Model**: Prometheus scrapes metrics from services
- **Alerting**: Prometheus Alertmanager for threshold alerts

**Metrics to Expose**:
```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Counters
events_consumed = Counter('events_consumed_total', 'Total events consumed', ['service', 'topic', 'event_type'])
events_produced = Counter('events_produced_total', 'Total events produced', ['service', 'topic'])
errors_total = Counter('errors_total', 'Total errors', ['service', 'error_type'])

# Histograms
event_processing_duration = Histogram('event_processing_duration_seconds', 'Event processing duration')
event_latency = Histogram('event_latency_seconds', 'Time from event publish to consumption')

# Gauges
consumer_lag = Gauge('consumer_lag_messages', 'Consumer lag in messages', ['service', 'topic', 'partition'])
active_consumers = Gauge('active_consumers', 'Number of active consumers', ['service'])
```

**Grafana Dashboards**:
- Events/minute per topic
- Consumer lag per service
- Event latency (p50, p95, p99)
- Error rate per service
- Notification delivery success rate

### 10. Local Development Setup

**Decision**: Docker Compose with Redpanda

**Rationale**:
- **Fast Startup**: Redpanda starts in seconds vs minutes for Kafka+ZooKeeper
- **Single Container**: No ZooKeeper dependency
- **Kafka-Compatible**: Works with same client libraries
- **Resource Efficient**: Lower memory footprint than Kafka

**docker-compose-kafka.yml**:
```yaml
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

  recurring-task-service:
    build: ./services/recurring-task-service
    depends_on:
      - redpanda
    environment:
      KAFKA_BOOTSTRAP_SERVERS: redpanda:9092
      DATABASE_URL: ${DATABASE_URL}

  notification-service:
    build: ./services/notification-service
    depends_on:
      - redpanda
    environment:
      KAFKA_BOOTSTRAP_SERVERS: redpanda:9092
      DATABASE_URL: ${DATABASE_URL}

  audit-service:
    build: ./services/audit-service
    depends_on:
      - redpanda
    environment:
      KAFKA_BOOTSTRAP_SERVERS: redpanda:9092
      DATABASE_URL: ${DATABASE_URL}
```

**Usage**:
```bash
docker-compose -f docker-compose-kafka.yml up -d
# Services available at localhost:19092
docker-compose -f docker-compose-kafka.yml logs -f recurring-task-service
```

## Best Practices

### Event Schema Design

1. **Versioning**: Include schema_version in all events
2. **Timestamps**: Always UTC in ISO 8601 format
3. **IDs**: Use UUIDs for event_id (idempotency), integers for task_id/user_id
4. **Backward Compatibility**: Add new fields as optional, never remove fields
5. **Event Types**: Use dot notation (task.created, task.updated, task.completed)

### Consumer Best Practices

1. **Commit After Processing**: Only commit offset after successful database write
2. **Batch Processing**: Process multiple events before committing for efficiency
3. **Graceful Shutdown**: Handle SIGTERM to commit offsets before exit
4. **Health Checks**: Expose /health endpoint, check Kafka connectivity
5. **Structured Logging**: Log event_id, user_id, task_id for correlation

### Security Best Practices

1. **SASL Authentication**: Always use SASL/SCRAM for Kafka authentication
2. **TLS Encryption**: Enable SSL for data in transit
3. **Secrets Management**: Store Kafka credentials in Kubernetes secrets
4. **IAM Policies**: Restrict topic access per service (if using cloud provider IAM)
5. **Network Policies**: Isolate Kafka cluster in private subnet

## Summary

All technology decisions resolved. No NEEDS CLARIFICATION items remaining. Ready to proceed to Phase 1 (data modeling and contracts).

**Key Technologies**:
- Kafka Platform: Redpanda Cloud
- Python Client: aiokafka
- Web Push: pywebpush
- Testing: pytest + testcontainers-python
- Monitoring: Prometheus + Grafana
- Local Dev: Docker Compose + Redpanda

**Next Steps**:
1. Create data-model.md with event schemas and audit log schema
2. Generate event schema contracts (JSON Schema or OpenAPI)
3. Create quickstart.md for local development setup
4. Run /sp.tasks to break down implementation tasks
