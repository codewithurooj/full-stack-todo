# Research: Cloud Kubernetes Deployment

**Feature**: 013-cloud-k8s-deployment
**Date**: 2026-01-18
**Status**: Complete

This document captures research findings and decisions for cloud Kubernetes deployment of the full-stack todo application.

---

## 1. Cloud Provider Selection

### Decision: Oracle Cloud OKE (Recommended Primary) with Azure AKS (Alternative)

### Analysis

| Provider | Free Tier | K8s Version | Node Resources | Container Registry | Strengths |
|----------|-----------|-------------|----------------|-------------------|-----------|
| **Oracle OKE** | Always Free: 4 OCPUs, 24GB RAM | 1.28+ | Up to 4 A1 instances | OCIR included | Best free tier, no credit expiry |
| **Azure AKS** | $200 credit (30 days) | 1.28+ | B2s VMs | ACR ($5/mo basic) | Best enterprise integration |
| **Google GKE** | $300 credit (90 days) | 1.29+ | e2-small VMs | GCR/Artifact Registry | Best K8s-native features |

### Rationale

1. **Oracle OKE** is recommended as primary because:
   - **Always Free tier** with no time limit (4 ARM OCPUs, 24GB RAM)
   - Sufficient resources for production workload (2 replicas each service)
   - OCIR container registry included at no cost
   - Supports cert-manager and NGINX Ingress
   - ARM-based (A1) instances require multi-arch Docker builds

2. **Azure AKS** is recommended alternative because:
   - Best developer experience with Azure CLI
   - ACR integrates seamlessly with AKS (no pull secrets needed with managed identity)
   - $200 credit sufficient for initial deployment and testing
   - Extensive documentation and community support

3. **Google GKE** is viable but:
   - Autopilot mode has limitations for custom configurations
   - Standard mode requires more manual management
   - 90-day credit window may expire during development

### Multi-Architecture Images

For Oracle OKE ARM support, Docker images must be built for both architectures:

```bash
# Build multi-arch images
docker buildx create --name multiarch --use
docker buildx build --platform linux/amd64,linux/arm64 \
  -t registry/todo-backend:latest --push ./backend
```

---

## 2. TLS Certificate Management

### Decision: cert-manager with Let's Encrypt (HTTP-01 challenge)

### Analysis

| Approach | Automation | Cost | Complexity | Wild Card Support |
|----------|------------|------|------------|-------------------|
| **cert-manager + LE** | Full | Free | Low | DNS-01 only |
| Cloud provider (ACM/GCP) | Full | Free | Very Low | Yes |
| Manual certificates | None | Varies | High | N/A |

### Rationale

1. **cert-manager with Let's Encrypt** chosen because:
   - Works across all three cloud providers (vendor-agnostic)
   - Free certificates with automatic renewal
   - HTTP-01 challenge works with NGINX Ingress
   - Well-documented integration patterns
   - Already specified in constitution (Section XI)

2. **HTTP-01 vs DNS-01 Challenge**:
   - HTTP-01 is simpler (no DNS API access needed)
   - Works with single-domain certificates (sufficient for this project)
   - DNS-01 required only for wildcards (out of scope)

### Configuration Pattern

```yaml
# ClusterIssuer for production
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

### Certificate Renewal Behavior

- cert-manager checks certificates daily
- Renewal triggered at 30 days before expiry (configurable)
- Let's Encrypt certificates valid for 90 days
- Effective renewal window: 60 days of validity guaranteed

---

## 3. CI/CD Pipeline Architecture

### Decision: GitHub Actions with multi-job workflow

### Analysis

| CI/CD Tool | Integration | Kubernetes Support | Cost | Complexity |
|------------|-------------|-------------------|------|------------|
| **GitHub Actions** | Native to repo | kubectl, Helm | Free (2000 min/mo) | Low |
| ArgoCD/Flux (GitOps) | Separate install | Native | Free | Medium |
| Jenkins | Self-hosted | Plugin-based | Free | High |

### Rationale

1. **GitHub Actions** chosen because:
   - Constitution mandates GitHub Actions (Section XI)
   - Native integration with repository
   - Free tier sufficient (2000 minutes/month)
   - Direct access to Helm for deployment
   - Built-in secrets management

2. **Pipeline Structure**:
   - **Job 1: Build & Test** - Run tests, build images
   - **Job 2: Push Images** - Authenticate and push to registry
   - **Job 3: Deploy** - Helm upgrade to cluster

3. **GitOps (ArgoCD/Flux) NOT chosen** because:
   - Constitution specifies GitHub Actions
   - Adds operational complexity
   - Overkill for single-environment deployment

### Workflow Design

```yaml
name: Deploy to Cloud Kubernetes

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deployment environment'
        required: true
        default: 'production'

jobs:
  build-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run backend tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest --tb=short
      - name: Run frontend tests
        run: |
          cd frontend
          npm ci
          npm test -- --passWithNoTests
      - name: Build Docker images
        run: |
          docker build -t ${{ env.REGISTRY }}/todo-backend:${{ github.sha }} ./backend
          docker build -t ${{ env.REGISTRY }}/todo-frontend:${{ github.sha }} ./frontend

  push-images:
    needs: build-test
    runs-on: ubuntu-latest
    steps:
      - name: Login to registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ secrets.REGISTRY_USERNAME }}
          password: ${{ secrets.REGISTRY_PASSWORD }}
      - name: Push images
        run: |
          docker push ${{ env.REGISTRY }}/todo-backend:${{ github.sha }}
          docker push ${{ env.REGISTRY }}/todo-frontend:${{ github.sha }}
          docker tag ... :latest && docker push ... :latest

  deploy:
    needs: push-images
    runs-on: ubuntu-latest
    steps:
      - name: Configure kubectl
        uses: azure/k8s-set-context@v3  # or appropriate cloud action
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG }}
      - name: Deploy with Helm
        run: |
          helm upgrade --install todo-backend ./charts/backend \
            --set image.tag=${{ github.sha }} \
            -f charts/backend/values-${{ env.CLOUD }}.yaml
          helm upgrade --install todo-frontend ./charts/frontend \
            --set image.tag=${{ github.sha }} \
            -f charts/frontend/values-${{ env.CLOUD }}.yaml
      - name: Verify rollout
        run: |
          kubectl rollout status deployment/todo-backend --timeout=300s
          kubectl rollout status deployment/todo-frontend --timeout=300s
```

---

## 4. Container Registry Strategy

### Decision: Docker Hub for portability, with cloud-native as secondary

### Analysis

| Registry | Multi-Cloud | Free Tier | Pull Rate Limits | Auth Complexity |
|----------|-------------|-----------|------------------|-----------------|
| **Docker Hub** | Yes | 1 private repo | 100 pulls/6hr (anon) | Low |
| Azure ACR | No (Azure only) | No free tier | None | Medium |
| Google GCR | No (GCP only) | Some free | None | Medium |
| Oracle OCIR | No (OCI only) | Yes | None | Medium |

### Rationale

1. **Primary: Docker Hub** chosen because:
   - Works with all three cloud providers
   - Simplifies multi-cloud support
   - Free tier includes 1 private repository
   - Familiar authentication model
   - Sufficient for development/staging

2. **Alternative: Cloud-native registries** for:
   - Production deployments on single cloud
   - Better latency (same region as cluster)
   - No rate limits
   - Integrated auth (e.g., ACR + AKS managed identity)

### Pull Secret Configuration

```yaml
# Kubernetes secret for Docker Hub
kubectl create secret docker-registry regcred \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=<username> \
  --docker-password=<password> \
  --docker-email=<email>

# Reference in Helm values
imagePullSecrets:
  - name: regcred
```

---

## 5. Ingress Controller Selection

### Decision: NGINX Ingress Controller (community version)

### Analysis

| Ingress Controller | TLS Termination | cert-manager | Cloud Support | Community |
|--------------------|-----------------|--------------|---------------|-----------|
| **NGINX (community)** | Yes | Excellent | All clouds | Large |
| NGINX (commercial) | Yes | Yes | All clouds | Enterprise |
| Traefik | Yes | Good | All clouds | Medium |
| Cloud-native (ALB/GKE) | Yes | Varies | Single cloud | N/A |

### Rationale

1. **NGINX Ingress Controller** chosen because:
   - Best cert-manager integration
   - Works consistently across all cloud providers
   - Extensive documentation
   - Constitution already specifies NGINX (Section XI)
   - Supports path-based routing needed for frontend/backend split

2. **Configuration Approach**:
   - Single Ingress resource with path-based routing
   - `/api/*` routes to backend service
   - `/*` routes to frontend service
   - TLS termination at ingress level

### Installation Commands

```bash
# Azure AKS
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Google GKE
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Oracle OKE
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
# May require LoadBalancer service annotation for OCI
```

---

## 6. Monitoring Stack

### Decision: kube-prometheus-stack (Helm chart)

### Analysis

| Monitoring Solution | Components | Deployment | Maintenance | Cost |
|--------------------|------------|------------|-------------|------|
| **kube-prometheus-stack** | Prometheus + Grafana + Alertmanager | Helm | Self-managed | Free |
| Cloud-native (Azure Monitor, etc.) | Varies | Managed | Minimal | Pay-per-use |
| Datadog/New Relic | Full observability | SaaS | None | $$$ |

### Rationale

1. **kube-prometheus-stack** chosen because:
   - Constitution specifies Prometheus + Grafana (Section XI)
   - Existing alerts.yaml can be imported
   - Existing Grafana dashboards ready
   - Free and self-contained
   - Works across all cloud providers

2. **Key Components**:
   - Prometheus server for metrics collection
   - Grafana for visualization
   - Alertmanager for alert routing
   - ServiceMonitors for automatic scraping

### Deployment

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install kube-prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set grafana.adminPassword=admin \
  --set prometheus.prometheusSpec.retention=7d
```

---

## 7. DNS and Domain Strategy

### Decision: Use free subdomain or user's existing domain

### Options

1. **Free Subdomain Services** (for demo/development):
   - nip.io (IP-based: `app.192.168.1.1.nip.io`)
   - sslip.io (similar to nip.io)
   - DuckDNS (free subdomain: `yourapp.duckdns.org`)

2. **User's Domain** (for production):
   - Requires DNS A record pointing to LoadBalancer IP
   - 24-48 hours for propagation

### DNS Configuration Steps

```bash
# 1. Get LoadBalancer external IP
kubectl get svc -n ingress-nginx ingress-nginx-controller

# 2. Configure DNS A record
# todo.yourdomain.com → <EXTERNAL-IP>

# 3. Or use nip.io for testing
# todo.<EXTERNAL-IP>.nip.io
```

---

## 8. Secrets Management

### Decision: Kubernetes Secrets with external injection via CI/CD

### Analysis

| Approach | Security | Rotation | Complexity | Cloud Support |
|----------|----------|----------|------------|---------------|
| **K8s Secrets + CI/CD** | Good | Manual | Low | All |
| External Secrets Operator | Better | Automatic | Medium | All |
| Cloud provider (Key Vault) | Best | Automatic | Medium | Single |
| Sealed Secrets | Good | Manual | Medium | All |

### Rationale

1. **Kubernetes Secrets + CI/CD injection** chosen because:
   - Simplest to implement
   - Works across all providers
   - GitHub Actions secrets for CI/CD
   - Helm values for deployment-time injection
   - Sufficient security for this project scope

2. **Secret Types**:
   - `DATABASE_URL` - Neon PostgreSQL connection
   - `BETTER_AUTH_SECRET` - JWT signing key
   - `OPENAI_API_KEY` - OpenAI API access
   - Registry credentials - Container pull access

### Implementation Pattern

```yaml
# In GitHub Actions
- name: Create secrets
  run: |
    kubectl create secret generic app-secrets \
      --from-literal=DATABASE_URL=${{ secrets.DATABASE_URL }} \
      --from-literal=BETTER_AUTH_SECRET=${{ secrets.BETTER_AUTH_SECRET }} \
      --dry-run=client -o yaml | kubectl apply -f -
```

---

## Summary of Decisions

| Component | Decision | Rationale |
|-----------|----------|-----------|
| Cloud Provider | Oracle OKE (primary), Azure AKS (alt) | Always-free tier, sufficient resources |
| TLS | cert-manager + Let's Encrypt | Free, automatic, vendor-agnostic |
| CI/CD | GitHub Actions | Constitution requirement, native integration |
| Registry | Docker Hub (multi-cloud), cloud-native (single) | Portability vs optimization |
| Ingress | NGINX Ingress Controller | Best cert-manager support |
| Monitoring | kube-prometheus-stack | Existing alerts/dashboards, free |
| DNS | User domain or nip.io | Flexibility for different use cases |
| Secrets | K8s Secrets + CI/CD | Simple, sufficient security |

---

## Alternatives Considered and Rejected

| Alternative | Reason for Rejection |
|-------------|---------------------|
| ArgoCD/Flux GitOps | Constitution specifies GitHub Actions |
| Cloud-native TLS (ACM, GCP) | Vendor lock-in, cert-manager more portable |
| AWS EKS | Not in constitution's provider list |
| Traefik Ingress | Less cert-manager documentation |
| Cloud Monitoring (Azure Monitor) | Existing Prometheus setup preferred |
| HashiCorp Vault | Over-engineered for project scope |

---

## Open Questions Resolved

1. **Q: Multi-arch builds for Oracle ARM?**
   - A: Use `docker buildx` for linux/amd64,linux/arm64

2. **Q: How to handle rate limits on Docker Hub?**
   - A: Authenticated pulls (200/6hr) sufficient; use cloud registry for production

3. **Q: HTTP-01 vs DNS-01 for cert-manager?**
   - A: HTTP-01 for simplicity; DNS-01 only needed for wildcards (out of scope)

4. **Q: How to verify TLS before DNS propagation?**
   - A: Use staging issuer first; test with nip.io

5. **Q: Shared or separate Ingress per service?**
   - A: Single Ingress with path-based routing (simpler certificate management)

---

**Research Status**: ✅ Complete - All NEEDS CLARIFICATION items resolved
