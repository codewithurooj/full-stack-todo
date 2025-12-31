# Helm Charts Deployment Guide

Complete guide for deploying the Full-Stack Todo application to Kubernetes using Helm charts.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Building Docker Images](#building-docker-images)
4. [Deploying to Minikube](#deploying-to-minikube)
5. [Configuring Environment Variables](#configuring-environment-variables)
6. [Accessing via Ingress](#accessing-via-ingress)
7. [Upgrading and Rollback](#upgrading-and-rollback)
8. [Monitoring Resources](#monitoring-resources)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

- **Minikube** v1.32+ (Kubernetes local environment)
- **kubectl** (Kubernetes CLI)
- **Helm** 3.0+ (Package manager)
- **Docker** (For building images)

### Installation

```powershell
# Windows (PowerShell as Administrator)
# Install Chocolatey first if needed
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install tools
choco install minikube kubernetes-cli kubernetes-helm docker-desktop -y
```

### Verify Installation

```bash
minikube version
kubectl version --client
helm version
docker --version
```

---

## Quick Start

### 1. Start Minikube

```bash
# Start Minikube with 2 CPUs and 3GB RAM on D: drive
minikube start --cpus=2 --memory=3072 --disk-size=20g --driver=docker
```

### 2. Build and Load Docker Images

```bash
# Build frontend
cd frontend
docker build -t todo-frontend:latest .
minikube image load todo-frontend:latest

# Build backend
cd ../backend
docker build -t todo-backend:latest .
minikube image load todo-backend:latest
```

### 3. Deploy with Helm

```bash
# Install backend
helm install todo-api ./charts/backend

# Install frontend
helm install todo-app ./charts/frontend

# Verify deployment
kubectl get pods
```

---

## Building Docker Images

### Frontend (Next.js)

```bash
cd frontend
docker build -t todo-frontend:latest .
minikube image load todo-frontend:latest

# Verify image
minikube image ls | grep todo-frontend
```

### Backend (FastAPI)

```bash
cd backend
docker build -t todo-backend:latest .
minikube image load todo-backend:latest

# Verify image
minikube image ls | grep todo-backend
```

### Tagging for Versions

```bash
# Tag with version
docker tag todo-frontend:latest todo-frontend:v1.0.0
docker tag todo-backend:latest todo-backend:v1.0.0

# Load versioned images
minikube image load todo-frontend:v1.0.0
minikube image load todo-backend:v1.0.0
```

---

## Deploying to Minikube

### Deploy Backend First

```bash
# Install backend with default values
helm install todo-api ./charts/backend

# Check deployment
kubectl get pods -l app.kubernetes.io/name=todo-backend
kubectl logs -f -l app.kubernetes.io/name=todo-backend

# Verify health
kubectl port-forward svc/todo-api-todo-backend 8000:8000
curl http://localhost:8000/health
```

### Deploy Frontend

```bash
# Install frontend
helm install todo-app ./charts/frontend

# Check deployment
kubectl get pods -l app.kubernetes.io/name=todo-frontend
kubectl logs -f -l app.kubernetes.io/name=todo-frontend

# Access frontend
kubectl port-forward svc/todo-app-todo-frontend 3000:3000
# Visit: http://localhost:3000
```

### Verify All Pods Running

```bash
# Should show 4 pods (2 frontend + 2 backend)
kubectl get pods

# Expected output:
# NAME                                    READY   STATUS    RESTARTS   AGE
# todo-app-todo-frontend-xxxxxxxxx-xxxxx  1/1     Running   0          2m
# todo-app-todo-frontend-xxxxxxxxx-xxxxx  1/1     Running   0          2m
# todo-api-todo-backend-xxxxxxxxx-xxxxx   1/1     Running   0          3m
# todo-api-todo-backend-xxxxxxxxx-xxxxx   1/1     Running   0          3m
```

---

## Configuring Environment Variables

### Using Custom Values

Create `custom-values.yaml`:

```yaml
# Frontend custom values
config:
  NEXT_PUBLIC_API_URL: "http://todo-api-todo-backend:8000"
  NODE_ENV: "production"

secrets:
  BETTER_AUTH_SECRET: "your-actual-secret-key-min-32-characters"
  NEXT_PUBLIC_OPENAI_DOMAIN_KEY: "your-openai-domain-key"
```

Deploy with custom values:

```bash
helm install todo-app ./charts/frontend -f custom-values.yaml
```

### Backend Configuration

Create `backend-values.yaml`:

```yaml
secrets:
  DATABASE_URL: "postgresql://user:pass@neon.host/dbname?sslmode=require"
  BETTER_AUTH_SECRET: "your-actual-secret-key-min-32-characters"
  OPENAI_API_KEY: "sk-your-actual-openai-api-key"

config:
  ENVIRONMENT: "production"
  LOG_LEVEL: "info"
```

Deploy:

```bash
helm install todo-api ./charts/backend -f backend-values.yaml
```

### Using --set Flags

```bash
# Set individual values
helm install todo-api ./charts/backend \
  --set replicaCount=3 \
  --set image.tag=v1.1.0 \
  --set resources.limits.memory=1Gi
```

### Upgrade with New Values

```bash
helm upgrade todo-app ./charts/frontend -f new-values.yaml
helm upgrade todo-api ./charts/backend -f new-backend-values.yaml
```

---

## Accessing via Ingress

### Enable Ingress Controller

```bash
# Enable NGINX ingress addon in Minikube
minikube addons enable ingress

# Verify ingress controller is running
kubectl get pods -n ingress-nginx
```

### Configure Ingress

```bash
# Deploy frontend with ingress enabled
helm upgrade todo-app ./charts/frontend --set ingress.enabled=true

# Or use values file
cat > ingress-values.yaml <<EOF
ingress:
  enabled: true
  className: "nginx"
  hosts:
    - host: todo.local
      paths:
        - path: /
          pathType: Prefix
  tls: []
EOF

helm upgrade todo-app ./charts/frontend -f ingress-values.yaml
```

### Configure /etc/hosts

```powershell
# Windows (Run as Administrator)
# Edit C:\Windows\System32\drivers\etc\hosts
Add-Content -Path C:\Windows\System32\drivers\etc\hosts -Value "127.0.0.1 todo.local"
```

```bash
# Linux/Mac
echo "127.0.0.1 todo.local" | sudo tee -a /etc/hosts
```

### Start Minikube Tunnel

```bash
# Run in separate terminal (keep running)
minikube tunnel
```

### Access Application

```bash
# Frontend
http://todo.local/

# Backend API (routed through frontend ingress)
http://todo.local/api/health
```

### Verify Ingress

```bash
kubectl get ingress
kubectl describe ingress todo-app-todo-frontend
```

---

## Upgrading and Rollback

### Upgrade to New Version

```bash
# Build new version
docker build -t todo-frontend:v1.1.0 ./frontend
minikube image load todo-frontend:v1.1.0

# Upgrade with new tag
helm upgrade todo-app ./charts/frontend --set image.tag=v1.1.0

# Monitor rolling update
kubectl rollout status deployment/todo-app-todo-frontend
kubectl get pods -w
```

### View Release History

```bash
helm history todo-app

# Output:
# REVISION  STATUS      CHART           DESCRIPTION
# 1         superseded  frontend-1.0.0  Install complete
# 2         deployed    frontend-1.0.0  Upgrade complete
```

### Rollback to Previous Version

```bash
# Rollback to previous revision
helm rollback todo-app

# Rollback to specific revision
helm rollback todo-app 1

# Verify rollback
helm history todo-app
kubectl get pods
```

### Rolling Update Strategy

The charts use zero-downtime rolling updates:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1        # Create 1 new pod before terminating old one
    maxUnavailable: 0  # Ensure at least all pods are always available
```

This ensures:
- New pods start before old ones terminate
- No downtime during updates
- Automatic rollback if new pods fail health checks

---

## Monitoring Resources

### Enable Metrics Server

```bash
# Enable metrics server in Minikube
minikube addons enable metrics-server

# Verify metrics server
kubectl get deployment metrics-server -n kube-system
```

### View Resource Usage

```bash
# Pod resource usage
kubectl top pods

# Node resource usage
kubectl top nodes

# Detailed pod resources
kubectl describe pod <pod-name> | grep -A 5 "Limits\|Requests"
```

### Resource Configuration

Charts include resource limits and requests:

**Frontend:**
```yaml
resources:
  limits:
    cpu: 500m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

**Backend:**
```yaml
resources:
  limits:
    cpu: 1000m
    memory: 512Mi
  requests:
    cpu: 200m
    memory: 256Mi
```

### Total Resources Required

- **Frontend**: 2 pods × (100m CPU, 128Mi RAM) = 200m CPU, 256Mi RAM
- **Backend**: 2 pods × (200m CPU, 256Mi RAM) = 400m CPU, 512Mi RAM
- **Total Requests**: 600m CPU (~0.6 cores), 768Mi RAM
- **Total Limits**: 2000m CPU (2 cores), 1.5Gi RAM

This fits within Minikube's 2 CPUs and 3GB RAM allocation.

### Adjust Resources

```bash
# Increase backend memory
helm upgrade todo-api ./charts/backend \
  --set resources.limits.memory=1Gi \
  --set resources.requests.memory=512Mi
```

---

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods
kubectl describe pod <pod-name>
kubectl logs <pod-name>

# Common issues:
# - ImagePullBackOff: Image not loaded to Minikube
# - CrashLoopBackOff: Application error, check logs
# - Pending: Resource constraints or node issues
```

**Solution for ImagePullBackOff:**
```bash
# Reload image to Minikube
minikube image load todo-frontend:latest
kubectl delete pod <pod-name>  # Force recreation
```

### Ingress Not Working

```bash
# Verify ingress controller
kubectl get pods -n ingress-nginx

# Check ingress resource
kubectl get ingress
kubectl describe ingress todo-app-todo-frontend

# Verify /etc/hosts entry
cat /etc/hosts | grep todo.local

# Check minikube tunnel is running
minikube tunnel
```

### Database Connection Errors

```bash
# Check backend logs
kubectl logs -l app.kubernetes.io/name=todo-backend | grep -i database

# Verify DATABASE_URL secret
kubectl get secret todo-api-todo-backend-secret -o jsonpath='{.data.DATABASE_URL}' | base64 -d

# Test database connection from pod
kubectl exec -it <backend-pod-name> -- python -c "
from sqlmodel import create_engine
import os
engine = create_engine(os.environ['DATABASE_URL'])
print('Connection successful!')
"
```

### Health Checks Failing

```bash
# Check health endpoint
kubectl port-forward svc/todo-api-todo-backend 8000:8000
curl http://localhost:8000/health

# Adjust probe timing if needed
helm upgrade todo-api ./charts/backend \
  --set livenessProbe.initialDelaySeconds=60 \
  --set readinessProbe.initialDelaySeconds=45
```

### Out of Resources

```bash
# Check Minikube resources
minikube status
kubectl top nodes

# Increase Minikube resources
minikube stop
minikube delete
minikube start --cpus=4 --memory=4096
```

### View All Resources

```bash
# Get all resources
kubectl get all

# Specific resources
kubectl get deployments
kubectl get services
kubectl get configmaps
kubectl get secrets
kubectl get ingress
```

### Helm Debugging

```bash
# Lint chart
helm lint ./charts/frontend

# Dry run
helm install todo-app ./charts/frontend --dry-run --debug

# Get rendered manifest
helm template todo-app ./charts/frontend

# View current values
helm get values todo-app

# View full manifest
helm get manifest todo-app
```

---

## Cleanup

### Uninstall Charts

```bash
# Uninstall frontend
helm uninstall todo-app

# Uninstall backend
helm uninstall todo-api

# Verify removal
kubectl get all
helm list
```

### Stop Minikube

```bash
# Stop Minikube
minikube stop

# Delete Minikube cluster
minikube delete
```

---

## Next Steps

1. **Production Deployment**: Adapt charts for cloud Kubernetes (AKS, EKS, GKE)
2. **CI/CD Integration**: Automate image builds and Helm deployments
3. **External Secrets**: Use tools like External Secrets Operator
4. **Monitoring**: Add Prometheus and Grafana
5. **Autoscaling**: Enable HPA for dynamic scaling

---

## Reference Commands

### Essential Commands Cheat Sheet

```bash
# Minikube
minikube start --cpus=2 --memory=3072
minikube status
minikube dashboard
minikube tunnel
minikube stop

# Helm
helm install <name> <chart>
helm upgrade <name> <chart>
helm rollback <name>
helm uninstall <name>
helm list
helm history <name>

# kubectl
kubectl get pods
kubectl describe pod <name>
kubectl logs -f <pod-name>
kubectl exec -it <pod-name> -- /bin/sh
kubectl port-forward svc/<service> <local-port>:<service-port>
kubectl get all
kubectl top pods
kubectl top nodes
```

---

**Deployment Complete!** Your Todo application is now running on Kubernetes with Helm. 🎉
