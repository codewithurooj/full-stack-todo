# Implementation Plan: Cloud Kubernetes Deployment

**Branch**: `013-cloud-k8s-deployment` | **Date**: 2026-01-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/013-cloud-k8s-deployment/spec.md`

## Summary

Deploy the full-stack todo application to production-grade cloud Kubernetes (Azure AKS, GCP GKE, or Oracle OKE) with automated TLS certificates via cert-manager/Let's Encrypt, CI/CD pipeline using GitHub Actions, and comprehensive monitoring with Prometheus/Grafana. The existing Helm charts and Docker configurations from Phase IV provide a solid foundation; this phase adds cloud registry integration, ingress with TLS, automated deployment pipelines, and cloud-specific configurations.

## Technical Context

**Language/Version**:
- Backend: Python 3.13+ (FastAPI 0.100+, SQLModel 0.0.8+)
- Frontend: Node.js 20+ (Next.js 16+, TypeScript)
- Infrastructure: YAML (Helm 3+, Kubernetes 1.28+)

**Primary Dependencies**:
- Helm 3+ for Kubernetes package management
- cert-manager 1.13+ for TLS certificate automation
- NGINX Ingress Controller for traffic routing
- GitHub Actions for CI/CD
- Prometheus + Grafana for monitoring

**Storage**:
- Neon Serverless PostgreSQL (existing, cloud-managed)
- Container registry (ACR/GCR/OCIR depending on cloud provider)

**Testing**:
- kubectl + Helm validation
- GitHub Actions workflow testing
- curl/httpie for endpoint verification
- k6 or hey for load testing

**Target Platform**:
- Azure AKS (with $200 free credit)
- Google Cloud GKE (with $300 free credit)
- Oracle Cloud OKE (Always Free tier - RECOMMENDED)

**Project Type**: Web application (monorepo with frontend/backend/services)

**Performance Goals**:
- Application accessible within 5 minutes of deployment
- Zero-downtime rolling updates
- Certificate renewal 7+ days before expiration
- < 60 second pod recovery from failures

**Constraints**:
- Single-region deployment (multi-region out of scope)
- Free tier infrastructure where possible
- Existing Helm charts must be extended (not replaced)
- GitHub-based CI/CD only

**Scale/Scope**:
- 100+ concurrent users
- 2+ replicas per service
- 7-day metrics retention
- 30-day image retention in registry

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Constitution Section | Status | Notes |
|------|---------------------|--------|-------|
| Spec-driven development | I | ✅ PASS | spec.md created before implementation |
| Cloud provider support (AKS/GKE/OKE) | XI | ✅ PASS | Multi-provider support specified |
| Container registry | XI | ✅ PASS | ACR/GCR/OCIR options per spec |
| TLS via cert-manager + Let's Encrypt | XI | ✅ PASS | FR-010 through FR-014 |
| CI/CD via GitHub Actions | XI | ✅ PASS | FR-015 through FR-020 |
| Prometheus + Grafana monitoring | XI | ✅ PASS | FR-021 through FR-025 |
| Helm charts for deployment | IX | ✅ PASS | Existing charts to extend |
| No hardcoded secrets | Constraints | ✅ PASS | K8s secrets + env vars |
| Non-root containers | Security | ✅ PASS | Already implemented in Dockerfiles |
| Rolling deployments | IX | ✅ PASS | Helm chart strategy configured |

**Pre-Phase 0 Constitution Status**: ✅ ALL GATES PASS

## Project Structure

### Documentation (this feature)

```text
specs/013-cloud-k8s-deployment/
├── plan.md              # This file
├── spec.md              # Feature specification (complete)
├── research.md          # Phase 0 output (to create)
├── data-model.md        # Phase 1 output (to create)
├── quickstart.md        # Phase 1 output (to create)
├── contracts/           # Phase 1 output (to create)
│   ├── github-actions-workflow.yaml
│   ├── cert-manager-issuer.yaml
│   └── ingress-templates.yaml
├── checklists/
│   └── requirements.md  # Validation checklist (complete)
└── tasks.md             # Phase 2 output (via /sp.tasks)
```

### Source Code (repository root)

```text
.github/
└── workflows/
    └── deploy.yml           # CI/CD pipeline (to create)

charts/
├── backend/
│   ├── values.yaml          # Existing - to extend
│   ├── values-aks.yaml      # Cloud-specific (to create)
│   ├── values-gke.yaml      # Cloud-specific (to create)
│   └── values-oke.yaml      # Cloud-specific (to create)
├── frontend/
│   ├── values.yaml          # Existing - to extend
│   ├── values-aks.yaml      # Cloud-specific (to create)
│   ├── values-gke.yaml      # Cloud-specific (to create)
│   └── values-oke.yaml      # Cloud-specific (to create)
├── notification-service/    # Existing - to update
├── recurring-task-service/  # Existing - to update
├── audit-service/           # Existing - to update
└── dapr-components/         # Existing - to update

k8s/
├── cert-manager/            # To create
│   ├── cluster-issuer-letsencrypt-staging.yaml
│   └── cluster-issuer-letsencrypt-prod.yaml
├── ingress/                 # To create
│   └── ingress-rules.yaml
└── namespaces/              # To create
    └── todo-app-namespace.yaml

monitoring/
├── alerts.yaml              # Existing - ready for cloud
├── grafana/                 # To create
│   └── dashboards/
└── prometheus/              # To create
    └── serviceMonitor.yaml
```

**Structure Decision**: Extend existing `/charts` directory with cloud-specific values files. Add new `/k8s` directory for cert-manager and ingress configurations. Create `.github/workflows` for CI/CD pipeline.

## Complexity Tracking

No constitution violations requiring justification - all planned components align with Phase V requirements.

---

## Phase V: Event-Driven & Cloud-Native Architecture

### Existing Infrastructure (Already Implemented)

**✅ Helm Charts** (charts/):
- Backend chart with 2 replicas, rolling updates, health checks
- Frontend chart with 2 replicas, standalone Next.js
- Microservice charts (notification, recurring-task, audit)
- Dapr components chart

**✅ Docker Images**:
- Backend: Multi-stage Python 3.13 slim (~150MB)
- Frontend: Three-stage Next.js standalone (~180MB)
- All services: Non-root users, health checks

**✅ Dapr Components**:
- kafka-pubsub for event streaming
- statestore for PostgreSQL state
- kubernetes-secrets for secret management
- Resiliency policies configured

**✅ Monitoring Infrastructure**:
- Prometheus alerts (21 rules)
- ServiceMonitor templates in Helm
- Grafana dashboard JSON files

### New Components Required for Cloud Deployment

#### 1. GitHub Actions CI/CD Pipeline

**Workflow Triggers**:
- Push to `main` branch
- Manual dispatch for rollback

**Pipeline Stages**:
```yaml
jobs:
  build-test:
    - Checkout code
    - Run backend tests (pytest)
    - Run frontend tests (npm test)
    - Build Docker images
    - Tag with git SHA and latest

  push-images:
    - Login to container registry
    - Push backend image
    - Push frontend image
    - Push microservice images

  deploy:
    - Configure kubectl context
    - Helm upgrade --install
    - Verify rollout status
    - Run smoke tests
```

**Secrets Required** (GitHub Repository Secrets):
- `REGISTRY_USERNAME` / `REGISTRY_PASSWORD`
- `KUBE_CONFIG` (base64 encoded)
- `DATABASE_URL`
- `BETTER_AUTH_SECRET`
- `OPENAI_API_KEY`

#### 2. Container Registry Configuration

**Azure ACR**:
```bash
az acr create --name todoregistry --sku Basic
# Image: todoregistry.azurecr.io/todo-backend:latest
```

**Google GCR**:
```bash
gcloud auth configure-docker
# Image: gcr.io/PROJECT_ID/todo-backend:latest
```

**Oracle OCIR**:
```bash
# Image: <region>.ocir.io/<tenancy>/todo-backend:latest
```

**Docker Hub** (Alternative):
```bash
# Image: username/todo-backend:latest
```

#### 3. TLS/HTTPS with cert-manager

**Installation**:
```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

**ClusterIssuer for Let's Encrypt**:
```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@yourdomain.com
    privateKeySecretRef:
      name: letsencrypt-prod-key
    solvers:
      - http01:
          ingress:
            class: nginx
```

**Certificate Request** (via Ingress annotation):
```yaml
annotations:
  cert-manager.io/cluster-issuer: "letsencrypt-prod"
```

#### 4. NGINX Ingress Controller

**Installation**:
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
```

**Ingress Rules**:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: todo-ingress
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - todo.yourdomain.com
      secretName: todo-tls
  rules:
    - host: todo.yourdomain.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: todo-backend
                port:
                  number: 8000
          - path: /
            pathType: Prefix
            backend:
              service:
                name: todo-frontend
                port:
                  number: 3000
```

### Cloud-Specific Helm Values

**values-aks.yaml** (Azure):
```yaml
image:
  repository: todoregistry.azurecr.io/todo-backend
  pullPolicy: Always

imagePullSecrets:
  - name: acr-secret

ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: todo.yourdomain.com
      paths:
        - path: /api
          pathType: Prefix
  tls:
    - secretName: todo-backend-tls
      hosts:
        - todo.yourdomain.com
```

**values-gke.yaml** (Google Cloud):
```yaml
image:
  repository: gcr.io/PROJECT_ID/todo-backend
  pullPolicy: Always

# GKE specific node selector if needed
nodeSelector:
  cloud.google.com/gke-nodepool: default-pool
```

**values-oke.yaml** (Oracle Cloud):
```yaml
image:
  repository: <region>.ocir.io/<tenancy>/todo-backend
  pullPolicy: Always

imagePullSecrets:
  - name: ocir-secret
```

### Monitoring & Observability

**Prometheus Stack** (via Helm):
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack
```

**ServiceMonitor for Backend**:
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: todo-backend
spec:
  selector:
    matchLabels:
      app: todo-backend
  endpoints:
    - port: http
      path: /metrics
      interval: 30s
```

**Grafana Dashboards**:
- Import existing `/monitoring/grafana-dashboards/`
- Configure data source for cloud Prometheus

---

## Implementation Phases

### Phase 0: Research (this planning session)

**Research Tasks**:
1. ✅ Cloud provider selection criteria (AKS vs GKE vs OKE)
2. ✅ cert-manager configuration patterns
3. ✅ GitHub Actions best practices for K8s deployment
4. ✅ Container registry authentication methods
5. ✅ Ingress controller selection (NGINX chosen)

**Output**: `research.md` with decisions and rationale

### Phase 1: Design & Contracts

**Artifacts to Create**:
1. `data-model.md` - Infrastructure component definitions
2. `contracts/github-actions-workflow.yaml` - CI/CD pipeline schema
3. `contracts/cert-manager-issuer.yaml` - TLS issuer configuration
4. `contracts/ingress-templates.yaml` - Ingress rule templates
5. `quickstart.md` - Deployment guide for each cloud provider

### Phase 2: Task Generation (via /sp.tasks)

**Expected Task Categories**:
1. GitHub Actions workflow creation
2. cert-manager installation and configuration
3. Ingress controller setup
4. Cloud-specific Helm values files
5. Container registry integration
6. DNS configuration guide
7. Monitoring stack deployment
8. Documentation and runbooks

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Free tier limits exceeded | Medium | Medium | Monitor usage, use OKE always-free |
| DNS propagation delays | Medium | Low | Use staging issuer first, allow 48h |
| cert-manager HTTP-01 challenges fail | Low | High | Ensure ingress controller working first |
| GitHub Actions secrets misconfigured | Medium | Medium | Document setup clearly, use test workflow |
| Container registry auth fails | Low | High | Test locally with docker login first |

---

## Success Criteria Mapping

| Success Criterion | Implementation Component |
|-------------------|-------------------------|
| SC-001: HTTPS with valid TLS | cert-manager + Let's Encrypt |
| SC-002: Zero-downtime deployments | Rolling update strategy in Helm |
| SC-003: Auto-deploy within 15 min | GitHub Actions pipeline |
| SC-004: Certificate auto-renewal | cert-manager renewal automation |
| SC-005: Pod recovery < 60s | Liveness/readiness probes |
| SC-006: Real-time metrics | Prometheus + Grafana |
| SC-007: Alerts within 5 min | Alertmanager configuration |
| SC-008: Pipeline failure notification | GitHub Actions notifications |
| SC-009: Image pull success | Registry auth + pull secrets |
| SC-010: 100 concurrent users | 2+ replicas + HPA |

---

## Next Steps

1. **Create research.md** - Document cloud provider comparison and final decisions
2. **Create data-model.md** - Define infrastructure components formally
3. **Create contracts/** - GitHub Actions workflow and K8s manifests
4. **Create quickstart.md** - Step-by-step deployment guide
5. **Run /sp.tasks** - Generate implementation task list
