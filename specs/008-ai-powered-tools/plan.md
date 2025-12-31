# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]  
**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]  
**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]  
**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]  
**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]
**Project Type**: [single/web/mobile - determines source structure]  
**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]  
**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]  
**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Gates determined based on constitution file]

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |

---

## Phase III: AI & MCP Server Design

> **Fill ONLY if this feature involves AI chatbot, MCP tools, or conversational interface**

### MCP Server Architecture

**MCP Tools to Implement**:
- [ ] `tool_name_1` - [Description, parameters, return type]
- [ ] `tool_name_2` - [Description, parameters, return type]
- [ ] `tool_name_3` - [Description, parameters, return type]

**Stateless Design Pattern**:
```python
# Example flow for stateless chat endpoint
async def chat_endpoint(user_id: int, message: str):
    # 1. Fetch conversation history from database
    # 2. Build message array (history + new message)
    # 3. Store user message in database
    # 4. Run OpenAI Agent with MCP tools
    # 5. Agent invokes appropriate MCP tool(s)
    # 6. Store assistant response in database
    # 7. Return response to client
    # 8. Server holds NO state (ready for next request)
```

**Conversation Database Schema**:
```sql
-- conversations table (if new)
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    started_at TIMESTAMP DEFAULT NOW(),
    last_message_at TIMESTAMP DEFAULT NOW()
);

-- messages table (if new)
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id),
    role VARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**OpenAI Agent Configuration**:
- **Agent SDK**: `openai-agents-sdk` version [X.X.X]
- **MCP SDK**: `mcp-sdk` version [X.X.X]
- **Model**: [e.g., gpt-4o, gpt-4o-mini]
- **System Prompt**: [Brief description or location]
- **Tool Invocation Pattern**: [Sequential/Parallel/Conditional]

**Natural Language Understanding Requirements**:
- [ ] [Example command format: "add task buy milk"]
- [ ] [Example command format: "show my tasks"]
- [ ] [Example command format: "mark task 5 as complete"]

---

## Phase IV: Containerization & Kubernetes

> **Fill ONLY if this feature requires containerization or Kubernetes deployment**

### Docker Strategy

**Containers to Build**:
- [ ] `frontend` - [Next.js app, base image, build strategy]
- [ ] `backend` - [FastAPI app, base image, build strategy]
- [ ] `mcp-server` - [MCP server, base image, build strategy] (if separate)

**Multi-Stage Build Pattern**:
```dockerfile
# Example multi-stage Dockerfile
FROM node:20-alpine AS builder
# Build stage...

FROM node:20-alpine AS runner
# Runtime stage (smaller image)...
```

**Docker AI (Gordon) Usage**:
- [ ] Generate Dockerfiles with `docker ai dockerfile`
- [ ] Optimize images with `docker ai optimize`
- [ ] Troubleshoot with `docker ai debug`

### Helm Chart Design

**Chart Structure**:
```text
helm/
├── Chart.yaml              # Chart metadata
├── values.yaml             # Default configuration values
├── values-dev.yaml         # Development overrides
├── values-prod.yaml        # Production overrides
└── templates/
    ├── deployment.yaml     # Kubernetes Deployments
    ├── service.yaml        # Kubernetes Services
    ├── ingress.yaml        # Ingress rules (if needed)
    ├── configmap.yaml      # Configuration
    ├── secrets.yaml        # Secrets (from external source)
    └── hpa.yaml            # Horizontal Pod Autoscaler (optional)
```

**Kubernetes Resources**:

| Resource | Name | Purpose | Replicas |
|----------|------|---------|----------|
| Deployment | `frontend` | [Next.js app] | [1-3] |
| Deployment | `backend` | [FastAPI API] | [1-3] |
| Service | `frontend-svc` | [ClusterIP/LoadBalancer] | N/A |
| Service | `backend-svc` | [ClusterIP] | N/A |
| ConfigMap | `app-config` | [Environment vars] | N/A |
| Secret | `app-secrets` | [API keys, DB creds] | N/A |

**Resource Requirements**:
```yaml
# Example resource limits
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

**kubectl-ai and kagent Usage**:
- [ ] Deploy with `kubectl ai deploy [feature]`
- [ ] Troubleshoot with `kagent diagnose [pod]`
- [ ] Scale with `kubectl ai scale [deployment]`

---

## Phase V: Event-Driven & Cloud-Native Architecture

> **Fill ONLY if this feature involves Kafka events, Dapr, microservices, or cloud deployment**

### Kafka Event Architecture

**Topics to Use**:

| Topic | Producer | Consumer(s) | Event Schema |
|-------|----------|-------------|--------------|
| `task-events` | [Backend API] | [Audit Service] | `{event_type, task_id, user_id, task_data, timestamp}` |
| `reminders` | [Recurring Task Service] | [Notification Service] | `{task_id, user_id, title, remind_at, timestamp}` |
| `task-updates` | [Backend API] | [WebSocket Service] | `{event_type, task_id, user_id, changes, timestamp}` |

**Event Schemas**:
```json
// task-events schema
{
  "event_type": "task.created | task.updated | task.deleted | task.completed",
  "task_id": 123,
  "user_id": 456,
  "task_data": { "title": "...", "description": "...", "..." },
  "timestamp": "2025-12-27T12:00:00Z"
}

// reminders schema
{
  "task_id": 123,
  "user_id": 456,
  "title": "Task title",
  "remind_at": "2025-12-27T15:00:00Z",
  "timestamp": "2025-12-27T12:00:00Z"
}
```

**Kafka Configuration**:
- **Platform**: [Redpanda Cloud / Strimzi on K8s / Confluent Cloud]
- **Partitions**: [Number per topic]
- **Replication Factor**: [1 for dev, 3 for prod]
- **Retention**: [7 days default]

### Dapr Components

**Components to Configure** (5 required):

1. **`kafka-pubsub`** - Pub/Sub for event streaming
   ```yaml
   # dapr-components/pubsub.yaml
   apiVersion: dapr.io/v1alpha1
   kind: Component
   metadata:
     name: kafka-pubsub
   spec:
     type: pubsub.kafka
     metadata:
       - name: brokers
         value: "localhost:9092"
   ```

2. **`statestore`** - PostgreSQL state management
   ```yaml
   # dapr-components/statestore.yaml
   apiVersion: dapr.io/v1alpha1
   kind: Component
   metadata:
     name: statestore
   spec:
     type: state.postgresql
   ```

3. **`dapr-jobs`** - Scheduled reminders (Jobs API)
   ```yaml
   # dapr-components/jobs.yaml
   # Configuration for job scheduling
   ```

4. **`kubernetes-secrets`** - Secrets management
   ```yaml
   # dapr-components/secrets.yaml
   # Reference to K8s secrets
   ```

5. **Service Invocation** - (Built-in, no config needed)

**Dapr Usage Patterns**:
- [ ] Publish events: `POST /v1.0/publish/kafka-pubsub/task-events`
- [ ] Subscribe to topics: `@app.route('/dapr/subscribe')`
- [ ] State management: `POST /v1.0/state/statestore`
- [ ] Schedule jobs: `POST /v1.0/jobs/schedule`

### Microservices Design

**Services to Implement**:

| Service | Type | Technology | Purpose | Kafka Topics |
|---------|------|------------|---------|--------------|
| Recurring Task Service | Consumer | [Python/Node] | Generate recurring tasks | Consumes: `task-events`, Produces: `task-events` |
| Notification Service | Consumer | [Python/Node] | Send reminders | Consumes: `reminders` | |
| Audit Service | Consumer | [Python/Node] | Log all task events | Consumes: `task-events` |
| WebSocket Service | Consumer/Server | [Node/FastAPI] | Real-time sync | Consumes: `task-updates` |

**Service Communication**:
```
Backend API → Kafka → Microservices
           ↓
      PostgreSQL
```

### Advanced Features (Phase V)

**Intermediate Features**:
- [ ] **Priorities** - High/Medium/Low priority levels
  - DB: `ALTER TABLE tasks ADD COLUMN priority VARCHAR(20) DEFAULT 'medium'`
- [ ] **Tags** - Categorize tasks with labels
  - DB: `ALTER TABLE tasks ADD COLUMN tags TEXT[]`
- [ ] **Search** - Full-text search by title/description
  - API: `GET /api/{user_id}/tasks?search=keyword`
- [ ] **Filter** - Filter by status, priority, tags
  - API: `GET /api/{user_id}/tasks?priority=high&status=pending`
- [ ] **Sort** - Sort by date, priority, title
  - API: `GET /api/{user_id}/tasks?sort=priority desc`

**Advanced Features**:
- [ ] **Recurring Tasks** - Daily, weekly, monthly patterns
  - DB: `ALTER TABLE tasks ADD COLUMN recurring VARCHAR(20)`
  - DB: `ALTER TABLE tasks ADD COLUMN recurring_interval INTEGER DEFAULT 1`
  - DB: `ALTER TABLE tasks ADD COLUMN parent_task_id INTEGER REFERENCES tasks(id)`
- [ ] **Due Dates** - Set task deadlines
  - DB: `ALTER TABLE tasks ADD COLUMN due_date TIMESTAMP`
- [ ] **Time Reminders** - Scheduled notifications
  - DB: `ALTER TABLE tasks ADD COLUMN remind_at TIMESTAMP`
  - DB: `ALTER TABLE tasks ADD COLUMN reminded BOOLEAN DEFAULT FALSE`

### Cloud Deployment Strategy

**Cloud Platform**: [Azure AKS / Google GKE / Oracle OKE]

**Infrastructure Components**:
- [ ] Kubernetes cluster (managed)
- [ ] Container registry (ACR/GCR/Docker Hub)
- [ ] PostgreSQL (managed database)
- [ ] Kafka/Redpanda (managed or self-hosted)
- [ ] Load balancer (managed)
- [ ] TLS certificates (Let's Encrypt via cert-manager)

**CI/CD Pipeline**:
```yaml
# .github/workflows/deploy.yml
# 1. Build Docker images
# 2. Push to container registry
# 3. Update Helm chart values
# 4. Deploy to Kubernetes with Helm
# 5. Run smoke tests
```

**DNS & TLS**:
- [ ] Domain: [your-domain.com]
- [ ] cert-manager with Let's Encrypt
- [ ] Ingress with TLS termination

**Monitoring & Observability**:
- [ ] [Prometheus/Grafana/DataDog/New Relic]
- [ ] Log aggregation: [ELK/Loki/Cloud provider]
- [ ] Distributed tracing: [Jaeger/Zipkin/OpenTelemetry]

---

## Implementation Phases

[Original phase breakdown section continues here...]
