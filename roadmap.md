# Complete Roadmap for Hackathon II - Phases 3, 4, and 5

**Project:** The Evolution of Todo - Mastering Spec-Driven Development & Cloud Native AI
**Status:** Phases 1 & 2 Completed ✅
**Remaining:** Phases 3, 4, 5

---

## Table of Contents

1. [Phase III: AI-Powered Todo Chatbot](#phase-iii-ai-powered-todo-chatbot)
2. [Phase IV: Local Kubernetes Deployment](#phase-iv-local-kubernetes-deployment)
3. [Phase V: Advanced Cloud Deployment](#phase-v-advanced-cloud-deployment)
4. [Submission Checklist](#submission-checklist-all-phases)
5. [Key Success Tips](#key-success-tips)
6. [Bonus Points Opportunities](#bonus-points-opportunities)
7. [Resources](#resources)

---

## PHASE III: AI-Powered Todo Chatbot

**Due Date:** December 21, 2025
**Points:** 200
**Technology Stack:** OpenAI ChatKit, OpenAI Agents SDK, Official MCP SDK, FastAPI, Next.js

### Objective

Transform your web app into an AI-powered chatbot using OpenAI Agents SDK and MCP (Model Context Protocol). The chatbot must manage tasks via natural language (e.g., "Reschedule my morning meetings to 2 PM").

### Architecture Overview

```
┌─────────────┐  ┌──────────────────────────────┐  ┌─────────────┐
│  ChatKit UI │──▶│ FastAPI Server               │──▶│  Neon DB    │
│ (Frontend)  │  │ ┌────────────────────────┐   │  │ - tasks     │
│             │  │ │ Chat Endpoint          │   │  │ - convos    │
│             │  │ │ POST /api/chat         │   │  │ - messages  │
│             │◀─│ └───────────┬────────────┘   │  │             │
│             │  │             │                 │  │             │
│             │  │             ▼                 │  │             │
│             │  │ ┌────────────────────────┐   │  │             │
│             │◀─│ │ OpenAI Agents SDK      │   │  │             │
│             │  │ │ (Agent + Runner)       │   │  │             │
│             │  │ └───────────┬────────────┘   │  │             │
│             │  │             │                 │  │             │
│             │  │             ▼                 │  │             │
│             │  │ ┌────────────────────────┐   │──▶│             │
│             │  │ │ MCP Server             │   │  │             │
│             │  │ │ (5 Task Tools)         │   │◀─│             │
│             │  │ └────────────────────────┘   │  │             │
└─────────────┘  └──────────────────────────────┘  └─────────────┘
```

---

### Step-by-Step Implementation

#### Step 1: Update Database Schema

**Action:** Add conversation tracking tables to your Neon PostgreSQL database.

**New Tables:**

1. **conversations**
   ```sql
   CREATE TABLE conversations (
     id SERIAL PRIMARY KEY,
     user_id VARCHAR(255) NOT NULL,
     created_at TIMESTAMP DEFAULT NOW(),
     updated_at TIMESTAMP DEFAULT NOW()
   );
   ```

2. **messages**
   ```sql
   CREATE TABLE messages (
     id SERIAL PRIMARY KEY,
     user_id VARCHAR(255) NOT NULL,
     conversation_id INTEGER REFERENCES conversations(id),
     role VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
     content TEXT NOT NULL,
     created_at TIMESTAMP DEFAULT NOW()
   );
   ```

**Using Spec-Driven Development:**
```bash
# 1. Update specs/database/schema.md with new tables
# 2. Generate migration plan
/sp.plan

# 3. Break into tasks
/sp.tasks

# 4. Implement
/sp.implement
```

---

#### Step 2: Build MCP Server with 5 Custom Tools

**Action:** Create an MCP server that exposes 5 task operation tools for the AI agent.

**Required Tools:**

1. **add_task**
   - **Purpose:** Create a new task
   - **Parameters:** `user_id` (string, required), `title` (string, required), `description` (string, optional)
   - **Returns:** `{ task_id, status, title }`
   - **Example Input:** `{"user_id": "user123", "title": "Buy groceries", "description": "Milk, eggs, bread"}`
   - **Example Output:** `{"task_id": 5, "status": "created", "title": "Buy groceries"}`

2. **list_tasks**
   - **Purpose:** Retrieve tasks from the list
   - **Parameters:** `user_id` (string, required), `status` (string, optional: "all", "pending", "completed")
   - **Returns:** Array of task objects
   - **Example Input:** `{"user_id": "user123", "status": "pending"}`
   - **Example Output:** `[{"id": 1, "title": "Buy groceries", "completed": false}, ...]`

3. **complete_task**
   - **Purpose:** Mark a task as complete
   - **Parameters:** `user_id` (string, required), `task_id` (integer, required)
   - **Returns:** `{ task_id, status, title }`
   - **Example Input:** `{"user_id": "user123", "task_id": 3}`
   - **Example Output:** `{"task_id": 3, "status": "completed", "title": "Call mom"}`

4. **delete_task**
   - **Purpose:** Remove a task from the list
   - **Parameters:** `user_id` (string, required), `task_id` (integer, required)
   - **Returns:** `{ task_id, status, title }`
   - **Example Input:** `{"user_id": "user123", "task_id": 2}`
   - **Example Output:** `{"task_id": 2, "status": "deleted", "title": "Old task"}`

5. **update_task**
   - **Purpose:** Modify task title or description
   - **Parameters:** `user_id` (string, required), `task_id` (integer, required), `title` (string, optional), `description` (string, optional)
   - **Returns:** `{ task_id, status, title }`
   - **Example Input:** `{"user_id": "user123", "task_id": 1, "title": "Buy groceries and fruits"}`
   - **Example Output:** `{"task_id": 1, "status": "updated", "title": "Buy groceries and fruits"}`

**MCP Implementation Location:**
```
backend/
├── mcp_server/
│   ├── __init__.py
│   ├── server.py          # MCP server setup
│   └── tools/
│       ├── __init__.py
│       ├── add_task.py
│       ├── list_tasks.py
│       ├── complete_task.py
│       ├── delete_task.py
│       └── update_task.py
```

**Key Requirements:**
- All tools must be **stateless**
- Store all state in the database
- Include `user_id` in every operation for security
- Return consistent JSON format

---

#### Step 3: Implement Stateless Chat API

**Action:** Create a single chat endpoint that handles conversation via OpenAI Agents SDK.

**API Endpoint:**
```
POST /api/{user_id}/chat
```

**Request Body:**
```json
{
  "conversation_id": 123,  // Optional - creates new if not provided
  "message": "Add a task to buy groceries"
}
```

**Response:**
```json
{
  "conversation_id": 123,
  "response": "I've added 'Buy groceries' to your task list.",
  "tool_calls": [
    {
      "tool": "add_task",
      "parameters": {"user_id": "user123", "title": "Buy groceries"}
    }
  ]
}
```

**Stateless Request Cycle:**

```python
# Pseudo-code flow
@app.post("/api/{user_id}/chat")
async def chat(user_id: str, request: ChatRequest):
    # 1. Receive user message
    message = request.message
    conversation_id = request.conversation_id

    # 2. Fetch conversation history from database
    if conversation_id:
        history = db.get_conversation_messages(conversation_id)
    else:
        conversation_id = db.create_conversation(user_id)
        history = []

    # 3. Build message array for agent (history + new message)
    messages = history + [{"role": "user", "content": message}]

    # 4. Store user message in database
    db.save_message(conversation_id, "user", message)

    # 5. Run agent with MCP tools
    response = await run_agent_with_mcp_tools(messages, user_id)

    # 6. Agent invokes appropriate MCP tool(s)
    # (handled internally by OpenAI Agents SDK)

    # 7. Store assistant response in database
    db.save_message(conversation_id, "assistant", response.content)

    # 8. Return response to client
    return {
        "conversation_id": conversation_id,
        "response": response.content,
        "tool_calls": response.tool_calls
    }

    # 9. Server holds NO state (ready for next request)
```

**Key Architecture Benefits:**
- **Scalability:** Any server instance can handle any request
- **Resilience:** Server restarts don't lose conversation state
- **Horizontal scaling:** Load balancer can route to any backend
- **Testability:** Each request is independent and reproducible

---

#### Step 4: Build Frontend with OpenAI ChatKit

**Action:** Integrate OpenAI ChatKit for the conversational UI.

##### 4.1: Setup OpenAI Domain Allowlist (REQUIRED)

Before deploying, you MUST configure OpenAI's domain allowlist:

1. **Deploy frontend first** to get production URL:
   - Vercel: `https://your-app.vercel.app`
   - GitHub Pages: `https://username.github.io/repo-name`
   - Custom domain: `https://yourdomain.com`

2. **Add domain to OpenAI allowlist:**
   - Navigate to: https://platform.openai.com/settings/organization/security/domain-allowlist
   - Click "Add domain"
   - Enter your frontend URL (without trailing slash)
   - Save changes

3. **Get ChatKit domain key:**
   - After adding domain, OpenAI provides a domain key
   - Pass this key to ChatKit configuration

##### 4.2: Environment Variables

**Frontend `.env.local`:**
```env
NEXT_PUBLIC_OPENAI_DOMAIN_KEY=your-domain-key-here
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Backend `.env`:**
```env
OPENAI_API_KEY=sk-your-openai-api-key
DATABASE_URL=postgresql://user:pass@host.neon.tech/dbname
BETTER_AUTH_SECRET=your-secret-key-min-32-chars
```

##### 4.3: Integrate ChatKit Component

```typescript
// frontend/app/chat/page.tsx
import { ChatKit } from '@openai/chatkit';

export default function ChatPage() {
  return (
    <ChatKit
      apiUrl={process.env.NEXT_PUBLIC_API_URL + '/api/chat'}
      domainKey={process.env.NEXT_PUBLIC_OPENAI_DOMAIN_KEY}
      placeholder="Ask me to manage your tasks..."
    />
  );
}
```

**Note:** Local development (`localhost`) typically works without domain allowlist configuration.

---

#### Step 5: Test Natural Language Commands

**Action:** Ensure the chatbot correctly understands and responds to various task management commands.

**Required Test Cases:**

| User Says | Agent Should |
|-----------|--------------|
| "Add a task to buy groceries" | Call `add_task` with title "Buy groceries" |
| "Show me all my tasks" | Call `list_tasks` with status "all" |
| "What's pending?" | Call `list_tasks` with status "pending" |
| "Mark task 3 as complete" | Call `complete_task` with task_id 3 |
| "Delete the meeting task" | Call `list_tasks` first, then `delete_task` |
| "Change task 1 to 'Call mom tonight'" | Call `update_task` with new title |
| "I need to remember to pay bills" | Call `add_task` with title "Pay bills" |
| "What have I completed?" | Call `list_tasks` with status "completed" |

**Agent Behavior Requirements:**

| Behavior | Description |
|----------|-------------|
| Task Creation | When user mentions adding/creating/remembering something, use `add_task` |
| Task Listing | When user asks to see/show/list tasks, use `list_tasks` with appropriate filter |
| Task Completion | When user says done/complete/finished, use `complete_task` |
| Task Deletion | When user says delete/remove/cancel, use `delete_task` |
| Task Update | When user says change/update/rename, use `update_task` |
| Confirmation | Always confirm actions with friendly response |
| Error Handling | Gracefully handle task not found and other errors |

---

#### Step 6: Deployment and Testing

**Local Testing:**
```bash
# Terminal 1: Start backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Start frontend
cd frontend
npm run dev
```

**Test Workflow:**
1. Open http://localhost:3000/chat
2. Send message: "Add a task to buy milk"
3. Verify task is created in database
4. Send message: "Show me my tasks"
5. Verify response includes the new task
6. Test all natural language commands

**Deployment:**
```bash
# Deploy frontend to Vercel
cd frontend
vercel --prod

# Deploy backend to Render/Railway
# (Follow platform-specific instructions)
```

---

### Phase III Deliverables

Submit via https://forms.gle/KMKEKaFUD6ZX4UtY8:

- ✅ **GitHub Repository** with:
  - `/backend/mcp_server` - MCP server with 5 tools
  - `/frontend` - ChatKit integration
  - `/specs/features/chatbot.md` - Chatbot specification
  - Updated database schema
  - README with setup instructions

- ✅ **Deployed Application:**
  - Frontend URL (Vercel)
  - Backend URL (Render/Railway)
  - Working chatbot interface

- ✅ **Demo Video** (<90 seconds):
  - Show natural language task management
  - Demonstrate all 5 MCP tools
  - Show conversation persistence

- ✅ **Key Features Working:**
  - Conversational interface for all Basic Level features
  - Stateless chat endpoint
  - Conversation state persisted to database
  - All MCP tools functional
  - Error handling

---

## PHASE IV: Local Kubernetes Deployment

**Due Date:** January 4, 2026
**Points:** 250
**Technology Stack:** Docker, Minikube, Helm Charts, kubectl-ai, kagent, Docker AI (Gordon)

### Objective

Deploy the Todo Chatbot on a local Kubernetes cluster using Minikube and Helm Charts. Use AI-powered DevOps tools (kubectl-ai, kagent, Docker AI) for intelligent operations.

### Architecture Overview

```
┌────────────────────────────────────────────────────────────┐
│                     MINIKUBE CLUSTER                       │
│                                                            │
│  ┌─────────────────┐         ┌─────────────────┐         │
│  │  Frontend Pod   │         │  Backend Pod    │         │
│  │  ┌───────────┐  │         │  ┌───────────┐  │         │
│  │  │ Next.js   │  │         │  │ FastAPI   │  │         │
│  │  │ Container │  │         │  │ Container │  │         │
│  │  └───────────┘  │         │  └───────────┘  │         │
│  │  Replicas: 2    │         │  Replicas: 2    │         │
│  └─────────────────┘         └─────────────────┘         │
│           │                           │                   │
│           └───────────┬───────────────┘                   │
│                       ▼                                   │
│           ┌─────────────────────┐                        │
│           │   Service (ClusterIP)│                        │
│           └─────────────────────┘                        │
│                       │                                   │
│                       ▼                                   │
│           ┌─────────────────────┐                        │
│           │      Ingress        │                        │
│           └─────────────────────┘                        │
└────────────────────────────────────────────────────────────┘
                       │
                       ▼
               http://localhost
```

---

### Step-by-Step Implementation

#### Step 1: Containerize Applications with Docker AI (Gordon)

**Action:** Create Docker containers for frontend and backend applications.

##### Option A: Using Docker AI Agent (Gordon) - Recommended

**Prerequisites:**
- Docker Desktop 4.53+ installed
- Enable Gordon: Settings > Beta features > Toggle on

**Commands:**
```bash
# Ask Gordon about capabilities
docker ai "What can you do?"

# Generate Dockerfile for Next.js
docker ai "Create an optimized multi-stage Dockerfile for Next.js 16 production build"

# Generate Dockerfile for FastAPI
docker ai "Create Dockerfile for Python 3.13 FastAPI app with uvicorn"

# Build images
docker ai "Build frontend image from ./frontend directory"
docker ai "Build backend image from ./backend directory"

# Test containers
docker ai "Run frontend container on port 3000"
docker ai "Run backend container on port 8000"
```

##### Option B: Manual Dockerfile Creation

**Frontend Dockerfile** (`frontend/Dockerfile`):
```dockerfile
# Multi-stage build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
EXPOSE 3000
CMD ["npm", "start"]
```

**Backend Dockerfile** (`backend/Dockerfile`):
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build and Test:**
```bash
# Build images
docker build -t todo-frontend:latest ./frontend
docker build -t todo-backend:latest ./backend

# Test locally
docker run -p 3000:3000 todo-frontend:latest
docker run -p 8000:8000 todo-backend:latest
```

---

#### Step 2: Setup Minikube

**Action:** Install and configure Minikube for local Kubernetes cluster.

**Installation:**
```bash
# Windows (using Chocolatey)
choco install minikube

# macOS
brew install minikube

# Linux
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
```

**Start Minikube:**
```bash
# Start cluster with sufficient resources
minikube start --cpus=4 --memory=8192 --driver=docker

# Enable required addons
minikube addons enable ingress
minikube addons enable metrics-server
minikube addons enable dashboard

# Verify installation
kubectl cluster-info
kubectl get nodes
```

**Access Dashboard:**
```bash
minikube dashboard
```

---

#### Step 3: Create Helm Charts

**Action:** Create Helm charts for deployment management using kubectl-ai or manual creation.

##### Option A: Using kubectl-ai (Recommended)

**Install kubectl-ai:**
```bash
npm install -g @kubectl-ai/cli

# Configure with your OpenAI API key
kubectl-ai config set OPENAI_API_KEY=sk-your-key
```

**Generate Helm Charts:**
```bash
# Frontend chart
kubectl-ai "create helm chart for Next.js frontend deployment with 2 replicas, service on port 3000, and ingress"

# Backend chart
kubectl-ai "create helm chart for FastAPI backend deployment with 2 replicas, service on port 8000"

# Review generated files
kubectl-ai "explain the frontend helm chart structure"
```

##### Option B: Manual Helm Chart Creation

**Create Chart Structure:**
```bash
# Create charts
helm create charts/frontend
helm create charts/backend

# Directory structure will be:
charts/
├── frontend/
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── templates/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── ingress.yaml
│   │   └── _helpers.tpl
│   └── .helmignore
└── backend/
    ├── Chart.yaml
    ├── values.yaml
    ├── templates/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   ├── configmap.yaml
    │   └── _helpers.tpl
    └── .helmignore
```

**Frontend Chart Configuration:**

`charts/frontend/values.yaml`:
```yaml
replicaCount: 2

image:
  repository: todo-frontend
  tag: latest
  pullPolicy: Never  # Use local image

service:
  type: ClusterIP
  port: 3000

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: todo.local
      paths:
        - path: /
          pathType: Prefix

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi

env:
  - name: NEXT_PUBLIC_API_URL
    value: "http://todo.local/api"
```

`charts/frontend/templates/deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "frontend.fullname" . }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: {{ include "frontend.name" . }}
  template:
    metadata:
      labels:
        app: {{ include "frontend.name" . }}
    spec:
      containers:
      - name: {{ .Chart.Name }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - containerPort: 3000
        env:
        {{- toYaml .Values.env | nindent 8 }}
        resources:
        {{- toYaml .Values.resources | nindent 10 }}
```

**Backend Chart Configuration:**

`charts/backend/values.yaml`:
```yaml
replicaCount: 2

image:
  repository: todo-backend
  tag: latest
  pullPolicy: Never

service:
  type: ClusterIP
  port: 8000

configMap:
  DATABASE_URL: "postgresql://user:pass@neon.tech/todo"

secret:
  OPENAI_API_KEY: "sk-your-key"
  BETTER_AUTH_SECRET: "your-secret"

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi
```

---

#### Step 4: Deploy to Minikube

**Action:** Load Docker images and deploy using Helm.

**Load Images into Minikube:**
```bash
# Point Docker CLI to Minikube's Docker daemon
eval $(minikube docker-env)

# Build images (they'll be available in Minikube)
docker build -t todo-frontend:latest ./frontend
docker build -t todo-backend:latest ./backend

# Verify images
docker images | grep todo
```

**Deploy with Helm:**
```bash
# Install frontend
helm install frontend ./charts/frontend

# Install backend
helm install backend ./charts/backend

# Verify deployments
kubectl get deployments
kubectl get pods
kubectl get services

# Check pod logs
kubectl logs -f deployment/frontend
kubectl logs -f deployment/backend
```

**Setup Ingress:**
```bash
# Add entry to /etc/hosts (or C:\Windows\System32\drivers\etc\hosts on Windows)
echo "$(minikube ip) todo.local" | sudo tee -a /etc/hosts

# Verify ingress
kubectl get ingress

# Access application
curl http://todo.local
```

---

#### Step 5: Use AI-Powered Kubectl Tools

**Action:** Leverage kubectl-ai and kagent for intelligent Kubernetes operations.

##### kubectl-ai Usage

**Install:**
```bash
npm install -g @kubectl-ai/cli
```

**Common Operations:**
```bash
# Deploy and scale
kubectl-ai "deploy the todo frontend with 2 replicas"
kubectl-ai "scale the backend to handle more load"
kubectl-ai "scale backend deployment to 3 replicas"

# Debugging
kubectl-ai "check why the frontend pods are failing"
kubectl-ai "show me logs from the backend pods"
kubectl-ai "describe the pod that's crashing"

# Resource management
kubectl-ai "show resource usage of all pods"
kubectl-ai "update frontend memory limit to 1Gi"

# Networking
kubectl-ai "expose backend service on port 8000"
kubectl-ai "create ingress for frontend on todo.local"
```

##### kagent Usage

**Install:**
```bash
pip install kagent
```

**Common Operations:**
```bash
# Cluster analysis
kagent "analyze the cluster health"
kagent "check for security vulnerabilities"
kagent "optimize resource allocation"

# Monitoring
kagent "show me the cluster resource usage trends"
kagent "identify pods with high CPU usage"

# Troubleshooting
kagent "why is my deployment failing?"
kagent "suggest improvements for my cluster"
```

**Best Practice:** Start with kubectl-ai for day-to-day operations, layer in kagent for advanced analysis and optimization.

---

#### Step 6: Setup Local Access

**Action:** Configure access to the deployed application.

**Option A: Port Forwarding**
```bash
# Forward frontend
kubectl port-forward svc/frontend 3000:3000

# Forward backend
kubectl port-forward svc/backend 8000:8000

# Access
open http://localhost:3000
```

**Option B: Minikube Tunnel**
```bash
# Start tunnel (requires admin/sudo)
minikube tunnel

# Access via ingress
open http://todo.local
```

**Option C: NodePort Service**
```bash
# Update service to NodePort
kubectl patch svc frontend -p '{"spec":{"type":"NodePort"}}'

# Get URL
minikube service frontend --url
```

---

#### Step 7: Monitoring and Management

**Action:** Set up monitoring and management tools.

**Kubernetes Dashboard:**
```bash
minikube dashboard
```

**View Resources:**
```bash
# Watch pods
kubectl get pods -w

# View logs
kubectl logs -f <pod-name>

# Describe resources
kubectl describe pod <pod-name>
kubectl describe deployment frontend

# Execute commands in pods
kubectl exec -it <pod-name> -- /bin/sh
```

**Resource Metrics:**
```bash
# Pod metrics
kubectl top pods

# Node metrics
kubectl top nodes
```

---

### Phase IV Deliverables

Submit via https://forms.gle/KMKEKaFUD6ZX4UtY8:

- ✅ **GitHub Repository** with:
  - `frontend/Dockerfile` - Frontend container
  - `backend/Dockerfile` - Backend container
  - `/charts/frontend` - Frontend Helm chart
  - `/charts/backend` - Backend Helm chart
  - `README.md` - Minikube setup instructions
  - Scripts for building and deploying

- ✅ **Local Deployment:**
  - Running on Minikube
  - Accessible via http://todo.local or port-forward
  - All pods healthy and running
  - Services properly exposed

- ✅ **Demo Video** (<90 seconds):
  - Show Docker images
  - Deploy using Helm
  - Access running application
  - Use kubectl-ai for operations

- ✅ **Documentation:**
  - Setup instructions
  - Helm chart configuration
  - Troubleshooting guide
  - kubectl-ai usage examples

---

## PHASE V: Advanced Cloud Deployment

**Due Date:** January 18, 2026
**Points:** 300
**Technology Stack:** Kafka, Dapr, Azure AKS/Google GKE/Oracle OKE, GitHub Actions, Helm

### Objective

Implement advanced features and deploy to production-grade Kubernetes with event-driven architecture using Kafka and Dapr. Includes recurring tasks, reminders, priorities, search/filter, and cloud deployment.

### Architecture Overview

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        KUBERNETES CLUSTER (Cloud)                         │
│                                                                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐ │
│  │ Frontend Pod    │  │ Backend Pod     │  │ Notification Pod        │ │
│  │ ┌────┐ ┌─────┐ │  │ ┌────┐ ┌─────┐ │  │ ┌────────┐ ┌──────────┐ │ │
│  │ │App │◀▶│Dapr │ │  │ │API │◀▶│Dapr │ │  │ │Service │◀▶│  Dapr   │ │ │
│  │ └────┘ └─────┘ │  │ └────┘ └─────┘ │  │ └────────┘ └──────────┘ │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘ │
│           │                    │                        │               │
│           └────────────────────┼────────────────────────┘               │
│                                ▼                                        │
│                   ┌────────────────────────┐                           │
│                   │   DAPR COMPONENTS      │                           │
│                   │ ┌──────────────────┐  │                           │
│                   │ │ pubsub.kafka     │──┼──▶ Kafka Cluster         │
│                   │ ├──────────────────┤  │    (Redpanda/Strimzi)     │
│                   │ │ state.postgresql │──┼──▶ Neon DB                │
│                   │ ├──────────────────┤  │                           │
│                   │ │ dapr-jobs        │  │    (Scheduled triggers)   │
│                   │ ├──────────────────┤  │                           │
│                   │ │ secretstores.k8s │  │    (API keys, secrets)    │
│                   │ └──────────────────┘  │                           │
│                   └────────────────────────┘                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

### Part A: Implement Advanced Features

#### Step 1: Add Intermediate Level Features

**Action:** Enhance task management with organization and usability features.

##### 1.1: Priorities & Tags/Categories

**Database Schema Updates:**
```sql
-- Add columns to tasks table
ALTER TABLE tasks ADD COLUMN priority VARCHAR(20) DEFAULT 'medium';
ALTER TABLE tasks ADD COLUMN tags TEXT[];  -- PostgreSQL array

-- Create index for filtering
CREATE INDEX idx_tasks_priority ON tasks(priority);
```

**Priority Values:** `high`, `medium`, `low`

**Update MCP Tools:**
- Modify `add_task` to accept `priority` and `tags`
- Modify `list_tasks` to filter by priority and tags
- Update `update_task` to modify priority and tags

**Spec-Driven Approach:**
```bash
# Update specification
# specs/features/task-organization.md

# Generate plan
/sp.plan

# Break into tasks
/sp.tasks

# Implement
/sp.implement
```

##### 1.2: Search & Filter

**Features to Implement:**
- Search tasks by keyword (in title or description)
- Filter by:
  - Status (pending, completed)
  - Priority (high, medium, low)
  - Tags
  - Date range (created_at, due_date)

**New MCP Tool (Optional):**
```python
def search_tasks(user_id: str, query: str, filters: dict):
    """
    Search and filter tasks

    Args:
        user_id: User identifier
        query: Search keyword
        filters: {
            "status": "pending",
            "priority": "high",
            "tags": ["work"],
            "date_from": "2025-01-01",
            "date_to": "2025-12-31"
        }

    Returns:
        Array of matching tasks
    """
```

##### 1.3: Sort Tasks

**Sorting Options:**
- By due_date (ascending/descending)
- By priority (high → medium → low)
- By created_at
- Alphabetically by title

**Update list_tasks MCP Tool:**
```python
def list_tasks(user_id: str, status: str = "all", sort_by: str = "created_at"):
    """
    sort_by options: "due_date", "priority", "created_at", "title"
    """
```

---

#### Step 2: Add Advanced Level Features

**Action:** Implement intelligent task management features.

##### 2.1: Recurring Tasks

**Database Schema:**
```sql
ALTER TABLE tasks ADD COLUMN recurring VARCHAR(20);  -- 'none', 'daily', 'weekly', 'monthly'
ALTER TABLE tasks ADD COLUMN recurring_interval INTEGER DEFAULT 1;
ALTER TABLE tasks ADD COLUMN parent_task_id INTEGER REFERENCES tasks(id);
```

**Logic:**
1. When a recurring task is marked complete:
   - Publish event to Kafka topic `task-events`
   - Event: `{ type: "recurring_task_completed", task_id, recurring, user_id }`
2. Recurring Task Service (consumer):
   - Listen to `task-events`
   - When recurring task completed, create new task with:
     - Same title, description, priority, tags
     - New due_date based on interval
     - Reference to parent_task_id

##### 2.2: Due Dates & Time Reminders

**Database Schema:**
```sql
ALTER TABLE tasks ADD COLUMN due_date TIMESTAMP;
ALTER TABLE tasks ADD COLUMN remind_at TIMESTAMP;
ALTER TABLE tasks ADD COLUMN reminded BOOLEAN DEFAULT FALSE;
```

**Reminder Flow:**
1. When task with `remind_at` is created:
   - Publish to Kafka topic `reminders`
   - Event: `{ task_id, user_id, remind_at, title }`
2. Notification Service (consumer):
   - Listen to `reminders`
   - Schedule notification using Dapr Jobs API
   - Send browser notification at scheduled time

**Browser Notifications:**
```typescript
// Frontend - Request permission
if ('Notification' in window) {
  Notification.requestPermission();
}

// Show notification
new Notification('Task Reminder', {
  body: 'Buy groceries is due in 1 hour',
  icon: '/icon.png'
});
```

---

### Part B: Event-Driven Architecture with Kafka

#### Step 3: Setup Kafka

**Action:** Choose and configure Kafka service.

##### Option 1: Redpanda Cloud (Recommended - Free Serverless Tier)

**Setup Steps:**
```bash
# 1. Sign up at redpanda.com/cloud
# 2. Create Serverless cluster (free tier)
# 3. Create topics:
#    - task-events
#    - reminders
#    - task-updates
# 4. Get credentials:
#    - Bootstrap server URL
#    - SASL username
#    - SASL password
```

**Environment Variables:**
```env
KAFKA_BOOTSTRAP_SERVERS=your-cluster.cloud.redpanda.com:9092
KAFKA_SASL_USERNAME=your-username
KAFKA_SASL_PASSWORD=your-password
KAFKA_SECURITY_PROTOCOL=SASL_SSL
KAFKA_SASL_MECHANISM=SCRAM-SHA-256
```

##### Option 2: Self-Hosted Kafka with Strimzi on Kubernetes

**Install Strimzi Operator:**
```bash
kubectl create namespace kafka
kubectl apply -f https://strimzi.io/install/latest?namespace=kafka
```

**Create Kafka Cluster:**

`kafka-cluster.yaml`:
```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: todo-kafka
  namespace: kafka
spec:
  kafka:
    replicas: 1
    listeners:
      - name: plain
        port: 9092
        type: internal
    storage:
      type: ephemeral
  zookeeper:
    replicas: 1
    storage:
      type: ephemeral
```

```bash
kubectl apply -f kafka-cluster.yaml

# Wait for cluster to be ready
kubectl wait kafka/todo-kafka --for=condition=Ready --timeout=300s -n kafka

# Create topics
kubectl apply -f - <<EOF
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: task-events
  namespace: kafka
  labels:
    strimzi.io/cluster: todo-kafka
spec:
  partitions: 3
  replicas: 1
---
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: reminders
  namespace: kafka
  labels:
    strimzi.io/cluster: todo-kafka
spec:
  partitions: 3
  replicas: 1
---
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: task-updates
  namespace: kafka
  labels:
    strimzi.io/cluster: todo-kafka
spec:
  partitions: 3
  replicas: 1
EOF
```

---

#### Step 4: Implement Event-Driven Services

**Action:** Create microservices that communicate via Kafka events.

##### 4.1: Publish Events from Chat API

**Update Chat API to publish events:**

```python
from kafka import KafkaProducer
import json

# Initialize producer
producer = KafkaProducer(
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# In add_task MCP tool
def add_task(user_id: str, title: str, description: str = "",
             due_date: str = None, remind_at: str = None):
    # Create task in database
    task = db.create_task(user_id, title, description, due_date)

    # Publish event to task-events topic
    producer.send('task-events', {
        'event_type': 'created',
        'task_id': task.id,
        'user_id': user_id,
        'task_data': task.dict(),
        'timestamp': datetime.utcnow().isoformat()
    })

    # If has reminder, publish to reminders topic
    if remind_at:
        producer.send('reminders', {
            'task_id': task.id,
            'user_id': user_id,
            'title': title,
            'remind_at': remind_at,
            'timestamp': datetime.utcnow().isoformat()
        })

    return {"task_id": task.id, "status": "created", "title": title}
```

##### 4.2: Recurring Task Service (Consumer)

**Create new service:**

`services/recurring-task-service/main.py`:
```python
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'task-events',
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    group_id='recurring-task-service'
)

for message in consumer:
    event = message.value

    if event['event_type'] == 'completed':
        task_data = event['task_data']

        # Check if task is recurring
        if task_data.get('recurring') and task_data['recurring'] != 'none':
            # Calculate next due date
            next_due_date = calculate_next_due_date(
                task_data['due_date'],
                task_data['recurring']
            )

            # Create new task
            db.create_task(
                user_id=event['user_id'],
                title=task_data['title'],
                description=task_data['description'],
                due_date=next_due_date,
                recurring=task_data['recurring'],
                parent_task_id=event['task_id']
            )

            print(f"Created next occurrence for task {event['task_id']}")
```

##### 4.3: Notification Service (Consumer)

**Create notification service:**

`services/notification-service/main.py`:
```python
from kafka import KafkaConsumer
import httpx
import asyncio

consumer = KafkaConsumer(
    'reminders',
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    group_id='notification-service'
)

async def send_notification(user_id: str, message: str):
    # Send to frontend via WebSocket or push notification
    # Implementation depends on your notification strategy
    pass

for message in consumer:
    reminder = message.value

    # Schedule reminder using Dapr Jobs API (see Dapr section)
    # Or use simple sleep-based scheduling for MVP

    delay = (datetime.fromisoformat(reminder['remind_at']) - datetime.utcnow()).total_seconds()

    if delay > 0:
        asyncio.sleep(delay)

    asyncio.run(send_notification(
        reminder['user_id'],
        f"Reminder: {reminder['title']}"
    ))
```

##### 4.4: Audit Log Service (Optional)

**Log all task operations:**

`services/audit-service/main.py`:
```python
from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'task-events',
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    group_id='audit-service'
)

for message in consumer:
    event = message.value

    # Store in audit log table
    db.save_audit_log(
        user_id=event['user_id'],
        event_type=event['event_type'],
        task_id=event['task_id'],
        timestamp=event['timestamp'],
        data=event['task_data']
    )
```

##### 4.5: Real-time Sync Service (Optional)

**Broadcast changes to all connected clients:**

`services/websocket-service/main.py`:
```python
from kafka import KafkaConsumer
from fastapi import WebSocket

consumer = KafkaConsumer(
    'task-updates',
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    group_id='websocket-service'
)

# Maintain WebSocket connections
active_connections = {}

for message in consumer:
    update = message.value
    user_id = update['user_id']

    # Broadcast to user's connected clients
    if user_id in active_connections:
        for connection in active_connections[user_id]:
            await connection.send_json(update)
```

---

### Part C: Integrate Dapr

#### Step 5: Install Dapr on Minikube

**Action:** Set up Dapr runtime for distributed application management.

**Install Dapr CLI:**
```bash
# macOS/Linux
curl -fsSL https://raw.githubusercontent.com/dapr/cli/master/install/install.sh | bash

# Windows (PowerShell)
powershell -Command "iwr -useb https://raw.githubusercontent.com/dapr/cli/master/install/install.ps1 | iex"

# Verify
dapr --version
```

**Initialize Dapr on Kubernetes:**
```bash
# Initialize on Minikube
dapr init -k

# Verify installation
kubectl get pods -n dapr-system

# Expected output:
# dapr-dashboard-xxx
# dapr-operator-xxx
# dapr-placement-server-xxx
# dapr-sentry-xxx
# dapr-sidecar-injector-xxx
```

**Access Dapr Dashboard:**
```bash
dapr dashboard -k
# Opens at http://localhost:8080
```

---

#### Step 6: Create Dapr Components

**Action:** Configure Dapr building blocks for your application.

Create directory: `/dapr-components`

##### 6.1: Pub/Sub Component (Kafka)

`dapr-components/kafka-pubsub.yaml`:
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: kafka-pubsub
  namespace: default
spec:
  type: pubsub.kafka
  version: v1
  metadata:
    # For Redpanda Cloud
    - name: brokers
      value: "your-cluster.cloud.redpanda.com:9092"
    - name: authType
      value: "password"
    - name: saslUsername
      value: "your-username"
    - name: saslPassword
      value: "your-password"
    - name: consumerGroup
      value: "todo-service"

    # For self-hosted Strimzi
    # - name: brokers
    #   value: "todo-kafka-kafka-bootstrap.kafka.svc:9092"
```

##### 6.2: State Management Component (PostgreSQL)

`dapr-components/statestore.yaml`:
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore
  namespace: default
spec:
  type: state.postgresql
  version: v1
  metadata:
    - name: connectionString
      secretKeyRef:
        name: db-secret
        key: connectionString
    - name: tableName
      value: "dapr_state"
```

**Create Secret:**
```bash
kubectl create secret generic db-secret \
  --from-literal=connectionString="host=neon.db user=... password=... dbname=todo"
```

##### 6.3: Dapr Jobs Component (Scheduled Reminders)

`dapr-components/dapr-jobs.yaml`:
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: dapr-jobs
  namespace: default
spec:
  type: jobs.postgresql
  version: v1
  metadata:
    - name: connectionString
      secretKeyRef:
        name: db-secret
        key: connectionString
```

##### 6.4: Secrets Component (Kubernetes Secrets)

`dapr-components/kubernetes-secrets.yaml`:
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: kubernetes-secrets
  namespace: default
spec:
  type: secretstores.kubernetes
  version: v1
  metadata: []
```

##### 6.5: Service Invocation (Implicit)

Service invocation is built into Dapr - no component file needed. Services can call each other using:
```
http://localhost:3500/v1.0/invoke/<service-name>/method/<method-name>
```

**Deploy Components:**
```bash
kubectl apply -f dapr-components/
```

---

#### Step 7: Update Services for Dapr

**Action:** Modify applications to use Dapr HTTP APIs instead of direct Kafka/DB calls.

##### 7.1: Publish Events via Dapr Pub/Sub

**Before (Direct Kafka):**
```python
from kafka import KafkaProducer

producer = KafkaProducer(bootstrap_servers="...")
producer.send('task-events', event_data)
```

**After (Dapr Pub/Sub):**
```python
import httpx

async def publish_event(topic: str, event: dict):
    """Publish via Dapr sidecar (no Kafka library needed!)"""
    await httpx.post(
        f"http://localhost:3500/v1.0/publish/kafka-pubsub/{topic}",
        json=event
    )

# Usage
await publish_event("task-events", {
    "event_type": "created",
    "task_id": 1,
    "user_id": "user123"
})
```

##### 7.2: State Management via Dapr

**Store conversation state:**
```python
import httpx

async def save_conversation_state(conversation_id: int, messages: list):
    """Save state via Dapr"""
    await httpx.post(
        "http://localhost:3500/v1.0/state/statestore",
        json=[{
            "key": f"conversation-{conversation_id}",
            "value": {"messages": messages}
        }]
    )

async def get_conversation_state(conversation_id: int):
    """Get state via Dapr"""
    response = await httpx.get(
        f"http://localhost:3500/v1.0/state/statestore/conversation-{conversation_id}"
    )
    return response.json()
```

##### 7.3: Schedule Reminders via Dapr Jobs API

**Schedule reminder at exact time:**
```python
import httpx
from datetime import datetime

async def schedule_reminder(task_id: int, remind_at: datetime, user_id: str):
    """Schedule reminder using Dapr Jobs API (not cron polling)"""
    await httpx.post(
        f"http://localhost:3500/v1.0-alpha1/jobs/reminder-task-{task_id}",
        json={
            "dueTime": remind_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "data": {
                "task_id": task_id,
                "user_id": user_id,
                "type": "reminder"
            }
        }
    )
```

**Handle callback when job fires:**
```python
from fastapi import FastAPI, Request

@app.post("/api/jobs/trigger")
async def handle_job_trigger(request: Request):
    """Dapr calls this endpoint at the exact scheduled time"""
    job_data = await request.json()

    if job_data["data"]["type"] == "reminder":
        # Publish to notification service via Dapr PubSub
        await publish_event("reminders", "reminder.due", job_data["data"])

    return {"status": "SUCCESS"}
```

**Benefits:**
- No polling overhead
- Exact timing (not "within 5 minutes")
- Scales better (no DB scans every minute)

##### 7.4: Service Invocation (Frontend → Backend)

**Before:**
```typescript
// Frontend must know backend URL
fetch("http://backend-service:8000/api/chat", {...})
```

**After (Dapr Service Invocation):**
```typescript
// Frontend calls via Dapr sidecar – automatic discovery
fetch("http://localhost:3500/v1.0/invoke/backend-service/method/api/chat", {...})
```

##### 7.5: Access Secrets via Dapr

**Before:**
```python
import os
api_key = os.getenv("OPENAI_API_KEY")
```

**After (Dapr Secrets):**
```python
import httpx

async def get_secret(key: str):
    response = await httpx.get(
        f"http://localhost:3500/v1.0/secrets/kubernetes-secrets/{key}"
    )
    return response.json()[key]

# Usage
api_key = await get_secret("openai-api-key")
```

##### 7.6: Update Deployment for Dapr Sidecars

**Add Dapr annotations to deployments:**

`charts/backend/templates/deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  template:
    metadata:
      labels:
        app: backend
      annotations:
        dapr.io/enabled: "true"
        dapr.io/app-id: "backend-service"
        dapr.io/app-port: "8000"
        dapr.io/log-level: "debug"
    spec:
      containers:
      - name: backend
        image: todo-backend:latest
        ports:
        - containerPort: 8000
```

When deployed, Dapr automatically injects a sidecar container into the pod.

---

### Part D: Cloud Deployment

#### Step 8: Choose Cloud Provider

**Action:** Select and setup cloud Kubernetes service.

##### Option 1: Azure AKS ($200 credit for 30 days)

**Prerequisites:**
- Sign up at https://azure.microsoft.com/en-us/free/
- Install Azure CLI: https://docs.microsoft.com/cli/azure/install-azure-cli

**Setup:**
```bash
# Login
az login

# Create resource group
az group create --name todo-rg --location eastus

# Create AKS cluster
az aks create \
  --resource-group todo-rg \
  --name todo-cluster \
  --node-count 2 \
  --node-vm-size Standard_B2s \
  --enable-addons monitoring \
  --generate-ssh-keys

# Get credentials
az aks get-credentials --resource-group todo-rg --name todo-cluster

# Verify
kubectl get nodes
```

##### Option 2: Google Cloud GKE ($300 credit for 90 days)

**Prerequisites:**
- Sign up at https://cloud.google.com/free
- Install gcloud CLI: https://cloud.google.com/sdk/install

**Setup:**
```bash
# Login
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Create GKE cluster
gcloud container clusters create todo-cluster \
  --num-nodes=2 \
  --machine-type=e2-medium \
  --zone=us-central1-a

# Get credentials
gcloud container clusters get-credentials todo-cluster --zone=us-central1-a

# Verify
kubectl get nodes
```

##### Option 3: Oracle Cloud OKE (Always Free - RECOMMENDED)

**Prerequisites:**
- Sign up at https://www.oracle.com/cloud/free/

**Benefits:**
- 4 OCPUs, 24GB RAM - always free
- No credit card charge after trial
- Best for learning without time pressure

**Setup:**
```bash
# Follow Oracle Cloud Console to create OKE cluster
# Download kubeconfig file
# Set KUBECONFIG environment variable

export KUBECONFIG=/path/to/kubeconfig

# Verify
kubectl get nodes
```

---

#### Step 9: Deploy to Cloud Kubernetes

**Action:** Deploy full application stack to cloud.

##### 9.1: Push Docker Images to Registry

**Create Container Registry:**

**Azure:**
```bash
# Create Azure Container Registry
az acr create --resource-group todo-rg --name todoregistry --sku Basic

# Login
az acr login --name todoregistry

# Tag images
docker tag todo-frontend:latest todoregistry.azurecr.io/todo-frontend:latest
docker tag todo-backend:latest todoregistry.azurecr.io/todo-backend:latest

# Push
docker push todoregistry.azurecr.io/todo-frontend:latest
docker push todoregistry.azurecr.io/todo-backend:latest
```

**Google Cloud:**
```bash
# Enable Container Registry API
gcloud services enable containerregistry.googleapis.com

# Tag images
docker tag todo-frontend:latest gcr.io/YOUR_PROJECT_ID/todo-frontend:latest
docker tag todo-backend:latest gcr.io/YOUR_PROJECT_ID/todo-backend:latest

# Push
docker push gcr.io/YOUR_PROJECT_ID/todo-frontend:latest
docker push gcr.io/YOUR_PROJECT_ID/todo-backend:latest
```

##### 9.2: Install Dapr on Cloud Cluster

```bash
# Initialize Dapr
dapr init -k

# Verify
kubectl get pods -n dapr-system
```

##### 9.3: Deploy Kafka

**Option A: Redpanda Cloud** (Recommended - update Dapr component with cloud credentials)

**Option B: Strimzi Self-Hosted**
```bash
# Install Strimzi
kubectl create namespace kafka
kubectl apply -f https://strimzi.io/install/latest?namespace=kafka

# Deploy Kafka cluster
kubectl apply -f kafka-cluster.yaml
```

##### 9.4: Deploy Dapr Components

```bash
# Apply components
kubectl apply -f dapr-components/

# Verify
kubectl get components
```

##### 9.5: Deploy Applications via Helm

**Update Helm values for cloud:**

`charts/frontend/values-cloud.yaml`:
```yaml
image:
  repository: todoregistry.azurecr.io/todo-frontend
  tag: latest
  pullPolicy: Always

replicaCount: 3

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: todo.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: todo-tls
      hosts:
        - todo.yourdomain.com
```

**Deploy:**
```bash
# Install cert-manager for TLS
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Install nginx ingress controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Deploy applications
helm install frontend ./charts/frontend -f charts/frontend/values-cloud.yaml
helm install backend ./charts/backend -f charts/backend/values-cloud.yaml
helm install notification-service ./charts/notification-service
helm install recurring-service ./charts/recurring-service

# Verify
kubectl get pods
kubectl get ingress
```

##### 9.6: Configure DNS

**Get LoadBalancer IP:**
```bash
kubectl get svc -n ingress-nginx
# Look for EXTERNAL-IP of ingress-nginx-controller
```

**Add DNS Record:**
- Create A record: `todo.yourdomain.com` → `<EXTERNAL-IP>`

**Test:**
```bash
curl https://todo.yourdomain.com
```

---

#### Step 10: Setup CI/CD with GitHub Actions

**Action:** Automate deployment pipeline.

**Create `.github/workflows/deploy.yml`:**
```yaml
name: Deploy to Kubernetes

on:
  push:
    branches: [main]

env:
  REGISTRY: todoregistry.azurecr.io
  CLUSTER_NAME: todo-cluster
  RESOURCE_GROUP: todo-rg

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Login to Azure
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}

    - name: Login to ACR
      run: az acr login --name todoregistry

    - name: Build and push frontend
      run: |
        docker build -t ${{ env.REGISTRY }}/todo-frontend:${{ github.sha }} ./frontend
        docker push ${{ env.REGISTRY }}/todo-frontend:${{ github.sha }}

    - name: Build and push backend
      run: |
        docker build -t ${{ env.REGISTRY }}/todo-backend:${{ github.sha }} ./backend
        docker push ${{ env.REGISTRY }}/todo-backend:${{ github.sha }}

    - name: Set up kubectl
      uses: azure/setup-kubectl@v3

    - name: Get AKS credentials
      run: |
        az aks get-credentials \
          --resource-group ${{ env.RESOURCE_GROUP }} \
          --name ${{ env.CLUSTER_NAME }}

    - name: Deploy to Kubernetes
      run: |
        helm upgrade --install frontend ./charts/frontend \
          --set image.tag=${{ github.sha }} \
          -f charts/frontend/values-cloud.yaml

        helm upgrade --install backend ./charts/backend \
          --set image.tag=${{ github.sha }} \
          -f charts/backend/values-cloud.yaml

    - name: Verify deployment
      run: |
        kubectl rollout status deployment/frontend
        kubectl rollout status deployment/backend
```

**Setup Secrets:**

1. Create Azure service principal:
```bash
az ad sp create-for-rbac \
  --name "github-actions" \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/todo-rg \
  --sdk-auth
```

2. Add output JSON to GitHub repository secrets as `AZURE_CREDENTIALS`

**Test Pipeline:**
```bash
git add .
git commit -m "Setup CI/CD pipeline"
git push origin main

# Watch GitHub Actions tab
```

---

#### Step 11: Monitoring and Logging

**Action:** Set up observability.

##### 11.1: Application Insights (Azure)

```bash
# Create Application Insights
az monitor app-insights component create \
  --app todo-insights \
  --location eastus \
  --resource-group todo-rg
```

Add to deployment:
```yaml
env:
  - name: APPLICATIONINSIGHTS_CONNECTION_STRING
    value: "InstrumentationKey=..."
```

##### 11.2: Prometheus + Grafana

```bash
# Install Prometheus
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack

# Access Grafana
kubectl port-forward svc/prometheus-grafana 3000:80

# Login: admin / prom-operator
```

##### 11.3: Dapr Dashboard

```bash
dapr dashboard -k -p 9999
# Access at http://localhost:9999
```

---

### Part E: Testing and Validation

#### Step 12: End-to-End Testing

**Action:** Validate entire system.

**Test Scenarios:**

1. **Basic CRUD:**
   - Create task via chatbot
   - List tasks
   - Update task
   - Delete task
   - Mark complete

2. **Advanced Features:**
   - Add task with priority and tags
   - Search tasks by keyword
   - Filter by priority
   - Sort by due date

3. **Recurring Tasks:**
   - Create recurring task (daily)
   - Mark complete
   - Verify new task created automatically

4. **Reminders:**
   - Create task with reminder
   - Verify notification received at scheduled time

5. **Event-Driven:**
   - Check Kafka topics for events
   - Verify consumers processing events
   - Check audit logs

6. **Load Testing:**
   - Use Apache Bench or k6
   - Test 100 concurrent users
   - Verify autoscaling works

**Example Test Script:**
```bash
# Load test
kubectl run -it --rm load-test --image=williamyeh/hey:latest --restart=Never -- \
  -z 60s -c 100 https://todo.yourdomain.com/api/health

# Check metrics
kubectl top pods
kubectl get hpa
```

---

### Phase V Deliverables

Submit via https://forms.gle/KMKEKaFUD6ZX4UtY8:

- ✅ **GitHub Repository** with:
  - All intermediate & advanced features
  - `/services` - Microservices (recurring, notification, audit)
  - `/dapr-components` - Dapr configuration files
  - `.github/workflows` - CI/CD pipeline
  - Updated Helm charts for cloud
  - Kafka integration code
  - Complete documentation

- ✅ **Deployed Application:**
  - Cloud Kubernetes URL (Azure/GCP/Oracle)
  - All services running
  - Kafka event-driven architecture working
  - Dapr integration functional
  - TLS/HTTPS enabled
  - Monitoring dashboard accessible

- ✅ **Demo Video** (<90 seconds):
  - Show all advanced features
  - Demonstrate event-driven architecture
  - Show recurring task creation
  - Show reminder notifications
  - Display Dapr dashboard
  - Show cloud deployment

- ✅ **Features Implemented:**
  - ✅ Priorities & Tags
  - ✅ Search & Filter
  - ✅ Sort Tasks
  - ✅ Recurring Tasks
  - ✅ Due Dates & Reminders
  - ✅ Kafka pub/sub (4 use cases)
  - ✅ Dapr (5 components)
  - ✅ Cloud deployment
  - ✅ CI/CD pipeline
  - ✅ Monitoring & logging

---

## Submission Checklist (All Phases)

For each phase, submit via https://forms.gle/KMKEKaFUD6ZX4UtY8:

### Required Submissions

1. **Public GitHub Repository**
   - All source code for all completed phases
   - `/specs` folder with all specification files
   - `CLAUDE.md` with Claude Code instructions
   - `README.md` with comprehensive documentation
   - Clear folder structure for each phase
   - `.specify/memory/constitution.md`
   - `/history/prompts` - PHRs (Prompt History Records)
   - `/history/adr` - Architecture Decision Records

2. **Deployed Application Links**
   - **Phase II:** Vercel frontend URL + Backend API URL
   - **Phase III:** Chatbot URL
   - **Phase IV:** Minikube setup instructions
   - **Phase V:** Cloud deployment URL (https://todo.yourdomain.com)

3. **Demo Video** (maximum 90 seconds)
   - Must be under 90 seconds (judges watch first 90 seconds only)
   - Demonstrate all implemented features
   - Show spec-driven development workflow
   - Use NotebookLM or screen recording
   - Upload to YouTube/Vimeo/Google Drive
   - Include link in submission

4. **WhatsApp Number**
   - For presentation invitation
   - Top submissions invited to present live on Zoom
   - Sundays at 8:00 PM

### Project Structure Checklist

```
full-stack-todo/
├── .github/
│   └── workflows/
│       └── deploy.yml          ✅ CI/CD pipeline
├── .specify/
│   └── memory/
│       └── constitution.md      ✅ Project principles
├── specs/
│   ├── overview.md             ✅ Project overview
│   ├── features/               ✅ Feature specifications
│   ├── api/                    ✅ API specifications
│   ├── database/               ✅ Database schema
│   └── ui/                     ✅ UI specifications
├── history/
│   ├── prompts/                ✅ PHRs
│   └── adr/                    ✅ ADRs
├── frontend/
│   ├── Dockerfile              ✅ Container
│   └── CLAUDE.md               ✅ Frontend instructions
├── backend/
│   ├── Dockerfile              ✅ Container
│   ├── mcp_server/             ✅ MCP tools
│   └── CLAUDE.md               ✅ Backend instructions
├── services/
│   ├── recurring-task-service/ ✅ Microservice
│   ├── notification-service/   ✅ Microservice
│   └── audit-service/          ✅ Optional
├── charts/
│   ├── frontend/               ✅ Helm chart
│   ├── backend/                ✅ Helm chart
│   └── services/               ✅ Service charts
├── dapr-components/            ✅ Dapr configs
├── testing-agent/              ✅ E2E testing (existing)
├── CLAUDE.md                   ✅ Root instructions
├── README.md                   ✅ Complete documentation
└── roadmap.md                  ✅ This file
```

---

## Key Success Tips

### 1. Use Spec-Driven Development (CRITICAL)

**The Golden Rule:** No manual coding allowed. You must refine specs until Claude Code generates correct output.

**Workflow:**
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

**Example:**
```bash
# Bad approach (manual coding)
vim backend/routes/tasks.py  # ❌ Don't do this

# Good approach (spec-driven)
# 1. Update specs/features/task-crud.md
# 2. Run: /sp.implement
# 3. Claude generates the code
```

### 2. Document Everything

**Required Documentation:**

- **Specifications:** Every feature must have a spec in `/specs`
- **PHRs:** Record significant AI exchanges in `/history/prompts`
- **ADRs:** Document major architecture decisions in `/history/adr`
- **CLAUDE.md:** Keep updated with latest patterns and instructions
- **README.md:** Comprehensive setup guide

**Template PHR:**
```markdown
# PHR-001: Implementing Recurring Tasks

## Date
2025-01-10

## Prompt
"Implement recurring tasks feature from @specs/features/recurring-tasks.md"

## Outcome
- Generated recurring_task_service
- Updated database schema
- Added Kafka event handling

## Lessons Learned
- Kafka consumer groups handle scaling
- Dapr Jobs API better than cron
```

### 3. Test Continuously

**Testing Strategy:**

1. **After Each Feature:**
   ```bash
   # Backend
   cd backend
   pytest

   # Frontend
   cd frontend
   npm test
   ```

2. **Before Moving to Next Phase:**
   - All tests passing
   - Manual testing complete
   - Features documented

3. **Before Submission:**
   - E2E testing with testing-agent
   - Load testing
   - Security scanning

**Test Coverage Goal:** 90%+

### 4. Start Early

**Recommended Timeline:**

| Phase | Start Date | Work Days | Completion Date |
|-------|-----------|-----------|-----------------|
| Phase 3 | Dec 15 | 6 days | Dec 21 |
| Phase 4 | Dec 23 | 12 days | Jan 4 |
| Phase 5 | Jan 6 | 12 days | Jan 18 |

**Daily Time Commitment:** 3-4 hours minimum

### 5. Use Free Tiers Wisely

**Cloud Resources:**

| Service | Free Tier | Notes |
|---------|-----------|-------|
| Neon DB | 10 projects | Sufficient for hackathon |
| Vercel | Unlimited deploys | Free for hobby |
| Azure | $200 credit (30 days) | Start on Dec 28 for Phase 5 |
| Google Cloud | $300 credit (90 days) | Most flexible |
| Oracle Cloud | Always free (4 OCPUs) | Best for learning |
| Redpanda Cloud | Serverless free tier | Recommended for Kafka |

**Cost Optimization:**
- Use Oracle Cloud Always Free for learning (no time limit)
- Start Azure/GCP credits only when needed for Phase 5
- Delete resources after demos to conserve credits

### 6. Leverage AI Tools

**AI-Powered DevOps:**

```bash
# Docker AI (Gordon)
docker ai "Create optimized Dockerfile for Next.js"

# kubectl-ai
kubectl-ai "scale backend to 3 replicas"
kubectl-ai "check why pods are failing"

# kagent
kagent "analyze cluster health"
kagent "optimize resource allocation"
```

**Claude Code:**
- Use MCP servers for Spec-KitPlus integration
- Create reusable subagents
- Build custom skills

### 7. Common Pitfalls to Avoid

❌ **Don't:**
- Write code manually (violates spec-driven requirement)
- Skip documentation
- Ignore test coverage
- Deploy without testing locally first
- Wait until last day to submit
- Hardcode credentials
- Ignore error handling

✅ **Do:**
- Use spec-driven development exclusively
- Document every decision
- Test after each feature
- Deploy to staging before production
- Submit early (can resubmit)
- Use environment variables and secrets
- Handle errors gracefully

---

## Bonus Points Opportunities

Earn up to +600 additional points:

### Bonus 1: Reusable Intelligence (+200 points)

**Task:** Create and use reusable intelligence via Claude Code Subagents and Agent Skills.

**What to Build:**

1. **Custom Subagents:**
   - Database migration agent
   - API testing agent
   - Documentation generator agent

2. **Agent Skills:**
   - FastAPI + SQLModel code generator
   - Next.js component generator
   - Kubernetes manifest generator

**Example Skill Structure:**
```
.claude/skills/
├── fastapi-sqlmodel/
│   ├── skill.md
│   └── templates/
│       ├── model.py.template
│       ├── route.py.template
│       └── test.py.template
└── k8s-manifest/
    ├── skill.md
    └── templates/
        ├── deployment.yaml.template
        └── service.yaml.template
```

**Deliverable:**
- 3+ working subagents or skills
- Documentation on how to use them
- Demo in video

### Bonus 2: Cloud-Native Blueprints (+200 points)

**Task:** Create Cloud-Native Blueprints via Agent Skills for spec-driven deployment.

**What to Build:**

Blueprints that generate deployment configurations from specs:

1. **Kubernetes Blueprint:**
   - Read specs/deployment/kubernetes.md
   - Generate Helm charts
   - Apply to cluster

2. **Terraform Blueprint:**
   - Read specs/infrastructure/cloud.md
   - Generate Terraform files
   - Provision infrastructure

3. **CI/CD Blueprint:**
   - Read specs/cicd/pipeline.md
   - Generate GitHub Actions workflow
   - Setup deployment pipeline

**Example:**
```yaml
# specs/deployment/kubernetes.md
service: todo-backend
replicas: 3
resources:
  cpu: 500m
  memory: 512Mi
ingress:
  host: todo.example.com
  tls: true

# Agent reads this and generates complete Helm chart
```

**Deliverable:**
- 2+ working blueprints
- Generator code/skills
- Demo in video

### Bonus 3: Multi-language Support (+100 points)

**Task:** Add Urdu language support to chatbot.

**Requirements:**

1. **Chatbot UI:**
   - Language selector
   - RTL (right-to-left) layout for Urdu
   - Translated UI labels

2. **Natural Language Understanding:**
   - Accept Urdu commands
   - OpenAI GPT-4 already supports Urdu
   - Example: "ایک کام شامل کریں" → Add task

3. **Responses:**
   - Return responses in user's selected language

**Implementation:**
```typescript
// Frontend
const [language, setLanguage] = useState('en');

// Chat API
const response = await chat({
  message: userMessage,
  language: language  // 'en' or 'ur'
});
```

**Deliverable:**
- Working Urdu language support
- RTL layout
- Demo in video

### Bonus 4: Voice Commands (+200 points)

**Task:** Add voice input for todo commands.

**Requirements:**

1. **Voice Input:**
   - Browser Web Speech API
   - Record and transcribe user voice

2. **Voice Commands:**
   - "Add a task to buy milk"
   - "Show me my tasks"
   - "Mark task one as complete"

3. **Voice Output (Optional):**
   - Text-to-speech for responses

**Implementation:**
```typescript
// Frontend - Voice input
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();

recognition.onresult = (event) => {
  const transcript = event.results[0][0].transcript;
  sendMessage(transcript);
};

recognition.start();
```

**Deliverable:**
- Working voice input
- Voice commands functional
- Demo in video

---

## Resources

### Core Tools

| Tool | Link | Description |
|------|------|-------------|
| Claude Code | https://claude.com/product/claude-code | AI coding assistant |
| Spec-Kit Plus | https://github.com/panaversity/spec-kit-plus | Specification management |
| OpenAI ChatKit | https://platform.openai.com/docs/guides/chatkit | Chatbot UI framework |
| MCP SDK | https://github.com/modelcontextprotocol/python-sdk | MCP server framework |

### Infrastructure

| Service | Link | Notes |
|---------|------|-------|
| Neon DB | https://neon.tech | Free tier available |
| Vercel | https://vercel.com | Free frontend hosting |
| Azure | https://azure.microsoft.com/en-us/free/ | $200 credit for 60 days |
| Google Cloud | https://cloud.google.com/free | $300 credit for 90 days |
| Oracle Cloud | https://www.oracle.com/cloud/free/ | Always free tier |
| Minikube | https://minikube.sigs.k8s.io | Local Kubernetes |
| Redpanda Cloud | https://redpanda.com/cloud | Free Kafka tier |

### Learning Resources

| Topic | Link |
|-------|------|
| Kubernetes | https://kubernetes.io/docs/tutorials/ |
| Helm | https://helm.sh/docs/ |
| Dapr | https://docs.dapr.io/ |
| Kafka | https://kafka.apache.org/documentation/ |
| FastAPI | https://fastapi.tiangolo.com/ |
| Next.js | https://nextjs.org/docs |

### AI DevOps Tools

| Tool | Link | Description |
|------|------|-------------|
| kubectl-ai | https://github.com/sozercan/kubectl-ai | AI-powered kubectl |
| kagent | https://github.com/kdave/kagent | Kubernetes AI agent |
| Docker AI | Built into Docker Desktop 4.53+ | Docker AI assistant |

---

## Support and Questions

### Getting Help

1. **Check Documentation:**
   - Read Hackathon PDF
   - Review CLAUDE.md
   - Check specs in `/specs`

2. **Debug with Claude Code:**
   - Ask Claude to explain errors
   - Use MCP tools for debugging

3. **Use AI DevOps Tools:**
   ```bash
   kubectl-ai "why is my deployment failing?"
   kagent "analyze cluster issues"
   ```

### Common Issues and Solutions

**Issue: Pods stuck in Pending**
```bash
kubectl describe pod <pod-name>
# Check Events section for errors
```

**Issue: Out of memory**
```bash
kubectl top pods
# Increase memory limits in Helm values
```

**Issue: Kafka connection failed**
```bash
# Check Dapr component configuration
kubectl get components
kubectl logs <pod-name> -c daprd
```

**Issue: CI/CD pipeline failing**
```bash
# Check GitHub Actions logs
# Verify secrets are set
# Test deployment locally first
```

---

## Final Checklist

Before submitting each phase, verify:

### Phase 3
- ✅ Chatbot interface working
- ✅ 5 MCP tools implemented and tested
- ✅ Conversation persisted to database
- ✅ Natural language commands working
- ✅ Deployed to Vercel + Render/Railway
- ✅ Demo video recorded (<90 seconds)
- ✅ GitHub repo updated
- ✅ Specs documented in `/specs`

### Phase 4
- ✅ Dockerfiles created
- ✅ Images built and tested
- ✅ Helm charts created
- ✅ Deployed to Minikube
- ✅ Application accessible locally
- ✅ kubectl-ai used for operations
- ✅ Demo video showing deployment
- ✅ README with setup instructions

### Phase 5
- ✅ Intermediate features (priorities, tags, search, filter, sort)
- ✅ Advanced features (recurring tasks, reminders)
- ✅ Kafka setup and event-driven architecture
- ✅ 4 Kafka use cases implemented
- ✅ Dapr installed and configured
- ✅ 5 Dapr components working
- ✅ Cloud Kubernetes cluster running
- ✅ All microservices deployed
- ✅ CI/CD pipeline functional
- ✅ TLS/HTTPS enabled
- ✅ Monitoring setup
- ✅ Demo video showing all features
- ✅ Complete documentation

---

## Conclusion

This roadmap provides a complete step-by-step guide to completing Phases 3, 4, and 5 of Hackathon II.

**Remember:**
- Follow spec-driven development (no manual coding!)
- Document everything
- Test continuously
- Start early
- Use AI tools to your advantage

**Key Dates:**
- **Phase 3:** December 21, 2025
- **Phase 4:** January 4, 2026
- **Phase 5:** January 18, 2026

**Total Possible Points:**
- Phase 3: 200
- Phase 4: 250
- Phase 5: 300
- Bonuses: +600
- **Grand Total: 1,350 points**

**Submission:** https://forms.gle/KMKEKaFUD6ZX4UtY8

**Live Presentations:** Sundays at 8:00 PM on Zoom
Meeting: https://us06web.zoom.us/j/84976847088?pwd=Z7t7NaeXwVmmR5fysCv7NiMbfbhIda.1

---

**Good luck, and may your specs be clear and your code be clean!** 🚀

— The Panaversity, PIAIC, and GIAIC Teams
