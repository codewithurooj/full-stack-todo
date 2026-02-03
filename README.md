# Full-Stack Todo Application

> Hackathon II: The Evolution of Todo - Spec-Driven Development

## 🎯 Project Overview

A modern todo application built using spec-driven development with Claude Code and Spec-Kit Plus for Hackathon II Phase 2.

**Phase:** Phase 2 - Full-Stack Web Application
**Due:** December 14, 2025
**Points:** 150

## 🌐 Live Demo

**Try it out now!**

- **Frontend Application:** https://full-stack-todo-application-five.vercel.app
- **Backend API:** https://full-stack-todo-98cf.onrender.com
- **API Documentation:** https://full-stack-todo-98cf.onrender.com/docs
- **Demo Video (Phase 4 - Kubernetes):** https://youtu.be/KqT4QNhNRcw
- **GitHub Repository:** https://github.com/codewithurooj/full-stack-todo

## ✨ Features

- ✅ Task CRUD operations (Create, Read, Update, Delete, Mark Complete)
- ✅ User authentication with Better Auth
- ✅ JWT-based API security
- ✅ Responsive UI with Tailwind CSS
- ✅ PostgreSQL database with Neon
- ✅ RESTful API design
- ✅ Spec-driven development workflow

## ⚡ Event-Driven Architecture (Feature 011)

### Kafka/Redpanda Event Streaming

The application uses an event-driven architecture powered by Kafka/Redpanda for:

- **Automatic Recurring Tasks:** Auto-creates task instances when recurring tasks are completed
- **Browser Notifications:** Sends Web Push notifications for task reminders
- **Complete Audit Trail:** Logs all task operations for compliance and forensics

### Microservices

Three production-ready Kafka consumers:

| Service | Purpose | Throughput |
|---------|---------|------------|
| **Recurring Task Service** | Auto-creates next recurring instance | 1000+ tasks/minute |
| **Notification Service** | Sends Web Push notifications with rate limiting | 500+ notifications/minute |
| **Audit Service** | Logs all events with batch processing | 10,000+ events/minute |

### Key Features

- ✅ **At-least-once delivery** - Zero data loss with manual offset commit
- ✅ **Idempotency** - Database unique constraints prevent duplicates
- ✅ **Event Replay** - CLI tool for disaster recovery and testing
- ✅ **Horizontal Scaling** - Kubernetes HPA based on consumer lag
- ✅ **Prometheus Metrics** - 45+ metrics across all services
- ✅ **SLA Monitoring** - Alerts for 99.9% reliability and <500ms latency

### Architecture Diagram

```
┌──────────┐    Kafka Events    ┌─────────────────┐
│ Backend  │──────task-events───▶│ Recurring Task  │──▶ Auto-create instances
│   API    │                     │    Service      │
└──────────┘                     └─────────────────┘
     │
     │         ┌─────────────────┐
     └────────▶│ Notification    │──▶ Web Push notifications
               │    Service      │
               └─────────────────┘
     │
     │         ┌─────────────────┐
     └────────▶│ Audit Service   │──▶ Complete audit trail
               │  (Batch: 100)   │
               └─────────────────┘
```

### Documentation

- **Event Replay:** `docs/runbooks/event-replay.md`
- **Kafka Failures:** `docs/runbooks/kafka-broker-failure.md`
- **Scaling:** `docs/runbooks/scale-consumers.md`
- **Monitoring:** `monitoring/README.md`

## 🛠️ Tech Stack

### Frontend
- **Framework:** Next.js 16+ (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Auth:** Better Auth (JWT)
- **Deployment:** Vercel

### Backend
- **Framework:** FastAPI
- **Language:** Python 3.13+
- **ORM:** SQLModel
- **Database:** Neon Serverless PostgreSQL
- **Deployment:** Render/Railway

### Development
- **Spec-Driven:** Claude Code + Spec-Kit Plus
- **Containerization:** Docker Compose
- **Testing:** Pytest + Jest
- **CI/CD:** GitHub Actions

## 📁 Project Structure

```
full-stack-todo/
├── frontend/           # Next.js application
│   ├── app/           # Pages (App Router)
│   ├── components/    # Reusable components
│   └── lib/           # Utilities & API client
├── backend/           # FastAPI server
│   ├── app/          # Application code
│   │   ├── models/   # SQLModel models
│   │   ├── routes/   # API endpoints
│   │   └── middleware/ # Auth & other middleware
│   └── tests/        # Pytest tests
├── specs/            # Specifications
│   ├── features/     # Feature specs
│   ├── api/         # API specs
│   ├── database/    # Database schemas
│   └── ui/          # UI specs
├── history/         # Historical records
│   ├── prompts/     # Prompt History Records
│   └── adr/        # Architecture Decision Records
└── .claude/        # Claude Code configuration
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.13+
- Neon Database account (free tier)
- Docker (optional)

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd full-stack-todo
   ```

2. **Set up environment variables**

   **Frontend** (create `frontend/.env.local`):
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   BETTER_AUTH_SECRET=your-secret-key-min-32-chars
   ```

   **Backend** (create `backend/.env`):
   ```env
   DATABASE_URL=postgresql://user:pass@host.neon.tech/dbname
   BETTER_AUTH_SECRET=your-secret-key-min-32-chars
   OPENAI_API_KEY=sk-your-openai-api-key
   ```

3. **Install dependencies**

   **Frontend:**
   ```bash
   cd frontend
   npm install
   ```

   **Backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

### Running Locally

**Option 1: Run services separately**

```bash
# Terminal 1 - Frontend
cd frontend
npm run dev
# → http://localhost:3000

# Terminal 2 - Backend
cd backend
uvicorn app.main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs (API docs)
```

**Option 2: Run with Docker Compose**

```bash
docker-compose up
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest                    # Run all tests
pytest --cov             # With coverage report
pytest -v                # Verbose output
```

### Frontend Tests
```bash
cd frontend
npm test                 # Run tests
npm run test:watch      # Watch mode
```

## 🌐 API Documentation

Interactive API documentation available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### API Endpoints

```
GET    /api/{user_id}/tasks              List all tasks
POST   /api/{user_id}/tasks              Create task
GET    /api/{user_id}/tasks/{id}         Get task
PUT    /api/{user_id}/tasks/{id}         Update task
DELETE /api/{user_id}/tasks/{id}         Delete task
PATCH  /api/{user_id}/tasks/{id}/complete Toggle completion
```

## 📚 Development Workflow

### Spec-Driven Development

This project follows spec-driven development principles:

1. **Write Specification**
   ```bash
   # Use spec-writer skill
   "Use spec-writer skill to create task CRUD spec"
   ```

2. **Generate Code**
   ```bash
   # Backend
   "Use fastapi-sqlmodel skill from @specs/features/task-crud.md"

   # Frontend
   "Use nextjs-betterauth skill from @specs/ui/task-management.md"
   ```

3. **Test & Iterate**
   ```bash
   pytest
   npm test
   ```

4. **Document**
   ```bash
   /sp.phr  # Create Prompt History Record
   ```

## 🚀 Deployment

### ✅ Production Deployment

This application is **already deployed and live!**

**Frontend (Vercel):**
- **URL:** https://full-stack-todo-application-five.vercel.app
- **Status:** ✅ Live
- **Auto-deploy:** Enabled (deploys on push to `master`)

**Backend (Render):**
- **URL:** https://full-stack-todo-98cf.onrender.com
- **Status:** ✅ Live
- **Auto-deploy:** Enabled (deploys on push to `master`)

**Database (Neon PostgreSQL):**
- **Status:** ✅ Connected
- **Type:** Serverless PostgreSQL

### Deploy Your Own Instance

**Frontend (Vercel):**

1. Push code to GitHub
2. Connect repository to Vercel
3. Set Root Directory to `frontend`
4. Set environment variables:
   - `NEXT_PUBLIC_API_URL`
   - `BETTER_AUTH_SECRET`
5. Deploy

```bash
cd frontend
vercel deploy
```

**Backend (Render/Railway):**

1. Connect GitHub repository
2. Set environment variables:
   - `DATABASE_URL`
   - `BETTER_AUTH_SECRET`
   - `OPENAI_API_KEY`
3. Deploy from main branch

## 📝 Documentation

- **Specifications:** `/specs/features/`
- **API Docs:** `/specs/api/rest-endpoints.md`
- **Database Schema:** `/specs/database/schema.md`
- **Frontend Guide:** `frontend/CLAUDE.md`
- **Backend Guide:** `backend/CLAUDE.md`
- **Constitution:** `.specify/memory/constitution.md`

## 🤝 Contributing

This project follows spec-driven development. All changes must:

1. Have a specification in `/specs`
2. Pass all tests
3. Include a PHR in `/history/prompts`
4. Follow code conventions in CLAUDE.md files

## 📋 Hackathon Submission

### Required Deliverables
- ✅ Public GitHub repository
- ✅ Deployed frontend (Vercel)
- ✅ Deployed backend (Render/Railway)
- ✅ Demo video (< 90 seconds) - **[Watch on YouTube](https://youtu.be/KqT4QNhNRcw)**
- ✅ All specifications documented

### Phase 4 - Kubernetes Deployment
- ✅ Dockerfiles for both applications
- ✅ Helm charts with proper configuration
- ✅ Running deployment on Minikube (local Kubernetes)
- ✅ Demo video showcasing Kubernetes deployment
- ✅ Complete setup documentation

### Phase 5 - Cloud Kubernetes Deployment (AKS)
- ✅ Deployed to Azure Kubernetes Service (AKS)
- ✅ Azure Container Registry (ACR) for image management
- ✅ NGINX Ingress Controller with HTTPS/TLS (Let's Encrypt)
- ✅ cert-manager for automatic certificate renewal
- ✅ Prometheus + Grafana monitoring stack
- ✅ Custom alerting rules and Grafana dashboards
- ✅ GitHub Actions CI/CD pipeline
- ✅ Multi-cloud Helm values (AKS, GKE, OKE)
- ✅ Operational runbooks (troubleshooting, rollback, scaling)

### Submission Form
Submit at: https://forms.gle/KMKEKaFUD6ZX4UtY8

## 📄 License

MIT

---

**Built with spec-driven development using Claude Code!** 🚀

## ☁️ Cloud Kubernetes Deployment (AKS)

### Live AKS Deployment

- **Application URL:** https://135.235.185.11.nip.io
- **Backend API:** https://135.235.185.11.nip.io/api
- **API Docs:** https://135.235.185.11.nip.io/docs
- **Health Check:** https://135.235.185.11.nip.io/health

### Infrastructure

| Component | Technology | Status |
|-----------|-----------|--------|
| Kubernetes | Azure AKS (K8s 1.33) | Running |
| Container Registry | Azure ACR (`todoappcr2026.azurecr.io`) | Active |
| Ingress | NGINX Ingress Controller | Running |
| TLS | cert-manager + Let's Encrypt | Auto-renewed |
| Monitoring | Prometheus + Grafana | Running |
| CI/CD | GitHub Actions | Configured |

### Deploy to AKS

```bash
# 1. Login to Azure and ACR
az login
az acr login --name todoappcr2026

# 2. Build and push images
docker build -t todoappcr2026.azurecr.io/todo-backend:latest ./backend
docker build -t todoappcr2026.azurecr.io/todo-frontend:latest ./frontend
docker push todoappcr2026.azurecr.io/todo-backend:latest
docker push todoappcr2026.azurecr.io/todo-frontend:latest

# 3. Connect to AKS
az aks get-credentials --resource-group todo-app-rg --name todo-cluster

# 4. Create secrets
kubectl create secret generic todo-backend-secrets -n todo-app \
  --from-literal=DATABASE_URL='your-db-url' \
  --from-literal=BETTER_AUTH_SECRET='your-secret' \
  --from-literal=OPENAI_API_KEY='your-key'

# 5. Deploy with Helm
helm upgrade --install todo-backend ./charts/backend -n todo-app \
  -f charts/backend/values-aks.yaml
helm upgrade --install todo-frontend ./charts/frontend -n todo-app \
  -f charts/frontend/values-aks.yaml

# 6. Apply ingress
kubectl apply -f k8s/ingress/todo-app-ingress.yaml

# 7. Verify
kubectl get pods -n todo-app
kubectl get ingress -n todo-app
```

### Monitoring

```bash
# Access Grafana (port-forward)
kubectl port-forward svc/kube-prometheus-grafana 3000:80 -n monitoring
# Login: admin / TodoAdmin2026!

# Access Prometheus
kubectl port-forward svc/kube-prometheus-kube-prome-prometheus 9090:9090 -n monitoring
```

### Multi-Cloud Support

Deploy to different providers using provider-specific values:

```bash
# Azure AKS
helm upgrade --install todo-backend ./charts/backend -f charts/backend/values-aks.yaml

# Google GKE
helm upgrade --install todo-backend ./charts/backend -f charts/backend/values-gke.yaml

# Oracle OKE
helm upgrade --install todo-backend ./charts/backend -f charts/backend/values-oke.yaml
```

## ☸️ Kubernetes Setup (Minikube)

### Local Kubernetes Cluster for Development

This project includes complete Minikube setup scripts for running the application in a local Kubernetes environment.

**Features:**
- 🎯 One-command cluster initialization
- 🔌 NGINX Ingress Controller for HTTP/HTTPS routing
- 📊 Metrics Server for resource monitoring
- 🌐 Kubernetes Dashboard for visual management
- ✅ Comprehensive health verification
- 🧹 Safe cleanup and management tools

### Quick Start

1. **Install Prerequisites**
   - Minikube 1.32+ ([Installation Guide](https://minikube.sigs.k8s.io/docs/start/))
   - kubectl 1.28+ ([Installation Guide](https://kubernetes.io/docs/tasks/tools/))
   - Docker 20.10+ ([Installation Guide](https://docs.docker.com/get-docker/))

2. **Start Cluster**
   ```bash
   ./scripts/minikube/start-cluster.sh
   ```

3. **Enable Addons**
   ```bash
   ./scripts/minikube/enable-addons.sh all
   ```

4. **Verify Health**
   ```bash
   ./scripts/minikube/verify-health.sh
   ```

5. **Access Dashboard**
   ```bash
   minikube dashboard -p todo-dev
   ```

### Cluster Configuration

- **Profile:** `todo-dev`
- **Driver:** Docker (cross-platform compatible)
- **Resources:** 4 CPUs, 8GB RAM, 40GB disk
- **Kubernetes Version:** Latest stable

### Available Scripts

| Script | Purpose |
|--------|---------|
| `start-cluster.sh` | Initialize Minikube cluster with resources |
| `enable-addons.sh` | Enable and verify addons (ingress, metrics, dashboard) |
| `verify-health.sh` | Comprehensive health check (11 tests) |
| `cleanup.sh` | Stop, pause, or delete cluster safely |

### Documentation

Complete setup guide: [docs/minikube-setup.md](docs/minikube-setup.md)

### Common Commands

```bash
# Cluster management
minikube start -p todo-dev              # Start cluster
minikube stop -p todo-dev               # Stop cluster (preserves data)
minikube delete -p todo-dev             # Delete cluster

# kubectl basics
kubectl get nodes                       # Check node status
kubectl get pods -A                     # List all pods
kubectl top nodes                       # View resource usage

# Addon management
./scripts/minikube/enable-addons.sh ingress        # Enable ingress
./scripts/minikube/enable-addons.sh metrics-server # Enable metrics
./scripts/minikube/enable-addons.sh dashboard      # Enable dashboard
./scripts/minikube/enable-addons.sh status         # Show addon status
```

### Deploying Todo App to Minikube

```bash
# 1. Start cluster
./scripts/minikube/start-cluster.sh

# 2. Enable ingress
./scripts/minikube/enable-addons.sh ingress

# 3. Deploy application manifests (example)
kubectl apply -f kubernetes/examples/hello-world-deployment.yaml
kubectl apply -f kubernetes/examples/hello-world-service.yaml
kubectl apply -f kubernetes/examples/hello-world-ingress.yaml

# 4. Add to hosts file
echo "$(minikube ip -p todo-dev) todo.local" | sudo tee -a /etc/hosts

# 5. Access application
curl http://todo.local
```

### Troubleshooting

See [docs/minikube-setup.md](docs/minikube-setup.md) for detailed troubleshooting guide covering:
- Prerequisites not met
- Resource constraints
- Network connectivity issues
- Addon failures
- Performance optimization

