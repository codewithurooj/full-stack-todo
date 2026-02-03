# Quickstart: Cloud Kubernetes Deployment

**Feature**: 013-cloud-k8s-deployment
**Date**: 2026-01-18
**Status**: Guide

This guide provides step-by-step instructions for deploying the full-stack todo application to cloud Kubernetes.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (5 Minutes)](#quick-start-5-minutes)
3. [Oracle Cloud OKE (Recommended)](#oracle-cloud-oke-recommended)
4. [Azure AKS](#azure-aks)
5. [Google Cloud GKE](#google-cloud-gke)
6. [Common Steps (All Providers)](#common-steps-all-providers)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

```bash
# Kubernetes CLI
kubectl version --client  # v1.28+

# Helm package manager
helm version  # v3.13+

# Docker for building images
docker version  # 24.0+

# Cloud provider CLI (choose one)
az version            # Azure CLI
gcloud version        # Google Cloud SDK
oci --version         # Oracle Cloud CLI
```

### Required Accounts

- GitHub account (for CI/CD)
- Container registry account (Docker Hub or cloud-native)
- Domain name (or use nip.io for testing)
- Cloud provider account (Azure/GCP/Oracle)

### Required Secrets (collect before starting)

| Secret | Description | Where to Get |
|--------|-------------|--------------|
| `DATABASE_URL` | Neon PostgreSQL connection | [Neon Console](https://console.neon.tech) |
| `BETTER_AUTH_SECRET` | JWT signing key (32+ chars) | Generate: `openssl rand -base64 32` |
| `OPENAI_API_KEY` | OpenAI API key | [OpenAI Platform](https://platform.openai.com) |
| `OPENAI_DOMAIN_KEY` | Domain allowlist key | OpenAI Settings |

---

## Quick Start (5 Minutes)

For the fastest deployment using Docker Hub and your existing cluster:

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/full-stack-todo.git
cd full-stack-todo

# 2. Build and push images to Docker Hub
export DOCKERHUB_USER=yourusername
docker login

docker build -t $DOCKERHUB_USER/todo-backend:latest ./backend
docker build -t $DOCKERHUB_USER/todo-frontend:latest ./frontend
docker push $DOCKERHUB_USER/todo-backend:latest
docker push $DOCKERHUB_USER/todo-frontend:latest

# 3. Create namespace and secrets
kubectl create namespace todo-app

kubectl create secret generic todo-backend-secret \
  --namespace todo-app \
  --from-literal=DATABASE_URL='your-neon-database-url' \
  --from-literal=BETTER_AUTH_SECRET='your-32-char-secret' \
  --from-literal=OPENAI_API_KEY='sk-your-openai-key'

kubectl create secret docker-registry regcred \
  --namespace todo-app \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=$DOCKERHUB_USER \
  --docker-password=your-docker-token

# 4. Deploy with Helm
helm upgrade --install todo-backend ./charts/backend \
  --namespace todo-app \
  --set image.repository=$DOCKERHUB_USER/todo-backend \
  --set image.pullPolicy=Always

helm upgrade --install todo-frontend ./charts/frontend \
  --namespace todo-app \
  --set image.repository=$DOCKERHUB_USER/todo-frontend \
  --set image.pullPolicy=Always

# 5. Access the application
kubectl port-forward svc/todo-frontend 3000:3000 -n todo-app
# Open http://localhost:3000
```

---

## Oracle Cloud OKE (Recommended)

Oracle Cloud offers an **Always Free** Kubernetes cluster with generous resources.

### Step 1: Create OKE Cluster

```bash
# Login to Oracle Cloud Console
# https://cloud.oracle.com

# Navigate: Developer Services → Kubernetes Clusters (OKE)
# Click "Create Cluster" → "Quick Create"

# Configuration:
# - Name: todo-cluster
# - Kubernetes Version: 1.28.x
# - Shape: VM.Standard.A1.Flex (ARM - Always Free)
# - Number of nodes: 2
# - OCPUs per node: 2
# - Memory per node: 12 GB
```

### Step 2: Configure kubectl

```bash
# Download kubeconfig from OCI Console
# Cluster Details → Access Cluster → Local Access

# Set KUBECONFIG
export KUBECONFIG=~/.kube/oke-config

# Verify connection
kubectl get nodes
```

### Step 3: Setup Container Registry (OCIR)

```bash
# Get your tenancy namespace
oci os ns get

# Login to OCIR
docker login <region>.ocir.io
# Username: <tenancy>/<username>
# Password: Auth token from OCI Console (Identity → Users → Auth Tokens)

# Tag and push images
export REGION=us-ashburn-1  # or your region
export TENANCY=your-tenancy
export OCIR_REPO=$REGION.ocir.io/$TENANCY

docker tag todo-backend:latest $OCIR_REPO/todo-backend:latest
docker tag todo-frontend:latest $OCIR_REPO/todo-frontend:latest
docker push $OCIR_REPO/todo-backend:latest
docker push $OCIR_REPO/todo-frontend:latest
```

### Step 4: Create Registry Secret

```bash
kubectl create secret docker-registry ocir-secret \
  --namespace todo-app \
  --docker-server=$REGION.ocir.io \
  --docker-username="$TENANCY/your-username" \
  --docker-password="your-auth-token" \
  --docker-email=your-email@example.com
```

### Step 5: Deploy with OKE-specific values

```bash
# Create values-oke.yaml
cat > charts/backend/values-oke.yaml << EOF
image:
  repository: $OCIR_REPO/todo-backend
  pullPolicy: Always
  tag: "latest"

imagePullSecrets:
  - name: ocir-secret

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
EOF

# Deploy
helm upgrade --install todo-backend ./charts/backend \
  --namespace todo-app \
  -f charts/backend/values-oke.yaml
```

---

## Azure AKS

### Step 1: Create AKS Cluster

```bash
# Login to Azure
az login

# Create resource group
az group create --name todo-rg --location eastus

# Create AKS cluster
az aks create \
  --resource-group todo-rg \
  --name todo-cluster \
  --node-count 2 \
  --node-vm-size Standard_B2s \
  --enable-managed-identity \
  --generate-ssh-keys

# Get credentials
az aks get-credentials --resource-group todo-rg --name todo-cluster
```

### Step 2: Create Azure Container Registry

```bash
# Create ACR
az acr create --resource-group todo-rg --name todoregistry --sku Basic

# Attach ACR to AKS (enables seamless image pulls)
az aks update \
  --resource-group todo-rg \
  --name todo-cluster \
  --attach-acr todoregistry

# Login to ACR
az acr login --name todoregistry

# Push images
docker tag todo-backend:latest todoregistry.azurecr.io/todo-backend:latest
docker push todoregistry.azurecr.io/todo-backend:latest
```

### Step 3: Deploy with AKS-specific values

```bash
# Create values-aks.yaml
cat > charts/backend/values-aks.yaml << EOF
image:
  repository: todoregistry.azurecr.io/todo-backend
  pullPolicy: Always
  tag: "latest"

# No imagePullSecrets needed when using attached ACR

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
EOF

helm upgrade --install todo-backend ./charts/backend \
  --namespace todo-app \
  -f charts/backend/values-aks.yaml
```

---

## Google Cloud GKE

### Step 1: Create GKE Cluster

```bash
# Login to Google Cloud
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Create GKE cluster
gcloud container clusters create todo-cluster \
  --region us-central1 \
  --num-nodes 2 \
  --machine-type e2-small \
  --enable-autoscaling --min-nodes 1 --max-nodes 5

# Get credentials
gcloud container clusters get-credentials todo-cluster --region us-central1
```

### Step 2: Configure Container Registry

```bash
# Enable Artifact Registry API
gcloud services enable artifactregistry.googleapis.com

# Create repository
gcloud artifacts repositories create todo-repo \
  --repository-format=docker \
  --location=us-central1

# Configure Docker auth
gcloud auth configure-docker us-central1-docker.pkg.dev

# Push images
export GCR_REPO=us-central1-docker.pkg.dev/YOUR_PROJECT_ID/todo-repo
docker tag todo-backend:latest $GCR_REPO/todo-backend:latest
docker push $GCR_REPO/todo-backend:latest
```

### Step 3: Deploy with GKE-specific values

```bash
# Create values-gke.yaml
cat > charts/backend/values-gke.yaml << EOF
image:
  repository: $GCR_REPO/todo-backend
  pullPolicy: Always
  tag: "latest"

# GKE nodes have implicit access to GCR/Artifact Registry

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
EOF

helm upgrade --install todo-backend ./charts/backend \
  --namespace todo-app \
  -f charts/backend/values-gke.yaml
```

---

## Common Steps (All Providers)

### Install NGINX Ingress Controller

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Wait for LoadBalancer IP
kubectl get svc -n ingress-nginx ingress-nginx-controller --watch
# Note the EXTERNAL-IP when it appears
```

### Install cert-manager

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Wait for pods to be ready
kubectl wait --for=condition=Ready pods -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=120s

# Create ClusterIssuer for Let's Encrypt
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod-key
    solvers:
      - http01:
          ingress:
            class: nginx
EOF
```

### Configure DNS

```bash
# Get LoadBalancer IP
INGRESS_IP=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "Add DNS A record: todo.yourdomain.com → $INGRESS_IP"

# OR use nip.io for testing (no DNS required)
echo "Access at: http://todo.$INGRESS_IP.nip.io"
```

### Create Application Secrets

```bash
kubectl create namespace todo-app

kubectl create secret generic todo-backend-secret \
  --namespace todo-app \
  --from-literal=DATABASE_URL='postgresql://user:pass@host.neon.tech/dbname?sslmode=require' \
  --from-literal=BETTER_AUTH_SECRET='your-32-character-secret-key-here' \
  --from-literal=OPENAI_API_KEY='sk-your-openai-api-key'

kubectl create secret generic todo-frontend-secret \
  --namespace todo-app \
  --from-literal=BETTER_AUTH_SECRET='your-32-character-secret-key-here' \
  --from-literal=NEXT_PUBLIC_OPENAI_DOMAIN_KEY='your-domain-key'
```

### Deploy Application

```bash
# Deploy backend
helm upgrade --install todo-backend ./charts/backend \
  --namespace todo-app \
  -f charts/backend/values-${CLOUD_PROVIDER}.yaml

# Deploy frontend
helm upgrade --install todo-frontend ./charts/frontend \
  --namespace todo-app \
  -f charts/frontend/values-${CLOUD_PROVIDER}.yaml

# Deploy microservices (optional)
helm upgrade --install notification-service ./charts/notification-service \
  --namespace todo-app

helm upgrade --install recurring-task-service ./charts/recurring-task-service \
  --namespace todo-app
```

### Install Monitoring Stack

```bash
# Add Prometheus Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set grafana.adminPassword=admin \
  --set prometheus.prometheusSpec.retention=7d

# Access Grafana
kubectl port-forward svc/prometheus-grafana 3001:80 -n monitoring
# Open http://localhost:3001 (admin/admin)
```

---

## Verification

### Check Deployment Status

```bash
# All pods running?
kubectl get pods -n todo-app

# Services created?
kubectl get svc -n todo-app

# Ingress with IP?
kubectl get ingress -n todo-app

# Certificate issued?
kubectl get certificates -n todo-app
kubectl describe certificate todo-app-tls -n todo-app
```

### Test Endpoints

```bash
# Get ingress IP/domain
DOMAIN=todo.yourdomain.com  # or use $INGRESS_IP.nip.io

# Test health endpoint
curl -s https://$DOMAIN/api/health | jq .

# Test frontend
curl -s https://$DOMAIN/ | head -20

# Test with browser
echo "Open https://$DOMAIN in your browser"
```

### Verify TLS Certificate

```bash
# Check certificate details
echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -dates

# Expected output:
# notBefore=...
# notAfter=... (90 days from now)
```

---

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n todo-app

# Check logs
kubectl logs <pod-name> -n todo-app

# Common issues:
# - ImagePullBackOff: Check registry credentials
# - CrashLoopBackOff: Check application logs
# - Pending: Check resource quotas/node capacity
```

### Certificate Not Issuing

```bash
# Check cert-manager logs
kubectl logs -n cert-manager -l app=cert-manager

# Check certificate status
kubectl describe certificate todo-app-tls -n todo-app

# Check challenges
kubectl get challenges -n todo-app
kubectl describe challenge <challenge-name> -n todo-app

# Common issues:
# - HTTP-01 challenge failing: Ingress not routing correctly
# - Rate limited: Wait or use staging issuer
```

### Ingress Not Working

```bash
# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx

# Verify ingress configuration
kubectl describe ingress todo-app-ingress -n todo-app

# Test directly via port-forward
kubectl port-forward svc/todo-backend 8000:8000 -n todo-app
curl http://localhost:8000/health
```

### Database Connection Issues

```bash
# Verify secret exists
kubectl get secret todo-backend-secret -n todo-app -o yaml

# Check backend logs for connection errors
kubectl logs deployment/todo-backend -n todo-app | grep -i database

# Test connection from pod
kubectl exec -it deployment/todo-backend -n todo-app -- python -c "
from app.db import engine
print(engine.url)
"
```

---

## Next Steps

After successful deployment:

1. **Configure GitHub Actions** - Set up CI/CD for automatic deployments
2. **Configure Monitoring Alerts** - Import existing alerts.yaml
3. **Set Up Backup** - Configure database backup schedule
4. **Document Runbooks** - Create operational procedures

---

## Quick Reference

| Task | Command |
|------|---------|
| View all pods | `kubectl get pods -n todo-app` |
| View logs | `kubectl logs deployment/todo-backend -n todo-app` |
| Scale deployment | `kubectl scale deployment/todo-backend --replicas=3 -n todo-app` |
| Restart deployment | `kubectl rollout restart deployment/todo-backend -n todo-app` |
| Rollback | `helm rollback todo-backend -n todo-app` |
| Delete deployment | `helm uninstall todo-backend -n todo-app` |
| Port forward | `kubectl port-forward svc/todo-frontend 3000:3000 -n todo-app` |
| Get external IP | `kubectl get svc -n ingress-nginx` |
