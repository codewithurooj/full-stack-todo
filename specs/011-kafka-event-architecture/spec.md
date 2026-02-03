# Feature Specification: Event-Driven Architecture with Kafka

**Feature Branch**: `011-kafka-event-architecture`
**Created**: 2026-01-12
**Status**: Draft
**Input**: User description: "Create specification for event-driven architecture using Kafka with 3 topics (task-events, reminders, task-updates) and 3 microservices: Recurring Task Service that auto-creates next occurrence when recurring task completed, Notification Service that sends browser notifications at scheduled times, and Audit Service that logs all task operations"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic Recurring Task Creation (Priority: P1)

As a task manager with recurring tasks, when I complete a recurring task instance, the system automatically creates the next occurrence in the background so that I always have upcoming recurring tasks ready without manual intervention.

**Why this priority**: This is the core value proposition of event-driven recurring tasks. It decouples task completion from instance generation, ensuring reliability and scalability. Users rely on recurring tasks appearing automatically.

**Independent Test**: Can be fully tested by completing a recurring task instance and verifying that within 5 seconds, a new instance appears with the correct next due date. Delivers autonomous recurring task management.

**Acceptance Scenarios**:

1. **Given** a daily recurring task instance is marked complete, **When** the completion event is processed, **Then** a new instance is created with a due date of tomorrow at the same time
2. **Given** a weekly recurring task (Mondays) is completed on Monday, **When** the completion event is processed, **Then** a new instance is created with a due date of next Monday
3. **Given** a recurring task with an end date of March 31, 2026, **When** an instance completed on March 30, 2026 is processed, **Then** no new instance is created since the pattern has ended
4. **Given** a recurring task is completed while the Recurring Task Service is temporarily offline, **When** the service comes back online, **Then** the completion event is still processed and the next instance is created
5. **Given** multiple recurring task instances are completed in rapid succession, **When** the completion events are processed, **Then** each generates exactly one new instance without duplication

---

### User Story 2 - Reliable Browser Notifications (Priority: P1)

As a task manager with time-sensitive tasks, I receive browser notifications exactly at my scheduled reminder times so that I never miss important deadlines, even during high system load or brief service interruptions.

**Why this priority**: Reliable notifications are critical for time-based reminders. Event-driven architecture ensures notifications are delivered even if the web server is busy or temporarily unavailable. This directly impacts user trust.

**Independent Test**: Can be fully tested by setting multiple reminders at specific times, simulating system load, and verifying notifications appear within 5 seconds of scheduled time with 99%+ delivery rate. Delivers dependable deadline alerts.

**Acceptance Scenarios**:

1. **Given** a task with a reminder scheduled for 2:00 PM, **When** the system clock reaches 2:00 PM, **Then** a browser notification appears within 5 seconds showing the task title and due time
2. **Given** 100 reminders scheduled for the same minute, **When** the scheduled time arrives, **Then** notifications are batched and all users receive their alerts within 10 seconds
3. **Given** a reminder scheduled for 3:00 PM while the Notification Service is restarting, **When** the service comes back online at 3:01 PM, **Then** the queued reminder is delivered immediately as a late notification
4. **Given** a user with notification permissions granted, **When** they click on a notification, **Then** the browser navigates directly to that specific task in the application
5. **Given** reminders scheduled for 5 tasks due at the same time, **When** notifications are triggered, **Then** they are batched into a single notification listing all 5 task titles

---

### User Story 3 - Complete Task Operation Audit Trail (Priority: P2)

As a task manager (or administrator), I can view a complete audit log of all task operations including creations, updates, completions, deletions, and recurring instance generations so that I can track task history, troubleshoot issues, and maintain accountability.

**Why this priority**: Audit logs enable debugging, compliance, and analytics. They'''re valuable for power users and administrators but don'''t directly impact core task functionality. Event-driven architecture makes comprehensive logging efficient.

**Independent Test**: Can be fully tested by performing various task operations (create, update, delete) and verifying all operations appear in the audit log with accurate timestamps, user IDs, and operation details. Delivers complete operational transparency.

**Acceptance Scenarios**:

1. **Given** a user creates a new task, **When** the creation event is processed by the Audit Service, **Then** an audit log entry is created with timestamp, user ID, task ID, and operation type "CREATE"
2. **Given** a user updates a task'''s title from "Old" to "New", **When** the update event is processed, **Then** an audit log entry captures both the old and new values with a diff
3. **Given** a recurring task instance is auto-generated, **When** the creation event is processed, **Then** the audit log includes metadata indicating it was system-generated (not user-created) with the recurring pattern ID
4. **Given** multiple task operations occur within 1 second, **When** audit events are processed, **Then** all operations are logged in the correct chronological order with microsecond precision
5. **Given** an administrator requests the audit log for a specific task, **When** they query the audit service, **Then** all historical operations for that task are returned in reverse chronological order

---



### User Story 4 - Event Sourcing and Replay (Priority: P3)

As a system administrator or developer, I need the ability to replay historical events from Kafka topics to rebuild service state, recover from data corruption, or backfill new analytics services so that the system remains resilient and can evolve over time without data loss.

**Why this priority**: Event replay enables system resilience and evolution. It allows recovery from service failures, migration to new data stores, and creation of new derived views from historical data. While not user-facing, it is critical for long-term system health.

**Independent Test**: Can be fully tested by simulating a service failure, clearing its state, and replaying events from Kafka to rebuild the correct state. Delivers disaster recovery and system evolution capabilities.

**Acceptance Scenarios**:

1. **Given** the Recurring Task Service crashes and loses in-memory state, **When** it restarts and replays task-events from the last checkpoint, **Then** all recurring task metadata is restored and new instances are generated correctly
2. **Given** a new analytics service is deployed, **When** it subscribes to the task-events topic and replays all historical events, **Then** it builds a complete view of task history without querying the primary database
3. **Given** the Audit Service detects data inconsistency, **When** an administrator triggers event replay for a specific time range, **Then** audit logs are regenerated from source events and consistency is restored
4. **Given** events published to the task-events topic, **When** Kafka retention is configured for 30 days, **Then** events remain available for replay within that window
5. **Given** multiple services consuming the same topic, **When** one service falls behind processing, **Then** it can catch up by reading from its last committed offset without affecting other consumers

---

### Edge Cases

- **Event Ordering**: When multiple events occur on the same task within milliseconds, Kafka partitioning by task_id ensures events for the same task are processed in order, but events across different tasks may be processed out of global order.
- **Service Downtime**: If a consumer service is offline for 10 minutes, Kafka retains messages up to the configured retention period (30 days), allowing the service to catch up when it comes back online without data loss.
- **Duplicate Event Processing**: Services must implement idempotent event handlers since Kafka guarantees at-least-once delivery; the same event may be delivered multiple times during failure scenarios.
- **Notification Timing During Outage**: If the Notification Service is down for 5 minutes and misses scheduled reminder times, it should detect missed reminders and deliver them immediately as late notifications upon recovery.
- **Recurring Task Instance Race Conditions**: When a user manually creates a task instance while the system is auto-generating the same instance, deduplication logic based on (recurring_pattern_id, due_date) prevents duplicate instances.
- **Kafka Partition Rebalancing**: When a new consumer joins a consumer group, partitions are rebalanced; services must handle graceful shutdown and checkpoint their offsets before termination.
- **Large Event Payloads**: Task update events with large description fields or many tags may approach Kafka default message size limit (1MB); events should include task references rather than full payloads when possible.
- **Event Schema Evolution**: When the task-events schema changes (e.g., adding new fields), both old and new consumers must handle backward/forward compatibility using versioned schemas or optional fields.
- **Audit Log Compaction**: Audit logs grow unbounded; implement log retention policies (e.g., 90 days for detailed logs, 1 year for aggregated summaries) to prevent storage exhaustion.
- **Notification Batching During Peak Load**: If 1,000 reminders fire at exactly 9:00 AM, the Notification Service must batch them efficiently to avoid overwhelming users with individual notifications.
- **Timezone Handling in Events**: Task due dates in events must include timezone information; recurring instance generation must account for daylight saving time transitions to maintain correct local times.
- **Dead Letter Queue (DLQ)**: Events that repeatedly fail processing (e.g., malformed JSON, missing required fields) are sent to a dead-letter topic for manual inspection and reprocessing.

## Requirements *(mandatory)*

### Functional Requirements

**Event Topics and Messaging (FR-001 to FR-010)**

- **FR-001**: System MUST define three Kafka topics: `task-events` for all task lifecycle operations (create, update, complete, delete), `reminders` for scheduled reminder triggers, and `task-updates` for real-time task change notifications to connected clients
- **FR-002**: System MUST publish events to appropriate topics based on operation type with consistent schema including event ID, timestamp, user ID, task ID, operation type, and payload data
- **FR-003**: System MUST use JSON serialization for event payloads with versioned schemas to support backward compatibility
- **FR-004**: System MUST guarantee at-least-once delivery for all events using Kafka producer acknowledgments
- **FR-005**: System MUST partition events by user ID to maintain operation ordering per user while allowing parallel processing across users
- **FR-006**: System MUST assign unique event IDs (UUIDs) to all events for idempotency tracking and deduplication
- **FR-007**: System MUST include event timestamps using ISO 8601 format with UTC timezone for consistent chronological ordering
- **FR-008**: System MUST support event retention of at least 7 days in Kafka topics to allow replay and recovery
- **FR-009**: System MUST publish events to Kafka asynchronously with callback handling to avoid blocking user-facing API requests
- **FR-010**: System MUST log all event publishing failures with retry attempts and eventual dead letter queue routing

**Recurring Task Service (FR-011 to FR-020)**

- **FR-011**: Service MUST consume events from `task-events` topic filtered to "TASK_COMPLETED" operations for recurring tasks
- **FR-012**: Service MUST calculate the next occurrence date/time based on the recurring pattern (daily, weekly, monthly, custom interval)
- **FR-013**: Service MUST create the next recurring task instance within 5 seconds of processing a completion event
- **FR-014**: Service MUST handle end dates for recurring patterns by not creating new instances after the end date
- **FR-015**: Service MUST detect and prevent duplicate instance creation using idempotency keys based on pattern ID + completion timestamp
- **FR-016**: Service MUST publish "TASK_CREATED" events to `task-events` topic when new instances are generated
- **FR-017**: Service MUST maintain a consumer offset per partition to track processing progress and enable resumption after failures
- **FR-018**: Service MUST commit offsets only after successfully creating the new task instance and publishing the creation event
- **FR-019**: Service MUST implement exponential backoff retry logic for transient failures (database unavailable, Kafka unavailable)
- **FR-020**: Service MUST log all recurring instance generation operations including pattern ID, completion timestamp, and new instance ID

**Notification Service (FR-021 to FR-030)**

- **FR-021**: Service MUST consume events from `reminders` topic containing scheduled reminder triggers with task ID, user ID, reminder time, and notification content
- **FR-022**: Service MUST send browser notifications via Web Push API or similar mechanism within 5 seconds of scheduled reminder time
- **FR-023**: Service MUST batch reminders scheduled within 2 minutes into a single notification per user listing all due tasks
- **FR-024**: Service MUST include task title, due time, and a clickable link to the task in all notifications
- **FR-025**: Service MUST handle notification delivery failures (permission denied, browser closed) by logging the failure and not retrying
- **FR-026**: Service MUST track notification delivery status (scheduled, sent, delivered, clicked, dismissed) for analytics
- **FR-027**: Service MUST publish notification status events to `task-updates` topic to inform the frontend of notification delivery
- **FR-028**: Service MUST implement rate limiting to prevent notification spam (max 10 notifications per user per minute)
- **FR-029**: Service MUST maintain a consumer offset per partition and commit offsets only after successful notification delivery or logged failure
- **FR-030**: Service MUST deduplicate reminder events using reminder ID to prevent duplicate notifications

**Audit Service (FR-031 to FR-040)**

- **FR-031**: Service MUST consume all events from `task-events` topic without filtering to create comprehensive audit logs
- **FR-032**: Service MUST persist audit log entries with event ID, timestamp, user ID, task ID, operation type, and full event payload
- **FR-033**: Service MUST capture before/after state for update operations by parsing the event payload diff
- **FR-034**: Service MUST tag system-generated operations (recurring instance creation) differently from user-initiated operations
- **FR-035**: Service MUST store audit logs with microsecond timestamp precision to maintain correct chronological ordering
- **FR-036**: Service MUST index audit logs by task ID, user ID, and timestamp for efficient querying
- **FR-037**: Service MUST retain audit logs for at least 90 days before archival or deletion
- **FR-038**: Service MUST support querying audit logs by task ID, user ID, date range, and operation type
- **FR-039**: Service MUST maintain a consumer offset per partition and commit offsets in batches (every 100 events or 10 seconds)
- **FR-040**: Service MUST implement at-least-once semantics with idempotent writes using event ID as primary key

**Event Schema and Contracts (FR-041 to FR-045)**

- **FR-041**: System MUST define versioned event schemas with explicit version numbers (e.g., "v1", "v2") in the event metadata
- **FR-042**: System MUST support schema evolution where new optional fields can be added without breaking existing consumers
- **FR-043**: System MUST validate event schemas on the producer side before publishing to Kafka
- **FR-044**: System MUST document all event schemas in a schema registry or central documentation
- **FR-045**: System MUST include event type discriminators (e.g., "TASK_CREATED", "TASK_UPDATED", "TASK_COMPLETED") in all events

**Service Resilience and Reliability (FR-046 to FR-055)**

- **FR-046**: All services MUST implement health check endpoints for monitoring and orchestration
- **FR-047**: All services MUST implement graceful shutdown that commits consumer offsets before terminating
- **FR-048**: All services MUST handle Kafka broker unavailability with exponential backoff retry (1s, 2s, 4s, 8s, max 60s)
- **FR-049**: All services MUST implement circuit breakers for external dependencies (database, notification APIs) to prevent cascading failures
- **FR-050**: All services MUST use distributed tracing with correlation IDs to track event processing across services
- **FR-051**: All services MUST emit metrics for event processing rate, latency, error rate, and consumer lag
- **FR-052**: All services MUST log structured logs with event ID, user ID, task ID, and service name for correlation
- **FR-053**: All services MUST implement dead letter queue handling for events that fail after 3 retry attempts
- **FR-054**: All services MUST be horizontally scalable with multiple consumer instances in the same consumer group
- **FR-055**: All services MUST handle consumer rebalancing gracefully without losing in-flight event processing

### Key Entities

- **Event**: Represents a domain operation that occurred in the system. Contains event ID (UUID), event type (e.g., "TASK_COMPLETED"), timestamp (ISO 8601 UTC), user ID, task ID, schema version, and operation-specific payload data. Events are immutable once published.

- **Kafka Topic**: Represents a category of events. Three topics exist: `task-events` for all task operations, `reminders` for scheduled notification triggers, and `task-updates` for real-time task state changes to connected clients.

- **Consumer Group**: Represents a logical group of service instances consuming from a topic. Each microservice type (Recurring Task Service, Notification Service, Audit Service) forms its own consumer group with multiple instances for horizontal scaling.

- **Consumer Offset**: Represents the position of a consumer in a Kafka partition. Tracks which events have been successfully processed. Committed offsets enable resumption after failures.

- **Recurring Task Instance**: Represents a specific occurrence of a recurring task generated by the Recurring Task Service. Links to the original recurring pattern and includes the calculated due date for this occurrence.

- **Notification Delivery Record**: Represents a notification sent by the Notification Service. Tracks reminder ID, user ID, task ID, delivery timestamp, delivery status (sent/failed), and user interaction (clicked/dismissed).

- **Audit Log Entry**: Represents a historical record of a task operation logged by the Audit Service. Contains event ID, timestamp, user ID, task ID, operation type, before/after state (for updates), and full event payload for forensic analysis.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Recurring task instances are created within 5 seconds of completion event processing with 99.9% reliability
- **SC-002**: Reminder notifications are delivered within 5 seconds of scheduled reminder time with 99% on-time delivery rate
- **SC-003**: All task operations are logged in the audit trail within 10 seconds of occurrence with zero data loss
- **SC-004**: System processes 10,000 task completion events per minute across all users without event loss or excessive consumer lag (lag < 30 seconds)
- **SC-005**: Services recover from failures and resume processing within 30 seconds of restart with no manual intervention
- **SC-006**: Event-to-event latency (publish to consumption) is less than 500ms under normal load (p95)
- **SC-007**: Services handle Kafka broker downtime gracefully with automatic reconnection within 60 seconds
- **SC-008**: Zero duplicate recurring instances are created despite duplicate event deliveries or retries
- **SC-009**: Zero duplicate notifications are sent despite consumer crashes or rebalancing
- **SC-010**: Audit logs support queries for any task complete operation history with response time under 200ms
- **SC-011**: System maintains consistent event ordering per user (operations for User A are processed in the order they occurred)
- **SC-012**: Services scale horizontally to 10+ instances per consumer group without data duplication or event loss
- **SC-013**: Event replay from Kafka topic (7-day retention) successfully recreates audit logs within 1 hour
- **SC-014**: Dead letter queue captures less than 0.1% of total events (well-formed events are processed successfully)
- **SC-015**: System supports 100,000 active recurring tasks with daily frequencies without performance degradation

## Assumptions

1. **Kafka Infrastructure Available**: Kafka cluster is provisioned, configured, and managed externally with appropriate replication and partitioning
2. **User Authentication Handled Upstream**: Events include authenticated user IDs; services trust event user IDs without re-authentication
3. **Database Availability**: Task database is highly available and supports concurrent writes from multiple microservice instances
4. **Web Push API Support**: Users have modern browsers that support Web Push API for browser notifications
5. **Network Reliability**: Network partitions between services and Kafka are transient (resolve within minutes, not hours)
6. **Clock Synchronization**: All service instances have reasonably synchronized clocks (NTP or similar) with skew < 1 second
7. **Single Kafka Cluster**: All topics exist in a single Kafka cluster (no multi-cluster replication)
8. **JSON Serialization**: All events are serialized as JSON (not Avro, Protobuf, or custom binary formats)
9. **Consumer Group Coordination**: Kafka consumer group protocol (partition assignment, rebalancing) works correctly
10. **Idempotent Operations**: Task creation and update operations are idempotent at the database level (duplicate writes do not cause errors)
11. **Event Schema Registry**: Event schemas are documented and versioned, but a formal schema registry (Confluent, etc.) is not required
12. **Monitoring Infrastructure**: External monitoring tools (Prometheus, Grafana, etc.) are available to collect metrics and logs

## Dependencies

- **Feature 010 (Recurring Tasks and Due Dates)**: Assumes recurring task patterns, reminders, and due dates are implemented in the task model
- **Kafka Cluster**: Requires a running Kafka cluster with at least 3 brokers for production-grade reliability
- **Task Database**: Requires existing task database with support for concurrent writes and transaction isolation
- **Web Push Infrastructure**: Requires browser notification support and possibly a push notification service (FCM, etc.) for mobile
- **Service Orchestration**: Requires container orchestration (Kubernetes, Docker Compose, etc.) to manage multiple microservice instances
- **Monitoring and Alerting**: Requires monitoring infrastructure to track consumer lag, event processing latency, and service health
- **Logging Infrastructure**: Requires centralized logging (ELK, Splunk, etc.) to aggregate structured logs from all services
- **API Gateway or Event Publisher**: Requires integration with existing task API to publish events to Kafka on task operations

## Out of Scope

1. **Complex Event Processing (CEP)**: No support for complex event queries, pattern matching, or real-time analytics beyond basic consumption
2. **Event Sourcing**: Task state is not fully derived from events; events are supplementary audit and messaging, not the source of truth
3. **Multi-Tenancy Isolation**: No separate Kafka topics or partitioning by tenant; all users share the same topics with user ID partitioning
4. **GDPR Event Deletion**: No support for deleting individual user events from Kafka (retention policy only); audit logs support deletion
5. **Event Transformation Pipelines**: No ETL or stream processing between topics; events are consumed as-is
6. **Cross-Region Replication**: No support for multi-region Kafka replication or disaster recovery across geographic regions
7. **Alternative Message Brokers**: Only Kafka is supported; no abstraction for RabbitMQ, AWS SQS, or other message brokers
8. **Real-Time Analytics Dashboards**: No built-in dashboards for event metrics; external tools (Grafana) are required
9. **Event Replay UI**: No user-facing UI for replaying events; replay is an operator/admin activity via CLI or scripts
10. **Schema Registry Enforcement**: Schema validation is manual via documentation; no Confluent Schema Registry or similar enforcement

## Notes

1. **Performance Optimization**: Partition `task-events` topic by user ID to allow parallel processing while maintaining per-user ordering. Use at least 12 partitions for 10+ consumer instances.

2. **Consumer Lag Monitoring**: Monitor consumer lag closely. Lag > 60 seconds indicates services are falling behind and may need scaling or optimization.

3. **Idempotency Implementation**: Use event ID as an idempotency key in the database (unique constraint). Duplicate event processing attempts will fail gracefully on constraint violation.

4. **Dead Letter Queue Strategy**: Route failed events to a separate `dlq-task-events` topic after 3 retries. Implement automated alerting when DLQ depth exceeds 10 events.

5. **Event Schema Versioning**: Always include schema version in events. When incrementing versions, maintain backward compatibility for at least 90 days.

6. **Testing Strategy**: Use testcontainers or embedded Kafka for integration tests. Test consumer offset management, rebalancing, and failure recovery scenarios explicitly.

7. **Operational Runbooks**: Document procedures for:
   - Replaying events from a specific offset or timestamp
   - Scaling consumer groups (adding/removing instances)
   - Handling Kafka broker failures
   - Investigating events in the dead letter queue
   - Manual notification retry for users who missed notifications

8. **Security Considerations**: Kafka topics should use ACLs to restrict which services can produce/consume from each topic. Events contain user IDs but no PII (personal identifiable information) beyond what is necessary.

9. **Cost Management**: Kafka retention of 7 days for 10K events/minute = ~100GB storage. Monitor costs and adjust retention if needed.

10. **Observability**: Use distributed tracing (OpenTelemetry) with correlation IDs propagated through events. This enables end-to-end request tracing from user action to event publish to service consumption to side effect.
