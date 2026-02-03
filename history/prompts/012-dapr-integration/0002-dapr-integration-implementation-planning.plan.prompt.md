---
id: 0002
title: dapr-integration-implementation-planning
stage: plan
date: 2026-01-18
surface: claude-code
model: claude-opus-4-5
feature: 012-dapr-integration
branch: 012-dapr-integration
user: developer
command: /sp.plan
labels: [dapr, event-driven, microservices, phase-v, kafka]
links:
  spec: specs/012-dapr-integration/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/012-dapr-integration/plan.md
  - specs/012-dapr-integration/research.md
  - specs/012-dapr-integration/data-model.md
  - specs/012-dapr-integration/quickstart.md
tests:
  - null
---

## Prompt

/sp.plan

Execute the implementation planning workflow for Dapr integration feature (012-dapr-integration). The spec describes integrating 5 Dapr components: kafka-pubsub for event streaming, statestore using PostgreSQL for conversation state, dapr-jobs for scheduled reminders, kubernetes-secrets for sensitive data, and service invocation for inter-service communication. Replace direct Kafka calls with Dapr HTTP APIs.

## Response snapshot

Completed implementation planning for Dapr integration:

1. **Technical Context**: Defined Python 3.13+, FastAPI 0.100+, Dapr 1.14+, httpx for HTTP calls, PostgreSQL for state store, Kafka/Redpanda for events.

2. **Constitution Check**: All gates PASS - spec-driven development, event-driven architecture, cloud-native deployment principles all satisfied.

3. **Research (Phase 0)**: 10 research decisions documented:
   - Use Dapr HTTP APIs directly via httpx (not Python SDK)
   - Push-based subscription model with HTTP endpoints
   - Single key per conversation for state store
   - Dapr Jobs API with cron binding fallback
   - Gradual secrets migration with env var fallback
   - Service invocation for all inter-service calls
   - Health checks with graceful degradation
   - Zipkin tracing + Prometheus metrics
   - Dapr CLI for local development
   - Built-in DLQ with 3 retry attempts

4. **Data Model**: Documented Dapr state table schema, conversation state structure, event schemas, job data structures, Kubernetes secrets.

5. **Quickstart**: Step-by-step local development and Kubernetes deployment guide.

6. **Implementation Tasks**: 27 tasks across 8 priority groups:
   - P1: Core infrastructure (Dapr client, config, components)
   - P2: Event publishing (replace Kafka producer)
   - P3: Event consumption (subscription endpoints)
   - P4: State management (conversation persistence)
   - P5: Scheduled jobs (reminders)
   - P6: Secrets management (K8s secrets)
   - P7: Service invocation (inter-service calls)
   - P8: Testing and observability

## Outcome

- Impact: Complete implementation plan ready for task generation (/sp.tasks)
- Tests: None (planning phase)
- Files: plan.md, research.md, data-model.md, quickstart.md created
- Next prompts: /sp.tasks to generate detailed implementation tasks
- Reflection: Comprehensive planning completed with research addressing all unknowns. Contracts already existed from previous spec phase.

## Evaluation notes (flywheel)

- Failure modes observed: None - planning completed successfully
- Graders run and results (PASS/FAIL): N/A (planning phase)
- Prompt variant (if applicable): standard /sp.plan workflow
- Next experiment (smallest change to try): Proceed to /sp.tasks for implementation breakdown
