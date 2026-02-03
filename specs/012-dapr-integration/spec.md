# Feature Specification: Dapr Integration for Event-Driven Architecture

**Feature Branch**: `012-dapr-integration`
**Created**: 2026-01-14
**Status**: Draft
**Input**: User description: "Dapr integration with 5 components: kafka-pubsub for event streaming, statestore using PostgreSQL for conversation state, dapr-jobs for scheduled reminders, kubernetes-secrets for sensitive data, and service invocation for inter-service communication. Replace direct Kafka calls with Dapr HTTP APIs"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Event Publishing and Consumption (Priority: P1)

When a task state changes (created, updated, completed, deleted), the system publishes events that other services can consume to trigger workflows like notifications, analytics, or audit logging. Users experience seamless integration without directly managing message brokers.

**Why this priority**: Core event-driven capability that enables all downstream integrations. Without event streaming, notification service, audit service, and analytics cannot function properly.

**Independent Test**: Can be fully tested by creating a task via API, verifying the event is published to the message broker, and confirming notification service receives and processes the event. Delivers immediate value by enabling real-time notifications.

**Acceptance Scenarios**:

1. **Given** a task is created by a user, **When** the task creation completes, **Then** a "task.created" event is published with task details
2. **Given** a task is marked complete, **When** the completion action occurs, **Then** a "task.completed" event is published
3. **Given** multiple services subscribe to task events, **When** an event is published, **Then** all subscribers receive the event independently
4. **Given** the message broker is temporarily unavailable, **When** an event publish is attempted, **Then** the system retries automatically with exponential backoff

---

### User Story 2 - State Management for Conversations (Priority: P2)

The chatbot maintains conversation context across multiple exchanges. When a user asks a follow-up question, the system retrieves prior messages and context to provide coherent responses. State is persisted reliably and accessible across service restarts.

**Why this priority**: Essential for chatbot user experience but can be developed after event streaming. Enables contextual conversations that users expect from AI assistants.

**Independent Test**: Can be tested by initiating a conversation, asking multiple related questions, restarting the service, and verifying context is maintained. Delivers value by enabling multi-turn conversations.

**Acceptance Scenarios**:

1. **Given** a user starts a conversation, **When** they send messages, **Then** conversation state is persisted after each exchange
2. **Given** a user returns to an existing conversation, **When** they send a new message, **Then** the system retrieves full conversation history
3. **Given** conversation state is stored, **When** a service instance crashes, **Then** state remains accessible from other instances
4. **Given** a conversation has been inactive for 30 days, **When** the retention policy runs, **Then** old conversation state is archived

---

### User Story 3 - Scheduled Task Reminders (Priority: P2)

Users with tasks that have due dates receive timely reminders. The system schedules reminder jobs that trigger at appropriate times (e.g., 1 day before, 1 hour before) and sends notifications via the notification service.

**Why this priority**: High-value feature for task completion but depends on event infrastructure (P1). Can be developed in parallel with conversation state management.

**Independent Test**: Can be tested by creating a task with a due date, scheduling a reminder job, advancing system time, and verifying reminder notification is sent. Delivers value by preventing missed deadlines.

**Acceptance Scenarios**:

1. **Given** a task has a due date, **When** the task is created, **Then** reminder jobs are scheduled (24 hours before, 1 hour before)
2. **Given** a scheduled reminder time is reached, **When** the job executes, **Then** a reminder notification is sent to the task owner
3. **Given** a task is completed before the reminder, **When** the completion event occurs, **Then** all pending reminder jobs are cancelled
4. **Given** a task due date is updated, **When** the update completes, **Then** existing reminder jobs are rescheduled accordingly

---

### User Story 4 - Secure Configuration Management (Priority: P3)

Sensitive configuration data (API keys, database passwords, service credentials) is stored securely and accessed by services at runtime. Operations teams can rotate secrets without code changes or redeployments.

**Why this priority**: Important for production security but doesn't block feature development. Can be implemented after core functionality is working with environment variables.

**Independent Test**: Can be tested by storing a secret (e.g., OpenAI API key), accessing it from a service, rotating the secret, and verifying the service picks up the new value. Delivers value by improving security posture.

**Acceptance Scenarios**:

1. **Given** a service needs sensitive configuration, **When** the service starts, **Then** it retrieves secrets from secure storage
2. **Given** a secret is updated, **When** the service next accesses it, **Then** the updated value is used without restart
3. **Given** a secret access fails, **When** the failure occurs, **Then** the service logs an error and falls back to default behavior without exposing secret values
4. **Given** access audit logs are enabled, **When** a secret is accessed, **Then** the access is logged with timestamp and service identity

---

### User Story 5 - Service-to-Service Communication (Priority: P3)

Services communicate with each other through standardized APIs without hardcoding hostnames or managing service discovery. When the notification service needs to fetch task details, it invokes the task service using a logical service name.

**Why this priority**: Improves maintainability and enables dynamic service scaling but can initially use direct HTTP calls. Provides long-term architectural benefits.

**Independent Test**: Can be tested by triggering a notification that requires task details, verifying the notification service invokes the task service, and confirming correct data is retrieved. Delivers value by simplifying inter-service communication.

**Acceptance Scenarios**:

1. **Given** notification service needs task details, **When** processing a task event, **Then** it invokes task service using logical service name
2. **Given** the task service is scaled to multiple instances, **When** an invocation occurs, **Then** the request is load-balanced automatically
3. **Given** the task service is temporarily unavailable, **When** an invocation is attempted, **Then** the system retries with timeout and circuit breaker logic
4. **Given** cross-service calls occur, **When** observing system behavior, **Then** distributed tracing headers are propagated for debugging

---

### Edge Cases

- What happens when the Dapr sidecar is unavailable or crashes while the application is running?
- How does the system handle state store connection failures when retrieving conversation history?
- What happens if a scheduled reminder job fails to execute (e.g., notification service is down)?
- How are duplicate events handled if the event broker delivers messages more than once?
- What happens when a service attempts to publish an event larger than the message size limit?
- How does the system behave when secrets rotation occurs during active service operation?
- What happens if service invocation times out due to network latency or slow downstream services?
- How are failed messages handled (dead letter queue, retry policy, alerting)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST replace all direct Kafka producer/consumer calls with Dapr pub/sub HTTP API calls
- **FR-002**: System MUST publish events to Dapr pub/sub component for all state-changing operations (task created, updated, deleted, completed)
- **FR-003**: System MUST include event metadata (timestamp, event type, correlation ID, source service) in all published events
- **FR-004**: Notification service MUST subscribe to task events via Dapr pub/sub and process events asynchronously
- **FR-005**: Audit service MUST subscribe to task events via Dapr pub/sub and log all operations for compliance
- **FR-006**: System MUST store and retrieve conversation state using Dapr state store API backed by PostgreSQL
- **FR-007**: Conversation state MUST include conversation ID, user ID, message history, context metadata, and timestamps
- **FR-008**: System MUST handle concurrent conversation state updates with optimistic locking or etags
- **FR-009**: System MUST schedule reminder jobs using Dapr jobs API with configurable trigger times
- **FR-010**: Reminder jobs MUST support scheduling (one-time execution at specific time), cancellation (when task completed), and rescheduling (when due date changes)
- **FR-011**: System MUST retrieve sensitive configuration (API keys, database credentials, service tokens) from Dapr secrets API backed by Kubernetes secrets
- **FR-012**: Services MUST NOT store secrets in code, configuration files, or environment variables (except Dapr configuration)
- **FR-013**: Notification service MUST invoke task service using Dapr service invocation API to retrieve task details
- **FR-014**: Service invocation MUST support HTTP method specification (GET, POST, PUT, DELETE), request/response body handling, and timeout configuration
- **FR-015**: All Dapr HTTP API calls MUST include proper error handling with retries for transient failures
- **FR-016**: System MUST implement health checks that verify Dapr sidecar availability before processing requests
- **FR-017**: System MUST emit structured logs for all Dapr interactions (component name, operation, latency, status)
- **FR-018**: Failed events MUST be routed to dead letter queue after 3 retry attempts with exponential backoff
- **FR-019**: System MUST implement idempotency for event processing to handle duplicate message delivery

### Key Entities

- **Dapr Pub/Sub Component (kafka-pubsub)**: Abstracts Kafka event streaming, manages topic creation, handles message routing, provides at-least-once delivery semantics
- **Dapr State Store Component (statestore)**: Abstracts PostgreSQL state persistence, manages conversation state storage, supports CRUD operations with etags for consistency
- **Dapr Jobs Component (dapr-jobs)**: Manages scheduled reminder execution, handles job lifecycle (schedule, execute, cancel), supports job metadata and payload storage
- **Dapr Secrets Component (kubernetes-secrets)**: Abstracts Kubernetes secret storage, provides secure secret retrieval, supports multiple secret scopes and namespaces
- **Dapr Service Invocation**: Enables service-to-service HTTP calls with service discovery, load balancing, retry policies, and distributed tracing

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All event publishing operations complete within 100ms (99th percentile) from application code perspective
- **SC-002**: Conversation state retrieval operations complete within 50ms (99th percentile) for typical conversation sizes (up to 50 messages)
- **SC-003**: System successfully processes 1000 task events per second without message loss or data corruption
- **SC-004**: Zero hardcoded service URLs or hostnames remain in application code after migration
- **SC-005**: 100% of sensitive configuration values (API keys, credentials) are retrieved from secure secret storage
- **SC-006**: Scheduled reminder jobs execute within 1 minute of their scheduled time under normal load conditions
- **SC-007**: Service-to-service communication failures trigger automatic retries with circuit breaker protection (fail after 3 attempts)
- **SC-008**: Operations team can rotate secrets without application restarts or code changes
- **SC-009**: System maintains 99.9% event delivery success rate with automatic retry and dead letter queue handling
- **SC-010**: All inter-service calls include distributed tracing context for end-to-end observability
- **SC-011**: Application startup time increases by no more than 2 seconds due to Dapr initialization and health checks

## Assumptions

1. **Dapr Runtime**: Dapr 1.12+ is deployed in the Kubernetes cluster with sidecar injection enabled for all application pods
2. **PostgreSQL**: Existing PostgreSQL database can be used for Dapr state store with dedicated schema/table for conversation state
3. **Kafka**: Existing Kafka cluster is accessible and configured as backend for Dapr pub/sub component
4. **Kubernetes Secrets**: Kubernetes cluster has secrets management enabled with RBAC policies allowing pod secret access
5. **Event Schema**: All services agree on event schema format (event type, payload structure, metadata fields)
6. **Idempotency**: Event consumers are designed to handle duplicate events (at-least-once delivery semantics)
7. **Backward Compatibility**: Migration from direct Kafka to Dapr can be done incrementally without breaking existing functionality
8. **Observability**: Prometheus and distributed tracing (Jaeger/Zipkin) are available for monitoring Dapr components

## Dependencies

1. **Dapr Component YAML Files**: Must create component definitions for kafka-pubsub, statestore, dapr-jobs, kubernetes-secrets
2. **PostgreSQL Schema**: Must create database schema for Dapr state store with proper indexes and constraints
3. **Kubernetes Secret Resources**: Must migrate existing secrets from environment variables to Kubernetes secret objects
4. **Event Schema Definitions**: Must document event types, payload structures, and metadata fields for all published events
5. **Service Discovery Configuration**: Must configure Dapr service invocation with proper app-id labels for all services
6. **Monitoring Dashboards**: Must update observability dashboards to include Dapr component metrics and health status

## Out of Scope

1. **Dapr Cluster Installation**: Assumes Dapr is already installed in Kubernetes cluster by platform team
2. **Kafka Topic Management**: Topic creation, partition configuration, and retention policies managed externally
3. **Database Migration for State Store**: Migrating existing conversation state from current storage to Dapr state store (if applicable)
4. **Secret Migration Tooling**: Automated tools to migrate environment variables to Kubernetes secrets
5. **Custom Dapr Components**: Building custom Dapr component implementations or middleware
6. **Load Testing at Scale**: Comprehensive load testing to validate system behavior under extreme traffic (separate activity)
7. **Multi-Region Deployment**: Dapr configuration for cross-region replication or geo-distributed state management
