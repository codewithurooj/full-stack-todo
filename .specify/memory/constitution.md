<!--
SYNC IMPACT REPORT
==================
Version Change: 2.0.0 → 3.0.0

Rationale: MAJOR version bump due to:
- Paradigm shift from web app to AI-powered chatbot with MCP architecture
- Addition of cloud-native principles (containerization, orchestration)
- Event-driven architecture requirements (Kafka, Dapr)
- New deployment models (Kubernetes, Helm)
- Microservices architecture introduction

Modified Principles:
- Architecture & Technology Stack: Extended to include AI/MCP components, containerization, Kubernetes
- RESTful API Design: Extended to include chat endpoint and MCP tools
- Data Management: Extended to include event streams and conversation state
- Testing & Quality Assurance: Expanded to include intermediate and advanced features
- Deployment & DevOps: Complete overhaul for multi-phase cloud-native deployment

Added Sections:
- VIII. AI & Conversational Interface (Phase III)
- IX. Containerization & Orchestration (Phase IV)
- X. Event-Driven Architecture (Phase V)
- XI. Cloud-Native Deployment (Phase V)
- XII. Microservices Architecture (Phase V)
- Feature Requirements: Intermediate Level (Phase V)
- Feature Requirements: Advanced Level (Phase V)
- Phase-specific deployment requirements

Removed Sections:
- None (all Phase II content preserved for backward compatibility)

Templates Requiring Updates:
- ✅ plan-template.md: Add sections for MCP tools, Kafka integration, Helm charts
- ✅ spec-template.md: Add AI agent behavior, event schema, microservices specs
- ✅ tasks-template.md: Add task types for containerization, K8s deployment, event handling
- ✅ CLAUDE.md files: Add MCP server patterns, Dapr usage, Kafka integration

Follow-up TODOs:
- Update plan template to include event-driven architecture section
- Update spec template to include MCP tool specifications
- Add Helm chart template for Kubernetes deployments
- Create Dapr component configuration templates

Last Updated: 2025-12-27
-->

# Full-Stack Todo Application Constitution
<!-- Phases II, III, IV, V: Evolution from Web Application to Cloud-Native AI System -->

**Version**: 3.0.0
**Ratified**: 2025-12-11
**Last Amended**: 2025-12-27
**Current Phase**: III-V (AI Chatbot to Cloud-Native Deployment)

---

## Core Principles

### I. Spec-Driven Development (NON-NEGOTIABLE)
**Every feature must be specified before implementation - no exceptions.**

- Write detailed specifications in Markdown before any code
- Specifications must include user stories, acceptance criteria, and API contracts
- Use Claude Code to generate implementation from refined specifications
- **Constraint**: Manual code writing is PROHIBITED - refine specs until Claude Code generates correct output
- All specs stored in `/specs` directory with clear organization by type:
  - `/specs/features/` - Feature specifications (what to build)
  - `/specs/api/` - API contracts and MCP tool specifications
  - `/specs/database/` - Schema definitions and event schemas
  - `/specs/ui/` - Component and page specifications
- Specs must be versioned and updated when requirements change
- Create ADRs (Architecture Decision Records) for significant decisions in `/history/adr/`
- Record prompt history in `/history/prompts/` for learning and traceability

**Workflow**:
```bash
# 1. Write specification
# Edit specs/features/your-feature.md

# 2. Generate plan
/sp.plan

# 3. Break into tasks
/sp.tasks

# 4. Implement
/sp.implement

# 5. Record prompt history
/sp.phr
```

### II. Architecture & Technology Stack
**Monorepo structure with progressive enhancement from web app to cloud-native AI system.**

#### Phase II: Full-Stack Web Application
**Frontend**:
- Next.js 16+ (App Router only)
- TypeScript for type safety
- Tailwind CSS for styling (no inline styles)
- Server components by default, client components only when necessary
- Better Auth for authentication

**Backend**:
- Python FastAPI for REST API
- SQLModel for ORM
- Neon Serverless PostgreSQL for database
- Stateless API design

#### Phase III: AI-Powered Chatbot
**AI & Conversational Layer**:
- OpenAI ChatKit for conversational UI
- OpenAI Agents SDK for agent orchestration
- Official MCP SDK for Model Context Protocol server
- 5 custom MCP tools for task operations (add, list, complete, delete, update)
- Stateless chat endpoint with database-persisted conversation history

**Additional Database Tables**:
- `conversations` - Chat session tracking
- `messages` - Conversation history (user/assistant messages)

#### Phase IV: Containerization & Kubernetes
**Container & Orchestration**:
- Docker for containerization (multi-stage builds)
- Docker AI (Gordon) for intelligent Docker operations
- Kubernetes for orchestration (Minikube locally)
- Helm Charts for deployment management
- kubectl-ai and kagent for AI-powered Kubernetes operations

**DevOps Tools**:
- Docker Desktop 4.53+ with Gordon enabled
- Minikube for local Kubernetes cluster
- Helm 3+ for package management

#### Phase V: Cloud-Native & Event-Driven
**Event Streaming**:
- Kafka for event-driven architecture (Redpanda Cloud or Strimzi)
- 3 Kafka topics: `task-events`, `reminders`, `task-updates`
- Dapr for distributed application runtime

**Microservices**:
- Recurring Task Service (Kafka consumer)
- Notification Service (Kafka consumer)
- Audit Service (optional, Kafka consumer)
- WebSocket Service (optional, real-time sync)

**Cloud Deployment**:
- Azure AKS, Google Cloud GKE, or Oracle Cloud OKE
- Container registry (ACR, GCR, or Docker Hub)
- GitHub Actions for CI/CD
- TLS/HTTPS via cert-manager and Let's Encrypt
- Monitoring via Prometheus + Grafana or Application Insights

**Dapr Components** (5 required):
1. `kafka-pubsub` - Pub/Sub for event streaming
2. `statestore` - PostgreSQL state management
3. `dapr-jobs` - Scheduled reminders (Jobs API)
4. `kubernetes-secrets` - Secrets management
5. Service invocation (implicit, built-in)

### III. RESTful API Design
**Consistent, predictable API contracts with stateless architecture.**

#### Phase II: Basic CRUD Endpoints
- Base path: `/api/{user_id}/`
- Standard HTTP methods: GET, POST, PUT, DELETE, PATCH
- JSON request/response format
- Pydantic models for validation
- HTTPException for error handling
- JWT token in `Authorization: Bearer <token>` header

**API Endpoints**:
```
GET    /api/{user_id}/tasks           - List all tasks
POST   /api/{user_id}/tasks           - Create new task
GET    /api/{user_id}/tasks/{id}      - Get task details
PUT    /api/{user_id}/tasks/{id}      - Update task
DELETE /api/{user_id}/tasks/{id}      - Delete task
PATCH  /api/{user_id}/tasks/{id}/complete - Toggle completion
```

#### Phase III: Chat Endpoint
```
POST   /api/{user_id}/chat            - Conversational interface
```

**Request**:
```json
{
  "conversation_id": 123,  // Optional
  "message": "Add a task to buy groceries"
}
```

**Response**:
```json
{
  "conversation_id": 123,
  "response": "I've added 'Buy groceries' to your task list.",
  "tool_calls": [{"tool": "add_task", "parameters": {...}}]
}
```

**Stateless Request Cycle** (CRITICAL):
1. Receive user message
2. Fetch conversation history from database
3. Build message array (history + new message)
4. Store user message in database
5. Run OpenAI Agent with MCP tools
6. Agent invokes appropriate MCP tool(s)
7. Store assistant response in database
8. Return response to client
9. Server holds NO state (ready for next request)

### IV. Data Management
**Database-first with clear schema definitions and event-driven state.**

#### Phase II: Core Tables
- `users` - Managed by Better Auth (id, email, name, created_at)
- `tasks` - Core task data (user_id, id, title, description, completed, created_at, updated_at)
- Indexes on user_id and completed fields

#### Phase III: Conversation Tables
- `conversations` - Chat sessions (id, user_id, created_at, updated_at)
- `messages` - Chat history (id, user_id, conversation_id, role, content, created_at)

#### Phase V: Extended Task Schema
**Intermediate Features**:
```sql
ALTER TABLE tasks ADD COLUMN priority VARCHAR(20) DEFAULT 'medium';  -- high/medium/low
ALTER TABLE tasks ADD COLUMN tags TEXT[];  -- PostgreSQL array
CREATE INDEX idx_tasks_priority ON tasks(priority);
```

**Advanced Features**:
```sql
ALTER TABLE tasks ADD COLUMN recurring VARCHAR(20);  -- none/daily/weekly/monthly
ALTER TABLE tasks ADD COLUMN recurring_interval INTEGER DEFAULT 1;
ALTER TABLE tasks ADD COLUMN parent_task_id INTEGER REFERENCES tasks(id);
ALTER TABLE tasks ADD COLUMN due_date TIMESTAMP;
ALTER TABLE tasks ADD COLUMN remind_at TIMESTAMP;
ALTER TABLE tasks ADD COLUMN reminded BOOLEAN DEFAULT FALSE;
```

**Event Schemas**:
- Task Event: `{ event_type, task_id, user_id, task_data, timestamp }`
- Reminder Event: `{ task_id, user_id, title, remind_at, timestamp }`
- Task Update: `{ event_type, task_id, user_id, changes, timestamp }`

**Data Isolation**:
- User data segregated at query level (all queries filter by user_id)
- No cross-user data access
- JWT token user_id must match URL user_id
- Event streams partitioned by user_id

### V. Testing & Quality Assurance
**Comprehensive testing across all feature levels and deployment stages.**

#### Phase II: Basic Level Features (MUST WORK)
- Add Task (title required 1-200 chars, description optional max 1000 chars)
- Delete Task (by ID, owner-only)
- Update Task (title and/or description)
- View Task List (with status indicators, user-filtered)
- Mark as Complete/Incomplete (toggle, owner-only)

#### Phase III: AI Chatbot Features
- Natural language understanding for all 5 basic operations
- MCP tools functional and stateless
- Conversation persistence across sessions
- Error handling for invalid commands
- Graceful degradation when AI unavailable

**Natural Language Test Cases**:
```
"Add a task to buy groceries"      → add_task
"Show me all my tasks"              → list_tasks (status: all)
"What's pending?"                   → list_tasks (status: pending)
"Mark task 3 as complete"           → complete_task (task_id: 3)
"Delete the meeting task"           → list_tasks + delete_task
"Change task 1 to 'Call mom'"       → update_task
```

#### Phase V: Intermediate Features (MUST WORK)
- Priorities & Tags: Assign and filter by priority (high/medium/low) and tags
- Search & Filter: Search by keyword, filter by status/priority/tags/date
- Sort Tasks: By due_date, priority, created_at, or title

#### Phase V: Advanced Features (MUST WORK)
- Recurring Tasks: Auto-create next occurrence when completed
- Due Dates & Reminders: Browser notifications at scheduled times

#### Testing Strategy
- Manual testing after each feature
- Automated testing via testing-agent (E2E)
- Integration testing for event-driven flows
- Load testing for scalability validation (kubectl, hey, or k6)
- 90%+ test coverage goal

### VI. Code Quality Standards
**Clean, maintainable, production-ready code across all services.**

**General Standards**:
- Follow clean code principles
- No hardcoded values - use environment variables
- Meaningful variable and function names
- No duplicate code - DRY principle
- Type hints in Python, TypeScript types in frontend
- Proper error messages for debugging
- Environment-based configuration (dev/staging/prod)

**Project Structure**:
```
Backend:
- main.py - FastAPI app entry point
- models.py - SQLModel database models
- routes/ - API route handlers
- db.py - Database connection
- mcp_server/ - MCP server and tools (Phase III)

Frontend:
- /components - Reusable UI components
- /app - Pages and layouts (App Router)
- /lib - Utility functions and API client

Services (Phase V):
- /services/recurring-task-service
- /services/notification-service
- /services/audit-service (optional)
```

**Code Patterns**:
- Server components by default (Next.js)
- Client components only for interactivity
- API calls through `/lib/api.ts`
- Tailwind CSS classes (no inline styles)
- Pydantic models for validation
- HTTPException for errors
- Async/await for I/O operations

### VII. Documentation & Repository Standards
**Clear, comprehensive documentation for multi-phase evolution.**

**Required Files**:
- `README.md` - Setup instructions, tech stack, all features
- `CLAUDE.md` - Root Claude Code instructions
- `frontend/CLAUDE.md` - Frontend-specific patterns
- `backend/CLAUDE.md` - Backend-specific patterns
- `/specs` - All specification files organized by type
- `/history/prompts` - Prompt history records (PHRs)
- `/history/adr` - Architecture Decision Records
- `.env.example` - Environment variable template
- `requirements.txt` (backend) and `package.json` (frontend)
- `roadmap.md` - Complete implementation roadmap for all phases

**Phase IV+ Additional Files**:
- `frontend/Dockerfile` - Multi-stage container build
- `backend/Dockerfile` - Python container
- `/charts/frontend` - Helm chart for frontend
- `/charts/backend` - Helm chart for backend
- `/charts/services` - Helm charts for microservices
- `/dapr-components` - Dapr component configurations
- `.github/workflows/deploy.yml` - CI/CD pipeline

**Folder Structure**:
```
full-stack-todo/
├── .github/
│   └── workflows/
│       └── deploy.yml           # CI/CD pipeline
├── .specify/
│   ├── memory/
│   │   └── constitution.md      # This file
│   └── templates/
├── specs/
│   ├── overview.md
│   ├── features/                # Feature specs
│   ├── api/                     # API & MCP tool specs
│   ├── database/                # Schema specs
│   └── ui/                      # UI component specs
├── history/
│   ├── prompts/                 # PHRs
│   └── adr/                     # ADRs
├── frontend/
│   ├── Dockerfile
│   ├── CLAUDE.md
│   └── [Next.js app]
├── backend/
│   ├── Dockerfile
│   ├── CLAUDE.md
│   ├── mcp_server/              # MCP tools
│   └── [FastAPI app]
├── services/                     # Microservices (Phase V)
│   ├── recurring-task-service/
│   ├── notification-service/
│   └── audit-service/
├── charts/                       # Helm charts (Phase IV+)
│   ├── frontend/
│   ├── backend/
│   └── services/
├── dapr-components/              # Dapr configs (Phase V)
├── CLAUDE.md                     # Root instructions
├── README.md
├── roadmap.md
└── docker-compose.yml
```

---

## Phase-Specific Requirements

### VIII. AI & Conversational Interface (Phase III)

**MCP (Model Context Protocol) Server**:
- 5 stateless MCP tools required:
  1. `add_task` - Create new task
  2. `list_tasks` - Retrieve tasks with filtering
  3. `complete_task` - Mark task complete
  4. `delete_task` - Remove task
  5. `update_task` - Modify task details
- All tools accept `user_id` parameter
- All tools return consistent JSON: `{ task_id, status, title }`
- Tools must be stateless (no in-memory state)
- All state stored in database

**OpenAI Agents SDK Integration**:
- Agent orchestrates MCP tool calls based on natural language
- Runner manages agent execution lifecycle
- Conversation history maintained in database
- No server-side session state

**ChatKit Frontend**:
- OpenAI domain allowlist configured (production deployments)
- `NEXT_PUBLIC_OPENAI_DOMAIN_KEY` environment variable set
- Conversational UI with message history
- Real-time response streaming
- Error handling for AI failures

**Agent Behavior**:
- Task Creation: Detect add/create/remember intents → `add_task`
- Task Listing: Detect show/list/view intents → `list_tasks`
- Task Completion: Detect done/complete/finish intents → `complete_task`
- Task Deletion: Detect delete/remove/cancel intents → `delete_task`
- Task Update: Detect change/update/rename intents → `update_task`
- Confirmation: Always respond with friendly confirmation
- Error Handling: Graceful error messages for task not found, etc.

**Security**:
- JWT authentication on chat endpoint
- User isolation enforced in MCP tools
- No cross-user conversation access
- OpenAI API key secured in environment variables

### IX. Containerization & Orchestration (Phase IV)

**Docker Requirements**:
- Multi-stage builds for optimized image size
- Frontend: Node 20 Alpine base image
- Backend: Python 3.13 Slim base image
- No secrets in images (use environment variables)
- Health checks defined in Dockerfiles
- `.dockerignore` files to exclude unnecessary files

**Kubernetes Deployment** (Minikube Local):
- Minimum 2 replicas per service for high availability
- Resource limits and requests defined
- Liveness and readiness probes configured
- ConfigMaps for configuration
- Secrets for sensitive data
- Service type: ClusterIP for internal, Ingress for external access

**Helm Charts**:
- Separate charts for frontend and backend
- Values files for dev/staging/prod environments
- Templated deployments, services, ingress
- Version pinning for reproducibility
- Release management via `helm upgrade --install`

**AI-Powered DevOps**:
- Docker AI (Gordon) for Dockerfile generation and optimization
- kubectl-ai for natural language Kubernetes operations
- kagent for cluster health analysis and optimization
- Examples:
  ```bash
  docker ai "Create optimized multi-stage Dockerfile for Next.js 16"
  kubectl-ai "scale backend to 3 replicas"
  kubectl-ai "check why pods are failing"
  kagent "analyze cluster health"
  ```

**Local Development**:
- Minikube cluster (4 CPUs, 8GB RAM minimum)
- Ingress addon enabled
- Metrics server enabled
- Images loaded into Minikube: `minikube image load`
- Access via port-forward, NodePort, or Minikube tunnel

### X. Event-Driven Architecture (Phase V)

**Kafka Integration**:
- Event streaming platform (Redpanda Cloud or self-hosted Strimzi)
- 3 topics: `task-events`, `reminders`, `task-updates`
- Producer: Chat API publishes events on task operations
- Consumers: Microservices consume and react to events
- At-least-once delivery semantics
- Consumer groups for scalability

**Event Use Cases**:
1. **Reminder/Notification System**:
   - Producer: Chat API → `reminders` topic
   - Consumer: Notification Service → Browser notifications

2. **Recurring Task Engine**:
   - Producer: Chat API → `task-events` topic (task completed)
   - Consumer: Recurring Task Service → Create next occurrence

3. **Activity/Audit Log**:
   - Producer: Chat API → `task-events` topic (all operations)
   - Consumer: Audit Service → Log to database

4. **Real-time Sync** (Optional):
   - Producer: Chat API → `task-updates` topic
   - Consumer: WebSocket Service → Broadcast to connected clients

**Event Schemas**:
```json
// Task Event
{
  "event_type": "created|updated|completed|deleted",
  "task_id": 123,
  "user_id": "user123",
  "task_data": { ... },
  "timestamp": "2025-01-18T10:30:00Z"
}

// Reminder Event
{
  "task_id": 123,
  "user_id": "user123",
  "title": "Buy groceries",
  "remind_at": "2025-01-18T14:00:00Z",
  "timestamp": "2025-01-18T10:30:00Z"
}
```

**Kafka Configuration**:
- Bootstrap servers from environment variables
- SASL/SSL authentication for cloud deployments
- Consumer group IDs: `recurring-task-service`, `notification-service`, etc.
- Partitioning by user_id for ordering guarantees

### XI. Cloud-Native Deployment (Phase V)

**Cloud Kubernetes Platforms** (choose one):
- **Azure AKS**: $200 credit for 30 days
- **Google Cloud GKE**: $300 credit for 90 days
- **Oracle Cloud OKE**: Always free (4 OCPUs, 24GB RAM) - RECOMMENDED

**Container Registry**:
- Azure: Azure Container Registry (ACR)
- GCP: Google Container Registry (GCR)
- Oracle: Oracle Cloud Infrastructure Registry (OCIR)
- Alternative: Docker Hub (public/private)

**Dapr Deployment**:
- Dapr CLI installed: `dapr init -k`
- Dapr control plane in `dapr-system` namespace
- 5 Dapr components configured (see Section XII)
- Sidecar injection via annotations:
  ```yaml
  annotations:
    dapr.io/enabled: "true"
    dapr.io/app-id: "backend-service"
    dapr.io/app-port: "8000"
  ```

**Ingress & TLS**:
- Nginx Ingress Controller installed
- cert-manager for automatic TLS certificates
- Let's Encrypt for free SSL/TLS
- DNS A record pointing to LoadBalancer IP
- HTTPS enforcement (HTTP → HTTPS redirect)

**CI/CD Pipeline** (GitHub Actions):
- Trigger on push to `main` branch
- Build and push Docker images (tagged with git SHA)
- Deploy to Kubernetes via Helm
- Automated rollout verification
- Secrets stored in GitHub repository secrets

**Monitoring & Logging**:
- Prometheus + Grafana for metrics (or cloud-native equivalents)
- Application Insights (Azure) or Cloud Monitoring (GCP)
- Dapr dashboard for distributed tracing
- kubectl top for resource monitoring
- Centralized logging (optional: ELK stack)

### XII. Microservices Architecture (Phase V)

**Service Communication Patterns**:
- **Synchronous**: HTTP/gRPC via Dapr service invocation
- **Asynchronous**: Kafka pub/sub via Dapr pubsub component
- **State**: Dapr state management (PostgreSQL backend)
- **Secrets**: Dapr secrets (Kubernetes secrets backend)
- **Scheduling**: Dapr Jobs API for time-based triggers

**Dapr Components** (Required):

1. **kafka-pubsub** (`dapr-components/kafka-pubsub.yaml`):
   ```yaml
   apiVersion: dapr.io/v1alpha1
   kind: Component
   metadata:
     name: kafka-pubsub
   spec:
     type: pubsub.kafka
     version: v1
     metadata:
       - name: brokers
         value: "kafka-bootstrap-url:9092"
       - name: authType
         value: "password"
       - name: consumerGroup
         value: "todo-service"
   ```

2. **statestore** (`dapr-components/statestore.yaml`):
   ```yaml
   apiVersion: dapr.io/v1alpha1
   kind: Component
   metadata:
     name: statestore
   spec:
     type: state.postgresql
     version: v1
     metadata:
       - name: connectionString
         secretKeyRef:
           name: db-secret
           key: connectionString
   ```

3. **dapr-jobs** (`dapr-components/dapr-jobs.yaml`):
   ```yaml
   apiVersion: dapr.io/v1alpha1
   kind: Component
   metadata:
     name: dapr-jobs
   spec:
     type: jobs.postgresql
     version: v1
     metadata:
       - name: connectionString
         secretKeyRef:
           name: db-secret
           key: connectionString
   ```

4. **kubernetes-secrets** (`dapr-components/kubernetes-secrets.yaml`):
   ```yaml
   apiVersion: dapr.io/v1alpha1
   kind: Component
   metadata:
     name: kubernetes-secrets
   spec:
     type: secretstores.kubernetes
     version: v1
   ```

5. **Service Invocation**: Built-in, no component file needed

**Dapr API Usage**:
```python
# Publish event via Dapr
await httpx.post(
    "http://localhost:3500/v1.0/publish/kafka-pubsub/task-events",
    json=event_data
)

# Save state via Dapr
await httpx.post(
    "http://localhost:3500/v1.0/state/statestore",
    json=[{"key": f"conversation-{id}", "value": messages}]
)

# Schedule job via Dapr
await httpx.post(
    f"http://localhost:3500/v1.0-alpha1/jobs/reminder-{task_id}",
    json={"dueTime": remind_at, "data": {...}}
)

# Invoke service via Dapr
fetch("http://localhost:3500/v1.0/invoke/backend-service/method/api/chat")
```

**Microservice Specifications**:

1. **Recurring Task Service**:
   - Consumes: `task-events` topic
   - Trigger: `event_type == "completed"` AND `recurring != "none"`
   - Action: Calculate next due_date, create new task
   - Deployment: Single replica, consumer group

2. **Notification Service**:
   - Consumes: `reminders` topic
   - Trigger: Reminder event received
   - Action: Schedule via Dapr Jobs API, send browser notification
   - Deployment: Single replica, consumer group

3. **Audit Service** (Optional):
   - Consumes: `task-events` topic
   - Trigger: All events
   - Action: Log to audit table
   - Deployment: Single replica, consumer group

---

## Security & Authentication Requirements

### User Authentication
- Better Auth integration required (Phases II-V)
- JWT tokens for API authentication
- Shared secret (`BETTER_AUTH_SECRET`) between frontend and backend
- Token expiry enforcement (default 7 days)
- Secure password handling (managed by Better Auth)
- OpenAI API key for Agents SDK (Phase III+)

### API Security
- JWT verification middleware on all protected routes
- User ID from token must match user_id in URL
- No cross-user data access
- SQL injection prevention via SQLModel/Pydantic
- CORS configuration for production
- Environment-based configuration (dev/prod)
- Rate limiting on chat endpoint (Phase III+)

### Data Privacy
- User isolation enforced at database query level
- Event streams partitioned by user_id (Phase V)
- No shared data between users
- Proper error messages (no sensitive data leakage)
- Secure connection strings (environment variables only)
- Kubernetes secrets for sensitive data (Phase IV+)

### Container & Kubernetes Security
- Non-root containers
- Read-only root filesystem where possible
- Resource limits to prevent resource exhaustion
- Network policies for service isolation (optional)
- RBAC for Kubernetes service accounts
- Image scanning for vulnerabilities (optional)

---

## Feature Requirements

### Basic Level Features (Phase II - MUST WORK)

#### 1. Add Task
- **User Story**: As a user, I can create a new task with a title and optional description
- **Acceptance Criteria**:
  - Title is required (1-200 characters)
  - Description is optional (max 1000 characters)
  - Task is associated with authenticated user
  - Newly created task appears in task list
  - Default status is "incomplete"
  - **Phase III**: Also accessible via natural language ("Add a task to...")

#### 2. Delete Task
- **User Story**: As a user, I can remove tasks I no longer need
- **Acceptance Criteria**:
  - User can delete task by ID
  - Only task owner can delete
  - Confirmation before deletion (UI)
  - Task removed from database
  - UI updates after deletion
  - **Phase III**: Also accessible via natural language ("Delete task 3")

#### 3. Update Task
- **User Story**: As a user, I can modify task details
- **Acceptance Criteria**:
  - Can update title and/or description
  - Only task owner can update
  - Changes persist in database
  - UI reflects updates immediately
  - Validation same as create
  - **Phase III**: Also accessible via natural language ("Change task 1 to...")

#### 4. View Task List
- **User Story**: As a user, I can see all my tasks
- **Acceptance Criteria**:
  - Display all tasks for current user only
  - Show title, status, created date
  - Clear visual distinction between complete/incomplete
  - Responsive design
  - Empty state when no tasks
  - **Phase III**: Also accessible via natural language ("Show me my tasks")

#### 5. Mark as Complete
- **User Story**: As a user, I can toggle task completion status
- **Acceptance Criteria**:
  - Toggle between complete/incomplete
  - Visual feedback (checkbox, strikethrough, etc.)
  - Status persists in database
  - Only task owner can toggle
  - Immediate UI update
  - **Phase III**: Also accessible via natural language ("Mark task 2 as complete")

---

### Intermediate Level Features (Phase V - MUST WORK)

#### 1. Priorities & Tags/Categories
- **User Story**: As a user, I can assign priorities and tags to organize my tasks
- **Acceptance Criteria**:
  - Priority levels: high, medium, low (default: medium)
  - Tags as array of strings (e.g., ["work", "personal"])
  - Can filter task list by priority
  - Can filter task list by tags
  - Priority and tags visible in UI
  - Update via natural language supported

**Database**:
```sql
ALTER TABLE tasks ADD COLUMN priority VARCHAR(20) DEFAULT 'medium';
ALTER TABLE tasks ADD COLUMN tags TEXT[];
CREATE INDEX idx_tasks_priority ON tasks(priority);
```

#### 2. Search & Filter
- **User Story**: As a user, I can search and filter tasks to find what I need
- **Acceptance Criteria**:
  - Search by keyword (in title or description)
  - Filter by status (pending/completed)
  - Filter by priority (high/medium/low)
  - Filter by tags
  - Filter by date range (created_at, due_date)
  - Filters can be combined
  - Results update in real-time

**MCP Tool** (Optional):
```python
def search_tasks(user_id: str, query: str, filters: dict):
    """
    filters: {
        "status": "pending",
        "priority": "high",
        "tags": ["work"],
        "date_from": "2025-01-01",
        "date_to": "2025-12-31"
    }
    """
```

#### 3. Sort Tasks
- **User Story**: As a user, I can sort my tasks in different ways
- **Acceptance Criteria**:
  - Sort by due_date (ascending/descending)
  - Sort by priority (high → medium → low)
  - Sort by created_at
  - Sort alphabetically by title
  - Sort order persists in session
  - Natural language sorting supported ("Sort by priority")

**Updated MCP Tool**:
```python
def list_tasks(user_id: str, status: str = "all", sort_by: str = "created_at"):
    # sort_by: "due_date", "priority", "created_at", "title"
```

---

### Advanced Level Features (Phase V - MUST WORK)

#### 1. Recurring Tasks
- **User Story**: As a user, I can set tasks to recur automatically
- **Acceptance Criteria**:
  - Recurrence options: none, daily, weekly, monthly
  - When recurring task marked complete, new task auto-created
  - New task has same title, description, priority, tags
  - New task's due_date calculated based on recurrence interval
  - Reference to parent_task_id maintained
  - Recurring task chain visible in UI

**Database**:
```sql
ALTER TABLE tasks ADD COLUMN recurring VARCHAR(20);  -- none/daily/weekly/monthly
ALTER TABLE tasks ADD COLUMN recurring_interval INTEGER DEFAULT 1;
ALTER TABLE tasks ADD COLUMN parent_task_id INTEGER REFERENCES tasks(id);
```

**Event Flow**:
1. Task completed → Publish `task-events` (event_type: "completed")
2. Recurring Task Service consumes event
3. If `recurring != "none"`, calculate next due_date
4. Create new task with same properties, new due_date

#### 2. Due Dates & Time Reminders
- **User Story**: As a user, I can set due dates and receive reminders
- **Acceptance Criteria**:
  - Can set due_date (date/time picker in UI)
  - Can set remind_at (date/time picker in UI)
  - Browser notification at remind_at time
  - Overdue tasks visually highlighted
  - Reminder fires only once (reminded flag)
  - Natural language date parsing ("tomorrow at 3pm")

**Database**:
```sql
ALTER TABLE tasks ADD COLUMN due_date TIMESTAMP;
ALTER TABLE tasks ADD COLUMN remind_at TIMESTAMP;
ALTER TABLE tasks ADD COLUMN reminded BOOLEAN DEFAULT FALSE;
```

**Event Flow**:
1. Task with remind_at created → Publish `reminders` event
2. Notification Service consumes event
3. Schedule via Dapr Jobs API for exact time
4. At scheduled time, send browser notification
5. Mark task as reminded

**Browser Notification**:
```typescript
if ('Notification' in window) {
  Notification.requestPermission();
}

new Notification('Task Reminder', {
  body: 'Buy groceries is due in 1 hour',
  icon: '/icon.png'
});
```

---

## Deployment & DevOps

### Phase II: Basic Web Deployment

**Frontend Deployment**:
- Deploy to Vercel (free tier)
- Environment variables configured in Vercel dashboard
- Public URL required for submission
- Better Auth domain allowlist configured

**Backend Deployment**:
- FastAPI server deployed (Railway, Render, or similar)
- Public API URL required
- Environment variables configured
- CORS enabled for frontend domain
- Database connection to Neon DB

**Environment Variables**:

**Frontend**:
```env
NEXT_PUBLIC_API_URL=https://backend.example.com
BETTER_AUTH_SECRET=your-secret-key-min-32-chars
```

**Backend**:
```env
DATABASE_URL=postgresql://user:pass@host.neon.tech/dbname
BETTER_AUTH_SECRET=your-secret-key-min-32-chars
ALLOWED_ORIGINS=https://frontend.vercel.app
```

### Phase III: AI Chatbot Deployment

**Additional Frontend Variables**:
```env
NEXT_PUBLIC_OPENAI_DOMAIN_KEY=your-openai-domain-key
```

**Additional Backend Variables**:
```env
OPENAI_API_KEY=sk-your-openai-api-key
```

**OpenAI Domain Allowlist**:
1. Deploy frontend to get production URL
2. Add domain at: https://platform.openai.com/settings/organization/security/domain-allowlist
3. Get domain key from OpenAI
4. Set in frontend environment variables

### Phase IV: Kubernetes Local Deployment

**Minikube Setup**:
```bash
minikube start --cpus=4 --memory=8192
minikube addons enable ingress
minikube addons enable metrics-server
```

**Image Management**:
```bash
# Build images
docker build -t todo-frontend:latest ./frontend
docker build -t todo-backend:latest ./backend

# Load into Minikube
eval $(minikube docker-env)
docker build -t todo-frontend:latest ./frontend
docker build -t todo-backend:latest ./backend
```

**Helm Deployment**:
```bash
helm install frontend ./charts/frontend
helm install backend ./charts/backend

# Verify
kubectl get pods
kubectl get services
kubectl get ingress
```

**Access Application**:
```bash
# Option 1: Port forward
kubectl port-forward svc/frontend 3000:3000

# Option 2: Minikube tunnel
minikube tunnel

# Option 3: Ingress
echo "$(minikube ip) todo.local" | sudo tee -a /etc/hosts
open http://todo.local
```

### Phase V: Cloud Kubernetes Deployment

**Cloud Provider Setup**:

**Azure AKS**:
```bash
az aks create --resource-group todo-rg --name todo-cluster --node-count 2
az aks get-credentials --resource-group todo-rg --name todo-cluster
```

**Google Cloud GKE**:
```bash
gcloud container clusters create todo-cluster --num-nodes=2
gcloud container clusters get-credentials todo-cluster
```

**Oracle Cloud OKE** (Always Free):
- Create via OCI Console
- Download kubeconfig
- Set KUBECONFIG environment variable

**Container Registry**:
```bash
# Azure ACR
az acr create --name todoregistry --sku Basic
docker tag todo-frontend:latest todoregistry.azurecr.io/todo-frontend:latest
docker push todoregistry.azurecr.io/todo-frontend:latest

# Google GCR
docker tag todo-frontend:latest gcr.io/PROJECT_ID/todo-frontend:latest
docker push gcr.io/PROJECT_ID/todo-frontend:latest
```

**Kafka Deployment**:

**Option 1: Redpanda Cloud** (Recommended):
- Sign up at redpanda.com/cloud
- Create Serverless cluster (free tier)
- Create topics: task-events, reminders, task-updates
- Get bootstrap server URL and credentials

**Option 2: Strimzi Self-Hosted**:
```bash
kubectl create namespace kafka
kubectl apply -f https://strimzi.io/install/latest?namespace=kafka
kubectl apply -f kafka-cluster.yaml
```

**Dapr Deployment**:
```bash
# Initialize Dapr
dapr init -k

# Verify
kubectl get pods -n dapr-system

# Apply components
kubectl apply -f dapr-components/
```

**Application Deployment**:
```bash
# Deploy services
helm install frontend ./charts/frontend -f values-cloud.yaml
helm install backend ./charts/backend -f values-cloud.yaml
helm install notification-service ./charts/notification-service
helm install recurring-service ./charts/recurring-service

# Verify
kubectl get pods
kubectl get services
kubectl get ingress
```

**TLS/HTTPS Setup**:
```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Install nginx ingress
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Get LoadBalancer IP
kubectl get svc -n ingress-nginx

# Add DNS A record
# todo.yourdomain.com → <EXTERNAL-IP>
```

**CI/CD Pipeline** (GitHub Actions):
```yaml
# .github/workflows/deploy.yml
on:
  push:
    branches: [main]

jobs:
  deploy:
    - Build and push images (tagged with git SHA)
    - Deploy via Helm
    - Verify rollout
```

---

## Governance

### Constitution Authority
- This constitution supersedes all other development practices
- All code, specs, and architectural decisions MUST comply
- Amendments require documentation and version update
- Non-compliance blocks submission acceptance

### Version Control
- **MAJOR**: Backward incompatible changes (e.g., Phase II → III → IV → V transitions)
- **MINOR**: New features, principles, or sections added
- **PATCH**: Clarifications, typos, non-semantic refinements

**Current Version**: 3.0.0 (MAJOR bump for Phases III-V additions)

### Quality Gates

**Phase II**:
- All 5 Basic Level features work end-to-end
- Specs written for every feature
- User authentication working (Better Auth)
- API requires JWT tokens
- User data isolation enforced
- No hardcoded secrets
- Frontend deployed to Vercel
- Backend deployed and accessible

**Phase III**:
- All Phase II gates PLUS:
- Chatbot interface functional
- 5 MCP tools implemented and tested
- Natural language commands working
- Conversation persistence functional
- OpenAI domain allowlist configured

**Phase IV**:
- All Phase III gates PLUS:
- Dockerfiles created (frontend + backend)
- Helm charts created and tested
- Deployed to Minikube successfully
- Application accessible locally
- kubectl-ai used for operations

**Phase V**:
- All Phase IV gates PLUS:
- Intermediate features (priorities, tags, search, filter, sort) working
- Advanced features (recurring tasks, reminders) working
- Kafka event-driven architecture functional
- 5 Dapr components configured and working
- Deployed to cloud Kubernetes
- CI/CD pipeline functional
- TLS/HTTPS enabled
- Monitoring setup

### Review Checklist (Phase V Final Submission)

**Features**:
- [ ] All 5 Basic Level features work
- [ ] All 3 Intermediate Level features work
- [ ] All 2 Advanced Level features work
- [ ] Chatbot interface functional
- [ ] Natural language understanding working

**Architecture**:
- [ ] MCP server with 5 tools
- [ ] Kafka event streaming (3 topics)
- [ ] Dapr components (5 configured)
- [ ] Microservices (recurring, notification)
- [ ] Stateless architecture verified

**Deployment**:
- [ ] Docker images built and pushed
- [ ] Helm charts created
- [ ] Deployed to cloud Kubernetes
- [ ] TLS/HTTPS enabled
- [ ] CI/CD pipeline functional
- [ ] Monitoring configured

**Documentation**:
- [ ] README comprehensive
- [ ] CLAUDE.md files present
- [ ] Specs documented in /specs
- [ ] PHRs recorded in /history/prompts
- [ ] ADRs for major decisions
- [ ] Roadmap.md complete

**Security**:
- [ ] JWT authentication on all endpoints
- [ ] User data isolation enforced
- [ ] No hardcoded secrets
- [ ] Kubernetes secrets for sensitive data
- [ ] CORS properly configured

**Quality**:
- [ ] Demo video created (<90 seconds)
- [ ] GitHub repository is public
- [ ] All tests passing
- [ ] No critical vulnerabilities

### Continuous Improvement
- Document learnings in `/history/prompts/`
- Create ADRs for significant architectural decisions in `/history/adr/`
- Update specs when requirements change
- Maintain version history in git
- Iterative refinement encouraged
- Share knowledge with community

---

## Constraints & Non-Negotiables

### Mandatory Requirements (All Phases)
- ✅ Spec-driven development (no manual coding)
- ✅ Better Auth for user authentication
- ✅ JWT-based API security
- ✅ User data isolation
- ✅ Monorepo structure with /specs folder
- ✅ Public GitHub repository
- ✅ Deployed and accessible application
- ✅ README with setup instructions
- ✅ Demo video (max 90 seconds)

### Phase III Additional Requirements
- ✅ OpenAI ChatKit integration
- ✅ OpenAI Agents SDK implementation
- ✅ MCP server with 5 tools
- ✅ Stateless chat endpoint
- ✅ Conversation persistence

### Phase IV Additional Requirements
- ✅ Docker containerization
- ✅ Helm charts for deployment
- ✅ Minikube local deployment
- ✅ AI DevOps tools usage (kubectl-ai/kagent)

### Phase V Additional Requirements
- ✅ Intermediate features (priorities, tags, search, filter, sort)
- ✅ Advanced features (recurring tasks, reminders)
- ✅ Kafka event-driven architecture
- ✅ Dapr integration (5 components)
- ✅ Cloud Kubernetes deployment
- ✅ CI/CD pipeline
- ✅ TLS/HTTPS enabled
- ✅ Microservices (recurring, notification)

### Prohibited Practices
- ❌ Manual code writing (must use Claude Code + specs)
- ❌ Hardcoded secrets or credentials
- ❌ Inline styles (use Tailwind only)
- ❌ Shared data between users
- ❌ Missing authentication/authorization
- ❌ Direct database access from frontend
- ❌ Skipping specification phase
- ❌ Stateful server architecture
- ❌ Secrets in Docker images
- ❌ Force push to main branch

---

**End of Constitution**

**Version**: 3.0.0
**Ratified**: 2025-12-11
**Last Amended**: 2025-12-27
**Next Review**: After Phase V completion (January 18, 2026)
