# Quickstart: Dapr Integration

**Feature**: 012-dapr-integration
**Date**: 2026-01-18

This guide provides step-by-step instructions to set up and run the Dapr-integrated Full-Stack Todo application locally.

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Docker Desktop | 4.25+ | Container runtime |
| Dapr CLI | 1.12+ | Dapr runtime management |
| Python | 3.13+ | Backend runtime |
| Node.js | 20+ | Frontend runtime |
| kubectl | 1.28+ | Kubernetes CLI (for K8s deployment) |
| Helm | 3.12+ | Kubernetes package manager |

### Install Dapr CLI

**Windows (PowerShell)**:
```powershell
powershell -Command "iwr -useb https://raw.githubusercontent.com/dapr/cli/master/install/install.ps1 | iex"
```

**macOS/Linux**:
```bash
curl -fsSL https://raw.githubusercontent.com/dapr/cli/master/install/install.sh | bash
```

### Initialize Dapr

```bash
# Initialize Dapr for local development
dapr init

# Verify installation
dapr --version
# Expected: CLI version: 1.12.0, Runtime version: 1.12.0
```

---

## Local Development Setup

### Step 1: Start Infrastructure

```bash
# Start Kafka/Redpanda and Redpanda Console
cd full-stack-todo
docker-compose -f docker-compose-kafka.yml up -d

# Verify Kafka is running
docker ps | grep redpanda
# Access Redpanda Console: http://localhost:8080
```

### Step 2: Configure Local Dapr Components

Create local component files:

```bash
mkdir -p ~/.dapr/components
```

**~/.dapr/components/pubsub.yaml**:
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
      value: "localhost:19092"
    - name: authType
      value: "none"
    - name: consumerGroup
      value: "local-dev"
```

**~/.dapr/components/statestore.yaml**:
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
      value: "your-neon-connection-string"
```

### Step 3: Run Backend with Dapr

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run with Dapr sidecar
dapr run \
  --app-id backend-service \
  --app-port 8000 \
  --dapr-http-port 3500 \
  --components-path ~/.dapr/components \
  -- uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at:
- Application: http://localhost:8000
- Dapr HTTP API: http://localhost:3500
- API Docs: http://localhost:8000/docs

### Step 4: Run Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend available at: http://localhost:3000

### Step 5: Run Microservices (Optional)

**Notification Service**:
```bash
cd services/notification-service
pip install -r requirements.txt

dapr run \
  --app-id notification-service \
  --app-port 8001 \
  --dapr-http-port 3501 \
  --components-path ~/.dapr/components \
  -- uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

**Recurring Task Service**:
```bash
cd services/recurring-task-service
pip install -r requirements.txt

dapr run \
  --app-id recurring-task-service \
  --app-port 8002 \
  --dapr-http-port 3502 \
  --components-path ~/.dapr/components \
  -- python -m src.main
```

---

## Multi-App Mode (Recommended)

Create a `dapr.yaml` file in the project root for running all services together:

**dapr.yaml**:
```yaml
version: 1
common:
  componentsPath: ./dapr-components
apps:
  - appID: backend-service
    appDirPath: ./backend
    appPort: 8000
    daprHTTPPort: 3500
    command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

  - appID: notification-service
    appDirPath: ./services/notification-service
    appPort: 8001
    daprHTTPPort: 3501
    command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

  - appID: recurring-task-service
    appDirPath: ./services/recurring-task-service
    appPort: 8002
    daprHTTPPort: 3502
    command: ["python", "-m", "src.main"]
```

Run all services:
```bash
dapr run -f dapr.yaml
```

Stop all services:
```bash
dapr stop -f dapr.yaml
```

---

## Verify Dapr Integration

### Check Dapr Health

```bash
# Check sidecar health
curl http://localhost:3500/v1.0/healthz
# Expected: 204 No Content

# List registered components
curl http://localhost:3500/v1.0/metadata
```

### Test Pub/Sub

```bash
# Publish test event
curl -X POST http://localhost:3500/v1.0/publish/kafka-pubsub/task-events \
  -H "Content-Type: application/json" \
  -d '{"event_type":"test","task_id":1,"user_id":"test","timestamp":"2026-01-18T10:00:00Z"}'
# Expected: 204 No Content
```

### Test State Store

```bash
# Save state
curl -X POST http://localhost:3500/v1.0/state/statestore \
  -H "Content-Type: application/json" \
  -d '[{"key":"test-key","value":{"hello":"world"}}]'

# Get state
curl http://localhost:3500/v1.0/state/statestore/test-key
# Expected: {"hello":"world"}
```

### Test Service Invocation

```bash
# Invoke backend service health check
curl http://localhost:3500/v1.0/invoke/backend-service/method/health
```

---

## Kubernetes Deployment

### Step 1: Start Minikube

```bash
minikube start --cpus=4 --memory=8192
minikube addons enable ingress
minikube addons enable metrics-server
```

### Step 2: Install Dapr on Kubernetes

```bash
# Install Dapr to cluster
dapr init -k

# Verify installation
dapr status -k
# All services should show "Running"
kubectl get pods -n dapr-system
```

### Step 3: Deploy Dapr Components

```bash
# Apply component configurations
kubectl apply -f dapr-components/

# Verify components
kubectl get components
```

### Step 4: Create Secrets

```bash
# Create application secrets
kubectl create secret generic app-secrets \
  --from-literal=OPENAI_API_KEY="sk-..." \
  --from-literal=BETTER_AUTH_SECRET="..."

kubectl create secret generic postgres-credentials \
  --from-literal=connectionString="postgresql://..."

kubectl create secret generic kafka-credentials \
  --from-literal=brokers="kafka:9092" \
  --from-literal=username="" \
  --from-literal=password=""
```

### Step 5: Deploy with Helm

```bash
# Build and load images
eval $(minikube docker-env)
docker build -t todo-backend:latest ./backend
docker build -t todo-frontend:latest ./frontend

# Deploy backend
helm install backend ./charts/backend \
  --set dapr.enabled=true \
  --set dapr.appId=backend-service

# Deploy frontend
helm install frontend ./charts/frontend \
  --set dapr.enabled=true

# Deploy microservices
helm install notification-service ./charts/notification-service \
  --set dapr.enabled=true \
  --set dapr.appId=notification-service

helm install recurring-task-service ./charts/recurring-task-service \
  --set dapr.enabled=true \
  --set dapr.appId=recurring-task-service
```

### Step 6: Access Application

```bash
# Port forward (development)
kubectl port-forward svc/frontend 3000:3000 &
kubectl port-forward svc/backend 8000:8000 &

# Or use Minikube tunnel
minikube tunnel
```

---

## Troubleshooting

### Dapr Sidecar Not Starting

```bash
# Check Dapr logs
dapr logs --app-id backend-service

# Check pod status in K8s
kubectl describe pod <pod-name>
kubectl logs <pod-name> -c daprd
```

### Pub/Sub Not Working

```bash
# Verify Kafka is running
docker ps | grep redpanda

# Check topic exists
docker exec -it redpanda rpk topic list

# Create topics manually if needed
docker exec -it redpanda rpk topic create task-events reminders task-updates
```

### State Store Errors

```bash
# Check PostgreSQL connection
psql "your-connection-string" -c "SELECT 1"

# Verify dapr_state table exists
psql "your-connection-string" -c "\dt dapr_state"
```

### Component Not Found

```bash
# List available components
curl http://localhost:3500/v1.0/metadata | jq '.components'

# Reload components (local mode)
dapr stop <app-id>
dapr run ... # restart with components
```

---

## Environment Variables Reference

### Backend (.env)

```env
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Dapr
DAPR_HTTP_PORT=3500

# Auth
BETTER_AUTH_SECRET=your-secret-key

# OpenAI
OPENAI_API_KEY=sk-...

# Kafka (fallback if Dapr unavailable)
KAFKA_BOOTSTRAP_SERVERS=localhost:19092
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
BETTER_AUTH_SECRET=your-secret-key
NEXT_PUBLIC_OPENAI_DOMAIN_KEY=your-domain-key
```

---

## Next Steps

1. **Implement Dapr client modules**: Create `dapr_client.py`, `dapr_state.py`, `dapr_secrets.py`
2. **Update event publisher**: Replace Kafka producer with Dapr pub/sub
3. **Add subscription endpoints**: Add `/dapr/subscribe` and `/events/*` routes
4. **Update Helm charts**: Add Dapr annotations to deployments
5. **Run integration tests**: Verify all Dapr components work together

See [tasks.md](./tasks.md) for the complete implementation task list.
