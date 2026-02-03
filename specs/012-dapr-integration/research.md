# Research: Dapr Integration for Event-Driven Architecture

**Feature**: 012-dapr-integration
**Date**: 2026-01-18
**Status**: Complete

## Executive Summary

This document consolidates research findings for integrating Dapr (Distributed Application Runtime) into the Full-Stack Todo application. The research addresses all unknowns identified in the Technical Context and provides actionable decisions with rationale.

---

## 1. Dapr HTTP API vs SDK Decision

### Question
Should we use the Dapr HTTP APIs directly or the official Dapr Python SDK?

### Decision
**Use Dapr HTTP APIs directly via httpx**

### Rationale
- The Dapr HTTP API is stable, well-documented, and REST-based
- httpx is already a dependency in the project (used by FastAPI)
- Direct HTTP calls provide better control over error handling and retries
- No additional dependency required (Dapr Python SDK adds dapr package)
- Easier to understand and debug for team members unfamiliar with Dapr SDK

### Alternatives Considered
| Alternative | Rejected Because |
|-------------|------------------|
| Dapr Python SDK (dapr-client) | Adds dependency, abstracts away HTTP details making debugging harder |
| gRPC API | More complex setup, HTTP sufficient for our throughput requirements |

### Code Pattern
```python
import httpx

DAPR_HTTP_PORT = 3500
DAPR_BASE_URL = f"http://localhost:{DAPR_HTTP_PORT}"

async def publish_event(pubsub_name: str, topic: str, data: dict) -> bool:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{DAPR_BASE_URL}/v1.0/publish/{pubsub_name}/{topic}",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        return response.status_code in (200, 204)
```

---

## 2. Event Consumer Migration Strategy

### Question
How should we migrate from AIOKafkaConsumer to Dapr subscription endpoints?

### Decision
**Push-based subscription model with HTTP endpoints**

### Rationale
- Dapr pushes events to HTTP endpoints, eliminating consumer polling
- Simplifies consumer code (no Kafka connection management)
- Built-in retry and dead letter queue support
- Scales with pod replicas automatically via consumer groups

### Migration Approach
1. Keep existing Kafka consumers as fallback during migration
2. Add new HTTP subscription endpoints to each service
3. Register subscriptions via /dapr/subscribe endpoint
4. Configure subscriptions.yaml for topic-to-route mapping
5. Enable idempotency using event_id in each handler
6. Once validated, remove old Kafka consumer code

### Subscription Registration Pattern
```python
@app.get("/dapr/subscribe")
async def dapr_subscribe():
    return [
        {
            "pubsubname": "kafka-pubsub",
            "topic": "task-events",
            "route": "/events/tasks",
            "metadata": {
                "rawPayload": "true"
            }
        }
    ]

@app.post("/events/tasks")
async def handle_task_event(request: Request):
    cloud_event = await request.json()
    event_data = cloud_event.get("data", {})

    # Idempotency check
    event_id = event_data.get("event_id")
    if await is_event_processed(event_id):
        return {"status": "DROP"}  # Already processed

    # Process event
    await process_task_event(event_data)
    await mark_event_processed(event_id)

    return {"status": "SUCCESS"}
```

---

## 3. Conversation State Store Design

### Question
How should conversation state be structured in Dapr state store?

### Decision
**Single key per conversation with message array value**

### Rationale
- Simple key-value model: conversation-{id} -> {messages: [], metadata: {}}
- Atomic updates for entire conversation state
- Easy to retrieve full history in single call
- Supports etag-based optimistic concurrency

### State Schema
```json
{
  "key": "conversation-123",
  "value": {
    "user_id": "user456",
    "messages": [
      {"role": "user", "content": "Add task buy groceries", "timestamp": "..."},
      {"role": "assistant", "content": "Added task successfully", "timestamp": "..."}
    ],
    "context": {
      "last_tool_call": "add_task",
      "preferences": {}
    },
    "created_at": "2026-01-18T10:00:00Z",
    "updated_at": "2026-01-18T10:05:00Z"
  }
}
```

### Concurrency Handling
```python
async def update_conversation_state(conversation_id: str, new_message: dict):
    async with httpx.AsyncClient() as client:
        # Get current state with etag
        resp = await client.get(
            f"{DAPR_BASE_URL}/v1.0/state/statestore/conversation-{conversation_id}",
            headers={"Accept": "application/json"}
        )
        etag = resp.headers.get("ETag")
        current_state = resp.json() if resp.status_code == 200 else {"messages": []}

        # Append new message
        current_state["messages"].append(new_message)
        current_state["updated_at"] = datetime.utcnow().isoformat()

        # Save with etag for optimistic locking
        await client.post(
            f"{DAPR_BASE_URL}/v1.0/state/statestore",
            json=[{
                "key": f"conversation-{conversation_id}",
                "value": current_state,
                "etag": etag,
                "options": {"concurrency": "first-write-wins"}
            }]
        )
```

---

## 4. Dapr Jobs API for Scheduled Reminders

### Question
Is the Dapr Jobs API (v1.0-alpha1) stable enough for production reminders?

### Decision
**Use Dapr Jobs API with fallback to cron binding**

### Rationale
- Jobs API provides exact-time scheduling (dueTime)
- Supports job cancellation (DELETE) and rescheduling
- Alpha status is acceptable for this use case (reminders are not mission-critical)
- Cron binding available as fallback if Jobs API has issues

### Primary Pattern (Jobs API)
```python
async def schedule_reminder(task_id: int, remind_at: datetime, payload: dict):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{DAPR_BASE_URL}/v1.0-alpha1/jobs/reminder-{task_id}",
            json={
                "dueTime": remind_at.isoformat() + "Z",
                "data": {
                    "@type": "type.googleapis.com/google.protobuf.StringValue",
                    "value": json.dumps(payload)
                }
            }
        )
```

### Fallback Pattern (Cron Polling)
```python
# Triggered by Dapr cron binding every minute
@app.post("/bindings/reminder-cron")
async def check_due_reminders():
    now = datetime.utcnow()
    due_reminders = await get_reminders_due_before(now)
    for reminder in due_reminders:
        await send_notification(reminder)
        await mark_reminder_sent(reminder.id)
    return {"processed": len(due_reminders)}
```

---

## 5. Secrets Migration Strategy

### Question
How to migrate from environment variables to Kubernetes secrets via Dapr?

### Decision
**Gradual migration with environment variable fallback**

### Rationale
- Immediate breaking change would disrupt local development
- Fallback allows developers without K8s to use env vars
- Production uses Dapr secrets, development uses env vars

### Migration Approach
1. Create Kubernetes Secret resources for production:
   - app-secrets: OPENAI_API_KEY, BETTER_AUTH_SECRET, VAPID keys
   - postgres-credentials: DATABASE_URL
   - kafka-credentials: brokers, username, password
2. Update service code to try Dapr secrets first, fallback to env vars
3. Log warning when using env var fallback

### Implementation Pattern
```python
import os
import logging

async def get_secret(name: str, key: str) -> str:
    """Get secret from Dapr or fallback to environment variable."""
    # Try Dapr secrets first (only works in K8s with Dapr sidecar)
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(
                f"{DAPR_BASE_URL}/v1.0/secrets/kubernetes-secrets/{name}"
            )
            if resp.status_code == 200:
                return resp.json().get(key, "")
    except Exception:
        pass  # Dapr not available

    # Fallback to environment variable
    env_key = f"{name.upper().replace('-', '_')}_{key.upper()}"
    value = os.getenv(env_key, os.getenv(key.upper(), ""))
    if value:
        logging.warning(f"Using env var fallback for secret: {name}/{key}")
    return value
```

---

## 6. Service Invocation Patterns

### Question
When should services use Dapr service invocation vs direct HTTP calls?

### Decision
**Use Dapr service invocation for all inter-service calls in Kubernetes**

### Rationale
- Automatic service discovery (no hardcoded URLs)
- Built-in retries, timeouts, and circuit breakers
- Distributed tracing propagation
- mTLS encryption between services

### Service Naming Convention
| Service | Dapr App ID | Port |
|---------|-------------|------|
| Backend API | backend-service | 8000 |
| Notification Service | notification-service | 8001 |
| Recurring Task Service | recurring-task-service | 8002 |
| Audit Service | audit-service | 8003 |

### Invocation Pattern
```python
async def invoke_backend_service(method: str, http_method: str = "GET", data: dict = None):
    async with httpx.AsyncClient() as client:
        url = f"{DAPR_BASE_URL}/v1.0/invoke/backend-service/method/{method}"

        if http_method == "POST" and data:
            return await client.post(url, json=data)
        elif http_method == "PUT" and data:
            return await client.put(url, json=data)
        elif http_method == "DELETE":
            return await client.delete(url)
        else:
            return await client.get(url)
```

### Example: Notification Service Getting Task Details
```python
# In notification-service
async def get_task_details(user_id: str, task_id: int):
    resp = await invoke_backend_service(f"api/{user_id}/tasks/{task_id}")
    if resp.status_code == 200:
        return resp.json()
    return None
```

---

## 7. Health Checks and Resiliency

### Question
How to handle Dapr sidecar unavailability?

### Decision
**Implement health checks with graceful degradation**

### Rationale
- Sidecar startup delay can cause initial failures
- Network issues may temporarily disconnect sidecar
- Application should continue with reduced functionality

### Health Check Implementation
```python
async def check_dapr_health() -> bool:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{DAPR_BASE_URL}/v1.0/healthz")
            return resp.status_code == 204
    except Exception:
        return False

@app.get("/health")
async def health_check():
    dapr_healthy = await check_dapr_health()
    return {
        "status": "healthy" if dapr_healthy else "degraded",
        "dapr": dapr_healthy,
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Graceful Degradation
```python
async def publish_event_with_fallback(topic: str, data: dict):
    if await check_dapr_health():
        await publish_via_dapr(topic, data)
    else:
        # Fallback: log to database for later processing
        logging.warning(f"Dapr unavailable, queuing event for later: {topic}")
        await queue_event_to_database(topic, data)
```

---

## 8. Observability and Tracing

### Question
How to integrate Dapr with existing observability stack?

### Decision
**Enable Dapr tracing with Zipkin, integrate with Prometheus metrics**

### Rationale
- Dapr natively supports OpenTelemetry and Zipkin
- Prometheus metrics available at /metrics endpoint
- Consistent with existing monitoring infrastructure

### Configuration (dapr-config.yaml)
```yaml
apiVersion: dapr.io/v1alpha1
kind: Configuration
metadata:
  name: dapr-config
spec:
  tracing:
    samplingRate: "1"  # 100% in dev, reduce in prod
    zipkin:
      endpointAddress: "http://zipkin:9411/api/v2/spans"
  metrics:
    enabled: true
  logging:
    apiLogging:
      enabled: true
```

### Trace Propagation
Dapr automatically propagates trace headers (traceparent, tracestate) across service invocations and pub/sub messages. No application code changes required.

---

## 9. Local Development Setup

### Question
How to run Dapr locally for development?

### Decision
**Use Dapr CLI with local mode for development**

### Setup Commands
```bash
# Install Dapr CLI
curl -fsSL https://raw.githubusercontent.com/dapr/cli/master/install/install.sh | bash

# Initialize Dapr (local development)
dapr init

# Run application with Dapr sidecar
dapr run --app-id backend-service --app-port 8000 --dapr-http-port 3500 \
    -- uvicorn app.main:app --reload

# Alternative: Use dapr.yaml for multi-app
dapr run -f dapr.yaml
```

### Local dapr.yaml
```yaml
version: 1
apps:
  - appID: backend-service
    appDirPath: ./backend
    appPort: 8000
    command: ["uvicorn", "app.main:app", "--reload"]
  - appID: notification-service
    appDirPath: ./services/notification-service
    appPort: 8001
    command: ["uvicorn", "app.main:app", "--reload"]
```

---

## 10. Error Handling and Dead Letter Queue

### Question
How to handle failed event processing?

### Decision
**Use Dapr built-in DLQ with 3 retry attempts**

### Configuration (subscriptions.yaml)
```yaml
apiVersion: dapr.io/v2alpha1
kind: Subscription
metadata:
  name: task-events-sub
spec:
  pubsubname: kafka-pubsub
  topic: task-events
  route: /events/tasks
  deadLetterTopic: task-events-dlq
  metadata:
    maxRetries: "3"
    backOffInitialInterval: "1000"
    backOffMaxInterval: "10000"
```

### Handler Response Codes
```python
@app.post("/events/tasks")
async def handle_task_event(request: Request):
    try:
        event = await request.json()
        await process_event(event)
        return {"status": "SUCCESS"}
    except ValidationError:
        return {"status": "DROP"}  # Do not retry, move to DLQ
    except TemporaryError:
        return {"status": "RETRY"}  # Retry with backoff
    except Exception:
        logging.exception("Unexpected error processing event")
        return {"status": "RETRY"}
```

---

## Conclusion

All research questions have been resolved with clear decisions and implementation patterns. The Dapr integration approach prioritizes:

1. **Simplicity**: Direct HTTP APIs over SDK abstractions
2. **Resilience**: Fallbacks for all critical paths
3. **Observability**: Full tracing and metrics integration
4. **Developer Experience**: Local development with Dapr CLI
5. **Gradual Migration**: Coexistence with existing Kafka consumers during transition

The implementation can proceed with confidence based on these findings.
