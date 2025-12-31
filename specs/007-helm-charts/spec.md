# Feature Specification: Helm Charts Deployment

**Feature Branch**: `007-helm-charts`
**Created**: 2025-12-30
**Status**: Draft
**Input**: User description: "write specification for Helm Charts - Frontend chart with 2 replicas - Backend chart with 2 replicas - Service configurations (ClusterIP) - Ingress for external access"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Deploy Full-Stack Application to Minikube (Priority: P1)

As a developer, I want to deploy the complete full-stack todo application to my local Minikube cluster using Helm charts, so that I can test Kubernetes deployment configurations locally before production.

**Why this priority**: This is the core MVP functionality. Without the ability to deploy the application, no other scenarios are possible. This delivers immediate value by enabling local Kubernetes testing.

**Independent Test**: Can be fully tested by running `helm install todo-app ./charts/frontend` and `helm install todo-api ./charts/backend` and verifying that all pods start successfully. Delivers a working application accessible via kubectl port-forward.

**Acceptance Scenarios**:

1. **Given** Minikube is running and Docker images are built, **When** I run `helm install todo-app ./charts/frontend`, **Then** the frontend deployment creates 2 replicas and all pods reach Running state within 60 seconds
2. **Given** Minikube is running and Docker images are built, **When** I run `helm install todo-api ./charts/backend`, **Then** the backend deployment creates 2 replicas and all pods reach Running state within 60 seconds
3. **Given** both charts are installed, **When** I run `kubectl get pods`, **Then** I see 4 total pods (2 frontend + 2 backend) all in Running state with READY 1/1

---

### User Story 2 - Configure Environment Variables (Priority: P2)

As a developer, I want to configure environment variables for the frontend and backend through Helm values, so that I can easily manage different configurations without rebuilding Docker images.

**Why this priority**: Environment configuration is essential for connecting the application components (frontend → backend → database). However, it can be tested after basic deployment works by using default values initially.

**Independent Test**: Can be tested by installing charts with custom values.yaml and verifying environment variables are correctly injected into pods via `kubectl exec`. Delivers configurable deployments.

**Acceptance Scenarios**:

1. **Given** I have a custom values.yaml with DATABASE_URL, **When** I install the backend chart with `helm install -f values.yaml`, **Then** the backend pods have DATABASE_URL environment variable set correctly
2. **Given** I have NEXT_PUBLIC_API_URL in values.yaml, **When** I install the frontend chart, **Then** the frontend pods can connect to the backend service
3. **Given** I need to change BETTER_AUTH_SECRET, **When** I update values.yaml and run `helm upgrade`, **Then** pods restart with the new secret value

---

### User Story 3 - Access Application via Ingress (Priority: P1)

As a developer, I want to access the application through a single ingress URL with path-based routing, so that I can test the application like it would work in production.

**Why this priority**: Ingress access is critical for realistic testing and user acceptance. Without it, developers would need to manually port-forward each service. This is essential MVP functionality.

**Independent Test**: Can be tested by installing the ingress resource and verifying paths route correctly using curl or browser. Delivers production-like access pattern.

**Acceptance Scenarios**:

1. **Given** ingress is deployed, **When** I visit `http://todo.local/`, **Then** I see the Next.js frontend application
2. **Given** ingress is deployed, **When** I send a request to `http://todo.local/api/health`, **Then** I receive a response from the FastAPI backend
3. **Given** ingress is deployed, **When** I interact with the frontend, **Then** API requests to `/api/*` are routed to the backend service without CORS errors

---

### User Story 4 - Upgrade and Rollback Deployments (Priority: P3)

As a developer, I want to upgrade my application using Helm and rollback if something goes wrong, so that I can safely test new versions without breaking my development environment.

**Why this priority**: Upgrade/rollback is important for ongoing development but not needed for initial deployment. Can be tested after basic deployment is working.

**Independent Test**: Can be tested by performing helm upgrade with a new image tag, then helm rollback. Delivers safe update mechanisms.

**Acceptance Scenarios**:

1. **Given** version 1.0 is deployed, **When** I run `helm upgrade todo-app --set image.tag=1.1`, **Then** pods gracefully terminate old version and start new version with zero downtime
2. **Given** version 1.1 has a bug, **When** I run `helm rollback todo-app`, **Then** the system reverts to version 1.0 within 30 seconds
3. **Given** I upgrade the backend chart, **When** the new version fails health checks, **Then** Kubernetes automatically keeps the old pods running

---

### User Story 5 - Monitor Resource Usage (Priority: P3)

As a developer, I want to set resource requests and limits in my Helm charts, so that my application runs efficiently within Minikube's resource constraints.

**Why this priority**: Resource management is important for production-readiness but not critical for initial local testing. Can be added after deployment works.

**Independent Test**: Can be tested by installing charts with resource definitions and verifying pods stay within limits using `kubectl top pods`. Delivers resource-aware deployments.

**Acceptance Scenarios**:

1. **Given** resource limits are defined in values.yaml, **When** I install the charts, **Then** each pod has CPU and memory requests/limits set correctly
2. **Given** the frontend pod exceeds memory limit, **When** memory usage spikes, **Then** Kubernetes restarts the pod automatically
3. **Given** resource requests are set, **When** Minikube has limited resources, **Then** Kubernetes schedules pods according to available capacity

---

### Edge Cases

- What happens when database connection fails? Backend pods should fail health checks and Kubernetes should show them as not ready
- How does the system handle image pull failures? Pods should remain in ImagePullBackOff state with clear error messages
- What if ingress controller is not installed? Ingress resource should be created but not functional, with status showing no endpoints
- How do we handle database migrations? Migrations should be run as Kubernetes Jobs before the main deployment starts
- What happens during rolling updates if new pods can't connect to services? Kubernetes should keep old pods running until new ones pass readiness checks

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide separate Helm charts in `charts/frontend/` and `charts/backend/` directories
- **FR-002**: Frontend chart MUST create a Deployment with 2 replicas running Next.js on port 3000
- **FR-003**: Backend chart MUST create a Deployment with 2 replicas running FastAPI on port 8000
- **FR-004**: Both charts MUST create ClusterIP Services to enable internal service discovery
- **FR-005**: System MUST provide an Ingress resource with path-based routing (`/` → frontend, `/api` → backend)
- **FR-006**: Charts MUST support environment variable configuration via `values.yaml` (DATABASE_URL, BETTER_AUTH_SECRET, NEXT_PUBLIC_API_URL, NEXT_PUBLIC_OPENAI_DOMAIN_KEY)
- **FR-007**: Sensitive environment variables (DATABASE_URL, BETTER_AUTH_SECRET, OPENAI_API_KEY) MUST be stored in Kubernetes Secrets
- **FR-008**: Non-sensitive environment variables MUST be stored in ConfigMaps
- **FR-009**: Deployments MUST include liveness and readiness probes to enable automatic health checking
- **FR-010**: Deployments MUST define resource requests and limits (CPU and memory) in values.yaml
- **FR-011**: Frontend MUST use production Docker image with multi-stage build (`frontend/Dockerfile`)
- **FR-012**: Backend MUST use production Docker image with multi-stage build (`backend/Dockerfile`)
- **FR-013**: Ingress MUST use NGINX ingress controller as the default ingress class
- **FR-014**: Charts MUST include proper metadata (name, version, description, appVersion) in Chart.yaml
- **FR-015**: Charts MUST include NOTES.txt with post-installation instructions and access URLs

### Key Entities

- **Frontend Chart**: Helm package containing Deployment, Service, and configuration for Next.js application (2 replicas, port 3000, health checks on `/`)
- **Backend Chart**: Helm package containing Deployment, Service, and configuration for FastAPI application (2 replicas, port 8000, health checks on `/health`)
- **Ingress Resource**: Kubernetes networking resource providing external HTTP access with path-based routing rules
- **ConfigMap**: Kubernetes resource storing non-sensitive configuration (NEXT_PUBLIC_API_URL, NEXT_PUBLIC_OPENAI_DOMAIN_KEY)
- **Secret**: Kubernetes resource storing sensitive configuration (DATABASE_URL, BETTER_AUTH_SECRET, OPENAI_API_KEY)
- **Service**: Kubernetes ClusterIP service providing internal DNS-based service discovery (frontend-service, backend-service)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can deploy both frontend and backend with a single `helm install` command per chart, completing in under 2 minutes total
- **SC-002**: All 4 pods (2 frontend + 2 backend) start successfully and pass health checks within 60 seconds of installation
- **SC-003**: Application is fully functional (can create, read, update, delete tasks) within 90 seconds of installation via ingress URL
- **SC-004**: Service discovery works 100% reliably (frontend can resolve backend-service DNS name)
- **SC-005**: Ingress routing works 100% accurately (100% of requests to `/` go to frontend, 100% of requests to `/api` go to backend)
- **SC-006**: Configuration changes via `helm upgrade` take effect within 30 seconds with zero downtime
- **SC-007**: `helm rollback` completes successfully and restores previous working state without data loss
- **SC-008**: Resource usage stays within defined limits (frontend: max 256Mi memory, backend: max 512Mi memory)
- **SC-009**: Rolling updates maintain at least 1 pod available at all times (zero downtime)
- **SC-010**: All charts pass `helm lint` validation without errors

## Scope

### In Scope

- Helm charts for frontend (Next.js) and backend (FastAPI)
- Kubernetes Deployments with 2 replicas each
- ClusterIP Services for internal communication
- Ingress resource with NGINX controller for external access
- Environment variable management via values.yaml, ConfigMaps, and Secrets
- Health checks (liveness and readiness probes)
- Resource limits and requests
- Chart documentation (README.md, NOTES.txt)
- Values.yaml with sensible defaults for Minikube

### Out of Scope

- Database deployment (Neon PostgreSQL is external SaaS, not in-cluster)
- Horizontal Pod Autoscaling (HPA) - not needed for local development
- Persistent storage for application data (stateless application)
- TLS/SSL certificates (local development uses HTTP)
- Multi-namespace deployment (single default namespace)
- Helm chart repository publishing (local development only)
- Production-grade monitoring/logging (Minikube testing focus)
- CI/CD pipeline integration (manual deployment)

## Assumptions

1. **Minikube Environment**: Developers have Minikube installed and running with sufficient resources (2+ CPUs, 3GB+ RAM)
2. **Docker Images**: Production Docker images are built and available locally (via `minikube image load` or local registry)
3. **Ingress Controller**: NGINX ingress controller is installed in Minikube (via `minikube addons enable ingress`)
4. **External Database**: Neon PostgreSQL database is provisioned and accessible from Minikube pods
5. **Network Access**: Minikube cluster can access external services (Neon database, OpenAI API)
6. **DNS Resolution**: Developers can access ingress via `/etc/hosts` entry or Minikube tunnel
7. **Helm Installed**: Helm 3.x is installed on the developer's machine
8. **Chart Pattern**: Following standard Helm best practices (templates/, values.yaml, Chart.yaml structure)

## Dependencies

### External Dependencies

- **Minikube**: Local Kubernetes cluster (v1.32+)
- **Helm**: Package manager (v3.x)
- **Docker**: Container runtime for building images
- **kubectl**: Kubernetes CLI for verification
- **NGINX Ingress Controller**: Minikube addon for ingress support

### Internal Dependencies

- **Docker Images**: `frontend/Dockerfile` and `backend/Dockerfile` must be built successfully
- **Environment Variables**: Neon DATABASE_URL, BETTER_AUTH_SECRET, OpenAI API key must be available
- **Existing Services**: Neon PostgreSQL database must be created and accessible
- **Git Branch**: Must be on `007-helm-charts` branch for this feature
- **Existing Manifests**: Can reference existing kubernetes/ directory for patterns (hello-world examples)

### Dependency Order

1. Minikube cluster must be running
2. NGINX ingress controller must be enabled
3. Docker images must be built and loaded into Minikube
4. Secrets/ConfigMaps must be created before Deployments
5. Services must be created before Ingress
6. Backend must be healthy before frontend can function fully

## Constraints

### Technical Constraints

- **Resource Limits**: Minikube has limited resources (currently 2 CPUs, 3GB RAM), charts must work within these constraints
- **Image Size**: Docker images should be optimized for multi-stage builds to reduce size and startup time
- **Ingress Pattern**: Must use path-based routing (not subdomain-based) due to Minikube limitations
- **Database Location**: Cannot deploy database in-cluster, must use external Neon PostgreSQL
- **Port Conflicts**: Cannot use host ports 3000 or 8000 if services are running locally
- **Storage**: Minikube on D: drive has limited space (40GB allocated), image sizes matter

### Business Constraints

- **Hackathon Timeline**: This is part of Phase 3 of Hackathon II project
- **Local Development Focus**: Charts are optimized for Minikube, not production-grade Kubernetes
- **Existing Deployment**: Phase 2 is already deployed to Vercel (frontend) + Render (backend), these charts are for local testing only
- **Learning Goal**: Part of learning Kubernetes and Helm, not production infrastructure
- **Cost**: Using free tiers (Neon, Vercel, Render), cannot use paid cloud Kubernetes services

### Design Constraints

- **Chart Structure**: Must follow Helm best practices for maintainability
- **Values Flexibility**: values.yaml must support easy customization without modifying templates
- **Documentation**: Charts must be self-documenting for team members unfamiliar with Helm
- **Compatibility**: Must work with existing Docker Compose setup for comparison
- **Testing**: Must be easily testable with `helm install --dry-run --debug`

---

**Next Steps**: After approval of this specification, run `/sp.plan` to generate the implementation plan for creating the Helm charts.
