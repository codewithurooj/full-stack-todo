# Implementation Plan: Dapr Integration for Event-Driven Architecture

**Branch**: `012-dapr-integration` | **Date**: 2026-01-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/012-dapr-integration/spec.md`

**Note**: This plan replaces direct Kafka calls with Dapr HTTP APIs, enabling vendor-neutral event streaming, state management, job scheduling, and service invocation across all microservices.

## Summary

Integrate Dapr runtime with 5 components (kafka-pubsub, statestore, dapr-jobs, kubernetes-secrets, service invocation) to abstract infrastructure dependencies from application code. This migration replaces direct AIOKafkaProducer/Consumer calls with Dapr HTTP APIs, adds conversation state persistence via Dapr state store, implements scheduled reminders via Dapr Jobs API, centralizes secrets management via Kubernetes secrets component, and enables service-to-service communication via Dapr service invocation. The goal is portable, cloud-native event-driven architecture with built-in resiliency, observability, and simplified operations.

## Technical Context

**Language/Version**: Python 3.13+ (backend, microservices), TypeScript (frontend)
**Primary Dependencies**: FastAPI 0.100+, Dapr SDK (dapr 1.14+), httpx (for Dapr HTTP calls), SQLModel 0.0.8+, Pydantic 2.0+
**Storage**: Neon PostgreSQL (primary), Dapr State Store (conversation state), Kafka/Redpanda (event streaming)
**Testing**: pytest, pytest-asyncio, pytest-cov
**Target Platform**: Kubernetes (Minikube local, cloud AKS/GKE/OKE production)
**Project Type**: Web application (monorepo with backend, frontend, microservices)
**Performance Goals**: <100ms event publish (P99), <50ms state retrieval (P99), 1000 events/sec throughput
**Constraints**: Zero hardcoded URLs, 99.9% event delivery, <2s startup overhead from Dapr
**Scale/Scope**: 4 services (backend + 3 microservices), 5 Dapr components, 3 Kafka topics

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Spec-Driven Development | PASS | Specification exists at spec.md, contracts defined |
| II. Architecture (Phase V) | PASS | Dapr + Kafka + microservices aligns with constitution |
| III. RESTful API Design | PASS | Dapr HTTP APIs follow REST patterns |
| IV. Data Management | PASS | State store uses PostgreSQL backend |
| V. Testing | PENDING | Must add Dapr integration tests |
| VI. Code Quality | PASS | Using typed Python, environment configs |
| VII. Documentation | PASS | Will generate quickstart.md |
| X. Event-Driven Architecture | PASS | Dapr abstracts Kafka, adds resiliency |
| XI. Cloud-Native Deployment | PASS | Dapr sidecar injection for K8s |
| XII. Microservices | PASS | 5 Dapr components as specified |

**Gate Evaluation**: All gates PASS. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/012-dapr-integration/
├── spec.md              # Feature specification (exists)
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Dapr component YAML files (exist)
│   ├── kafka-pubsub.yaml
│   ├── statestore.yaml
│   ├── dapr-jobs.yaml
│   ├── kubernetes-secrets.yaml
│   ├── subscriptions.yaml
│   ├── resiliency.yaml
│   └── dapr-config.yaml
└── tasks.md             # Phase 2 output (/sp.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py                    # FastAPI app (modify startup)
│   ├── config.py                  # Add Dapr config options
│   ├── services/
│   │   ├── kafka_producer.py      # DEPRECATED - replace with dapr_client
│   │   ├── event_publisher.py     # MODIFY - use Dapr pub/sub
│   │   ├── dapr_client.py         # NEW - Dapr HTTP client wrapper
│   │   ├── dapr_state.py          # NEW - State store operations
│   │   └── dapr_secrets.py        # NEW - Secrets retrieval
│   └── routes/
│       ├── tasks.py               # Modify to use Dapr event publish
│       └── dapr_subscriptions.py  # NEW - Subscription endpoints
└── tests/
    └── test_dapr_integration.py   # NEW - Dapr integration tests

services/
├── notification-service/
│   ├── app/
│   │   ├── consumer.py            # MODIFY - Dapr subscription handler
│   │   ├── dapr_client.py         # NEW - Service invocation client
│   │   └── routes.py              # NEW - /events/reminders endpoint
│   └── Dockerfile                 # Add Dapr annotations
│
├── recurring-task-service/
│   ├── src/
│   │   ├── consumer.py            # MODIFY - Dapr subscription handler
│   │   └── routes.py              # NEW - /events/tasks endpoint
│   └── Dockerfile
│
└── audit-service/
    ├── src/
    │   ├── consumer.py            # MODIFY - Dapr subscription handler
    │   └── routes.py              # NEW - /events/tasks endpoint
    └── Dockerfile

dapr-components/                   # NEW - Deploy to K8s
├── kafka-pubsub.yaml
├── statestore.yaml
├── dapr-jobs.yaml
├── kubernetes-secrets.yaml
├── subscriptions.yaml
├── resiliency.yaml
└── config.yaml

charts/
├── backend/
│   └── templates/
│       └── deployment.yaml        # Add Dapr annotations
├── notification-service/
│   └── templates/
│       └── deployment.yaml        # Add Dapr annotations
├── recurring-task-service/
│   └── templates/
│       └── deployment.yaml        # Add Dapr annotations
└── audit-service/
    └── templates/
        └── deployment.yaml        # Add Dapr annotations
```

**Structure Decision**: Web application monorepo with existing backend, frontend, and services directories. Dapr components stored in `/dapr-components/` at repo root for centralized deployment.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 4+ services | Required by spec (backend + 3 microservices) | Monolith insufficient for event-driven patterns |
| Dapr abstraction layer | Spec mandates 5 Dapr components | Direct Kafka sufficient but not cloud-portable |
| Multiple config components | Resiliency, tracing, security configs | Single config harder to manage in production |

---

## Phase V: Event-Driven & Cloud-Native Architecture

### Kafka Event Architecture

**Topics in Use**:

| Topic | Producer | Consumer(s) | Event Schema |
|-------|----------|-------------|--------------|
| `task-events` | Backend API (via Dapr) | Audit Service, Recurring Task Service | `{event_type, event_id, task_id, user_id, task_data, timestamp}` |
| `reminders` | Backend API (via Dapr) | Notification Service | `{task_id, user_id, title, remind_at, timestamp}` |
| `task-updates` | Backend API (via Dapr) | WebSocket Service (future) | `{event_type, task_id, user_id, changes, timestamp}` |

**Event Schemas** (existing, no changes):
```json
// Task Event
{
  "event_type": "task.created | task.updated | task.completed | task.deleted",
  "event_id": "uuid-v4",
  "task_id": 123,
  "user_id": "user123",
  "task_data": { "title": "...", "description": "...", "priority": "...", "tags": [...] },
  "timestamp": "2026-01-18T10:30:00Z"
}

// Reminder Event
{
  "task_id": 123,
  "user_id": "user123",
  "title": "Task title",
  "remind_at": "2026-01-18T14:00:00Z",
  "timestamp": "2026-01-18T10:30:00Z"
}
```

**Kafka Configuration**:
- **Platform**: Redpanda (local docker-compose) / Redpanda Cloud (production)
- **Partitions**: 3 per topic (partitioned by user_id hash)
- **Replication Factor**: 1 (local), 3 (production)
- **Retention**: 7 days

### Dapr Components

**5 Components to Configure**:

1. **`kafka-pubsub`** - Pub/Sub for event streaming
   - Replaces direct AIOKafkaProducer/Consumer
   - SASL authentication via Kubernetes secrets
   - Scoped to all 4 services

2. **`statestore`** - PostgreSQL state management
   - For conversation state persistence
   - Uses existing Neon PostgreSQL
   - Creates `dapr_state` table automatically
   - Scoped to backend-service only

3. **`scheduler`** (dapr-jobs) - Scheduled reminders
   - Uses Kubernetes built-in etcd
   - Alternative: cron binding for polling pattern
   - Scoped to notification-service

4. **`kubernetes-secrets`** - Secrets management
   - Replaces environment variables
   - Secrets: app-secrets, postgres-credentials, kafka-credentials
   - No additional configuration (uses K8s RBAC)

5. **Service Invocation** - (Built-in, no config needed)
   - notification-service invokes backend-service for task details
   - Uses logical service names (app-id)

**Dapr API Usage Patterns**:

```python
# Publish event via Dapr HTTP API
async def publish_event(topic: str, data: dict):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"http://localhost:3500/v1.0/publish/kafka-pubsub/{topic}",
            json=data,
            headers={"Content-Type": "application/json"}
        )

# Subscribe endpoint (Dapr pushes to this)
@app.post("/events/tasks")
async def handle_task_event(event: CloudEvent):
    # Process event
    return {"status": "SUCCESS"}

# Subscription registration
@app.get("/dapr/subscribe")
async def subscribe():
    return [
        {"pubsubname": "kafka-pubsub", "topic": "task-events", "route": "/events/tasks"}
    ]

# State store operations
async def save_conversation_state(conversation_id: str, messages: list):
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://localhost:3500/v1.0/state/statestore",
            json=[{"key": f"conversation-{conversation_id}", "value": messages}]
        )

async def get_conversation_state(conversation_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"http://localhost:3500/v1.0/state/statestore/conversation-{conversation_id}"
        )
        return resp.json() if resp.status_code == 200 else None

# Schedule job via Dapr Jobs API
async def schedule_reminder(task_id: int, remind_at: datetime, payload: dict):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"http://localhost:3500/v1.0-alpha1/jobs/reminder-{task_id}",
            json={
                "dueTime": remind_at.isoformat(),
                "data": payload
            }
        )

# Cancel scheduled job
async def cancel_reminder(task_id: int):
    async with httpx.AsyncClient() as client:
        await client.delete(
            f"http://localhost:3500/v1.0-alpha1/jobs/reminder-{task_id}"
        )

# Service invocation
async def invoke_backend_service(method: str, data: dict = None):
    async with httpx.AsyncClient() as client:
        if data:
            return await client.post(
                f"http://localhost:3500/v1.0/invoke/backend-service/method/{method}",
                json=data
            )
        return await client.get(
            f"http://localhost:3500/v1.0/invoke/backend-service/method/{method}"
        )

# Get secret from Kubernetes secrets store
async def get_secret(secret_name: str, key: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"http://localhost:3500/v1.0/secrets/kubernetes-secrets/{secret_name}"
        )
        return resp.json().get(key) if resp.status_code == 200 else None
```

### Microservices Changes

**Services to Modify**:

| Service | Current State | Dapr Changes |
|---------|--------------|--------------|
| Backend API | Direct Kafka producer | Replace with Dapr pub/sub publish API |
| Notification Service | AIOKafkaConsumer | Add subscription endpoint, receive events via HTTP |
| Recurring Task Service | AIOKafkaConsumer | Add subscription endpoint, invoke backend via Dapr |
| Audit Service | AIOKafkaConsumer | Add subscription endpoint, receive all task events |

**Service Communication Flow**:
```
Frontend → Backend API → Dapr Sidecar → Kafka → Dapr Sidecar → Microservices
                ↓
         PostgreSQL (state store via Dapr)
                ↓
         Kubernetes Secrets (via Dapr)
```

### Helm Chart Updates

Each service deployment needs Dapr annotations:

```yaml
# templates/deployment.yaml
spec:
  template:
    metadata:
      annotations:
        dapr.io/enabled: "true"
        dapr.io/app-id: "{{ .Values.dapr.appId }}"
        dapr.io/app-port: "{{ .Values.service.port }}"
        dapr.io/log-level: "{{ .Values.dapr.logLevel }}"
        dapr.io/config: "dapr-config"
        dapr.io/enable-api-logging: "true"
```

**values.yaml additions**:
```yaml
dapr:
  enabled: true
  appId: "backend-service"  # or notification-service, etc.
  logLevel: "info"
```

---

## Implementation Phases

### Phase 0: Research & Discovery (Complete)

Research findings consolidated from codebase exploration:
- Existing Kafka integration uses AIOKafkaProducer in `backend/app/services/kafka_producer.py`
- Three microservices already consuming from Kafka
- Dapr component YAML files already defined in `specs/012-dapr-integration/contracts/`
- Helm charts exist for all services but lack Dapr annotations

### Phase 1: Foundation (Design)

1. **Data Model**: No new database tables required
   - Dapr state store auto-creates `dapr_state` table
   - Event schemas unchanged

2. **API Contracts**: Dapr component files (already in contracts/)
   - kafka-pubsub.yaml
   - statestore.yaml
   - dapr-jobs.yaml
   - kubernetes-secrets.yaml
   - subscriptions.yaml
   - resiliency.yaml
   - dapr-config.yaml

3. **Quickstart**: Local development setup with Dapr

### Phase 2: Implementation Tasks

**Priority 1: Core Infrastructure**
- [ ] T001: Create Dapr HTTP client wrapper module
- [ ] T002: Update backend config.py with Dapr settings
- [ ] T003: Deploy Dapr components to Kubernetes
- [ ] T004: Update Helm charts with Dapr annotations

**Priority 2: Event Publishing (User Story 1)**
- [ ] T005: Replace kafka_producer.py with dapr_client.py
- [ ] T006: Update event_publisher.py to use Dapr pub/sub
- [ ] T007: Modify tasks.py routes to publish via Dapr
- [ ] T008: Add health check for Dapr sidecar availability

**Priority 3: Event Consumption**
- [ ] T009: Add subscription endpoints to notification-service
- [ ] T010: Add subscription endpoints to recurring-task-service
- [ ] T011: Add subscription endpoints to audit-service
- [ ] T012: Implement idempotency checks in handlers

**Priority 4: State Management (User Story 2)**
- [ ] T013: Create dapr_state.py module for state operations
- [ ] T014: Integrate conversation state with Dapr state store
- [ ] T015: Add etag-based optimistic locking

**Priority 5: Scheduled Jobs (User Story 3)**
- [ ] T016: Implement reminder scheduling via Dapr Jobs API
- [ ] T017: Add job cancellation on task completion
- [ ] T018: Add job rescheduling on due date update

**Priority 6: Secrets Management (User Story 4)**
- [ ] T019: Create dapr_secrets.py module
- [ ] T020: Migrate API keys from env vars to K8s secrets
- [ ] T021: Update service configs to use Dapr secrets

**Priority 7: Service Invocation (User Story 5)**
- [ ] T022: Implement service invocation in notification-service
- [ ] T023: Remove hardcoded service URLs
- [ ] T024: Add circuit breaker and retry logic

**Priority 8: Testing & Observability**
- [ ] T025: Add Dapr integration tests
- [ ] T026: Configure distributed tracing (Zipkin)
- [ ] T027: Update monitoring dashboards

---

## Success Criteria Validation

| Criterion | Metric | Validation Method |
|-----------|--------|-------------------|
| SC-001 | Event publish <100ms P99 | Load test with metrics |
| SC-002 | State retrieval <50ms P99 | Load test with metrics |
| SC-003 | 1000 events/sec | Load test |
| SC-004 | Zero hardcoded URLs | Code review |
| SC-005 | 100% secrets from store | Configuration audit |
| SC-006 | Reminders within 1 minute | Functional test |
| SC-007 | Auto-retry with circuit breaker | Integration test |
| SC-008 | Secret rotation without restart | Operational test |
| SC-009 | 99.9% event delivery | Monitoring |
| SC-010 | Distributed tracing context | Trace analysis |
| SC-011 | <2s startup overhead | Startup timing |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Dapr sidecar unavailable | Events fail to publish | Health check + fallback logging |
| State store latency | Slow conversation retrieval | Cache frequently accessed state |
| Jobs API alpha status | API breaking changes | Pin Dapr version, monitor releases |
| Secret access failures | Service startup fails | Fallback to env vars with warning |
| Network partitions | Service invocation timeout | Circuit breaker + retry policies |

---

## Dependencies

1. **Dapr Runtime**: v1.12+ installed in Kubernetes cluster
2. **Kubernetes Secrets**: Must create secret resources before deployment
3. **PostgreSQL**: Existing Neon database accessible for state store
4. **Kafka/Redpanda**: Running and accessible (local or cloud)

---

## Out of Scope

- Dapr cluster installation (platform team responsibility)
- Kafka topic management (external)
- Multi-region Dapr configuration
- Custom Dapr components
- Load testing at scale
