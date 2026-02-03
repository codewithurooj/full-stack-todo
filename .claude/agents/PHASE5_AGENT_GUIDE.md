# Phase 5 Custom Agents Guide

## Overview

These 4 custom agents will **save you 42+ hours** on Phase 5 implementation. Each agent specializes in a specific aspect of cloud-native development.

## The 4 Priority Agents

| Agent | Purpose | Time Saved |
|-------|---------|------------|
| **db-migrator** | Database schema migrations | 7.5 hours |
| **microservice-scaffolder** | Complete microservice generation | 15 hours |
| **dapr-generator** | Dapr component configuration | 7.5 hours |
| **helm-updater** | Helm chart maintenance | 12 hours |
| **TOTAL** | | **42 hours** 🎉 |

---

## Complete Phase 5 Workflow Using Agents

### CYCLE 1: Intermediate Features (Priorities, Tags, Search, Filter, Sort)

#### Step 1: Create Specification
```bash
/sp.specify
```
"Create specification for intermediate task features: priorities, tags, search, filter, sort"

#### Step 2: Generate Database Migration
```bash
"Use db-migrator agent to generate migration for adding:
- priority VARCHAR(20) DEFAULT 'medium' with constraint (high/medium/low)
- tags TEXT[] DEFAULT '{}'
- index on priority column
Based on @specs/features/intermediate-features.md"
```

**What you get:**
- ✅ Forward migration SQL
- ✅ Rollback migration SQL
- ✅ Updated SQLModel definitions
- ✅ Validation queries
- ✅ Testing checklist

#### Step 3: Generate Implementation Plan
```bash
/sp.plan
```

#### Step 4: Generate Tasks
```bash
/sp.tasks
```

#### Step 5: Implement
```bash
/sp.implement
```

#### Step 6: Update Helm Charts
```bash
"Use helm-updater agent to update backend chart for new filter/sort parameters:
- No new env vars needed
- Version bump to 1.1.0 (MINOR - new feature)
- Document new API capabilities in README"
```

#### Step 7: Record
```bash
/sp.phr
```

---

### CYCLE 2: Advanced Features (Recurring Tasks, Reminders)

#### Step 1: Create Specification
```bash
/sp.specify
```
"Create specification for advanced features: recurring tasks and time-based reminders"

#### Step 2: Generate Database Migration
```bash
"Use db-migrator agent for recurring tasks schema:
- Add recurring VARCHAR(20)
- Add recurring_interval INTEGER DEFAULT 1
- Add parent_task_id INTEGER REFERENCES tasks(id)
- Add due_date TIMESTAMP
- Add remind_at TIMESTAMP
- Add reminded BOOLEAN DEFAULT FALSE
From @specs/features/advanced-features.md"
```

#### Step 3: Plan & Tasks
```bash
/sp.plan
/sp.tasks
```

#### Step 4: Implement Backend Changes
```bash
/sp.implement
```

---

### CYCLE 3: Event-Driven Architecture (Kafka + Microservices)

#### Step 1: Create Specification
```bash
/sp.specify
```
"Create specification for event-driven architecture with Kafka"

#### Step 2: Generate Recurring Task Service
```bash
"Use microservice-scaffolder agent to create Recurring Task Service:
- Consumes: task-events topic (Kafka)
- Consumer group: recurring-task-service-group
- On event_type='completed' AND recurring!='none':
  - Calculate next due_date based on recurring interval
  - Create new task with same properties
  - Set parent_task_id to completed task
- Database: PostgreSQL via DATABASE_URL
- Dapr enabled: yes, app-id: recurring-service, port: not exposed
- Resources: 250m CPU, 256Mi memory, 1 replica
- Include Dockerfile and Helm chart"
```

**What you get:**
- ✅ Complete service code (app/main.py, consumer.py, config.py)
- ✅ Dockerfile with multi-stage build
- ✅ Helm chart with Dapr annotations
- ✅ Unit tests
- ✅ Complete documentation

#### Step 3: Generate Notification Service
```bash
"Use microservice-scaffolder agent to create Notification Service:
- Consumes: reminders topic (Kafka)
- Consumer group: notification-service-group
- On reminder event:
  - Schedule via Dapr Jobs API at remind_at time
  - When job fires, send browser notification
  - Mark task reminded=true in database
- Dapr enabled: yes, app-id: notification-service, port: 8001
- Includes /api/jobs/trigger endpoint for Dapr callbacks
- Resources: 250m CPU, 256Mi memory, 1 replica
- Include Dockerfile and Helm chart"
```

#### Step 4: Update Backend to Publish Events
```bash
/sp.plan
/sp.tasks
/sp.implement
```

#### Step 5: Update Helm Charts for Kafka
```bash
"Use helm-updater agent to add Kafka configuration to backend chart:
- KAFKA_BOOTSTRAP_SERVERS with default 'kafka:9092'
- KAFKA_TOPIC_EVENTS with default 'task-events'
- KAFKA_TOPIC_REMINDERS with default 'reminders'
- Create values-cloud.yaml with Redpanda Cloud bootstrap servers
- Version bump to 2.0.0 (MAJOR - new Kafka dependency)"
```

---

### CYCLE 4: Dapr Integration

#### Step 1: Create Specification
```bash
/sp.specify
```
"Create specification for Dapr integration with 5 components"

#### Step 2: Generate All Dapr Components
```bash
"Use dapr-generator agent to create all 5 Dapr components:

1. kafka-pubsub:
   - Provider: Kafka (Redpanda Cloud)
   - Bootstrap servers: from KAFKA_BOOTSTRAP_SERVERS env
   - Auth: SASL username/password from kafka-credentials secret
   - Consumer group: todo-service
   - Used by: backend-service, recurring-service, notification-service

2. statestore:
   - Provider: PostgreSQL
   - Connection string: from db-secret Kubernetes secret
   - Table: dapr_state
   - Used by: backend-service for conversation state

3. dapr-jobs:
   - Provider: PostgreSQL
   - Connection string: from db-secret
   - Used by: notification-service for scheduled reminders

4. kubernetes-secrets:
   - Provider: Kubernetes
   - Used by: all services for accessing secrets

5. Document service invocation pattern for inter-service calls

Read credentials from backend/.env for reference"
```

**What you get:**
- ✅ 5 component YAML files in `dapr-components/`
- ✅ Kubernetes secret manifests
- ✅ Deployment annotation examples
- ✅ Integration code (Python + TypeScript)
- ✅ Testing commands
- ✅ Complete troubleshooting guide

#### Step 3: Update Backend to Use Dapr APIs
```bash
/sp.plan
```
"Replace direct Kafka producer with Dapr pub/sub HTTP API calls"

```bash
/sp.tasks
/sp.implement
```

#### Step 4: Update All Helm Charts with Dapr Annotations
```bash
"Use helm-updater agent to add Dapr sidecar to backend chart:
- Add Dapr annotations to deployment.yaml
- App ID: backend-service
- App port: 8000
- Enable metrics and tracing
- Version bump to 2.1.0"
```

```bash
"Use helm-updater agent to add Dapr sidecar to recurring-service chart:
- App ID: recurring-service
- No app port (consumer only)
- Version bump to 1.1.0"
```

```bash
"Use helm-updater agent to add Dapr sidecar to notification-service chart:
- App ID: notification-service
- App port: 8001
- Version bump to 1.1.0"
```

---

### CYCLE 5: Cloud Deployment

#### Step 1: Create Cloud Infrastructure Specification
```bash
/sp.specify
```
"Create specification for cloud deployment to [Azure AKS/GCP GKE/Oracle OKE]"

#### Step 2: Update Helm Charts for Cloud
```bash
"Use helm-updater agent to create values-cloud.yaml for backend:
- Image repository: myregistry.azurecr.io/todo-backend
- Replicas: 3
- Resources: 2 CPU, 2Gi memory
- Kafka: Redpanda Cloud bootstrap servers
- Ingress enabled with TLS
- Host: api.example.com
- Secrets from cloud provider"
```

```bash
"Use helm-updater agent to create values-cloud.yaml for frontend:
- Image repository: myregistry.azurecr.io/todo-frontend
- Replicas: 3
- Resources: 1 CPU, 1Gi memory
- Ingress enabled with TLS
- Host: todo.example.com
- API URL: https://api.example.com"
```

#### Step 3: Generate CI/CD Pipeline
```bash
/sp.plan
```
"Create GitHub Actions workflow for deploying to [cloud provider]"

```bash
/sp.tasks
/sp.implement
```

---

## Quick Reference: Common Agent Combinations

### Adding Any New Feature

1. **Spec-driven workflow:**
   ```bash
   /sp.specify → /sp.plan → /sp.tasks → /sp.implement
   ```

2. **If requires database changes:**
   ```bash
   "Use db-migrator agent from @specs/features/my-feature.md"
   ```

3. **If adds new microservice:**
   ```bash
   "Use microservice-scaffolder agent to create [Service]..."
   ```

4. **If requires new Dapr component:**
   ```bash
   "Use dapr-generator agent to create [component]..."
   ```

5. **If updates configuration:**
   ```bash
   "Use helm-updater agent to add [config] to [chart]..."
   ```

6. **Record work:**
   ```bash
   /sp.phr
   ```

---

## Agent Invocation Examples

### Simple Invocation
```bash
"Use db-migrator agent to add priority column"
```

### With Context
```bash
"Use db-migrator agent to add priority column based on @specs/features/intermediate-features.md"
```

### With Details
```bash
"Use microservice-scaffolder agent to create Audit Service that:
- Consumes task-events topic (all event types)
- Logs to audit_log table with timestamp, user_id, action, data
- Consumer group: audit-service-group
- No Dapr integration needed
- Resources: 250m CPU, 256Mi memory
- 1 replica
- Include Dockerfile and Helm chart"
```

### Multiple Agents in Sequence
```bash
# First: Generate migration
"Use db-migrator agent for recurring tasks from @specs/features/advanced-features.md"

# Review migration, then implement
/sp.implement

# Then: Create microservice
"Use microservice-scaffolder agent to create Recurring Task Service..."

# Finally: Update Helm
"Use helm-updater agent to add Kafka config to backend chart"
```

---

## Expected Output Structure

After using all agents in Phase 5, your project will have:

```
full-stack-todo/
├── backend/
│   ├── migrations/
│   │   ├── 001_add_priority_tags.sql
│   │   ├── 002_add_recurring_reminders.sql
│   │   └── ...
│   └── app/models.py (updated)
│
├── services/
│   ├── recurring-task-service/
│   │   ├── app/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── README.md
│   └── notification-service/
│       ├── app/
│       ├── tests/
│       ├── Dockerfile
│       └── README.md
│
├── dapr-components/
│   ├── kafka-pubsub.yaml
│   ├── statestore.yaml
│   ├── dapr-jobs.yaml
│   └── kubernetes-secrets.yaml
│
└── charts/
    ├── backend/
    │   ├── values.yaml (updated)
    │   ├── values-cloud.yaml (new)
    │   └── templates/
    │       └── deployment.yaml (Dapr annotations)
    ├── frontend/
    │   ├── values-cloud.yaml (new)
    │   └── ...
    ├── recurring-task-service/
    │   ├── Chart.yaml
    │   ├── values.yaml
    │   └── templates/
    └── notification-service/
        └── ...
```

---

## Time Savings Breakdown

### Without Agents (Manual Work)
- Database migrations: 3 hrs × 3 = **9 hours**
- Microservices: 6 hrs × 3 = **18 hours**
- Dapr components: 2 hrs × 5 = **10 hours**
- Helm updates: 2 hrs × 8 = **16 hours**
- Documentation: **4 hours**
- Testing: **8 hours**
- CI/CD: **4 hours**
- **TOTAL: 69 hours**

### With Agents
- Database migrations: 0.5 hrs × 3 = **1.5 hours**
- Microservices: 1 hr × 3 = **3 hours**
- Dapr components: 0.5 hrs × 5 = **2.5 hours**
- Helm updates: 0.5 hrs × 8 = **4 hours**
- Documentation: **0.5 hours** (auto-generated)
- Testing: **2 hours** (tests included)
- CI/CD: **1 hour**
- **TOTAL: 14.5 hours**

### **YOU SAVE: 54.5 HOURS! 🎉**

---

## Tips for Maximum Efficiency

1. **Always provide context:**
   - Reference spec files: `@specs/features/my-feature.md`
   - Mention related files: `backend/.env`, `charts/backend/values.yaml`

2. **Be specific:**
   - "Add priority column" → "Add priority VARCHAR(20) with constraint (high/medium/low)"
   - "Create service" → "Create Recurring Task Service that consumes task-events and..."

3. **Review outputs:**
   - Agents generate complete solutions
   - Review before applying to understand what changed
   - Validate with linting/testing commands provided

4. **Combine with spec-driven workflow:**
   - Always start with `/sp.specify`
   - Use agents during implementation
   - End with `/sp.phr`

5. **Ask agents to read files:**
   - "Read credentials from backend/.env"
   - "Based on charts/backend/values.yaml"
   - "Check specs/database/schema.md"

---

## Next Steps

1. ✅ **Agents Created** - You now have all 4 priority agents
2. 🚀 **Start Phase 5** - Begin with Cycle 1 (Intermediate Features)
3. 📝 **Use Spec-Driven Workflow** - /sp.specify → plan → tasks → implement
4. 🤖 **Invoke Agents** - Use agents to accelerate each cycle
5. ✍️ **Record Work** - /sp.phr after each cycle

---

## Support

Each agent has:
- Complete agent definition in `agent.md`
- Quick reference guide in `README.md`
- Usage examples
- Integration patterns

**Questions?** Review the agent README files or ask:
```bash
"Show me examples of using [agent-name] agent"
```

---

**Ready to complete Phase 5 in record time? Let's start with Cycle 1!** 🚀

```bash
# Begin Phase 5:
/sp.specify

# Prompt: "Create specification for intermediate task features: priorities, tags, search, filter, sort"
```
