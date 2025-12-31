# Minikube Setup - Quick Start Guide

**Feature Branch**: `006-minikube-setup`
**Created**: 2025-12-30
**Version**: 1.0

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [One-Command Cluster Setup](#one-command-cluster-setup)
3. [Addon Verification](#addon-verification)
4. [Testing with Sample Application](#testing-with-sample-application)
5. [Accessing Dashboard and Metrics](#accessing-dashboard-and-metrics)
6. [Troubleshooting Common Issues](#troubleshooting-common-issues)
7. [Daily Workflow Commands](#daily-workflow-commands)
8. [Cleanup and Reset Procedures](#cleanup-and-reset-procedures)

---

## Prerequisites

### System Requirements

**Minimum Requirements:**
- **CPU:** 6+ cores (4 for Minikube + 2 for host OS)
- **Memory:** 12GB+ RAM (8GB for Minikube + 4GB for host OS)
- **Disk:** 20GB+ free disk space
- **OS:** Windows 10+, macOS 10.13+, or Linux (Ubuntu 18.04+)

**Recommended for Full-Stack Todo App:**
- **CPU:** 8 cores
- **Memory:** 16GB RAM
- **Disk:** 40GB free space

### Software Installation

#### 1. Install Docker

**Windows/macOS:**
```bash
# Download and install Docker Desktop from:
# https://www.docker.com/products/docker-desktop

# Verify installation
docker --version
docker info
```

**Linux (Ubuntu/Debian):**
```bash
# Install Docker Engine
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group (avoid sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
```

#### 2. Install Minikube

**Windows (PowerShell as Administrator):**
```powershell
# Download Minikube installer
New-Item -Path 'c:\' -Name 'minikube' -ItemType Directory -Force
Invoke-WebRequest -OutFile 'c:\minikube\minikube.exe' -Uri 'https://github.com/kubernetes/minikube/releases/latest/download/minikube-windows-amd64.exe' -UseBasicParsing

# Add to PATH
$oldPath = [Environment]::GetEnvironmentVariable('Path', [EnvironmentVariableTarget]::Machine)
if ($oldPath.Split(';') -inotcontains 'C:\minikube'){
  [Environment]::SetEnvironmentVariable('Path', $('{0};C:\minikube' -f $oldPath), [EnvironmentVariableTarget]::Machine)
}

# Verify (restart terminal)
minikube version
```

**macOS:**
```bash
# Using Homebrew
brew install minikube

# Or download binary
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-darwin-amd64
sudo install minikube-darwin-amd64 /usr/local/bin/minikube

# Verify
minikube version
```

**Linux:**
```bash
# Download latest release
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64

# Install to /usr/local/bin
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Verify
minikube version
```

#### 3. Install kubectl

**Windows (PowerShell):**
```powershell
# Download kubectl
curl.exe -LO "https://dl.k8s.io/release/v1.28.0/bin/windows/amd64/kubectl.exe"

# Move to C:\minikube (or another directory in PATH)
Move-Item kubectl.exe c:\minikube\kubectl.exe

# Verify
kubectl version --client
```

**macOS:**
```bash
# Using Homebrew
brew install kubectl

# Or download binary
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/darwin/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Verify
kubectl version --client
```

**Linux:**
```bash
# Download latest stable version
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

# Install
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Verify
kubectl version --client
```

### Verification Checklist

Before proceeding, verify all prerequisites:

```bash
# Check Docker
docker --version
# Expected: Docker version 20.10.0 or higher

docker info
# Expected: Server running, no errors

# Check Minikube
minikube version
# Expected: minikube version: v1.30.0 or higher

# Check kubectl
kubectl version --client
# Expected: Client Version: v1.28.0 or higher
```

---

## One-Command Cluster Setup

### Quick Start (Recommended Configuration)

**Single command to start cluster with all addons:**

```bash
# Start Minikube cluster with recommended configuration
minikube start \
  --profile=todo-dev \
  --driver=docker \
  --cpus=4 \
  --memory=8192 \
  --disk-size=40g \
  --kubernetes-version=stable \
  --addons=ingress,metrics-server,dashboard
```

**Expected output:**
```
😄  [todo-dev] minikube v1.30.1 on Windows 10
✨  Using the docker driver based on user configuration
👍  Starting control plane node todo-dev in cluster todo-dev
🚜  Pulling base image ...
🔥  Creating docker container (CPUs=4, Memory=8192MB) ...
🐳  Preparing Kubernetes v1.28.3 on Docker 24.0.7 ...
🔗  Configuring bridge CNI (Container Networking Interface) ...
🔎  Verifying Kubernetes components...
🌟  Enabled addons: storage-provisioner, default-storageclass, ingress, metrics-server, dashboard
🏄  Done! kubectl is now configured to use "todo-dev" cluster.
```

**Time estimate:** 2-5 minutes (first run may take longer due to image downloads)

### Step-by-Step Setup (Alternative)

If you prefer step-by-step setup or encounter issues:

**1. Start basic cluster:**
```bash
minikube start \
  --profile=todo-dev \
  --driver=docker \
  --cpus=4 \
  --memory=8192 \
  --disk-size=40g
```

**2. Set as active profile:**
```bash
minikube profile todo-dev
```

**3. Enable addons individually:**
```bash
# Enable ingress controller
minikube addons enable ingress

# Enable metrics server
minikube addons enable metrics-server

# Enable dashboard
minikube addons enable dashboard
```

**4. Verify cluster is running:**
```bash
minikube status
```

**Expected output:**
```
todo-dev
type: Control Plane
host: Running
kubelet: Running
apiserver: Running
kubeconfig: Configured
```

### Verify Installation

```bash
# Check cluster status
minikube status -p todo-dev

# Check nodes
kubectl get nodes

# Expected output:
# NAME       STATUS   ROLES           AGE   VERSION
# todo-dev   Ready    control-plane   2m    v1.28.3

# Check system pods
kubectl get pods -A

# All pods should be Running or Completed
```

---

## Addon Verification

### 1. Verify Ingress Controller

**Check addon status:**
```bash
minikube addons list -p todo-dev | grep ingress
```

**Expected output:**
```
| ingress                     | todo-dev | enabled ✅   | Kubernetes                     |
```

**Check ingress-nginx pods:**
```bash
kubectl get pods -n ingress-nginx
```

**Expected output:**
```
NAME                                        READY   STATUS      RESTARTS   AGE
ingress-nginx-admission-create-xxxxx        0/1     Completed   0          2m
ingress-nginx-admission-patch-xxxxx         0/1     Completed   0          2m
ingress-nginx-controller-xxxxxxxxxx-xxxxx   1/1     Running     0          2m
```

**Wait for controller to be ready:**
```bash
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s
```

### 2. Verify Metrics Server

**Check addon status:**
```bash
minikube addons list -p todo-dev | grep metrics-server
```

**Expected output:**
```
| metrics-server              | todo-dev | enabled ✅   | Kubernetes                     |
```

**Check metrics-server pod:**
```bash
kubectl get pods -n kube-system -l k8s-app=metrics-server
```

**Expected output:**
```
NAME                              READY   STATUS    RESTARTS   AGE
metrics-server-xxxxxxxxxx-xxxxx   1/1     Running   0          2m
```

**Wait for metrics to be available (requires 1-2 minutes):**
```bash
# Wait 60 seconds for metrics collection
sleep 60

# Check node metrics
kubectl top nodes

# Expected output:
# NAME       CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
# todo-dev   250m         6%     1024Mi          12%

# Check pod metrics
kubectl top pods -A
```

### 3. Verify Dashboard

**Check addon status:**
```bash
minikube addons list -p todo-dev | grep dashboard
```

**Expected output:**
```
| dashboard                   | todo-dev | enabled ✅   | Kubernetes                     |
```

**Check dashboard pods:**
```bash
kubectl get pods -n kubernetes-dashboard
```

**Expected output:**
```
NAME                                         READY   STATUS    RESTARTS   AGE
dashboard-metrics-scraper-xxxxxxxxxx-xxxxx   1/1     Running   0          2m
kubernetes-dashboard-xxxxxxxxxx-xxxxx        1/1     Running   0          2m
```

### Comprehensive Verification Script

Run all checks at once:

```bash
echo "=== Cluster Status ==="
minikube status -p todo-dev

echo -e "\n=== Node Status ==="
kubectl get nodes

echo -e "\n=== System Pods ==="
kubectl get pods -n kube-system

echo -e "\n=== Ingress Controller ==="
kubectl get pods -n ingress-nginx

echo -e "\n=== Dashboard ==="
kubectl get pods -n kubernetes-dashboard

echo -e "\n=== Enabled Addons ==="
minikube addons list -p todo-dev | grep enabled

echo -e "\n=== Node Metrics (if available) ==="
kubectl top nodes || echo "Metrics not yet available (wait 1-2 minutes)"

echo -e "\n=== Cluster Info ==="
kubectl cluster-info
```

---

## Testing with Sample Application

### Deploy Test Application

Create a simple nginx deployment to test cluster functionality:

**1. Create deployment:**
```bash
kubectl create deployment hello-minikube --image=nginx:alpine
```

**2. Expose as service:**
```bash
kubectl expose deployment hello-minikube --type=NodePort --port=80
```

**3. Check deployment status:**
```bash
kubectl get deployments
kubectl get pods
kubectl get services
```

**Expected output:**
```
NAME             READY   UP-TO-DATE   AVAILABLE   AGE
hello-minikube   1/1     1            1           30s

NAME                              READY   STATUS    RESTARTS   AGE
hello-minikube-xxxxxxxxxx-xxxxx   1/1     Running   0          30s

NAME             TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
hello-minikube   NodePort    10.96.123.45    <none>        80:30123/TCP   20s
```

### Test Service Access

**Method 1: Using minikube service (easiest):**
```bash
# Get service URL
minikube service hello-minikube -p todo-dev --url

# Example output: http://127.0.0.1:54321
# Open in browser or curl
curl $(minikube service hello-minikube -p todo-dev --url)
```

**Method 2: Using port-forward:**
```bash
kubectl port-forward service/hello-minikube 8080:80

# In another terminal or browser:
curl http://localhost:8080
```

**Method 3: Using ingress (test ingress routing):**

Create ingress resource:

```bash
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: hello-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: hello.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: hello-minikube
            port:
              number: 80
EOF
```

Add to hosts file:

```bash
# Get cluster IP
CLUSTER_IP=$(minikube ip -p todo-dev)
echo "$CLUSTER_IP hello.local"

# Add to /etc/hosts (Linux/macOS):
echo "$CLUSTER_IP hello.local" | sudo tee -a /etc/hosts

# Windows: Add to C:\Windows\System32\drivers\etc\hosts (as Administrator):
# <CLUSTER_IP> hello.local
```

Test ingress:

```bash
curl http://hello.local
```

**Expected output:** Nginx welcome page HTML

### Cleanup Test Application

```bash
kubectl delete ingress hello-ingress
kubectl delete service hello-minikube
kubectl delete deployment hello-minikube
```

---

## Accessing Dashboard and Metrics

### Kubernetes Dashboard

**Method 1: Quick access (opens browser automatically):**
```bash
minikube dashboard -p todo-dev
```

**Method 2: Get URL without opening browser:**
```bash
minikube dashboard -p todo-dev --url
```

**Expected output:**
```
🤔  Verifying dashboard health ...
🚀  Launching proxy ...
🤔  Verifying proxy health ...
http://127.0.0.1:12345/api/v1/namespaces/kubernetes-dashboard/services/http:kubernetes-dashboard:/proxy/
```

**Method 3: Manual access via kubectl proxy:**
```bash
# Start proxy
kubectl proxy

# Access dashboard at:
# http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/http:kubernetes-dashboard:/proxy/
```

### Dashboard Features

Once in dashboard, you can:

1. **View cluster resources:**
   - Nodes, Namespaces, Persistent Volumes

2. **Manage workloads:**
   - Deployments, Pods, ReplicaSets, StatefulSets

3. **View services and networking:**
   - Services, Ingresses, Network Policies

4. **View configuration:**
   - ConfigMaps, Secrets

5. **Monitor resources (with metrics-server):**
   - CPU and memory usage graphs
   - Resource utilization charts

### Metrics Server

**View node metrics:**
```bash
kubectl top nodes
```

**Expected output:**
```
NAME       CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
todo-dev   250m         6%     2048Mi          25%
```

**View pod metrics (all namespaces):**
```bash
kubectl top pods -A
```

**View pod metrics (specific namespace):**
```bash
kubectl top pods -n default
```

**View specific pod metrics:**
```bash
kubectl top pod <pod-name>
```

**Expected output:**
```
NAME                              CPU(cores)   MEMORY(bytes)
hello-minikube-xxxxxxxxxx-xxxxx   1m           8Mi
```

**Continuous monitoring:**
```bash
# Watch node metrics (updates every 2 seconds)
watch kubectl top nodes

# Watch pod metrics
watch kubectl top pods -A
```

### Resource Monitoring Best Practices

1. **Wait 2-3 minutes after cluster start** before expecting accurate metrics
2. **Metrics refresh every 15 seconds** by default
3. **Use metrics for right-sizing** pod resource requests/limits
4. **Monitor before and after deployments** to understand resource impact

---

## Troubleshooting Common Issues

### Issue 1: Cluster Won't Start

**Symptoms:**
- `minikube start` fails with error
- Timeout during cluster creation

**Diagnosis:**
```bash
# Check Docker daemon
docker info

# Check available resources
docker system df

# Check Minikube logs
minikube logs -p todo-dev
```

**Solutions:**

**A. Docker not running:**
```bash
# Windows: Start Docker Desktop
# Linux: Start Docker daemon
sudo systemctl start docker

# Verify
docker info
```

**B. Insufficient resources:**
```bash
# Reduce allocation
minikube start -p todo-dev --cpus=2 --memory=4096

# Or close other applications to free resources
```

**C. Driver issues:**
```bash
# Try alternative driver (VirtualBox)
minikube start -p todo-dev --driver=virtualbox

# Or reset Minikube
minikube delete -p todo-dev
minikube start -p todo-dev --driver=docker
```

### Issue 2: Pods Stuck in Pending State

**Symptoms:**
- Pods show `Pending` status indefinitely
- `kubectl describe pod` shows scheduling errors

**Diagnosis:**
```bash
# Check pod status
kubectl get pods

# Get detailed info
kubectl describe pod <pod-name>

# Check node resources
kubectl top nodes
kubectl describe node todo-dev
```

**Solutions:**

**A. Insufficient resources:**
```bash
# Check allocatable resources
kubectl describe node todo-dev | grep -A 5 "Allocatable"

# Increase cluster resources
minikube delete -p todo-dev
minikube start -p todo-dev --cpus=4 --memory=8192
```

**B. Image pull errors:**
```bash
# Check events
kubectl describe pod <pod-name> | grep -A 10 "Events"

# If image pull fails, check network
docker pull <image-name>

# Or use image registry mirror
minikube start -p todo-dev --image-mirror-country=us
```

### Issue 3: Ingress Not Working

**Symptoms:**
- `curl http://hello.local` returns connection refused or 404
- Ingress shows no ADDRESS

**Diagnosis:**
```bash
# Check ingress status
kubectl get ingress

# Check ingress controller pods
kubectl get pods -n ingress-nginx

# Check ingress details
kubectl describe ingress <ingress-name>

# Check hosts file
cat /etc/hosts | grep local  # Linux/macOS
type C:\Windows\System32\drivers\etc\hosts | findstr local  # Windows
```

**Solutions:**

**A. Ingress addon not enabled:**
```bash
minikube addons enable ingress -p todo-dev

# Wait for controller to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s
```

**B. Missing hosts file entry:**
```bash
# Get cluster IP
CLUSTER_IP=$(minikube ip -p todo-dev)

# Add to hosts file
# Linux/macOS:
echo "$CLUSTER_IP hello.local" | sudo tee -a /etc/hosts

# Windows (run as Administrator):
# Add to C:\Windows\System32\drivers\etc\hosts:
# <CLUSTER_IP> hello.local
```

**C. Service backend not ready:**
```bash
# Check service exists
kubectl get service <service-name>

# Check pods are running
kubectl get pods -l app=<app-label>

# Check service endpoints
kubectl get endpoints <service-name>
```

### Issue 4: Metrics Not Available

**Symptoms:**
- `kubectl top nodes` returns error: "Metrics API not available"
- Dashboard shows no graphs

**Diagnosis:**
```bash
# Check metrics-server addon
minikube addons list -p todo-dev | grep metrics-server

# Check metrics-server pod
kubectl get pods -n kube-system -l k8s-app=metrics-server

# Check metrics-server logs
kubectl logs -n kube-system -l k8s-app=metrics-server
```

**Solutions:**

**A. Metrics-server not enabled:**
```bash
minikube addons enable metrics-server -p todo-dev
```

**B. Metrics not yet collected (wait 2-3 minutes):**
```bash
# Wait for metrics collection
sleep 120

# Try again
kubectl top nodes
```

**C. Metrics-server misconfiguration:**
```bash
# Disable and re-enable
minikube addons disable metrics-server -p todo-dev
minikube addons enable metrics-server -p todo-dev

# Wait 2 minutes
sleep 120

# Verify
kubectl top nodes
```

### Issue 5: Cannot Connect with kubectl

**Symptoms:**
- `kubectl get nodes` returns: "The connection to the server was refused"
- kubectl commands timeout

**Diagnosis:**
```bash
# Check cluster status
minikube status -p todo-dev

# Check kubectl context
kubectl config current-context

# Check kubectl config
kubectl config view
```

**Solutions:**

**A. Cluster not running:**
```bash
# Start cluster
minikube start -p todo-dev
```

**B. Wrong kubectl context:**
```bash
# List contexts
kubectl config get-contexts

# Switch to correct context
kubectl config use-context todo-dev
```

**C. API server not responding:**
```bash
# Restart cluster
minikube stop -p todo-dev
minikube start -p todo-dev
```

### Issue 6: Docker Driver Network Issues

**Symptoms:**
- Cannot access cluster IP directly
- Services accessible via `minikube service` but not via IP

**This is expected behavior on Windows/macOS with Docker driver.**

**Solutions:**

**Use one of these methods:**

```bash
# Method 1: minikube service (creates tunnel)
minikube service <service-name> -p todo-dev --url

# Method 2: kubectl port-forward
kubectl port-forward service/<service-name> 8080:80

# Method 3: Ingress with hosts file entry
# (Recommended for production-like testing)
```

### Getting Help

**View Minikube logs:**
```bash
minikube logs -p todo-dev
```

**View detailed cluster info:**
```bash
kubectl cluster-info dump
```

**Check Minikube version and config:**
```bash
minikube version
minikube config view
```

**Reset cluster (last resort):**
```bash
minikube delete -p todo-dev
minikube start -p todo-dev --driver=docker --cpus=4 --memory=8192
```

---

## Daily Workflow Commands

### Starting Your Work Day

```bash
# 1. Start cluster (if stopped)
minikube start -p todo-dev

# 2. Verify cluster is ready
minikube status -p todo-dev

# 3. Check all pods are running
kubectl get pods -A

# 4. View resource usage
kubectl top nodes
kubectl top pods -A

# 5. (Optional) Open dashboard
minikube dashboard -p todo-dev
```

**Estimated time:** 1-2 minutes (cluster is already configured)

### During Development

**Deploy application:**
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Or apply specific files
kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f ingress.yaml
```

**Check deployment status:**
```bash
# Watch deployment progress
kubectl get deployments -w

# Check pod status
kubectl get pods

# View pod logs
kubectl logs <pod-name>

# Follow logs in real-time
kubectl logs -f <pod-name>

# Logs for all pods with label
kubectl logs -l app=backend --all-containers=true
```

**Update application:**
```bash
# Update image (rolling update)
kubectl set image deployment/backend-api backend-api=backend:v2

# Watch rollout status
kubectl rollout status deployment/backend-api

# Rollback if needed
kubectl rollout undo deployment/backend-api
```

**Access application:**
```bash
# Via ingress (if configured)
curl http://todo.local
curl http://todo.local/api/health

# Via port-forward
kubectl port-forward service/frontend 3000:3000
# Access: http://localhost:3000

# Via minikube service
minikube service frontend -p todo-dev --url
```

**Debug issues:**
```bash
# Describe pod for events
kubectl describe pod <pod-name>

# Execute command in pod
kubectl exec -it <pod-name> -- /bin/sh

# Check service endpoints
kubectl get endpoints

# View cluster events
kubectl get events --sort-by=.metadata.creationTimestamp
```

### End of Day

**Option 1: Stop cluster (preserves state):**
```bash
# Stop cluster (keeps all data)
minikube stop -p todo-dev
```

**Option 2: Pause cluster (faster resume):**
```bash
# Pause cluster (freezes state)
minikube pause -p todo-dev

# Resume next day
minikube unpause -p todo-dev
```

**Option 3: Keep running (if sufficient resources):**
```bash
# No action needed
# Cluster continues running in background
```

### Weekly Maintenance

```bash
# Update Minikube
minikube update-check

# Clean unused Docker resources
docker system prune -f

# View cluster resource usage
kubectl top nodes
kubectl top pods -A

# Check for failed pods
kubectl get pods -A | grep -v Running

# View Minikube version and configuration
minikube version
minikube config view
```

---

## Cleanup and Reset Procedures

### Stop Cluster (Preserves Data)

**Stop cluster without deleting data:**
```bash
minikube stop -p todo-dev
```

**Restart later:**
```bash
minikube start -p todo-dev
```

**When to use:** End of day, weekend, preserve all work

### Pause Cluster (Faster Resume)

**Pause cluster (freeze state):**
```bash
minikube pause -p todo-dev
```

**Resume cluster:**
```bash
minikube unpause -p todo-dev
```

**When to use:** Short breaks, lunch, faster than stop/start

### Delete Specific Resources

**Delete deployment:**
```bash
kubectl delete deployment <deployment-name>
```

**Delete service:**
```bash
kubectl delete service <service-name>
```

**Delete ingress:**
```bash
kubectl delete ingress <ingress-name>
```

**Delete all resources in namespace:**
```bash
kubectl delete all --all -n default
```

### Delete Entire Cluster

**⚠️ WARNING: This permanently deletes all cluster data!**

```bash
# Delete cluster (requires confirmation)
minikube delete -p todo-dev
```

**Recreate cluster from scratch:**
```bash
minikube start -p todo-dev --driver=docker --cpus=4 --memory=8192
```

### Delete All Minikube Clusters

**⚠️ DANGER: Deletes ALL clusters!**

```bash
# Delete all Minikube profiles
minikube delete --all
```

### Clean Docker Resources

**Free up disk space:**
```bash
# Remove unused Docker images
docker image prune -a -f

# Remove unused containers
docker container prune -f

# Remove unused volumes
docker volume prune -f

# Remove all unused resources
docker system prune -a -f

# View disk usage before/after
docker system df
```

### Reset Minikube Configuration

**Reset to default settings:**
```bash
# View current config
minikube config view

# Unset specific config
minikube config unset <key>

# Delete all config (Linux/macOS)
rm -rf ~/.minikube/config/config.json

# Delete all config (Windows)
del %USERPROFILE%\.minikube\config\config.json
```

### Complete System Reset

**Nuclear option - start completely fresh:**

```bash
# 1. Delete all clusters
minikube delete --all

# 2. Remove Minikube directory (Linux/macOS)
rm -rf ~/.minikube

# Remove Minikube directory (Windows)
# rmdir /s %USERPROFILE%\.minikube

# 3. Clean Docker resources
docker system prune -a -f

# 4. Restart from scratch
minikube start -p todo-dev --driver=docker --cpus=4 --memory=8192
```

---

## Quick Reference Card

### Essential Commands

```bash
# Cluster Management
minikube start -p todo-dev              # Start cluster
minikube stop -p todo-dev               # Stop cluster
minikube pause -p todo-dev              # Pause cluster
minikube unpause -p todo-dev            # Resume cluster
minikube delete -p todo-dev             # Delete cluster
minikube status -p todo-dev             # Check status
minikube ip -p todo-dev                 # Get cluster IP

# Addon Management
minikube addons list -p todo-dev        # List addons
minikube addons enable <addon>          # Enable addon
minikube addons disable <addon>         # Disable addon

# Dashboard & Metrics
minikube dashboard -p todo-dev          # Open dashboard
kubectl top nodes                       # Node metrics
kubectl top pods -A                     # Pod metrics

# Application Management
kubectl apply -f <file>                 # Deploy app
kubectl get pods                        # List pods
kubectl get services                    # List services
kubectl get ingress                     # List ingresses
kubectl logs <pod>                      # View logs
kubectl describe pod <pod>              # Pod details
kubectl exec -it <pod> -- /bin/sh       # Shell into pod

# Troubleshooting
minikube logs -p todo-dev               # Cluster logs
kubectl get events                      # Cluster events
kubectl cluster-info                    # Cluster info
minikube ssh -p todo-dev                # SSH into node
```

### Configuration Reference

**Recommended Setup:**
- **Profile:** `todo-dev`
- **Driver:** `docker`
- **CPU:** `4` cores
- **Memory:** `8192` MB (8GB)
- **Disk:** `40g`
- **Addons:** `ingress`, `metrics-server`, `dashboard`

**One-line start command:**
```bash
minikube start -p todo-dev --driver=docker --cpus=4 --memory=8192 --disk-size=40g --addons=ingress,metrics-server,dashboard
```

---

## Next Steps

1. **Deploy Full-Stack Todo App:**
   - Apply Kubernetes manifests for backend, frontend, and database
   - Configure ingress for routing
   - Set up persistent storage for PostgreSQL

2. **Learn Kubernetes Concepts:**
   - Deployments, Services, Ingresses
   - ConfigMaps and Secrets
   - Persistent Volumes and Claims
   - Resource requests and limits

3. **Optimize Configuration:**
   - Tune resource allocation based on usage
   - Configure autoscaling (HPA)
   - Set up health checks and readiness probes

4. **Explore Advanced Features:**
   - Helm charts for package management
   - Network policies for security
   - Service mesh (Istio, Linkerd)

---

**Questions or issues?** Refer to [Troubleshooting](#troubleshooting-common-issues) or check Minikube documentation:
- **Official Docs:** https://minikube.sigs.k8s.io/docs/
- **GitHub Issues:** https://github.com/kubernetes/minikube/issues

---

**Document Owner**: DevOps/Infrastructure Team
**Last Updated**: 2025-12-30
**Next Review**: 2025-01-15
