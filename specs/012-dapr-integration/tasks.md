# Tasks: Dapr Integration for Event-Driven Architecture

**Input**: Design documents from `/specs/012-dapr-integration/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in spec. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/`, `services/`, `dapr-components/`, `charts/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, Dapr components deployment, and base configuration

- [X] T001 Create dapr-components/ directory at repository root with component YAML files from specs/012-dapr-integration/contracts/
- [X] T002 [P] Create dapr.yaml multi-app configuration file at repository root for local development
- [X] T003 [P] Update backend/requirements.txt to add httpx dependency (if not present)
- [X] T004 [P] Create Kubernetes Secret manifests in dapr-components/secrets/ for app-secrets, postgres-credentials, kafka-credentials

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core Dapr client infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create Dapr HTTP client wrapper module in backend/app/services/dapr_client.py with base URL config and health check function
- [X] T006 Update backend/app/config.py to add Dapr configuration settings (DAPR_HTTP_PORT, DAPR_HOST, component names)
- [X] T007 Add Dapr sidecar health check endpoint integration in backend/app/main.py startup event
- [X] T008 [P] Create processed_events table migration for idempotency tracking in backend/migrations/

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Event Publishing and Consumption (Priority: P1)

**Goal**: Replace direct Kafka producer/consumer with Dapr pub/sub HTTP APIs for event-driven communication

**Independent Test**: Create a task via API, verify event is published to Kafka via Dapr, confirm notification-service receives and processes the event through subscription endpoint

### Implementation for User Story 1

- [X] T009 [US1] Implement publish_event function in backend/app/services/dapr_client.py using Dapr pub/sub API
- [X] T010 [US1] Create new event_publisher module backend/app/services/dapr_event_publisher.py that uses dapr_client for publishing
- [X] T011 [US1] Update backend/app/services/event_publisher.py to delegate to dapr_event_publisher with fallback to kafka_producer
- [X] T012 [US1] Add CloudEvent metadata (event_id, correlation_id, timestamp) to all published events in dapr_event_publisher.py
- [X] T013 [P] [US1] Add /dapr/subscribe endpoint in backend/app/routes/dapr_subscriptions.py returning empty subscriptions list (backend is publisher only)
- [X] T014 [P] [US1] Create subscription endpoint /events/tasks in services/notification-service/app/routes.py for task events
- [X] T015 [P] [US1] Create subscription endpoint /events/reminders in services/notification-service/app/routes.py for reminder events
- [X] T016 [P] [US1] Create subscription endpoint /events/tasks in services/recurring-task-service/src/routes.py for task events
- [X] T017 [P] [US1] Create subscription endpoint /events/task-completed in services/recurring-task-service/src/routes.py for completed events
- [X] T018 [P] [US1] Create subscription endpoint /events/tasks in services/audit-service/src/routes.py for all task events
- [X] T019 [US1] Add /dapr/subscribe endpoint in services/notification-service/app/routes.py returning subscription config
- [X] T020 [US1] Add /dapr/subscribe endpoint in services/recurring-task-service/src/routes.py returning subscription config
- [X] T021 [US1] Add /dapr/subscribe endpoint in services/audit-service/src/routes.py returning subscription config
- [X] T022 [US1] Implement idempotency check helper using processed_events table in backend/app/services/dapr_client.py
- [X] T023 [US1] Add idempotency checks to all subscription handlers in notification-service, recurring-task-service, audit-service
- [X] T024 [US1] Implement graceful degradation with fallback logging when Dapr sidecar is unavailable in dapr_event_publisher.py

**Checkpoint**: Event publishing via Dapr and subscription endpoints should be functional. Test by creating a task and verifying events flow through the system.

---

## Phase 4: User Story 2 - State Management for Conversations (Priority: P2)

**Goal**: Persist chatbot conversation state using Dapr state store backed by PostgreSQL for multi-turn conversation support

**Independent Test**: Start a conversation, send multiple messages, restart the backend service, verify conversation history is preserved and accessible

### Implementation for User Story 2

- [X] T025 [US2] Create Dapr state store operations module in backend/app/services/dapr_state.py with save_state, get_state, delete_state functions
- [X] T026 [US2] Implement conversation state schema (user_id, messages, context, timestamps) in dapr_state.py
- [X] T027 [US2] Add etag-based optimistic locking for concurrent conversation updates in dapr_state.py
- [X] T028 [US2] Create conversation state service in backend/app/services/conversation_state_service.py using dapr_state module
- [X] T029 [US2] Integrate conversation_state_service with existing chat endpoint in backend/app/routes/ (if exists) or create new endpoint
- [X] T030 [US2] Add conversation state retrieval on chat request to load previous messages
- [X] T031 [US2] Add conversation state save after each assistant response
- [X] T032 [US2] Implement fallback to in-memory state when Dapr state store is unavailable

**Checkpoint**: Chatbot conversations should persist across service restarts. Test by chatting, restarting backend, and continuing the conversation.

---

## Phase 5: User Story 3 - Scheduled Task Reminders (Priority: P2)

**Goal**: Schedule and manage task reminder notifications using Dapr Jobs API with automatic job lifecycle management

**Independent Test**: Create a task with due date, verify reminder jobs are scheduled, advance time or wait, confirm reminder notification is triggered

### Implementation for User Story 3

- [X] T033 [US3] Implement schedule_job function in backend/app/services/dapr_client.py using Dapr Jobs API (v1.0-alpha1)
- [X] T034 [US3] Implement cancel_job function in backend/app/services/dapr_client.py
- [X] T035 [US3] Create reminder scheduler service in backend/app/services/reminder_scheduler.py using dapr_client
- [X] T036 [US3] Implement schedule_task_reminders function to create 24h and 1h reminder jobs in reminder_scheduler.py
- [X] T037 [US3] Implement cancel_task_reminders function to remove jobs when task is completed in reminder_scheduler.py
- [X] T038 [US3] Implement reschedule_task_reminders function when due date is updated in reminder_scheduler.py
- [X] T039 [US3] Integrate reminder_scheduler with task creation flow in backend/app/routes/tasks.py
- [X] T040 [US3] Integrate reminder_scheduler with task update flow (due date changes) in backend/app/routes/tasks.py
- [X] T041 [US3] Integrate reminder_scheduler with task completion flow in backend/app/routes/tasks.py
- [X] T042 [US3] Add job execution endpoint /jobs/reminder in services/notification-service/app/routes.py to receive Dapr job callbacks
- [X] T043 [US3] Implement fallback cron polling pattern in services/notification-service/ when Jobs API is unavailable

**Checkpoint**: Task reminders should be scheduled automatically and trigger notifications at the right time.

---

## Phase 6: User Story 4 - Secure Configuration Management (Priority: P3)

**Goal**: Migrate sensitive configuration from environment variables to Kubernetes secrets accessed via Dapr secrets component

**Independent Test**: Store a secret in Kubernetes, access it from a service via Dapr, rotate the secret, verify service picks up new value without restart

### Implementation for User Story 4

- [X] T044 [US4] Create Dapr secrets retrieval module in backend/app/services/dapr_secrets.py with get_secret function
- [X] T045 [US4] Implement fallback to environment variables when Dapr secrets unavailable in dapr_secrets.py
- [X] T046 [US4] Add warning logging when using env var fallback for secrets in dapr_secrets.py
- [X] T047 [US4] Update backend/app/config.py to use dapr_secrets for OPENAI_API_KEY retrieval
- [X] T048 [US4] Update backend/app/config.py to use dapr_secrets for DATABASE_URL retrieval
- [X] T049 [US4] Update backend/app/config.py to use dapr_secrets for BETTER_AUTH_SECRET retrieval
- [X] T050 [P] [US4] Create dapr_secrets module in services/notification-service/app/dapr_secrets.py
- [X] T051 [P] [US4] Create dapr_secrets module in services/recurring-task-service/src/dapr_secrets.py
- [X] T052 [P] [US4] Create dapr_secrets module in services/audit-service/src/dapr_secrets.py
- [X] T053 [US4] Update notification-service config to use Dapr secrets
- [X] T054 [US4] Update recurring-task-service config to use Dapr secrets
- [X] T055 [US4] Update audit-service config to use Dapr secrets

**Checkpoint**: All sensitive configuration should be retrieved from Dapr secrets with env var fallback for local development.

---

## Phase 7: User Story 5 - Service-to-Service Communication (Priority: P3)

**Goal**: Enable service invocation through Dapr for inter-service communication with automatic service discovery and built-in resiliency

**Independent Test**: Trigger a notification that requires task details, verify notification-service invokes backend-service via Dapr, confirm correct data is retrieved

### Implementation for User Story 5

- [X] T056 [US5] Implement invoke_service function in backend/app/services/dapr_client.py using Dapr service invocation API
- [X] T057 [US5] Create Dapr service invocation client in services/notification-service/app/dapr_client.py
- [X] T058 [US5] Implement get_task_details function in notification-service using Dapr service invocation to call backend-service
- [X] T059 [US5] Update notification event handler to fetch task details via Dapr service invocation when needed
- [X] T060 [US5] Remove hardcoded backend service URLs from notification-service configuration
- [X] T061 [P] [US5] Create Dapr service invocation client in services/recurring-task-service/src/dapr_client.py
- [X] T062 [US5] Implement invoke_backend_service function in recurring-task-service for task operations
- [X] T063 [US5] Remove hardcoded service URLs from recurring-task-service configuration
- [X] T064 [US5] Add timeout configuration for all service invocation calls (default 30s)
- [X] T065 [US5] Add retry policy with exponential backoff for transient failures in service invocation

**Checkpoint**: Services should communicate via Dapr service invocation without hardcoded URLs.

---

## Phase 8: Helm Chart Updates & Kubernetes Deployment

**Purpose**: Update all Helm charts with Dapr annotations for Kubernetes deployment

- [X] T066 [P] Update charts/backend/templates/deployment.yaml with Dapr annotations (app-id, app-port, config)
- [X] T067 [P] Update charts/backend/values.yaml with Dapr configuration section
- [X] T068 [P] Update charts/notification-service/templates/deployment.yaml with Dapr annotations
- [X] T069 [P] Update charts/notification-service/values.yaml with Dapr configuration section
- [X] T070 [P] Update charts/recurring-task-service/templates/deployment.yaml with Dapr annotations
- [X] T071 [P] Update charts/recurring-task-service/values.yaml with Dapr configuration section
- [X] T072 [P] Update charts/audit-service/templates/deployment.yaml with Dapr annotations
- [X] T073 [P] Update charts/audit-service/values.yaml with Dapr configuration section
- [X] T074 Create Helm chart for Dapr components deployment in charts/dapr-components/

**Checkpoint**: All services should have Dapr sidecar injection enabled in Kubernetes deployments.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Observability, documentation, and final cleanup

- [X] T075 [P] Configure distributed tracing with Zipkin in dapr-components/dapr-config.yaml
- [X] T076 [P] Add Dapr metrics endpoints to monitoring configuration in monitoring/
- [X] T077 Update backend health endpoint to include Dapr component status in backend/app/main.py
- [X] T078 [P] Deprecate backend/app/services/kafka_producer.py with warning comments (keep for fallback)
- [X] T079 Update quickstart.md with Dapr local development setup instructions in specs/012-dapr-integration/quickstart.md
- [X] T080 Create runbook for Dapr troubleshooting in docs/runbooks/dapr-troubleshooting.md
- [X] T081 Run quickstart.md validation to ensure all setup instructions work

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-7)**: All depend on Foundational phase completion
  - US1 (Event Publishing) can start immediately after Foundational
  - US2 (State Management) can start immediately after Foundational (parallel with US1)
  - US3 (Scheduled Jobs) can start immediately after Foundational (parallel with US1, US2)
  - US4 (Secrets) can start immediately after Foundational (parallel with others)
  - US5 (Service Invocation) can start immediately after Foundational (parallel with others)
- **Helm Updates (Phase 8)**: Can start after US1 is complete (needs subscription endpoints)
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories - Core event-driven capability
- **User Story 2 (P2)**: No dependencies on other stories - Conversation state is independent
- **User Story 3 (P2)**: No direct dependencies, but benefits from US1 being complete for event publishing
- **User Story 4 (P3)**: No dependencies on other stories - Secrets management is cross-cutting
- **User Story 5 (P3)**: No dependencies on other stories - Service invocation is independent

### Within Each User Story

- Core client modules before service modules
- Service modules before route integrations
- Backend changes before microservice changes
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**:
```bash
Task: "T002 Create dapr.yaml multi-app configuration"
Task: "T003 Update backend/requirements.txt"
Task: "T004 Create Kubernetes Secret manifests"
```

**Phase 2 (Foundational)** - T008 can run in parallel with others:
```bash
Task: "T005 Create Dapr HTTP client wrapper"
Task: "T008 [P] Create processed_events migration"
```

**User Story 1 - Subscription Endpoints**:
```bash
Task: "T013 [P] Add /dapr/subscribe in backend"
Task: "T014 [P] Create /events/tasks in notification-service"
Task: "T015 [P] Create /events/reminders in notification-service"
Task: "T016 [P] Create /events/tasks in recurring-task-service"
Task: "T017 [P] Create /events/task-completed in recurring-task-service"
Task: "T018 [P] Create /events/tasks in audit-service"
```

**User Story 4 - dapr_secrets modules**:
```bash
Task: "T050 [P] Create dapr_secrets in notification-service"
Task: "T051 [P] Create dapr_secrets in recurring-task-service"
Task: "T052 [P] Create dapr_secrets in audit-service"
```

**Phase 8 - Helm Charts** (all parallel):
```bash
Task: "T066-T073 All Helm chart updates can run in parallel"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (Dapr components)
2. Complete Phase 2: Foundational (Dapr client wrapper)
3. Complete Phase 3: User Story 1 (Event Publishing)
4. **STOP and VALIDATE**: Test event flow from backend through Kafka to microservices
5. Deploy to Minikube and verify Dapr sidecar injection

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Events) → Test event flow → **MVP!**
3. Add User Story 2 (State) → Test conversation persistence
4. Add User Story 3 (Jobs) → Test scheduled reminders
5. Add User Story 4 (Secrets) → Test secure config
6. Add User Story 5 (Invocation) → Test service communication
7. Add Phase 8 (Helm) → Deploy to Kubernetes
8. Add Phase 9 (Polish) → Production-ready

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Event Publishing) - Critical path
   - Developer B: User Story 2 (State Management)
   - Developer C: User Story 3 (Scheduled Jobs)
3. After US1-3:
   - Developer A: User Story 4 (Secrets)
   - Developer B: User Story 5 (Service Invocation)
   - Developer C: Phase 8 (Helm Charts)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Dapr HTTP APIs used directly via httpx (no SDK dependency)
- Fallback mechanisms ensure graceful degradation when Dapr unavailable
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
