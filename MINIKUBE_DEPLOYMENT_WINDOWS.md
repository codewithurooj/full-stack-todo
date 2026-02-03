# Minikube Deployment Guide - Windows PowerShell

**Environment:** Windows 10/11 with Docker Desktop
**Shell:** PowerShell (Administrator)
**Duration:** 10-15 minutes

---

## Prerequisites Check

Open **PowerShell as Administrator** and verify:

```powershell
# Check if tools are installed
minikube version
kubectl version --client
helm version
docker --version

# Ensure Docker Desktop is running
docker ps
```

**If any tool is missing:**
```powershell
# Install using Chocolatey
choco install minikube kubernetes-cli kubernetes-helm -y
```

---

## Step 1: Start Minikube Cluster

```powershell
# Start Minikube with Docker driver
minikube start --cpus=2 --memory=3072 --disk-size=20g --driver=docker

# Verify cluster is running
minikube status

# Should show:
# minikube
# type: Control Plane
# host: Running
# kubelet: Running
# apiserver: Running
```

---

## Step 2: Enable Kubernetes Addons

```powershell
# Enable NGINX Ingress Controller
minikube addons enable ingress

# Enable Metrics Server
minikube addons enable metrics-server

# Enable Kubernetes Dashboard
minikube addons enable dashboard

# Verify addons are enabled
minikube addons list | Select-String "enabled"
```

---

## Step 3: Build Docker Images

```powershell
# Navigate to project root
cd C:\Users\pc1\Desktop\full-stack-todo

# Build backend image
cd backend
docker build -t todo-backend:latest .
minikube image load todo-backend:latest

# Build frontend image
cd ..\frontend
docker build -t todo-frontend:latest .
minikube image load todo-frontend:latest

# Return to project root
cd ..

# Verify images are loaded in Minikube
minikube image ls | Select-String "todo"
```

**Expected output:**
```
docker.io/library/todo-backend:latest
docker.io/library/todo-frontend:latest
```

---

## Step 4: Deploy Backend with Helm

```powershell
# Install backend chart
helm install todo-api ./charts/backend

# Wait for backend pods to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=todo-backend --timeout=300s

# Check backend pods (should show 2 Running)
kubectl get pods -l app.kubernetes.io/name=todo-backend
```

**Expected output:**
```
NAME                                   READY   STATUS    RESTARTS   AGE
todo-api-todo-backend-xxxxxxxxx-xxxxx  1/1     Running   0          1m
todo-api-todo-backend-xxxxxxxxx-xxxxx  1/1     Running   0          1m
```

---

## Step 5: Deploy Frontend with Helm

```powershell
# Install frontend chart
helm install todo-app ./charts/frontend

# Wait for frontend pods to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=todo-frontend --timeout=300s

# Check frontend pods (should show 2 Running)
kubectl get pods -l app.kubernetes.io/name=todo-frontend
```

---

## Step 6: Verify All Deployments

```powershell
# Check all pods (should show 4 total)
kubectl get pods

# Check all services
kubectl get svc

# Check Helm releases
helm list
```

**Expected helm list output:**
```
NAME            NAMESPACE       REVISION        STATUS          CHART
todo-api        default         1               deployed        todo-backend-1.0.0
todo-app        default         1               deployed        todo-frontend-1.0.0
```

---

## Step 7: Test Backend API

```powershell
# Start port-forward in background
Start-Job -ScriptBlock { kubectl port-forward svc/todo-api-todo-backend 8000:8000 }

# Wait 3 seconds for port-forward to start
Start-Sleep -Seconds 3

# Test health endpoint
Invoke-WebRequest -Uri http://localhost:8000/health | Select-Object -ExpandProperty Content

# Expected: {"status":"healthy"}

# Stop port-forward
Get-Job | Stop-Job
Get-Job | Remove-Job
```

---

## Step 8: Access Frontend Application

```powershell
# Start port-forward for frontend
kubectl port-forward svc/todo-app-todo-frontend 3000:3000
```

**Keep PowerShell window open!** Then:

1. Open browser to: **http://localhost:3000**
2. You should see the Todo application
3. Test creating/completing/deleting tasks
4. Test AI chatbot at: **http://localhost:3000/chat**

**To stop port-forward:** Press `Ctrl+C` in PowerShell

---

## Step 9: View Logs

```powershell
# View backend logs (real-time)
kubectl logs -f -l app.kubernetes.io/name=todo-backend --max-log-requests=5

# In a new PowerShell window, view frontend logs
kubectl logs -f -l app.kubernetes.io/name=todo-frontend --max-log-requests=5
```

---

## Step 10: Access Kubernetes Dashboard

```powershell
# Open dashboard in browser (runs in foreground)
minikube dashboard

# OR get URL only (run in background)
Start-Process powershell -ArgumentList "minikube dashboard"
```

**Dashboard shows:**
- All pods and their status
- Resource usage (CPU/Memory)
- Deployments, Services, ConfigMaps
- Logs and events

---

## Troubleshooting Commands

```powershell
# Check if pods are crashing
kubectl get pods --all-namespaces

# Describe a failing pod
kubectl describe pod <pod-name>

# Check events
kubectl get events --sort-by='.lastTimestamp'

# Check Minikube IP
minikube ip

# SSH into Minikube VM
minikube ssh

# Delete and recreate a deployment
helm uninstall todo-app
helm install todo-app ./charts/frontend
```

---

## Cleanup

### Option 1: Keep cluster, remove deployments
```powershell
# Uninstall applications
helm uninstall todo-app
helm uninstall todo-api

# Stop cluster (preserves data for next time)
minikube stop
```

### Option 2: Complete cleanup
```powershell
# Delete entire cluster
minikube delete

# Remove Docker images
docker rmi todo-frontend:latest
docker rmi todo-backend:latest
```

---

## Quick Reference Commands

```powershell
# Start existing cluster
minikube start

# Stop cluster
minikube stop

# Get cluster info
kubectl cluster-info

# Get all resources
kubectl get all

# Watch pods in real-time
kubectl get pods --watch

# Get pod logs
kubectl logs <pod-name>

# Execute command in pod
kubectl exec -it <pod-name> -- /bin/sh

# Port-forward service
kubectl port-forward svc/<service-name> <local-port>:<service-port>

# Update deployment
helm upgrade todo-app ./charts/frontend

# Rollback deployment
helm rollback todo-app
```

---

## Environment Variable Configuration

If you need to set custom environment variables:

### Backend
```powershell
# Create custom values file
@"
config:
  DATABASE_URL: "postgresql://user:pass@host.neon.tech/dbname"

secrets:
  BETTER_AUTH_SECRET: "your-secret-key-min-32-chars"
  OPENAI_API_KEY: "sk-your-openai-key"
"@ | Out-File -FilePath backend-values.yaml -Encoding UTF8

# Deploy with custom values
helm install todo-api ./charts/backend -f backend-values.yaml
```

### Frontend
```powershell
# Create custom values file
@"
config:
  NEXT_PUBLIC_API_URL: "http://todo-api-todo-backend:8000"
  NODE_ENV: "production"

secrets:
  BETTER_AUTH_SECRET: "your-secret-key-min-32-chars"
"@ | Out-File -FilePath frontend-values.yaml -Encoding UTF8

# Deploy with custom values
helm install todo-app ./charts/frontend -f frontend-values.yaml
```

---

## Common Issues & Solutions

### Issue 1: "minikube start" fails
**Solution:**
```powershell
# Delete old cluster and start fresh
minikube delete
minikube start --cpus=2 --memory=3072 --driver=docker
```

### Issue 2: Pods stuck in "ImagePullBackOff"
**Solution:**
```powershell
# Rebuild and reload images
docker build -t todo-frontend:latest ./frontend
minikube image load todo-frontend:latest --overwrite
kubectl rollout restart deployment -l app.kubernetes.io/name=todo-frontend
```

### Issue 3: Port-forward already in use
**Solution:**
```powershell
# Find process using port 3000
netstat -ano | findstr :3000

# Kill process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### Issue 4: Docker Desktop not running
**Solution:**
1. Start Docker Desktop from Start menu
2. Wait for "Docker Desktop is running" notification
3. Run `docker ps` to verify

---

## Performance Tuning

If you have more resources available:

```powershell
# Delete existing cluster
minikube delete

# Start with more resources
minikube start --cpus=4 --memory=8192 --disk-size=40g --driver=docker

# This gives better performance for larger applications
```

---

## Next Steps

1. ✅ Deploy to Minikube (follow this guide)
2. 📹 Record demo video showing:
   - `kubectl get pods` output
   - Frontend at localhost:3000
   - Creating/completing tasks
   - AI chatbot interaction
3. 🎬 Upload demo video (<90 seconds)
4. 📝 Update README with demo video link

---

**Built with Claude Code** 🚀
**Last Updated:** December 31, 2025
