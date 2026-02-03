# Data Model: Cloud Kubernetes Deployment Infrastructure

**Feature**: 013-cloud-k8s-deployment
**Date**: 2026-01-18
**Status**: Complete

This document defines the infrastructure components, their relationships, and configuration schemas for cloud Kubernetes deployment.

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLOUD KUBERNETES CLUSTER                          │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        NAMESPACE: todo-app                            │   │
│  │  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐  │   │
│  │  │   INGRESS    │────▶│   SERVICE    │────▶│     DEPLOYMENT       │  │   │
│  │  │  (NGINX)     │     │ (ClusterIP)  │     │ (Pods + ReplicaSet)  │  │   │
│  │  └──────┬───────┘     └──────────────┘     └──────────────────────┘  │   │
│  │         │                                                             │   │
│  │         ▼                                                             │   │
│  │  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐  │   │
│  │  │ CERTIFICATE  │◀────│CLUSTER ISSUER│     │    CONFIG MAP        │  │   │
│  │  │ (TLS Secret) │     │(Let's Encrypt)│     │   (Environment)      │  │   │
│  │  └──────────────┘     └──────────────┘     └──────────────────────┘  │   │
│  │                                                                       │   │
│  │  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐  │   │
│  │  │    SECRET    │     │     HPA      │     │   SERVICE MONITOR    │  │   │
│  │  │ (Credentials)│     │(Autoscaling) │     │   (Prometheus)       │  │   │
│  │  └──────────────┘     └──────────────┘     └──────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    NAMESPACE: ingress-nginx                           │   │
│  │  ┌──────────────────────────────────────────────────────────────┐    │   │
│  │  │              NGINX INGRESS CONTROLLER                         │    │   │
│  │  │   LoadBalancer Service → Public IP → DNS A Record            │    │   │
│  │  └──────────────────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                       NAMESPACE: cert-manager                         │   │
│  │  ┌──────────────────────────────────────────────────────────────┐    │   │
│  │  │              CERT-MANAGER CONTROLLER                          │    │   │
│  │  │   Watches Ingress annotations → Creates Certificates          │    │   │
│  │  └──────────────────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                       NAMESPACE: monitoring                           │   │
│  │  ┌────────────┐  ┌────────────┐  ┌───────────────┐                   │   │
│  │  │ PROMETHEUS │  │  GRAFANA   │  │ ALERTMANAGER  │                   │   │
│  │  └────────────┘  └────────────┘  └───────────────┘                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────────────┐
                    │       EXTERNAL SERVICES         │
                    │                                 │
                    │  ┌───────────────────────────┐  │
                    │  │   CONTAINER REGISTRY      │  │
                    │  │ (DockerHub/ACR/GCR/OCIR)  │  │
                    │  └───────────────────────────┘  │
                    │                                 │
                    │  ┌───────────────────────────┐  │
                    │  │   NEON POSTGRESQL DB      │  │
                    │  │   (Serverless Managed)    │  │
                    │  └───────────────────────────┘  │
                    │                                 │
                    │  ┌───────────────────────────┐  │
                    │  │   GITHUB REPOSITORY       │  │
                    │  │   (Source + CI/CD)        │  │
                    │  └───────────────────────────┘  │
                    └─────────────────────────────────┘
```

---

## Infrastructure Components

### 1. Kubernetes Cluster

**Entity Definition**:

```yaml
Cluster:
  name: string                    # e.g., "todo-cluster"
  provider: enum                  # AKS | GKE | OKE
  region: string                  # e.g., "eastus", "us-central1"
  version: string                 # e.g., "1.28.0"
  nodePool:
    name: string
    nodeCount: integer            # 2-3 for HA
    machineType: string           # e.g., "Standard_B2s", "e2-small", "VM.Standard.A1.Flex"
    architecture: enum            # amd64 | arm64
  status: enum                    # Creating | Running | Updating | Deleting
```

**Provider-Specific Configurations**:

| Field | Azure AKS | Google GKE | Oracle OKE |
|-------|-----------|------------|------------|
| machineType | Standard_B2s | e2-small | VM.Standard.A1.Flex |
| architecture | amd64 | amd64 | arm64 |
| nodeCount | 2 | 2 | 2 |
| resourceGroup | Required | N/A | Compartment |

### 2. Namespace

**Entity Definition**:

```yaml
Namespace:
  name: string                    # "todo-app" | "monitoring" | "ingress-nginx" | "cert-manager"
  labels:
    app.kubernetes.io/name: string
    app.kubernetes.io/part-of: string
  annotations:
    description: string
```

**Namespace Inventory**:

| Namespace | Purpose | Components |
|-----------|---------|------------|
| `todo-app` | Main application | Frontend, Backend, Microservices |
| `ingress-nginx` | Ingress controller | NGINX pods, LoadBalancer service |
| `cert-manager` | TLS automation | cert-manager pods, issuers |
| `monitoring` | Observability | Prometheus, Grafana, Alertmanager |
| `dapr-system` | Dapr runtime | Dapr sidecar injector, placement |

### 3. Deployment

**Entity Definition**:

```yaml
Deployment:
  name: string                    # e.g., "todo-backend"
  namespace: string               # "todo-app"
  replicas: integer               # 2 (default)
  selector:
    matchLabels: map[string]string
  template:
    metadata:
      labels: map[string]string
      annotations: map[string]string  # Dapr annotations if enabled
    spec:
      containers:
        - name: string
          image: string           # registry/repo:tag
          ports:
            - containerPort: integer
          env: list[EnvVar]
          envFrom: list[EnvSource]
          resources:
            requests:
              cpu: string         # "200m"
              memory: string      # "256Mi"
            limits:
              cpu: string         # "1000m"
              memory: string      # "512Mi"
          livenessProbe: Probe
          readinessProbe: Probe
          startupProbe: Probe
      imagePullSecrets:
        - name: string
      serviceAccountName: string
  strategy:
    type: string                  # "RollingUpdate"
    rollingUpdate:
      maxSurge: string            # "1" or "25%"
      maxUnavailable: string      # "0" or "25%"
```

**Deployments Inventory**:

| Deployment | Image | Port | Replicas | Probes |
|------------|-------|------|----------|--------|
| todo-backend | todo-backend:latest | 8000 | 2 | /health |
| todo-frontend | todo-frontend:latest | 3000 | 2 | / |
| notification-service | notification-service:latest | 8002 | 1 | /health |
| recurring-task-service | recurring-task-service:latest | 8001 | 1 | /health |
| audit-service | audit-service:latest | 8003 | 1 | /health |

### 4. Service

**Entity Definition**:

```yaml
Service:
  name: string
  namespace: string
  type: enum                      # ClusterIP | LoadBalancer | NodePort
  selector:
    matchLabels: map[string]string
  ports:
    - name: string
      port: integer               # Service port
      targetPort: integer         # Container port
      protocol: string            # "TCP"
```

**Services Inventory**:

| Service | Type | Port | Target |
|---------|------|------|--------|
| todo-backend | ClusterIP | 8000 | 8000 |
| todo-frontend | ClusterIP | 3000 | 3000 |
| notification-service | ClusterIP | 8002 | 8002 |
| recurring-task-service | ClusterIP | 8001 | 8001 |

### 5. Ingress

**Entity Definition**:

```yaml
Ingress:
  name: string
  namespace: string
  className: string               # "nginx"
  annotations:
    cert-manager.io/cluster-issuer: string
    nginx.ingress.kubernetes.io/ssl-redirect: string
    nginx.ingress.kubernetes.io/proxy-body-size: string
  tls:
    - hosts: list[string]
      secretName: string
  rules:
    - host: string                # "todo.example.com"
      http:
        paths:
          - path: string          # "/" or "/api"
            pathType: enum        # Prefix | Exact | ImplementationSpecific
            backend:
              service:
                name: string
                port:
                  number: integer
```

**Ingress Rules Schema**:

| Host | Path | Service | Port |
|------|------|---------|------|
| todo.example.com | /api | todo-backend | 8000 |
| todo.example.com | / | todo-frontend | 3000 |

### 6. ClusterIssuer (cert-manager)

**Entity Definition**:

```yaml
ClusterIssuer:
  name: string                    # "letsencrypt-staging" | "letsencrypt-prod"
  spec:
    acme:
      server: string              # Let's Encrypt ACME URL
      email: string               # Admin email for notifications
      privateKeySecretRef:
        name: string              # Secret to store ACME account key
      solvers:
        - http01:
            ingress:
              class: string       # "nginx"
```

**Issuer Types**:

| Issuer | Server URL | Use Case |
|--------|------------|----------|
| letsencrypt-staging | https://acme-staging-v02.api.letsencrypt.org/directory | Testing |
| letsencrypt-prod | https://acme-v02.api.letsencrypt.org/directory | Production |

### 7. Certificate

**Entity Definition**:

```yaml
Certificate:
  name: string
  namespace: string
  secretName: string              # TLS secret created by cert-manager
  issuerRef:
    name: string                  # "letsencrypt-prod"
    kind: string                  # "ClusterIssuer"
  dnsNames: list[string]          # ["todo.example.com"]
  duration: string                # "2160h" (90 days)
  renewBefore: string             # "360h" (15 days)
```

**Certificate Lifecycle**:

| State | Duration | Action |
|-------|----------|--------|
| Valid | 90 days | Active |
| Renewing | 30 days before expiry | cert-manager initiates renewal |
| Renewed | After successful renewal | New secret created |
| Failed | On ACME challenge failure | Alert triggered |

### 8. ConfigMap

**Entity Definition**:

```yaml
ConfigMap:
  name: string
  namespace: string
  data:
    KEY: value                    # Non-sensitive configuration
```

**ConfigMaps Inventory**:

| ConfigMap | Data Keys | Consumer |
|-----------|-----------|----------|
| todo-backend-config | ENVIRONMENT, LOG_LEVEL | Backend deployment |
| todo-frontend-config | NEXT_PUBLIC_API_URL, NODE_ENV | Frontend deployment |

### 9. Secret

**Entity Definition**:

```yaml
Secret:
  name: string
  namespace: string
  type: enum                      # Opaque | kubernetes.io/dockerconfigjson | kubernetes.io/tls
  data:
    KEY: base64_encoded_value
```

**Secrets Inventory**:

| Secret | Type | Keys | Source |
|--------|------|------|--------|
| todo-backend-secret | Opaque | DATABASE_URL, BETTER_AUTH_SECRET, OPENAI_API_KEY | GitHub Actions |
| todo-frontend-secret | Opaque | BETTER_AUTH_SECRET, OPENAI_DOMAIN_KEY | GitHub Actions |
| regcred | dockerconfigjson | .dockerconfigjson | kubectl create |
| todo-tls | tls | tls.crt, tls.key | cert-manager |

### 10. HorizontalPodAutoscaler

**Entity Definition**:

```yaml
HorizontalPodAutoscaler:
  name: string
  namespace: string
  spec:
    scaleTargetRef:
      apiVersion: string          # "apps/v1"
      kind: string                # "Deployment"
      name: string
    minReplicas: integer          # 2
    maxReplicas: integer          # 10
    metrics:
      - type: enum                # Resource | Pods | Object
        resource:
          name: string            # "cpu" | "memory"
          target:
            type: string          # "Utilization"
            averageUtilization: integer  # 80
```

**HPA Configuration**:

| Deployment | Min | Max | CPU Target | Memory Target |
|------------|-----|-----|------------|---------------|
| todo-backend | 2 | 10 | 80% | 80% |
| todo-frontend | 2 | 10 | 80% | 80% |
| recurring-task-service | 1 | 5 | 80% | - |
| notification-service | 1 | 5 | 80% | - |

### 11. ServiceMonitor (Prometheus)

**Entity Definition**:

```yaml
ServiceMonitor:
  name: string
  namespace: string
  spec:
    selector:
      matchLabels: map[string]string
    endpoints:
      - port: string              # Named port
        path: string              # "/metrics"
        interval: string          # "30s"
    namespaceSelector:
      matchNames: list[string]
```

---

## CI/CD Pipeline Data Model

### GitHub Actions Workflow

**Entity Definition**:

```yaml
Workflow:
  name: string
  on:
    push:
      branches: list[string]
    pull_request:
      branches: list[string]
    workflow_dispatch:
      inputs: map[string]Input
  env:
    REGISTRY: string
    CLOUD: string
  jobs: map[string]Job
```

### Job

**Entity Definition**:

```yaml
Job:
  name: string
  runs-on: string                 # "ubuntu-latest"
  needs: list[string]             # Dependencies
  environment: string             # "production"
  steps: list[Step]
  outputs: map[string]string
```

### Step

**Entity Definition**:

```yaml
Step:
  name: string
  uses: string                    # Action reference
  with: map[string]string         # Action inputs
  run: string                     # Shell command
  env: map[string]string          # Step environment
  if: string                      # Conditional
```

---

## Container Registry Schema

### Image Reference

**Entity Definition**:

```yaml
Image:
  registry: string                # "docker.io" | "gcr.io" | "*.azurecr.io" | "*.ocir.io"
  repository: string              # "username/todo-backend"
  tag: string                     # "v1.0.0" | "latest" | "sha-abc123"
  digest: string                  # "sha256:..."

  # Full reference: registry/repository:tag@digest
```

**Tagging Strategy**:

| Tag Pattern | Example | Use Case |
|-------------|---------|----------|
| `v{semver}` | v1.0.0 | Release versions |
| `latest` | latest | Current main branch |
| `sha-{short}` | sha-abc123 | Git commit SHA |
| `{branch}` | feature-xyz | Branch builds |

---

## State Transitions

### Deployment Lifecycle

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   PENDING   │────▶│  CREATING   │────▶│   RUNNING   │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                    ┌─────────────┐             │
                    │   FAILED    │◀────────────┤
                    └─────────────┘             │
                                               ▼
                    ┌─────────────┐     ┌─────────────┐
                    │  UPDATING   │◀────│   SCALED    │
                    └──────┬──────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   RUNNING   │
                    └─────────────┘
```

### Certificate Lifecycle

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  REQUESTED  │────▶│  PENDING    │────▶│   ISSUED    │
└─────────────┘     └─────────────┘     └──────┬──────┘
                           │                   │
                           ▼                   │ (30 days before expiry)
                    ┌─────────────┐            │
                    │   FAILED    │            ▼
                    └─────────────┘     ┌─────────────┐
                                       │  RENEWING   │
                                       └──────┬──────┘
                                              │
                                              ▼
                                       ┌─────────────┐
                                       │   RENEWED   │
                                       └─────────────┘
```

### CI/CD Pipeline States

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  QUEUED     │────▶│  RUNNING    │────▶│  SUCCESS    │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                           ├───────────────────┐
                           ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐
                    │  FAILED     │     │  CANCELLED  │
                    └─────────────┘     └─────────────┘
```

---

## Validation Rules

### Resource Naming

| Resource | Pattern | Max Length | Example |
|----------|---------|------------|---------|
| Namespace | `^[a-z0-9]([-a-z0-9]*[a-z0-9])?$` | 63 | todo-app |
| Deployment | `^[a-z0-9]([-a-z0-9]*[a-z0-9])?$` | 253 | todo-backend |
| Service | `^[a-z0-9]([-a-z0-9]*[a-z0-9])?$` | 63 | todo-backend |
| Secret | `^[a-z0-9]([-a-z0-9]*[a-z0-9])?$` | 253 | todo-backend-secret |
| ConfigMap | `^[a-z0-9]([-a-z0-9]*[a-z0-9])?$` | 253 | todo-backend-config |

### Resource Limits

| Resource | Minimum | Default | Maximum |
|----------|---------|---------|---------|
| CPU Request | 50m | 200m | 2000m |
| CPU Limit | 100m | 1000m | 4000m |
| Memory Request | 64Mi | 256Mi | 2Gi |
| Memory Limit | 128Mi | 512Mi | 4Gi |
| Replicas | 1 | 2 | 20 |

### Port Ranges

| Port Type | Range | Reserved |
|-----------|-------|----------|
| Service Port | 1-65535 | 443, 80 for ingress |
| Container Port | 1024-65535 | Avoid well-known ports |
| NodePort | 30000-32767 | Cluster-defined |

---

## Data Flow

### Deployment Flow

```
GitHub Push
    │
    ▼
┌─────────────────┐
│ GitHub Actions  │
│   Workflow      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Build & Test    │────▶│ Container       │
│ (pytest, npm)   │     │ Registry        │
└─────────────────┘     └────────┬────────┘
                                 │
                                 ▼
┌─────────────────┐     ┌─────────────────┐
│ Kubernetes      │◀────│ Helm Deploy     │
│ Cluster         │     │ (upgrade)       │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│ Rolling Update  │
│ (Deployment)    │
└─────────────────┘
```

### Request Flow

```
User Browser
    │
    ▼ (HTTPS)
┌─────────────────┐
│ Cloud Load      │
│ Balancer        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ NGINX Ingress   │────▶│ cert-manager    │
│ Controller      │     │ (TLS)           │
└────────┬────────┘     └─────────────────┘
         │
         ├──── /api/* ──────┐
         │                  ▼
         │          ┌─────────────────┐
         │          │ Backend Service │
         │          └────────┬────────┘
         │                   │
         │                   ▼
         │          ┌─────────────────┐
         │          │ Backend Pods    │
         │          └─────────────────┘
         │
         └──── /* ──────────┐
                            ▼
                    ┌─────────────────┐
                    │ Frontend Service│
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Frontend Pods   │
                    └─────────────────┘
```

---

**Data Model Status**: ✅ Complete
