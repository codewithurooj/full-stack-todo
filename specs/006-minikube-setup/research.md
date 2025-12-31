# Minikube Setup Best Practices - Research Document

**Document Version:** 1.0
**Last Updated:** December 30, 2025
**Status:** Active Research

## Table of Contents

1. [Minikube Driver Selection](#1-minikube-driver-selection)
2. [Resource Allocation](#2-resource-allocation)
3. [Addon Management](#3-addon-management)
4. [Minikube Profiles](#4-minikube-profiles)
5. [Persistent Storage](#5-persistent-storage)
6. [Networking](#6-networking)
7. [Common Issues and Solutions](#7-common-issues-and-solutions)
8. [Production-Like Testing](#8-production-like-testing)
9. [Decision Summary](#9-decision-summary)
10. [References](#10-references)

---

## 1. Minikube Driver Selection

### Overview

Minikube supports multiple drivers that determine how the Kubernetes cluster runs on your local machine. The choice of driver significantly impacts performance, compatibility, and feature availability.

### Available Drivers

#### 1.1 Docker Driver

**Description:**
The Docker driver runs the Kubernetes cluster within a Docker container rather than a full VM, making it lightweight and efficient.

**Pros:**
- **Lightweight:** No VM overhead, uses containers directly
- **Fast startup:** Typically faster than VM-based drivers
- **Cross-platform:** Works on Linux, macOS, and Windows
- **Easy setup:** Minimal configuration required
- **CI/CD friendly:** Ideal for automated pipelines
- **Safe default:** Recommended by Minikube on all common platforms

**Cons:**
- **Limited isolation:** Less isolated than full VMs
- **Networking limitations:** On macOS and Windows, Node IP is not directly reachable
- **No DNS resolution:** Docker driver on macOS doesn't support DNS resolution
- **No tunnel on Linux:** Running on Linux with Docker driver will not create a tunnel

**When to Use:**
- Development environments requiring quick iteration
- CI/CD pipelines
- When you don't need full VM isolation
- When host resources are limited
- Cross-platform development teams

**Performance Implications:**
- Lower memory overhead (no hypervisor layer)
- Faster I/O operations (no VM disk abstraction)
- Better CPU utilization for containerized workloads

#### 1.2 VirtualBox Driver

**Description:**
VirtualBox is a universal hypervisor that provides full VM isolation across platforms.

**Pros:**
- **Cross-platform compatibility:** Works on macOS, Windows, and Linux
- **Free and open-source:** No licensing costs
- **Full VM isolation:** Complete separation from host OS
- **Stable and mature:** Long-standing hypervisor technology
- **Fallback option:** Useful on Windows Home (where Hyper-V isn't available)

**Cons:**
- **Type-2 hypervisor overhead:** Less performant than Type-1 hypervisors
- **Slower than native solutions:** Not as fast as Hyper-V on Windows or KVM2 on Linux
- **Additional installation required:** Must install VirtualBox separately
- **Resource intensive:** Higher memory and CPU overhead

**When to Use:**
- Windows Home edition (no Hyper-V support)
- Cross-platform development requiring consistent behavior
- Teams needing the same driver across different OSes
- When you need full VM isolation but don't have native hypervisor access

**Performance Implications:**
- Higher memory overhead due to Type-2 hypervisor architecture
- Slower disk I/O compared to native hypervisors
- More CPU cycles consumed by virtualization layer

#### 1.3 Hyper-V Driver (Windows)

**Description:**
Hyper-V is Microsoft's native Type-1 hypervisor, available on Windows 10/11 Pro, Enterprise, and Education editions.

**Pros:**
- **Type-1 hypervisor:** Better performance than VirtualBox on Windows
- **Native Windows integration:** Built into Windows OS
- **Hardware-level virtualization:** Direct access to CPU virtualization features
- **Production-grade:** Same technology used in Azure
- **No additional installation:** Already part of Windows Pro/Enterprise/Education

**Cons:**
- **Windows Pro/Enterprise/Education only:** Not available on Windows Home
- **Conflicts with other hypervisors:** Cannot run VirtualBox simultaneously
- **Complex networking:** May require additional network configuration
- **WSL2 conflicts:** Can conflict with WSL2 in some scenarios

**When to Use:**
- Windows 10/11 Pro, Enterprise, or Education users
- When you need optimal performance on Windows
- Enterprise Windows environments
- When you want production-like VM behavior

**Performance Implications:**
- Better performance than VirtualBox on Windows
- Lower CPU overhead (Type-1 hypervisor)
- Faster VM startup and runtime performance
- Near-native disk and network I/O

#### 1.4 KVM2 Driver (Linux)

**Description:**
KVM2 utilizes KVM (Kernel-based Virtual Machine), a Linux kernel virtualization infrastructure built into the Linux kernel.

**Pros:**
- **Native Linux virtualization:** Kernel-level integration
- **Type-1 hypervisor performance:** Hardware-accelerated virtualization
- **Efficient resource usage:** Minimal overhead
- **Production-grade:** Used in enterprise Linux deployments
- **Preferred on Linux:** Recommended by Minikube for Linux users

**Cons:**
- **Linux-only:** Not available on Windows or macOS
- **Requires CPU virtualization support:** Hardware VT-x/AMD-V required
- **Additional dependencies:** May need libvirt and related packages
- **Initial setup complexity:** More configuration than Docker driver

**When to Use:**
- Linux development machines
- When you need optimal VM performance on Linux
- Production-like testing on Linux
- When you need hardware-accelerated virtualization

**Performance Implications:**
- Excellent performance (Type-1 hypervisor)
- Low CPU overhead
- Near-native memory and I/O performance
- Hardware-accelerated virtualization features

### Decision Matrix

| Driver | Platform | Performance | Isolation | Ease of Setup | Best For |
|--------|----------|-------------|-----------|---------------|----------|
| **Docker** | All | High | Medium | Easy | Dev, CI/CD |
| **VirtualBox** | All | Medium | High | Medium | Cross-platform, Win Home |
| **Hyper-V** | Windows | High | High | Medium | Windows Pro/Enterprise |
| **KVM2** | Linux | Highest | High | Medium | Linux production-like |

### Recommendation

**For this project (Full-Stack Todo App on Windows):**

**Primary Choice: Docker Driver**
```bash
minikube start --driver=docker
```

**Rationale:**
1. **Fast iteration:** Quick startup times for development workflow
2. **Resource efficient:** Lower overhead for development machine
3. **CI/CD ready:** Same driver can be used in GitHub Actions
4. **Cross-platform:** Team members on different OSes can use same driver
5. **Simple setup:** Minimal configuration required

**Alternative: Hyper-V Driver** (if you have Windows Pro/Enterprise)
```bash
minikube start --driver=hyperv
```

**When to use Hyper-V:**
- When you need closer-to-production VM behavior
- Testing scenarios requiring full VM isolation
- Enterprise Windows environments with Hyper-V already enabled

### Code Examples

#### Setting Default Driver
```bash
# Set Docker as default driver
minikube config set driver docker

# Set Hyper-V as default driver (Windows Pro+)
minikube config set driver hyperv

# Verify configuration
minikube config view
```

#### Starting with Specific Driver
```bash
# Start with Docker driver explicitly
minikube start --driver=docker --cpus=4 --memory=8192

# Start with Hyper-V driver
minikube start --driver=hyperv --cpus=4 --memory=8192

# Start with VirtualBox (fallback)
minikube start --driver=virtualbox --cpus=2 --memory=4096
```

---

## 2. Resource Allocation

### Overview

Proper resource allocation is critical for Minikube performance. Allocating too few resources causes performance issues and deployment failures; allocating too many impacts host machine performance.

### Minimum Requirements

According to official Minikube documentation (2025):

- **CPUs:** Minimum 2 CPUs
- **Memory:** Minimum 2GB (1800MB absolute minimum)
- **Disk:** Minimum 20GB free disk space

### Recommended Allocation

#### 2.1 Development Workloads

**Light Development** (Simple apps, testing):
```bash
minikube start --cpus=2 --memory=4096 --disk-size=20g
```
- **CPUs:** 2 cores
- **Memory:** 4GB
- **Disk:** 20GB
- **Use case:** Single microservice, basic testing

**Standard Development** (Multi-service apps):
```bash
minikube start --cpus=4 --memory=8192 --disk-size=40g
```
- **CPUs:** 4 cores
- **Memory:** 8GB
- **Disk:** 40GB
- **Use case:** Full-stack applications with multiple services

**Heavy Development** (Complex apps, resource-intensive):
```bash
minikube start --cpus=6 --memory=12288 --disk-size=60g
```
- **CPUs:** 6 cores
- **Memory:** 12GB
- **Disk:** 60GB
- **Use case:** Multiple microservices, databases, monitoring stack

#### 2.2 Special Workloads

**Knative/Serverless:**
```bash
minikube start --cpus=3 --memory=3072
```
Minimum recommendation for Knative and similar serverless platforms.

**AI/ML Workloads:**
```bash
minikube start --cpus=8 --memory=16384 --disk-size=100g
```
Higher resources needed for model training/inference.

### Best Practices

#### 1. Start Conservatively
Begin with lower resource allocation and scale up based on actual usage:

```bash
# Start conservative
minikube start --cpus=2 --memory=4096

# Monitor usage
kubectl top nodes
kubectl top pods --all-namespaces

# If needed, recreate with more resources
minikube delete
minikube start --cpus=4 --memory=8192
```

#### 2. Leave Resources for Host OS

**Rule of Thumb:**
- Reserve at least 25-30% of system resources for host OS
- On 16GB machine: Allocate maximum 10-12GB to Minikube
- On 8-core CPU: Allocate maximum 6 cores to Minikube

**Example calculation for 16GB RAM, 8-core machine:**
```bash
# Leave 4-6GB for host OS, allocate 10-12GB to Minikube
minikube start --cpus=6 --memory=10240

# Conservative approach (leaves more for host)
minikube start --cpus=4 --memory=8192
```

#### 3. Monitor and Adjust

Use monitoring to guide resource decisions:

```bash
# Check node resources
kubectl top node

# Check pod resources
kubectl top pods -A

# View Minikube resource usage (Docker driver)
docker stats minikube

# View detailed metrics (requires metrics-server addon)
minikube addons enable metrics-server
kubectl top nodes
```

#### 4. Avoid Over-Allocation

**Symptoms of over-allocation:**
- Host system becomes sluggish
- Other applications slow down
- Frequent disk swapping
- High host CPU usage

**Solution:**
```bash
minikube stop
minikube delete
minikube start --cpus=4 --memory=6144  # Reduce allocation
```

#### 5. Changing Resources Requires Recreate

**Important:** You cannot change CPU/memory allocation on running cluster. Must recreate:

```bash
# Stop current cluster
minikube stop

# Delete cluster (preserves config)
minikube delete

# Start with new resources
minikube start --cpus=4 --memory=8192

# Redeploy applications
kubectl apply -f your-manifests/
```

### Impact on Host Machine

#### Docker Driver
- Runs as Docker container
- Memory is dynamically allocated (may use less than allocated)
- CPU shares with host processes
- Lower overall overhead

#### VM-based Drivers (Hyper-V, VirtualBox, KVM2)
- Full memory allocation (reserved upfront)
- Dedicated CPU cores (less sharing)
- Higher overhead but better isolation

### For This Project

**Recommended Configuration:**

```bash
# Full-stack todo app with backend, frontend, database, and ingress
minikube start \
  --driver=docker \
  --cpus=4 \
  --memory=8192 \
  --disk-size=40g \
  --addons=ingress,metrics-server,dashboard
```

**Rationale:**
1. **4 CPUs:** Sufficient for FastAPI backend, Next.js frontend, PostgreSQL, and Kubernetes system components
2. **8GB Memory:** Enough for all services plus headroom for builds and updates
3. **40GB Disk:** Space for images, persistent volumes, and logs
4. **Addons enabled:** Pre-configure essential addons to avoid resource spikes later

**Minimum viable configuration** (resource-constrained machines):
```bash
minikube start \
  --driver=docker \
  --cpus=2 \
  --memory=4096 \
  --disk-size=20g
```

### Code Examples

#### View Current Allocation
```bash
# Check Minikube configuration
minikube config view

# Check actual resource usage
kubectl top node

# For Docker driver, check container stats
docker stats minikube
```

#### Update Resources
```bash
# Delete and recreate with new resources
minikube delete
minikube start --cpus=6 --memory=12288

# Or use profile-specific resources
minikube start -p production-test --cpus=6 --memory=12288
```

#### Save Default Configuration
```bash
# Set defaults for future clusters
minikube config set cpus 4
minikube config set memory 8192
minikube config set disk-size 40g

# Verify
minikube config view

# Start with defaults
minikube start
```

---

## 3. Addon Management

### Overview

Minikube addons extend the cluster with additional functionality. Three critical addons for this project are NGINX Ingress Controller, Metrics Server, and Kubernetes Dashboard.

### 3.1 NGINX Ingress Controller

#### Overview
NGINX Ingress Controller routes external HTTP/HTTPS traffic to Kubernetes services based on host names and paths.

#### Setup

**Enable Ingress Addon:**
```bash
# Enable the addon
minikube addons enable ingress

# Verify installation
kubectl get pods -n ingress-nginx

# Wait for controller to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s
```

#### Configuration Best Practices

**1. Default Configuration:**
The addon uses default configuration listening on ports 80 (HTTP) and 443 (HTTPS).

**2. TCP/UDP Services:**
For non-HTTP/HTTPS services, edit ConfigMaps:

```bash
# View TCP services ConfigMap
kubectl get configmap tcp-services -n ingress-nginx -o yaml

# View UDP services ConfigMap
kubectl get configmap udp-services -n ingress-nginx -o yaml

# Example: Expose PostgreSQL on TCP port 5432
kubectl edit configmap tcp-services -n ingress-nginx
# Add:
# data:
#   5432: "default/postgres-service:5432"
```

**3. Custom NGINX Configuration:**
```bash
# Edit main nginx-configuration ConfigMap
kubectl edit configmap ingress-nginx-controller -n ingress-nginx

# Common settings to add:
# data:
#   proxy-body-size: "10m"
#   proxy-read-timeout: "600"
#   proxy-send-timeout: "600"
```

**4. SSL/TLS Configuration:**
```yaml
# Example Ingress with TLS
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: todo-app-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  tls:
  - hosts:
    - todo.local
    secretName: todo-tls-secret
  rules:
  - host: todo.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 3000
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8000
```

#### Troubleshooting

**Issue: Ingress not accessible**
```bash
# Check ingress controller status
kubectl get pods -n ingress-nginx

# Check ingress resources
kubectl get ingress -A

# Check service
kubectl get svc -n ingress-nginx

# View controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller
```

**Issue: 404 Not Found**
- Verify service names and ports match ingress backend
- Check service endpoints: `kubectl get endpoints`
- Verify path configuration and rewrite rules

**Issue: SSL/TLS errors**
- Ensure TLS secret exists: `kubectl get secret todo-tls-secret`
- Verify certificate validity
- Check NGINX logs for specific errors

#### Important Note

**Deprecation Warning:** The community Ingress NGINX controller entered best-effort maintenance mode and is scheduled for retirement in March 2026. After that date, it will no longer receive new releases, bug fixes, or security patches.

**Recommendation:** Plan migration to alternative ingress solutions:
- **Kong Ingress Controller**
- **Traefik**
- **HAProxy Ingress**
- **Cloud-native solutions** (for production)

### 3.2 Metrics Server

#### Overview
Metrics Server provides resource usage metrics (CPU, memory) for nodes and pods, enabling `kubectl top` commands and Horizontal Pod Autoscaling (HPA).

#### Setup

**Enable Metrics Server Addon:**
```bash
# Enable the addon
minikube addons enable metrics-server

# Verify installation
kubectl get deployment metrics-server -n kube-system

# Check metrics server pod
kubectl get pods -n kube-system | grep metrics-server

# Wait for metrics to be available (may take 30-60 seconds)
kubectl top nodes

# View pod metrics
kubectl top pods -A
```

#### Configuration Best Practices

**1. TLS Configuration:**
Minikube's metrics-server addon is pre-configured with `--kubelet-insecure-tls` flag to avoid TLS verification issues with self-signed certificates.

**2. Verify Metrics Availability:**
```bash
# Check if metrics API is responding
kubectl get --raw /apis/metrics.k8s.io/v1beta1/nodes

# Check pod metrics API
kubectl get --raw /apis/metrics.k8s.io/v1beta1/pods
```

**3. Custom Resource Requests (for HPA):**
```yaml
# Example deployment with resource requests (required for HPA)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-api
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: fastapi
        image: backend:latest
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

**4. Horizontal Pod Autoscaler Example:**
```bash
# Create HPA based on CPU usage
kubectl autoscale deployment backend-api \
  --cpu-percent=70 \
  --min=2 \
  --max=10

# View HPA status
kubectl get hpa

# Detailed HPA info
kubectl describe hpa backend-api
```

#### Troubleshooting

**Issue: "Metrics not available" error**

**Cause:** Metrics Server needs time to collect initial metrics (30-60 seconds after pod creation).

**Solution:**
```bash
# Wait for metrics to become available
sleep 60

# Try again
kubectl top pods

# If still failing, check metrics-server logs
kubectl logs -n kube-system deployment/metrics-server
```

**Issue: "Metrics API not available" error**

**Cause:** Metrics Server pod not running or API registration failed.

**Solution:**
```bash
# Check metrics-server pod status
kubectl get pods -n kube-system -l k8s-app=metrics-server

# Check metrics-server logs
kubectl logs -n kube-system -l k8s-app=metrics-server

# Restart metrics-server
kubectl rollout restart deployment/metrics-server -n kube-system

# Disable and re-enable addon (last resort)
minikube addons disable metrics-server
minikube addons enable metrics-server
```

**Issue: TLS certificate verification errors**

**Cause:** Self-signed certificates or certificate SAN issues.

**Solution:**
The Minikube addon already includes `--kubelet-insecure-tls` flag. If you're deploying manually:

```yaml
# Edit metrics-server deployment
kubectl edit deployment metrics-server -n kube-system

# Add to container args:
spec:
  containers:
  - args:
    - --kubelet-insecure-tls
    - --kubelet-preferred-address-types=InternalIP
```

**Issue: Recent v0.8.0 API errors (December 2025)**

**Workaround:**
```bash
# Check current metrics-server version
kubectl get deployment metrics-server -n kube-system -o yaml | grep image:

# If needed, disable and wait for addon update
minikube addons disable metrics-server

# Monitor Minikube GitHub for addon updates
# https://github.com/kubernetes/minikube/issues
```

#### Verification Commands

```bash
# Check node metrics
kubectl top node

# Check pod metrics (all namespaces)
kubectl top pods -A

# Check pod metrics with containers breakdown
kubectl top pods -A --containers

# Sort by CPU usage
kubectl top pods -A --sort-by=cpu

# Sort by memory usage
kubectl top pods -A --sort-by=memory
```

### 3.3 Kubernetes Dashboard

#### Overview
Kubernetes Dashboard is a web-based UI for managing and monitoring Kubernetes clusters, providing visual access to workloads, services, and cluster resources.

#### Setup

**Enable Dashboard Addon:**
```bash
# Enable the addon
minikube addons enable dashboard

# Verify installation
kubectl get pods -n kubernetes-dashboard

# Access dashboard (opens browser automatically)
minikube dashboard

# Get dashboard URL without opening browser
minikube dashboard --url
```

#### Access Methods

**Method 1: Minikube Dashboard Command (Recommended for local development)**
```bash
# Start dashboard proxy and open browser
minikube dashboard

# Get URL without opening browser
minikube dashboard --url

# Output example:
# http://127.0.0.1:37283/api/v1/namespaces/kubernetes-dashboard/services/http:kubernetes-dashboard:/proxy/
```

**Method 2: kubectl proxy**
```bash
# Start kubectl proxy (port 8001 by default)
kubectl proxy

# Access dashboard at:
# http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
```

**Method 3: Port Forwarding**
```bash
# Forward dashboard service to localhost
kubectl port-forward -n kubernetes-dashboard service/kubernetes-dashboard 8080:80

# Access at: http://localhost:8080
```

#### Security Best Practices

**1. Local Access Only (Default - Secure)**
```bash
# Start proxy (only accessible from localhost)
kubectl proxy

# Dashboard accessible at:
# http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
```

**2. Remote Access (Use with Caution)**

**WARNING:** Exposing dashboard to network has security implications.

```bash
# Allow access from LAN (INSECURE - development only)
kubectl proxy --address='0.0.0.0' --disable-filter=true

# Better approach: Use SSH tunnel
# On remote machine:
kubectl proxy

# On local machine:
ssh -L 8001:localhost:8001 user@remote-host

# Access dashboard at localhost:8001
```

**3. Authentication**

**Skip Authentication (Development only):**
The Minikube dashboard addon is pre-configured to skip login. This is acceptable for local development but never for shared environments.

**Token-Based Authentication (Recommended for shared environments):**
```bash
# Create service account
kubectl create serviceaccount dashboard-admin -n kubernetes-dashboard

# Create cluster role binding
kubectl create clusterrolebinding dashboard-admin \
  --clusterrole=cluster-admin \
  --serviceaccount=kubernetes-dashboard:dashboard-admin

# Get token (Kubernetes 1.24+)
kubectl create token dashboard-admin -n kubernetes-dashboard

# For long-lived token, create secret:
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: dashboard-admin-token
  namespace: kubernetes-dashboard
  annotations:
    kubernetes.io/service-account.name: dashboard-admin
type: kubernetes.io/service-account-token
EOF

# Get token from secret
kubectl get secret dashboard-admin-token -n kubernetes-dashboard -o jsonpath='{.data.token}' | base64 --decode
```

**4. Network Policies (Advanced)**

Restrict dashboard access using network policies:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: dashboard-network-policy
  namespace: kubernetes-dashboard
spec:
  podSelector:
    matchLabels:
      k8s-app: kubernetes-dashboard
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: default
    ports:
    - protocol: TCP
      port: 8443
```

#### Troubleshooting

**Issue: Dashboard not accessible**
```bash
# Check dashboard pod status
kubectl get pods -n kubernetes-dashboard

# Check dashboard service
kubectl get svc -n kubernetes-dashboard

# View dashboard logs
kubectl logs -n kubernetes-dashboard -l k8s-app=kubernetes-dashboard

# Restart dashboard
kubectl rollout restart deployment/kubernetes-dashboard -n kubernetes-dashboard
```

**Issue: Login button disabled (remote access)**
This occurs when accessing dashboard remotely without proper authentication setup. Use token-based authentication (see above).

**Issue: "Forbidden" errors in dashboard**
```bash
# Grant more permissions to dashboard service account
kubectl create clusterrolebinding kubernetes-dashboard \
  --clusterrole=cluster-admin \
  --serviceaccount=kubernetes-dashboard:kubernetes-dashboard

# WARNING: This grants full admin access. Use carefully.
```

#### Security Recommendations

**For Development (Minikube):**
- Use `minikube dashboard` command (secure, convenient)
- Access only from localhost
- No authentication needed (local only)

**For Shared/Team Environments:**
- Use token-based authentication
- Implement RBAC with limited permissions
- Use SSH tunnels for remote access
- Consider network policies

**For Production-like Testing:**
- Disable dashboard or use read-only access
- Implement strict RBAC
- Use OAuth/OIDC authentication
- Audit dashboard access logs

**NEVER in Production:**
- Do not expose dashboard to public internet
- Do not use --disable-filter=true in production
- Do not grant cluster-admin to dashboard service account without careful consideration

### Addon Management Commands

```bash
# List all available addons
minikube addons list

# Enable multiple addons at once
minikube addons enable ingress metrics-server dashboard

# Disable addon
minikube addons disable dashboard

# Configure addon (some addons support configuration)
minikube addons configure registry-creds

# Check addon status
minikube addons list | grep enabled
```

### Recommended Addons for This Project

```bash
# Essential addons for full-stack todo app
minikube addons enable ingress          # HTTP routing
minikube addons enable metrics-server   # Resource monitoring
minikube addons enable dashboard        # Visual cluster management

# Optional but useful addons
minikube addons enable storage-provisioner    # Dynamic PV provisioning (enabled by default)
minikube addons enable default-storageclass   # Default storage class (enabled by default)

# For advanced scenarios
minikube addons enable registry         # Local Docker registry
minikube addons enable metallb          # LoadBalancer implementation
```

---

## 4. Minikube Profiles

### Overview

Minikube profiles enable running multiple isolated Kubernetes clusters on the same machine, each with independent configurations, resources, and network settings.

### Key Benefits

1. **Environment Isolation:** Separate dev, test, staging clusters
2. **Version Testing:** Test different Kubernetes versions side-by-side
3. **Configuration Testing:** Different resource allocations, addons, drivers
4. **Parallel Development:** Work on multiple projects simultaneously
5. **Safe Experimentation:** Break one cluster without affecting others

### Profile Management

#### Creating Profiles

```bash
# Create development profile
minikube start -p dev-cluster \
  --driver=docker \
  --cpus=2 \
  --memory=4096 \
  --kubernetes-version=v1.28.0

# Create staging profile (different resources)
minikube start -p staging-cluster \
  --driver=docker \
  --cpus=4 \
  --memory=8192 \
  --kubernetes-version=v1.29.0

# Create testing profile (VM-based for better isolation)
minikube start -p testing-cluster \
  --driver=hyperv \
  --cpus=4 \
  --memory=6144
```

#### Switching Between Profiles

```bash
# Set active profile to dev
minikube profile dev-cluster

# Verify current profile
minikube profile

# Run kubectl commands against active profile
kubectl get nodes
kubectl get pods -A

# Switch to staging profile
minikube profile staging-cluster
kubectl get nodes

# Or use -p flag without changing default
minikube status -p dev-cluster
minikube dashboard -p staging-cluster
```

#### Listing Profiles

```bash
# List all profiles
minikube profile list

# Example output:
# |--------------|-----------|---------|------------|------|---------|---------|-------|--------|
# | Profile Name | VM Driver | Runtime |     IP     | Port | Version | Status  | Nodes | Active |
# |--------------|-----------|---------|------------|------|---------|---------|-------|--------|
# | dev-cluster  | docker    | docker  | 192.168.49.2| 8443 | v1.28.0 | Running | 1     |        |
# | staging      | docker    | docker  | 192.168.49.3| 8443 | v1.29.0 | Running | 1     | *      |
# | test-cluster | hyperv    | docker  | 172.18.0.2  | 8443 | v1.28.0 | Stopped | 1     |        |
# |--------------|-----------|---------|------------|------|---------|---------|-------|--------|
```

#### Managing Individual Profiles

```bash
# Start specific profile
minikube start -p dev-cluster

# Stop specific profile
minikube stop -p dev-cluster

# Delete specific profile
minikube delete -p dev-cluster

# Get status of specific profile
minikube status -p staging-cluster

# Access dashboard for specific profile
minikube dashboard -p dev-cluster
```

### Use Cases for Multiple Profiles

#### Use Case 1: Development and Testing Separation

```bash
# Development environment (lightweight, fast iteration)
minikube start -p dev \
  --driver=docker \
  --cpus=2 \
  --memory=4096 \
  --addons=ingress,dashboard

# Testing environment (closer to production)
minikube start -p test \
  --driver=hyperv \
  --cpus=4 \
  --memory=8192 \
  --addons=ingress,metrics-server,dashboard

# Switch between environments
minikube profile dev      # Work on features
minikube profile test     # Run integration tests
```

#### Use Case 2: Multi-Project Development

```bash
# Todo app cluster
minikube start -p todo-app \
  --driver=docker \
  --cpus=4 \
  --memory=8192

# E-commerce app cluster
minikube start -p ecommerce-app \
  --driver=docker \
  --cpus=4 \
  --memory=8192

# Microservices learning cluster
minikube start -p learning \
  --driver=docker \
  --cpus=2 \
  --memory=4096

# Work on different projects without conflicts
minikube profile todo-app
kubectl apply -f ./todo-k8s/

minikube profile ecommerce-app
kubectl apply -f ./ecommerce-k8s/
```

#### Use Case 3: Kubernetes Version Testing

```bash
# Test on current stable version
minikube start -p k8s-1-29 \
  --kubernetes-version=v1.29.0 \
  --cpus=4 \
  --memory=8192

# Test on previous version (compatibility check)
minikube start -p k8s-1-28 \
  --kubernetes-version=v1.28.0 \
  --cpus=4 \
  --memory=8192

# Test on latest version (future compatibility)
minikube start -p k8s-1-30 \
  --kubernetes-version=v1.30.0 \
  --cpus=4 \
  --memory=8192

# Deploy same manifests to all versions
for profile in k8s-1-28 k8s-1-29 k8s-1-30; do
  minikube profile $profile
  kubectl apply -f ./manifests/
done
```

#### Use Case 4: Driver Comparison

```bash
# Docker driver profile
minikube start -p docker-test \
  --driver=docker \
  --cpus=4 \
  --memory=8192

# Hyper-V driver profile
minikube start -p hyperv-test \
  --driver=hyperv \
  --cpus=4 \
  --memory=8192

# Compare performance
minikube profile docker-test
time kubectl apply -f large-deployment.yaml

minikube profile hyperv-test
time kubectl apply -f large-deployment.yaml
```

### Best Practices

#### 1. Naming Convention

Use descriptive profile names:
```bash
# Good names
minikube start -p todo-dev
minikube start -p todo-staging
minikube start -p project-name-environment

# Avoid
minikube start -p cluster1
minikube start -p test
```

#### 2. Resource Management

Monitor total resource usage across profiles:
```bash
# Check all running profiles
minikube profile list

# Stop unused profiles to free resources
minikube stop -p unused-profile

# View resources by profile (Docker driver)
docker stats $(docker ps --filter "name=minikube" --format "{{.Names}}")
```

#### 3. Context Management

Kubernetes contexts are automatically created per profile:
```bash
# View all contexts
kubectl config get-contexts

# Example output:
# CURRENT   NAME              CLUSTER           AUTHINFO          NAMESPACE
#           dev-cluster       dev-cluster       dev-cluster       default
# *         staging-cluster   staging-cluster   staging-cluster   default
#           todo-app          todo-app          todo-app          default

# Switch context directly (alternative to minikube profile)
kubectl config use-context dev-cluster
```

#### 4. Profile Configuration Files

Each profile has isolated configuration:
```bash
# Profile configs stored in:
# ~/.minikube/profiles/<profile-name>/

# View profile config
cat ~/.minikube/profiles/dev-cluster/config.json

# Backup profile
cp -r ~/.minikube/profiles/dev-cluster ~/backups/
```

#### 5. Automation Scripts

Create helper scripts for common profile workflows:

```bash
# create-profile.sh
#!/bin/bash
PROFILE_NAME=$1
CPUS=${2:-4}
MEMORY=${3:-8192}

minikube start -p "$PROFILE_NAME" \
  --driver=docker \
  --cpus="$CPUS" \
  --memory="$MEMORY" \
  --addons=ingress,metrics-server,dashboard

echo "Profile $PROFILE_NAME created successfully"
minikube profile "$PROFILE_NAME"
```

Usage:
```bash
./create-profile.sh todo-dev 4 8192
./create-profile.sh todo-test 2 4096
```

### For This Project

**Recommended Profile Setup:**

```bash
# Primary development profile
minikube start -p todo-dev \
  --driver=docker \
  --cpus=4 \
  --memory=8192 \
  --disk-size=40g \
  --addons=ingress,metrics-server,dashboard

# Set as default
minikube profile todo-dev

# Optional: Testing/staging profile
minikube start -p todo-staging \
  --driver=docker \
  --cpus=4 \
  --memory=8192 \
  --disk-size=40g \
  --addons=ingress,metrics-server
```

**Workflow:**
```bash
# Daily development
minikube profile todo-dev
kubectl apply -f k8s/

# Before deployment, test on staging profile
minikube profile todo-staging
kubectl apply -f k8s/
# Run integration tests

# Switch back to dev
minikube profile todo-dev
```

---

## 5. Persistent Storage

### Overview

Minikube provides multiple storage solutions for persisting data beyond pod lifecycles. Understanding storage options is critical for stateful applications like databases.

### Default Storage Class

#### Standard Storage Class

Minikube includes a pre-configured storage class called `standard`:

```bash
# View storage classes
kubectl get storageclass

# Output:
# NAME                 PROVISIONER                RECLAIMPOLICY   VOLUMEBINDINGMODE   ALLOWVOLUMEEXPANSION   AGE
# standard (default)   k8s.io/minikube-hostpath   Delete          Immediate           false                  5m
```

**Characteristics:**
- **Provisioner:** `k8s.io/minikube-hostpath`
- **Type:** hostPath (stores data on Minikube VM/container filesystem)
- **Reclaim Policy:** Delete (PV deleted when PVC deleted)
- **Binding Mode:** Immediate (PV bound as soon as PVC created)
- **Default:** Automatically used if no storageClassName specified

#### How It Works

```yaml
# PersistentVolumeClaim using default storage class
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  # storageClassName: standard  # Optional, used by default if omitted
```

When this PVC is created:
1. Dynamic provisioner creates a PersistentVolume (PV)
2. PV stores data in `/tmp/hostpath-provisioner/<pvc-name>` on Minikube node
3. PV binds to PVC
4. Pod can mount PVC and read/write data

### CSI Hostpath Driver (Advanced)

For advanced features like snapshots and multi-node support:

```bash
# Enable CSI hostpath driver addon
minikube addons enable csi-hostpath-driver

# Verify installation
kubectl get storageclass

# Output includes:
# NAME               PROVISIONER                RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
# csi-hostpath-sc    hostpath.csi.k8s.io        Delete          WaitForFirstConsumer   true                   1m
# standard           k8s.io/minikube-hostpath   Delete          Immediate              false                  10m
```

**CSI Driver Features:**
- **Volume Snapshots:** Backup and restore volumes
- **Multi-Node Support:** Works with multi-node Minikube clusters
- **WaitForFirstConsumer:** Better pod scheduling (volume created on same node as pod)
- **Volume Expansion:** Resize volumes without recreating

**Storage Location:** `/var/lib/csi-hostpath-data/` on Minikube node

**Using CSI Storage Class:**
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-csi-pvc
spec:
  storageClassName: csi-hostpath-sc
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```

### Storage Best Practices

#### 1. Always Specify Storage Class

**Avoid relying on defaults:**
```yaml
# Good: Explicit storage class
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
spec:
  storageClassName: standard  # Explicit
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```

**Why:** Default storage class can change, causing unpredictable behavior.

#### 2. Use Appropriate Access Modes

```yaml
# ReadWriteOnce: Single node, single pod (databases)
accessModes:
  - ReadWriteOnce

# ReadOnlyMany: Multiple pods can read (static content)
accessModes:
  - ReadOnlyMany

# ReadWriteMany: Multiple pods can read/write (shared storage)
# NOTE: Not supported by standard hostPath provisioner
accessModes:
  - ReadWriteMany  # Requires NFS or similar
```

#### 3. Set Appropriate Storage Sizes

```yaml
# Development: Smaller sizes
resources:
  requests:
    storage: 1Gi    # Small apps

# Databases: Larger sizes
resources:
  requests:
    storage: 10Gi   # PostgreSQL, MySQL

# Media/logs: Even larger
resources:
  requests:
    storage: 50Gi   # Media storage, extensive logs
```

#### 4. Consider Reclaim Policy

```yaml
# For production-like data: Retain policy
apiVersion: v1
kind: PersistentVolume
metadata:
  name: postgres-pv-manual
spec:
  capacity:
    storage: 5Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain  # Keep data when PVC deleted
  hostPath:
    path: /mnt/data/postgres
```

Default `Delete` policy removes PV when PVC deleted. Use `Retain` for important data.

#### 5. Use Volume Binding Mode Wisely

**Immediate (default standard storage class):**
- PV created immediately when PVC created
- May bind to wrong node in multi-node clusters

**WaitForFirstConsumer (CSI driver):**
- PV created when pod scheduled
- Ensures PV on same node as pod
- **Recommended for multi-node clusters**

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-storage
provisioner: k8s.io/minikube-hostpath
volumeBindingMode: WaitForFirstConsumer  # Better scheduling
```

### Data Persistence Across Reboots

#### HostPath Behavior

**Standard storage class:**
- Data stored on Minikube node filesystem
- **Docker driver:** Data lost on `minikube delete` but persists on `minikube stop/start`
- **VM drivers:** Data persists in VM disk image

**Guaranteeing Persistence:**

Create PV in mounted host directory:
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: host-mounted-pv
spec:
  capacity:
    storage: 5Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  hostPath:
    path: /mnt/data  # Mount host directory to Minikube
```

Mount host directory to Minikube:
```bash
# Start Minikube with mounted volume
minikube start --mount --mount-string="/host/path:/minikube/path"

# Example:
minikube start --mount --mount-string="C:/data/postgres:/mnt/data"
```

### Example: PostgreSQL with Persistent Storage

**Complete example for this project:**

```yaml
# postgres-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  labels:
    app: postgres
spec:
  storageClassName: standard
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi

---
# postgres-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
spec:
  replicas: 1  # Database should have 1 replica
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:16-alpine
        env:
        - name: POSTGRES_DB
          value: "tododb"
        - name: POSTGRES_USER
          value: "todouser"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
          subPath: postgres  # Avoid postgres directory issues
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc

---
# postgres-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
```

**Deploy:**
```bash
# Create secret
kubectl create secret generic postgres-secret \
  --from-literal=password=securepassword

# Deploy PostgreSQL with PVC
kubectl apply -f postgres-pvc.yaml
kubectl apply -f postgres-deployment.yaml
kubectl apply -f postgres-service.yaml

# Verify PVC bound
kubectl get pvc postgres-pvc

# Verify pod running
kubectl get pods -l app=postgres

# Test persistence
kubectl exec -it <postgres-pod> -- psql -U todouser -d tododb -c "CREATE TABLE test (id INT);"

# Delete pod, data persists
kubectl delete pod <postgres-pod>

# New pod comes up, data still there
kubectl exec -it <new-postgres-pod> -- psql -U todouser -d tododb -c "\dt"
```

### Troubleshooting Storage

**Issue: PVC stuck in Pending**
```bash
# Check PVC status
kubectl describe pvc postgres-pvc

# Common causes:
# 1. No storage class available
kubectl get storageclass

# 2. Insufficient disk space
minikube ssh "df -h"

# 3. No PV matching PVC requirements
kubectl get pv
```

**Issue: Permission denied in mounted volume**
```bash
# Check pod logs
kubectl logs <pod-name>

# Fix: Use securityContext
# Add to pod spec:
securityContext:
  fsGroup: 999  # postgres group
  runAsUser: 999  # postgres user
```

**Issue: Data lost after minikube delete**
```bash
# Use host-mounted volumes (see above)
# Or backup/restore data:

# Backup
kubectl exec <postgres-pod> -- pg_dump -U todouser tododb > backup.sql

# After recreate
kubectl exec -i <new-postgres-pod> -- psql -U todouser tododb < backup.sql
```

### For This Project

**Recommended Storage Configuration:**

```bash
# Use default standard storage class (simple, works well)
kubectl get storageclass

# Deploy PostgreSQL with PVC (see example above)
kubectl apply -f k8s/postgres/

# Verify storage
kubectl get pvc
kubectl get pv

# For CSI features (optional):
minikube addons enable csi-hostpath-driver
# Use csi-hostpath-sc storage class in PVCs
```

---

## 6. Networking

### Overview

Minikube provides multiple methods to access services running in the cluster. Understanding these options is crucial for local development workflows.

### Networking Methods Comparison

| Method | Use Case | Accessibility | Complexity | Production-Like |
|--------|----------|---------------|------------|-----------------|
| **minikube tunnel** | LoadBalancer services | localhost | Low | Medium |
| **NodePort** | Direct service access | minikube IP:port | Low | Medium |
| **Ingress** | HTTP routing | hostname-based | Medium | High |
| **Port Forwarding** | Quick testing | localhost:port | Very Low | Low |

### 6.1 LoadBalancer with minikube tunnel

#### Overview

Services of type `LoadBalancer` normally require cloud provider integration. Minikube tunnel creates network routes to expose LoadBalancer services on localhost.

#### How It Works

```bash
# Start tunnel (must run in separate terminal)
minikube tunnel

# Output:
# Status:
#     machine: minikube
#     pid: 12345
#     route: 10.96.0.0/12 -> 192.168.49.2
#     minikube: Running
#     services: [frontend-service, backend-service]
#     errors:
#         minikube: no errors
#         router: no errors
#         loadbalancer emulator: no errors
```

The tunnel:
1. Creates network route from host to cluster CIDR
2. Assigns external IPs to LoadBalancer services
3. Makes services accessible on localhost

#### Example Usage

```yaml
# frontend-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
spec:
  type: LoadBalancer  # Use LoadBalancer type
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 3000
```

```bash
# Deploy service
kubectl apply -f frontend-service.yaml

# Start tunnel (separate terminal)
minikube tunnel

# Check service (EXTERNAL-IP assigned)
kubectl get svc frontend-service

# Output:
# NAME               TYPE           CLUSTER-IP      EXTERNAL-IP     PORT(S)        AGE
# frontend-service   LoadBalancer   10.96.123.45    127.0.0.1       80:30123/TCP   1m

# Access service
curl http://127.0.0.1
# Or open http://localhost in browser
```

#### Limitations

**Docker driver on macOS/Windows:**
- Node IP not directly reachable
- Tunnel creates routes to services, not nodes

**Docker driver on Linux:**
- No tunnel created (direct access possible)

**macOS tunnel features:**
- DNS resolution for services from host (only on macOS)

### 6.2 NodePort Access

#### Overview

NodePort exposes service on static port (30000-32767) on each node. Access via `<node-ip>:<node-port>`.

#### Example Usage

```yaml
# backend-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  type: NodePort
  selector:
    app: backend
  ports:
  - port: 8000        # ClusterIP port
    targetPort: 8000  # Container port
    nodePort: 30800   # Optional: specify NodePort (default: random 30000-32767)
```

```bash
# Deploy service
kubectl apply -f backend-service.yaml

# Get Minikube IP
minikube ip
# Output: 192.168.49.2

# Check service
kubectl get svc backend-service

# Output:
# NAME              TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)          AGE
# backend-service   NodePort   10.96.45.67    <none>        8000:30800/TCP   1m

# Access service
curl http://192.168.49.2:30800/api/health

# Or use minikube service command (opens browser)
minikube service backend-service

# Get URL without opening browser
minikube service backend-service --url
# Output: http://192.168.49.2:30800
```

#### Custom NodePort Range

```bash
# Expand NodePort range (default: 30000-32767)
minikube start --extra-config=apiserver.service-node-port-range=1-65535

# Now you can use lower ports like 8000, 3000
```

#### When to Use NodePort

**Good for:**
- Quick testing and development
- Direct service access
- Services that don't need HTTP routing

**Avoid for:**
- Production (hard to manage many ports)
- Complex routing scenarios (use Ingress)

### 6.3 Ingress Setup

#### Overview

Ingress provides HTTP/HTTPS routing to services based on hostnames and paths, similar to production Kubernetes clusters.

#### Setup

```bash
# Enable ingress addon
minikube addons enable ingress

# Verify ingress controller running
kubectl get pods -n ingress-nginx
```

#### Basic Ingress Example

```yaml
# todo-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: todo-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: todo.local  # Hostname-based routing
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 3000
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8000
```

**Deploy and access:**
```bash
# Deploy ingress
kubectl apply -f todo-ingress.yaml

# Get ingress address
kubectl get ingress todo-ingress

# Output:
# NAME           CLASS    HOSTS        ADDRESS        PORTS   AGE
# todo-ingress   <none>   todo.local   192.168.49.2   80      1m

# Add to /etc/hosts (Linux/Mac) or C:\Windows\System32\drivers\etc\hosts (Windows)
# 192.168.49.2 todo.local

# Access application
curl http://todo.local
curl http://todo.local/api/health

# Or open in browser: http://todo.local
```

#### Path-Based Routing

```yaml
# Multiple services on same host
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: multi-service-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$2
spec:
  rules:
  - host: myapp.local
    http:
      paths:
      - path: /frontend(/|$)(.*)
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 3000
      - path: /api(/|$)(.*)
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8000
```

#### TLS/HTTPS Ingress

```bash
# Create TLS certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt -subj "/CN=todo.local"

# Create secret
kubectl create secret tls todo-tls-secret \
  --cert=tls.crt --key=tls.key
```

```yaml
# Ingress with TLS
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: todo-ingress-tls
spec:
  tls:
  - hosts:
    - todo.local
    secretName: todo-tls-secret
  rules:
  - host: todo.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 3000
```

```bash
# Access via HTTPS
curl -k https://todo.local
# Or browser: https://todo.local (accept self-signed certificate)
```

### 6.4 Port Forwarding

#### Overview

Port forwarding is the simplest method for quick testing, forwarding local port to pod/service port.

#### Usage

```bash
# Forward to pod
kubectl port-forward pod/backend-pod-12345 8000:8000

# Forward to service (recommended)
kubectl port-forward service/backend-service 8000:8000

# Forward to deployment
kubectl port-forward deployment/backend 8000:8000

# Access service
curl http://localhost:8000/api/health

# Forward multiple ports
kubectl port-forward service/frontend-service 3000:3000 8000:8000

# Forward to different local port
kubectl port-forward service/backend-service 9000:8000
curl http://localhost:9000  # Access 8000 via local 9000
```

#### When to Use Port Forwarding

**Good for:**
- Quick testing during development
- Debugging specific pods
- Temporary database access
- One-off administrative tasks

**Not suitable for:**
- Permanent access (process must stay running)
- Multiple services (need multiple terminals)
- Sharing with team (only accessible on your machine)

### 6.5 Accessing Services Summary

#### Frontend (Next.js) Access Methods

**Option 1: LoadBalancer + Tunnel**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 3000
```
```bash
minikube tunnel
# Access: http://localhost
```

**Option 2: NodePort**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
spec:
  type: NodePort
  ports:
  - port: 3000
    nodePort: 30300
```
```bash
minikube service frontend-service --url
# Access: http://192.168.49.2:30300
```

**Option 3: Ingress (Recommended)**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: frontend-ingress
spec:
  rules:
  - host: todo.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 3000
```
```bash
# Add to /etc/hosts: 192.168.49.2 todo.local
# Access: http://todo.local
```

#### Backend (FastAPI) Access Methods

Usually accessed through Ingress `/api` path or directly via port-forward for testing.

**Development (Port Forward):**
```bash
kubectl port-forward service/backend-service 8000:8000
curl http://localhost:8000/docs  # FastAPI Swagger UI
```

**Production-like (Ingress):**
```yaml
- path: /api
  pathType: Prefix
  backend:
    service:
      name: backend-service
      port:
        number: 8000
```

### Platform-Specific Considerations

#### Docker Driver on Windows/macOS

**Limitations:**
- Node IP not directly reachable from host
- Must use `minikube tunnel`, `minikube service`, or port-forwarding

**Recommended approach:**
```bash
# Use Ingress for HTTP services
minikube addons enable ingress
kubectl apply -f ingress.yaml

# Or use minikube service for quick access
minikube service frontend-service
```

#### Docker Driver on Linux

**Advantages:**
- Direct access to Node IP possible
- No tunnel needed for most cases

**Access methods:**
```bash
# Get node IP
minikube ip

# Access NodePort directly
curl http://$(minikube ip):30800
```

### For This Project (Recommended Networking Setup)

**Architecture:**
```
                    ┌─────────────────┐
                    │   Host Browser  │
                    └────────┬────────┘
                             │
                    http://todo.local
                             │
                    ┌────────▼────────┐
                    │  Ingress NGINX  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         / (root)        /api          /admin
              │              │              │
     ┌────────▼───────┐ ┌───▼────────┐ ┌───▼────────┐
     │   Frontend     │ │  Backend   │ │ Dashboard  │
     │  (Next.js)     │ │ (FastAPI)  │ │ (K8s UI)   │
     │  Port 3000     │ │ Port 8000  │ │            │
     └────────────────┘ └────┬───────┘ └────────────┘
                             │
                      ┌──────▼──────┐
                      │  PostgreSQL │
                      │  Port 5432  │
                      └─────────────┘
```

**Setup commands:**
```bash
# 1. Enable ingress
minikube addons enable ingress

# 2. Deploy services (ClusterIP for internal, no external access needed)
kubectl apply -f k8s/frontend-service.yaml
kubectl apply -f k8s/backend-service.yaml
kubectl apply -f k8s/postgres-service.yaml

# 3. Deploy ingress
kubectl apply -f k8s/ingress.yaml

# 4. Add to hosts file
echo "$(minikube ip) todo.local" | sudo tee -a /etc/hosts

# 5. Access application
# Frontend: http://todo.local
# Backend API docs: http://todo.local/api/docs
# Dashboard: minikube dashboard
```

**Ingress configuration for project:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: todo-app-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$2
spec:
  rules:
  - host: todo.local
    http:
      paths:
      - path: /()(.*)                    # Root path to frontend
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 3000
      - path: /api(/|$)(.*)              # /api/* to backend
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8000
```

---

## 7. Common Issues and Solutions

### Overview

This section documents frequently encountered Minikube issues and their solutions based on 2025 documentation and community reports.

### 7.1 Slow Startup Times

#### Issue

Minikube takes 5-10+ minutes to start, often hanging at "Waiting for SSH to be available" or "Waiting for VM to power on".

#### Common Causes

1. **VM driver initialization delays**
2. **Resource constraints on host machine**
3. **Network/proxy configuration issues**
4. **Previous unclean shutdown**
5. **Large image pre-pulling**

#### Solutions

**Solution 1: Clean start after proper shutdown**
```bash
# Always stop before shutting down host machine
minikube stop

# Before restarting Minikube
minikube delete  # Clean slate
minikube start --driver=docker --cpus=4 --memory=8192
```

**Solution 2: Use Docker driver (faster than VMs)**
```bash
# Docker driver typically 2-3x faster startup than VM drivers
minikube start --driver=docker
```

**Solution 3: Increase verbosity to identify bottleneck**
```bash
# Enable detailed logging
minikube start --alsologtostderr --v=2

# Look for where startup hangs
# Common hang points:
# - "Waiting for SSH": Network/driver issue
# - "Pulling images": Slow network
# - "Starting kubelet": Resource constraint
```

**Solution 4: Pre-pull base images**
```bash
# If Docker driver, pre-pull Kubernetes images
minikube start --base-image="gcr.io/k8s-minikube/kicbase:v0.0.42"

# Or cache images
minikube cache add k8s.gcr.io/kube-apiserver:v1.28.0
minikube cache add k8s.gcr.io/kube-controller-manager:v1.28.0
```

**Solution 5: Reduce resource allocation temporarily**
```bash
# Start with minimal resources first
minikube start --cpus=2 --memory=2048

# Once running, can delete and restart with more resources
minikube delete
minikube start --cpus=4 --memory=8192
```

**Solution 6: Disable unnecessary addons at startup**
```bash
# Start without addons (faster)
minikube start

# Enable addons after cluster running
minikube addons enable ingress
minikube addons enable metrics-server
```

**Solution 7: Check for VPN/proxy interference**
```bash
# Temporarily disable VPN

# Or configure proxy
minikube start --docker-env HTTP_PROXY=http://proxy:8080 \
  --docker-env HTTPS_PROXY=https://proxy:8080 \
  --docker-env NO_PROXY=localhost,127.0.0.1
```

#### Verification

```bash
# Time the startup
time minikube start --driver=docker --cpus=4 --memory=8192

# Target: Under 2 minutes for Docker driver
# Anything over 5 minutes indicates an issue
```

### 7.2 Image Pull Issues

#### Issue

Pods stuck in `ImagePullBackOff` or `ErrImagePull` state. Image pulling takes extremely long (15+ minutes).

#### Common Causes

1. **Network connectivity issues**
2. **Docker Hub rate limiting**
3. **Incorrect image names/tags**
4. **Registry authentication required**
5. **Proxy configuration needed**

#### Solutions

**Solution 1: Use Minikube's Docker daemon**
```bash
# Point your Docker CLI to Minikube's Docker daemon
eval $(minikube docker-env)

# Build images directly in Minikube (no pull needed)
docker build -t backend:latest ./backend
docker build -t frontend:latest ./frontend

# Deploy using locally built images (imagePullPolicy: Never/IfNotPresent)
```

```yaml
# In deployment spec
spec:
  containers:
  - name: backend
    image: backend:latest
    imagePullPolicy: Never  # Don't pull, use local image
```

**Solution 2: Pre-load images into Minikube**
```bash
# Load image from tar
docker save backend:latest | (eval $(minikube docker-env) && docker load)

# Or use minikube image load (newer versions)
minikube image load backend:latest

# Or SSH and pull directly
minikube ssh "docker pull postgres:16-alpine"
```

**Solution 3: Configure image pull secrets for private registries**
```bash
# Create Docker registry secret
kubectl create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=user \
  --docker-password=password \
  --docker-email=user@example.com
```

```yaml
# Use in pod spec
spec:
  imagePullSecrets:
  - name: regcred
  containers:
  - name: backend
    image: registry.example.com/backend:latest
```

**Solution 4: Use proxy configuration**
```bash
# Start Minikube with proxy settings
minikube start \
  --docker-env HTTP_PROXY=http://proxy:8080 \
  --docker-env HTTPS_PROXY=https://proxy:8080 \
  --docker-env NO_PROXY=localhost,127.0.0.1,10.96.0.0/12

# Or configure Docker daemon inside Minikube
minikube ssh
# Edit /etc/systemd/system/docker.service.d/http-proxy.conf
```

**Solution 5: Increase timeout and retry**
```bash
# Check pod events
kubectl describe pod <pod-name>

# Delete pod to trigger retry
kubectl delete pod <pod-name>

# Or delete deployment and recreate
kubectl delete deployment <deployment-name>
kubectl apply -f deployment.yaml
```

**Solution 6: Use alternative registries**
```yaml
# Instead of Docker Hub rate-limited images
- image: docker.io/postgres:16-alpine  # May hit rate limit

# Use alternative registries
- image: ghcr.io/postgres/postgres:16-alpine
- image: quay.io/postgres/postgres:16-alpine
```

**Solution 7: Enable local registry addon**
```bash
# Enable registry addon
minikube addons enable registry

# Configure Docker to use it
export REGISTRY_PORT=$(kubectl get svc registry -n kube-system -o jsonpath='{.spec.ports[0].nodePort}')
export REGISTRY_IP=$(minikube ip)

# Tag and push images to local registry
docker tag backend:latest $REGISTRY_IP:$REGISTRY_PORT/backend:latest
docker push $REGISTRY_IP:$REGISTRY_PORT/backend:latest
```

#### Troubleshooting Steps

```bash
# 1. Check pod status
kubectl get pods
kubectl describe pod <pod-name>

# 2. Check image name (typos are common!)
kubectl get pod <pod-name> -o jsonpath='{.spec.containers[0].image}'

# 3. Try pulling manually
minikube ssh "docker pull <image-name>"

# 4. Check Docker Hub rate limits
# Visit: https://hub.docker.com/
# Or check response headers:
curl -I https://registry-1.docker.io/v2/library/postgres/manifests/16-alpine

# 5. Check network connectivity
minikube ssh
ping gcr.io
ping registry-1.docker.io
```

### 7.3 Resource Constraints

#### Issue

Pods stuck in `Pending` state, `OutOfMemory` errors, or cluster becomes unresponsive.

#### Common Causes

1. **Insufficient CPU/memory allocated to Minikube**
2. **Too many pods for allocated resources**
3. **Resource requests/limits too high**
4. **Host machine resource exhaustion**

#### Solutions

**Solution 1: Increase Minikube resources**
```bash
# Current resources
minikube config view

# Recreate with more resources
minikube delete
minikube start --cpus=6 --memory=12288 --disk-size=60g
```

**Solution 2: Reduce pod resource requests**
```yaml
# Before (too high for Minikube)
resources:
  requests:
    memory: "4Gi"
    cpu: "2000m"

# After (Minikube-friendly)
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

**Solution 3: Monitor resource usage**
```bash
# Enable metrics-server
minikube addons enable metrics-server

# Check node resources
kubectl top node

# Check pod resources
kubectl top pods -A

# Sort by memory usage
kubectl top pods -A --sort-by=memory

# Check what's pending and why
kubectl get pods -A | grep Pending
kubectl describe pod <pending-pod>
```

**Solution 4: Reduce replica counts**
```yaml
# In development, use 1 replica
spec:
  replicas: 1  # Not 3 or 5 like production
```

**Solution 5: Remove resource limits for development**
```yaml
# For development only (not recommended for production)
spec:
  containers:
  - name: backend
    # No resources section = no limits (risky but works in dev)
```

**Solution 6: Free up host machine resources**
```bash
# Stop unused Minikube profiles
minikube profile list
minikube stop -p unused-profile

# Stop Docker containers
docker ps
docker stop $(docker ps -q)

# Close resource-heavy applications
# (IDEs, browsers, etc.)
```

#### Troubleshooting Steps

```bash
# 1. Check pending pods
kubectl get pods -A | grep Pending

# 2. Describe to see why pending
kubectl describe pod <pod-name>
# Look for: "Insufficient memory" or "Insufficient cpu"

# 3. Check node capacity
kubectl describe node minikube | grep -A 5 "Allocated resources"

# 4. Check actual usage vs requests
kubectl top node
kubectl top pods -A

# 5. Identify resource hogs
kubectl top pods -A --sort-by=memory | head -10
kubectl top pods -A --sort-by=cpu | head -10
```

### 7.4 Addon Failures

#### Issue

Addons fail to enable or don't work properly after enabling.

#### Common Scenarios

**Scenario 1: Ingress addon pods not starting**
```bash
# Check ingress pods
kubectl get pods -n ingress-nginx

# If failing, check logs
kubectl logs -n ingress-nginx <ingress-controller-pod>

# Solution: Disable and re-enable
minikube addons disable ingress
minikube addons enable ingress

# Wait for pods to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s
```

**Scenario 2: Metrics-server not providing metrics**
```bash
# Check metrics-server pod
kubectl get pods -n kube-system | grep metrics-server

# Check logs
kubectl logs -n kube-system deployment/metrics-server

# Common issue: TLS certificate errors
# Solution: Restart metrics-server
kubectl rollout restart deployment/metrics-server -n kube-system

# Or disable/re-enable addon
minikube addons disable metrics-server
sleep 10
minikube addons enable metrics-server
```

**Scenario 3: Dashboard not accessible**
```bash
# Check dashboard pod
kubectl get pods -n kubernetes-dashboard

# Restart dashboard
kubectl rollout restart deployment/kubernetes-dashboard -n kubernetes-dashboard

# Access using minikube command (handles proxy automatically)
minikube dashboard
```

**Scenario 4: Registry addon issues**
```bash
# Check registry pod
kubectl get pods -n kube-system | grep registry

# Verify registry service
kubectl get svc -n kube-system | grep registry

# Test registry connectivity
minikube ssh "curl -I localhost:5000/v2/"
```

#### General Addon Troubleshooting

```bash
# 1. List all addons and status
minikube addons list

# 2. Check addon-specific pods
kubectl get pods -A | grep <addon-name>

# 3. View addon logs
kubectl logs -n <namespace> <pod-name>

# 4. Disable and re-enable
minikube addons disable <addon-name>
sleep 10
minikube addons enable <addon-name>

# 5. Check Minikube version (outdated versions have addon bugs)
minikube version
minikube update-check

# 6. Update Minikube if needed
# Download latest from: https://minikube.sigs.k8s.io/docs/start/
```

### 7.5 Networking Issues

#### Issue

Cannot access services, ingress returns 404, or DNS resolution fails.

#### Solutions

**Issue: Ingress returns 404**
```bash
# 1. Check ingress resource
kubectl get ingress
kubectl describe ingress <ingress-name>

# 2. Verify service backends exist
kubectl get svc

# 3. Check service endpoints
kubectl get endpoints <service-name>

# If no endpoints, pods not matching selector
kubectl get pods --show-labels
# Compare labels with service selector

# 4. Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller
```

**Issue: LoadBalancer stuck in Pending**
```bash
# Check service
kubectl get svc

# Solution: Start minikube tunnel
minikube tunnel

# Verify external IP assigned
kubectl get svc  # EXTERNAL-IP should show
```

**Issue: NodePort not accessible**
```bash
# Get minikube IP
minikube ip

# Check service
kubectl get svc <service-name>

# Try minikube service command
minikube service <service-name> --url

# If still not working, check pod logs
kubectl logs <pod-name>

# Check firewall rules (Windows)
netsh advfirewall firewall add rule name="Minikube" dir=in action=allow protocol=TCP localport=30000-32767
```

**Issue: DNS resolution fails inside pods**
```bash
# Test DNS from pod
kubectl run test --image=busybox --rm -it -- nslookup kubernetes.default

# Check CoreDNS pods
kubectl get pods -n kube-system -l k8s-app=kube-dns

# Restart CoreDNS if needed
kubectl rollout restart deployment/coredns -n kube-system
```

### 7.6 Windows-Specific Issues

#### Issue: Hyper-V conflicts with other hypervisors

```bash
# Cannot use VirtualBox when Hyper-V enabled
# Solution: Use Docker or Hyper-V driver only

# Check Hyper-V status
Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V

# Disable Hyper-V (requires restart)
Disable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All

# Or use Docker driver (works with Hyper-V)
minikube start --driver=docker
```

#### Issue: VPN interference on Windows

```bash
# Minikube tunnel fails with VPN active
# Solution: Add routes manually or disable VPN temporarily

# Or use NodePort instead of LoadBalancer
```

### 7.7 General Troubleshooting Commands

```bash
# Check Minikube status
minikube status

# View Minikube logs
minikube logs

# View Minikube logs with verbosity
minikube logs --alsologtostderr --v=2

# SSH into Minikube node
minikube ssh

# Check Docker daemon (Docker driver)
docker ps --filter "name=minikube"
docker logs minikube

# Check system resources
kubectl top nodes
kubectl top pods -A

# Check cluster info
kubectl cluster-info
kubectl get nodes
kubectl get pods -A

# Describe resources for events
kubectl describe node minikube
kubectl describe pod <pod-name>

# Delete and recreate cluster (last resort)
minikube delete --all --purge
minikube start
```

---

## 8. Production-Like Testing

### Overview

While Minikube is explicitly **not recommended for production**, it can be configured to simulate production Kubernetes environments for testing purposes.

### Official Stance

**From Minikube FAQ (2025):**
> "Minikube's primary goal is to quickly set up local Kubernetes clusters, and therefore we strongly discourage using minikube in production or for listening to remote traffic."

### Limitations for Production Simulation

1. **Single-node by default** (production typically multi-node)
2. **No high availability** (production has redundant control planes)
3. **Limited network isolation** (compared to cloud-native solutions)
4. **Resource constraints** (local machine vs cloud infrastructure)
5. **Different storage backends** (hostPath vs cloud storage)
6. **No load balancer integration** (requires minikube tunnel workaround)

### When to Use Minikube for Testing

**Appropriate scenarios:**
- Testing Kubernetes manifests before production deployment
- Validating Helm charts locally
- Testing application behavior in Kubernetes environment
- CI/CD pipeline local testing
- Learning and experimentation

**Not appropriate:**
- Performance testing at scale
- Load testing with realistic traffic
- Multi-region/multi-zone testing
- Production-level HA/disaster recovery testing

### Configuring Minikube for Production-Like Testing

#### 1. Resource Allocation

Match production resource ratios:
```bash
# If production pods use 4GB RAM, 2 CPUs
# Allocate similar ratios in Minikube
minikube start \
  --cpus=6 \
  --memory=12288 \
  --disk-size=60g
```

#### 2. Multi-Node Cluster

Simulate multi-node production cluster:
```bash
# Create 3-node cluster (1 control plane, 2 workers)
minikube start \
  --nodes=3 \
  --cpus=4 \
  --memory=8192 \
  --driver=docker

# Verify nodes
kubectl get nodes

# Output:
# NAME           STATUS   ROLES           AGE   VERSION
# minikube       Ready    control-plane   2m    v1.28.0
# minikube-m02   Ready    <none>          1m    v1.28.0
# minikube-m03   Ready    <none>          1m    v1.28.0
```

Test pod distribution:
```yaml
# Deployment that spreads across nodes
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 3
  template:
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - backend
              topologyKey: kubernetes.io/hostname
```

#### 3. Production Kubernetes Version

Use same Kubernetes version as production:
```bash
# Check production version
# kubectl version --short (on production cluster)

# Start Minikube with matching version
minikube start --kubernetes-version=v1.28.3
```

#### 4. Enable Production-Like Addons

```bash
# Ingress (production uses ingress controllers)
minikube addons enable ingress

# Metrics (production has monitoring)
minikube addons enable metrics-server

# Storage (production has dynamic provisioning)
minikube addons enable storage-provisioner
minikube addons enable default-storageclass

# Optional: CSI driver (closer to production storage)
minikube addons enable csi-hostpath-driver
```

#### 5. Network Policies

Test network isolation like production:
```bash
# Enable network policy (requires CNI plugin)
minikube start --cni=calico

# Or use cilium
minikube start --cni=cilium
```

Example network policy:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-network-policy
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
```

#### 6. Resource Limits and Quotas

Enforce production-like resource constraints:
```yaml
# Namespace resource quota
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: default
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "10"
```

```yaml
# LimitRange for default limits
apiVersion: v1
kind: LimitRange
metadata:
  name: limit-range
  namespace: default
spec:
  limits:
  - default:
      memory: 512Mi
      cpu: 500m
    defaultRequest:
      memory: 256Mi
      cpu: 250m
    type: Container
```

#### 7. Secrets Management

Use same secret management approach as production:
```bash
# Sealed Secrets (production-like)
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# External Secrets Operator (cloud production)
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets -n external-secrets-system --create-namespace
```

#### 8. Helm Charts

Test with same Helm charts as production:
```bash
# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Test Helm chart locally
helm install todo-app ./charts/todo-app --dry-run --debug
helm install todo-app ./charts/todo-app
helm test todo-app
```

#### 9. CI/CD Integration

Use Minikube in CI pipeline to mirror production deployments:
```yaml
# GitHub Actions example
name: Test Deployment
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Start Minikube
      uses: medyagh/setup-minikube@latest
      with:
        cpus: 4
        memory: 8192
        kubernetes-version: v1.28.0

    - name: Deploy to Minikube
      run: |
        kubectl apply -f k8s/
        kubectl wait --for=condition=ready pod -l app=backend --timeout=120s

    - name: Run Tests
      run: |
        kubectl port-forward svc/backend 8000:8000 &
        npm run test:integration
```

#### 10. Observability Stack

Deploy monitoring like production:
```bash
# Prometheus + Grafana (via Helm)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack

# Access Grafana
kubectl port-forward svc/prometheus-grafana 3000:80

# Access Prometheus
kubectl port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090
```

### Production-Like Configuration Example

Complete Minikube setup for production-like testing:
```bash
#!/bin/bash
# production-like-minikube.sh

# Start multi-node cluster with production settings
minikube start \
  --nodes=3 \
  --cpus=4 \
  --memory=8192 \
  --disk-size=60g \
  --driver=docker \
  --kubernetes-version=v1.28.3 \
  --cni=calico \
  --addons=ingress,metrics-server,storage-provisioner

# Enable additional addons
minikube addons enable csi-hostpath-driver

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install monitoring stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack --create-namespace -n monitoring

# Apply resource quotas
kubectl apply -f - <<EOF
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: default
spec:
  hard:
    requests.cpu: "6"
    requests.memory: 12Gi
    limits.cpu: "12"
    limits.memory: 24Gi
    pods: "20"
EOF

# Apply network policies
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
EOF

echo "Production-like Minikube cluster ready!"
kubectl get nodes
kubectl top nodes
```

### Alternatives for More Production-Like Testing

If Minikube's limitations are too restrictive:

**Kind (Kubernetes in Docker):**
- Better multi-node support
- Faster than Minikube for CI/CD
- Good for testing Kubernetes itself
```bash
kind create cluster --config kind-config.yaml
```

**K3s (Lightweight Kubernetes):**
- Closer to production (used in edge/IoT production)
- Lower resource overhead
- Production-grade features
```bash
curl -sfL https://get.k3s.io | sh -
```

**MicroK8s:**
- Production-ready (Canonical support)
- Addon ecosystem similar to cloud providers
- HA capabilities
```bash
snap install microk8s --classic
```

**Cloud-based Dev Clusters:**
- Google Kubernetes Engine (GKE) Autopilot free tier
- Azure Kubernetes Service (AKS) dev/test clusters
- Amazon EKS with Fargate spot instances

### For This Project

**Recommended approach:**
```bash
# Development: Single-node Minikube
minikube start -p todo-dev \
  --driver=docker \
  --cpus=4 \
  --memory=8192 \
  --addons=ingress,metrics-server

# Production-like testing: Multi-node Minikube
minikube start -p todo-staging \
  --nodes=3 \
  --driver=docker \
  --cpus=4 \
  --memory=8192 \
  --kubernetes-version=v1.28.3 \
  --addons=ingress,metrics-server,csi-hostpath-driver

# Deploy and test
minikube profile todo-staging
kubectl apply -f k8s/
kubectl wait --for=condition=ready pod --all --timeout=180s

# Run integration tests
npm run test:integration
```

---

## 9. Decision Summary

### Recommended Configuration for Full-Stack Todo App

Based on comprehensive research, here are the recommended decisions for the 006-minikube-setup feature:

#### Driver Selection

**Decision:** Docker Driver

**Rationale:**
- Fast startup times for iterative development
- Lower resource overhead on host machine
- Cross-platform compatibility for team collaboration
- Works well with CI/CD pipelines
- Adequate isolation for development purposes

**Command:**
```bash
minikube config set driver docker
```

#### Resource Allocation

**Decision:** 4 CPUs, 8GB RAM, 40GB Disk

**Rationale:**
- Sufficient for FastAPI backend, Next.js frontend, PostgreSQL, and Kubernetes system components
- Leaves adequate resources for host OS (assuming 16GB host RAM, 8-core CPU)
- Allows for monitoring stack (metrics-server) and ingress controller
- Headroom for builds and updates

**Command:**
```bash
minikube start --cpus=4 --memory=8192 --disk-size=40g
```

#### Essential Addons

**Decision:** Enable ingress, metrics-server, dashboard

**Rationale:**
- **Ingress:** Production-like HTTP routing, cleaner than NodePort
- **Metrics-server:** Essential for monitoring resource usage and troubleshooting
- **Dashboard:** Visual cluster management for debugging

**Commands:**
```bash
minikube addons enable ingress
minikube addons enable metrics-server
minikube addons enable dashboard
```

#### Profile Configuration

**Decision:** Use dedicated profile `todo-dev`

**Rationale:**
- Isolates project from other Minikube experiments
- Allows parallel development on other projects
- Easy to recreate without affecting other work
- Clear naming convention

**Command:**
```bash
minikube start -p todo-dev --driver=docker --cpus=4 --memory=8192 --disk-size=40g
minikube profile todo-dev
```

#### Persistent Storage

**Decision:** Use default `standard` storage class

**Rationale:**
- Simple, works out of box
- Sufficient for development database storage
- Dynamic provisioning without manual PV creation
- Data persists across pod restarts

**Usage:**
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
spec:
  storageClassName: standard
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```

#### Networking Approach

**Decision:** Ingress-based routing with host file entry

**Rationale:**
- Most production-like approach
- Clean URLs (http://todo.local vs http://192.168.49.2:30123)
- Single entry point for frontend and backend
- Easy to share with team members

**Setup:**
```bash
# 1. Enable ingress
minikube addons enable ingress

# 2. Add to hosts file
echo "$(minikube ip) todo.local" | sudo tee -a /etc/hosts

# 3. Access at http://todo.local
```

#### Kubernetes Version

**Decision:** Use Minikube default (latest stable)

**Rationale:**
- Latest features and security patches
- Minikube defaults to well-tested stable versions
- Can be pinned later if production uses specific version

**Command:**
```bash
# Let Minikube choose stable version
minikube start

# Or pin to specific version if needed
minikube start --kubernetes-version=v1.28.3
```

### Complete Setup Script

```bash
#!/bin/bash
# setup-minikube-todo.sh
# Setup Minikube for full-stack-todo project

set -e

echo "Setting up Minikube for full-stack-todo project..."

# Configure driver
minikube config set driver docker

# Start cluster with dedicated profile
minikube start -p todo-dev \
  --cpus=4 \
  --memory=8192 \
  --disk-size=40g

# Set as default profile
minikube profile todo-dev

# Enable essential addons
echo "Enabling addons..."
minikube addons enable ingress
minikube addons enable metrics-server
minikube addons enable dashboard

# Wait for ingress controller
echo "Waiting for ingress controller..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s

# Add hosts file entry
MINIKUBE_IP=$(minikube ip)
echo "Adding hosts entry: $MINIKUBE_IP todo.local"
echo "$MINIKUBE_IP todo.local" | sudo tee -a /etc/hosts

# Display cluster info
echo ""
echo "Minikube cluster ready!"
echo "Profile: todo-dev"
echo "Nodes:"
kubectl get nodes
echo ""
echo "Enabled addons:"
minikube addons list | grep enabled
echo ""
echo "Access application at: http://todo.local"
echo "Dashboard: minikube dashboard"
echo ""
```

### Usage Workflow

```bash
# Initial setup (run once)
./setup-minikube-todo.sh

# Daily development
minikube profile todo-dev        # Ensure correct profile active
minikube status                  # Check cluster status
# If stopped:
minikube start -p todo-dev       # Start cluster

# Deploy application
kubectl apply -f k8s/            # Deploy all resources
kubectl get pods                 # Verify pods running
kubectl get ingress              # Verify ingress configured

# Access application
# Browser: http://todo.local
# API docs: http://todo.local/api/docs
# Dashboard: minikube dashboard

# Monitor resources
kubectl top nodes
kubectl top pods

# End of day
minikube stop -p todo-dev        # Stop cluster (preserves data)

# Clean slate (if needed)
minikube delete -p todo-dev      # Delete cluster
./setup-minikube-todo.sh         # Recreate
```

### Troubleshooting Quick Reference

| Issue | Quick Fix |
|-------|-----------|
| Slow startup | `minikube delete && minikube start --driver=docker` |
| Image pull fails | `eval $(minikube docker-env) && docker build -t app:latest .` |
| Ingress 404 | `kubectl describe ingress` (check service names/ports) |
| Metrics not available | Wait 60 seconds, then `kubectl top nodes` |
| Dashboard not accessible | `minikube dashboard` (auto-handles proxy) |
| Pod pending | `kubectl describe pod <name>` (check resources) |
| Service not accessible | `minikube tunnel` (for LoadBalancer) or use Ingress |

---

## 10. References

### Official Documentation

**Minikube:**
- [Minikube Drivers](https://minikube.sigs.k8s.io/docs/drivers/)
- [Minikube FAQ](https://minikube.sigs.k8s.io/docs/faq/)
- [Accessing Apps](https://minikube.sigs.k8s.io/docs/handbook/accessing/)
- [Persistent Volumes](https://minikube.sigs.k8s.io/docs/handbook/persistent_volumes/)
- [Minikube Tunnel](https://minikube.sigs.k8s.io/docs/commands/tunnel/)
- [Dashboard](https://minikube.sigs.k8s.io/docs/handbook/dashboard/)
- [Ingress nginx for TCP and UDP services](https://minikube.sigs.k8s.io/docs/tutorials/nginx_tcp_udp_ingress/)
- [CSI Driver and Volume Snapshots](https://minikube.sigs.k8s.io/docs/tutorials/volume_snapshots_and_csi/)
- [Troubleshooting](https://minikube.sigs.k8s.io/docs/handbook/troubleshooting/)

**Kubernetes:**
- [Kubernetes Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- [Ingress-Nginx Controller](https://kubernetes.github.io/ingress-nginx/deploy/)
- [Assign Memory Resources](https://kubernetes.io/docs/tasks/configure-pod-container/assign-memory-resource/)
- [Assign CPU Resources](https://kubernetes.io/docs/tasks/configure-pod-container/assign-cpu-resource/)

### Community Resources

**Tutorials and Guides (2025):**
- [How to Use Minikube Profiles in 2025](https://aryalinux.org/blog/how-to-use-minikube-profiles)
- [How to Allocate More Resources (CPU/Memory) to Minikube in 2025](https://aryalinux.org/blog/how-to-allocate-more-resources-cpu-memory-to)
- [How to Set Up Ingress In Minikube in 2025](https://elvanco.com/blog/how-to-set-up-ingress-in-minikube)
- [How To Use minikube for Local Kubernetes Development and Testing - DigitalOcean](https://www.digitalocean.com/community/tutorials/how-to-use-minikube-for-local-kubernetes-development-and-testing)
- [A Guide to Local Kubernetes Development with Minikube - Better Stack](https://betterstack.com/community/guides/scaling-docker/minikube/)

**Comparisons and Alternatives:**
- [Minikube vs Kind: A Comprehensive Comparison - Better Stack](https://betterstack.com/community/guides/scaling-docker/minikube-vs-kubernetes/)
- [Local Kubernetes for Windows - MiniKube vs Docker Desktop - Codefresh](https://codefresh.io/blog/local-kubernetes-windows-minikube-vs-docker-desktop/)
- [Choosing the Right Kubernetes Edge Flavor - OneUptime](https://oneuptime.com/blog/post/2025-11-27-kubernetes-edge-flavors/view)

**Specific Topics:**
- [Minikube Set CPU And Memory - ShellHacks](https://www.shellhacks.com/minikube-start-with-more-memory-cpus/)
- [Kubernetes Persistent Volumes - Spacelift](https://spacelift.io/blog/kubernetes-persistent-volumes)
- [Kubernetes Ingress with NGINX - Spacelift](https://spacelift.io/blog/kubernetes-ingress)
- [Understanding Kubernetes Metrics Server - Last9](https://last9.io/blog/kubernetes-metrics-server/)

**Platform-Specific:**
- [Minikube on Windows: Hyper-V vs Vagrant/VirtualBox - Medium](https://medium.com/oracledevs/minikube-on-windows-hyper-v-vs-vagrant-virtualbox-f63e9d7c8240)
- [Setting up Kubernetes on Windows with Minikube - Harshad Ranganathan](https://rharshad.com/kubernetes-minikube-windows-setup/)

**Troubleshooting:**
- [Troubleshooting annoying issues with Minikube - Medium](https://medium.com/@maumribeiro/troubleshooting-annoying-issues-with-minikube-34486955fc54)
- [Kubernetes ImagePullBackOff - Tutorial Works](https://www.tutorialworks.com/kubernetes-imagepullbackoff/)
- [Kubernetes ImagePullBackOff - Spacelift](https://spacelift.io/blog/kubernetes-imagepullbackoff)

### GitHub Issues (Relevant)

- [Very slow startup and shutdown of Minikube VM instance #14222](https://github.com/kubernetes/minikube/issues/14222)
- [Speed up minikube start #1202](https://github.com/kubernetes/minikube/issues/1202)
- [Error "Metrics not available for pod" #13969](https://github.com/kubernetes/minikube/issues/13969)
- [Metrics API not available #22157](https://github.com/kubernetes/minikube/issues/22157)

### Tools and Related Projects

- **Kind:** https://kind.sigs.k8s.io/
- **K3s:** https://k3s.io/
- **MicroK8s:** https://microk8s.io/
- **Docker Desktop Kubernetes:** https://docs.docker.com/desktop/kubernetes/

---

**Document End**

This research document provides comprehensive guidance for implementing Minikube setup for the full-stack-todo project. All recommendations are based on 2025 best practices and official documentation.

**Next Steps:**
1. Review this research document
2. Implement setup script based on recommendations in section 9
3. Create Kubernetes manifests (deployments, services, ingress, PVCs)
4. Test complete workflow from setup to deployment
5. Document any project-specific adjustments needed
