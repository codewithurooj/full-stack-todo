# Implementation Plan: Event-Driven Architecture with Kafka

**Branch**: `011-kafka-event-architecture` | **Date**: 2026-01-12 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/011-kafka-event-architecture/spec.md`

## Summary

Implement event-driven architecture using Apache Kafka to enable scalable, fault-tolerant background processing for recurring tasks, notifications, and audit logging. The system consists of 3 Kafka topics (task-events, reminders, task-updates) and 3 microservices: Recurring Task Service (auto-creates next task occurrence on completion), Notification Service (sends browser notifications at scheduled times), and Audit Service (logs all task operations). This architecture decouples task operations from background processing, ensuring reliability, horizontal scalability, and support for 100,000+ active recurring tasks with 99.9% reliability and <500ms event latency.

## Technical Context

**Language/Version**: Python 3.13+ (microservices), Node.js 20+ (alternative for notification service)

**Primary Dependencies**:
- Kafka Client: aiokafka (Python) or kafkajs (Node.js)
- FastAPI 0.100+ (existing backend for event publishing)
- SQLModel 0.0.8+ (database ORM)
- Web Push libraries: pywebpush (Python) or web-push (Node.js)
- Dapr SDK (optional): dapr-python for simplified Kafka integration

**Storage**:
- PostgreSQL (Neon Serverless) - existing task database + audit logs
- Kafka topics - 7-day retention for event replay
- No additional state storage needed (database-backed)

**Testing**:
- pytest with pytest-asyncio for Python microservices
- testcontainers-python for Kafka integration tests
- Manual browser notification testing
- Load testing with k6 or locust for throughput validation
- Consumer lag monitoring tests

**Target Platform**:
- Development: Docker Compose locally, Minikube for Kubernetes testing
- Production: Cloud Kubernetes (Azure AKS, Google GKE, or Oracle OKE)
- Kafka: Redpanda Cloud (recommended) or Strimzi self-hosted

**Project Type**: Web application with event-driven microservices architecture

**Performance Goals**:
- 10,000 task completion events per minute throughput
- 99% on-time notification delivery (within 5 seconds of scheduled time)
- 99.9% reliability for recurring instance creation
- <500ms event-to-event latency (p95)
- Support 100,000 active recurring tasks without degradation
- Consumer lag <30 seconds under normal load

**Constraints**:
- At-least-once event delivery semantics (idempotency required)
- Zero duplicate recurring instances or notifications despite retries
- Zero data loss for audit logs
- Event ordering per user maintained (partition by user_id)
- Graceful handling of Kafka broker downtime (60 second recovery)

**Scale/Scope**:
- 3 Kafka topics with 12+ partitions each for parallelism
- 3 microservice types (Recurring Task, Notification, Audit)
- 55 functional requirements across 5 groups
- Event replay capability for 7-day retention window
- Horizontal scaling to 10+ consumer instances per service

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Phase V Requirements (Event-Driven Architecture)

**✅ PASS: Kafka Integration**
- 3 Kafka topics defined: task-events, reminders, task-updates
- Event streaming platform specified (Redpanda Cloud or Strimzi)
- Producer (Backend API) publishes events on task operations
- Consumers (microservices) react to events
- At-least-once delivery semantics with idempotency

**✅ PASS: Microservices Architecture**
- Recurring Task Service: Consumes task-events, generates next occurrence
- Notification Service: Consumes reminders, sends browser notifications
- Audit Service: Consumes task-events, logs all operations
- Each service independently deployable and scalable

**✅ PASS: Event Schemas**
- Task Event: event_type, task_id, user_id, task_data, timestamp
- Reminder Event: task_id, user_id, title, remind_at, timestamp
- Task Update: event_type, task_id, user_id, changes, timestamp
- All schemas documented and versioned

**✅ PASS: Cloud-Native Deployment**
- Containerized microservices (Docker)
- Kubernetes deployment (Helm charts)
- Horizontal pod autoscaling support
- Health checks and readiness probes

**⚠️ OPTIONAL: Dapr Components**
- Constitution suggests 5 Dapr components (kafka-pubsub, statestore, dapr-jobs, kubernetes-secrets, service invocation)
- DECISION: Dapr is OPTIONAL for this feature - can use direct Kafka clients
- Benefit: Simplified Kafka interaction, unified API
- Tradeoff: Additional complexity, learning curve
- RECOMMENDATION: Start without Dapr, add later if needed

**✅ PASS: Advanced Features Dependency**
- Depends on Feature 010 (Recurring Tasks and Due Dates)
- Assumes recurring_pattern, due_date, remind_at fields in tasks table
- Builds on existing MCP tools and chat endpoint

### Security Requirements

**✅ PASS: User Isolation**
- Event streams partitioned by user_id
- No cross-user event consumption
- JWT authentication enforced upstream

**✅ PASS: Secrets Management**
- Kafka credentials in Kubernetes secrets
- Database connection string in secrets
- No secrets in container images

**✅ PASS: Network Security**
- Kafka communication secured (SASL/SSL for cloud)
- Internal services use ClusterIP (not exposed)
- TLS/HTTPS on ingress

### No Constitution Violations

All Phase V requirements met. No complexity justification needed.

## Project Structure

### Documentation (this feature)

```text
specs/011-kafka-event-architecture/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (in progress)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (event schemas, audit log schema)
├── quickstart.md        # Phase 1 output (local dev setup)
├── contracts/           # Phase 1 output
│   ├── event-schemas.json    # Kafka event schemas
│   ├── recurring-service-api.yaml    # Health check endpoints
│   ├── notification-service-api.yaml # Health check endpoints
│   └── audit-service-api.yaml        # Query endpoints (optional)
└── tasks.md             # Phase 2 output (/sp.tasks command)
