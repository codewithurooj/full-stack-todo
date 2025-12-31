# Data Model: Minikube Setup

**Feature Branch**: `006-minikube-setup`
**Created**: 2025-12-30
**Version**: 1.0

---

## Overview

This document defines the configuration models and state management for Minikube cluster setup. It captures the structure of cluster configuration, addon management, resource allocation, and network configuration needed for local Kubernetes development.

---

## 1. Minikube Cluster Configuration

### 1.1 Cluster Entity

**Description**: Represents a Minikube cluster instance with all configuration parameters.

**Attributes**:

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `profile_name` | string | Yes | "minikube" | Unique identifier for the cluster profile |
| `driver` | enum | Yes | "docker" | Container/VM driver (docker, hyperv, virtualbox, kvm2) |
| `kubernetes_version` | string | No | "stable" | Kubernetes version to install (e.g., "v1.28.3") |
| `container_runtime` | enum | No | "docker" | Container runtime (docker, containerd, cri-o) |
| `cpu_count` | integer | Yes | 2 | Number of CPUs allocated to cluster |
| `memory_mb` | integer | Yes | 2048 | Memory in MB allocated to cluster |
| `disk_size_gb` | integer | No | 20 | Disk size in GB for cluster storage |
| `status` | enum | - | - | Current cluster state (see State Machine) |
| `ip_address` | string | - | - | Cluster IP address (assigned at runtime) |
| `api_server_port` | integer | No | 8443 | Kubernetes API server port |
| `created_at` | timestamp | - | - | Cluster creation timestamp |
| `last_started` | timestamp | - | - | Last startup timestamp |

**Constraints**:

```yaml
# Validation Rules
cpu_count:
  minimum: 2
  maximum: 32
  recommended: 4

memory_mb:
  minimum: 2048  # 2GB
  maximum: 65536  # 64GB
  recommended: 8192  # 8GB

disk_size_gb:
  minimum: 20
  maximum: 1000
  recommended: 40

profile_name:
  pattern: "^[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$"
  max_length: 63
```

### 1.2 Cluster State Machine

**States**:

```
┌──────────┐
│  NONE    │ (Initial state - cluster doesn't exist)
└────┬─────┘
     │ minikube start
     ▼
┌──────────┐
│ STARTING │ (Initializing VM/container, bootstrapping Kubernetes)
└────┬─────┘
     │ Success
     ▼
┌──────────┐ ◄──── minikube unpause
│ RUNNING  │
└────┬─────┘
     │
     ├─── minikube stop ───► ┌──────────┐
     │                        │ STOPPED  │
     │                        └──────────┘
     │
     ├─── minikube pause ──► ┌──────────┐
     │                        │ PAUSED   │
     │                        └──────────┘
     │
     ├─── Error ───────────► ┌──────────┐
     │                        │ ERROR    │
     │                        └──────────┘
     │
     └─── minikube delete ─► ┌──────────┐
                              │ DELETED  │
                              └──────────┘
```

**State Transitions**:

| From | To | Trigger | Validation |
|------|-----|---------|------------|
| NONE | STARTING | `minikube start` | Resources available, driver accessible |
| STARTING | RUNNING | Cluster ready | All system pods Running, API server responsive |
| STARTING | ERROR | Initialization failure | Resource constraints, driver issues |
| RUNNING | STOPPED | `minikube stop` | No active connections required |
| RUNNING | PAUSED | `minikube pause` | - |
| RUNNING | ERROR | System failure | Node NotReady, API server down |
| RUNNING | DELETED | `minikube delete` | Confirmation (if configured) |
| STOPPED | STARTING | `minikube start` | - |
| PAUSED | RUNNING | `minikube unpause` | - |
| ERROR | STARTING | `minikube start` (recovery) | - |
| STOPPED | DELETED | `minikube delete` | - |
| ERROR | DELETED | `minikube delete` | - |

**Health Checks**:

```yaml
# Cluster health validation
health_checks:
  - name: "api_server_reachable"
    command: "kubectl cluster-info"
    expected: "Kubernetes control plane is running"
    timeout: 5s

  - name: "node_ready"
    command: "kubectl get nodes"
    expected: "STATUS: Ready"
    timeout: 5s

  - name: "system_pods_running"
    command: "kubectl get pods -n kube-system"
    expected: "All pods Running or Completed"
    timeout: 10s

  - name: "dns_working"
    command: "kubectl run test-dns --image=busybox --rm -it --restart=Never -- nslookup kubernetes.default"
    expected: "Name resolution successful"
    timeout: 30s
```

---

## 2. Addon Configuration

### 2.1 Addon Entity

**Description**: Represents a Minikube addon that extends cluster functionality.

**Attributes**:

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Addon identifier (ingress, metrics-server, dashboard) |
| `type` | enum | Yes | Addon category (networking, monitoring, ui, storage, security) |
| `status` | enum | - | Current addon state (see Addon States) |
| `namespace` | string | - | Kubernetes namespace where addon is deployed |
| `version` | string | - | Addon version (managed by Minikube) |
| `enabled_at` | timestamp | - | When addon was enabled |
| `dependencies` | array[string] | No | Other addons required (e.g., metrics-server → none) |
| `images` | array[string] | - | Container images used by addon |
| `config_options` | map[string, any] | No | Addon-specific configuration |

**Core Addons**:

```yaml
# Ingress Controller
addon_ingress:
  name: "ingress"
  type: "networking"
  namespace: "ingress-nginx"
  description: "NGINX Ingress Controller for HTTP/HTTPS routing"
  dependencies: []
  default_images:
    - "registry.k8s.io/ingress-nginx/controller:v1.9.4"
    - "registry.k8s.io/ingress-nginx/kube-webhook-certgen:v20231011-8b53cabe0"
  config_options:
    enable_ssl_passthrough: false
    custom_http_errors: ""
  resources:
    controller_pods: 1
    webhook_pods: 1
  ports:
    http: 80
    https: 443

# Metrics Server
addon_metrics_server:
  name: "metrics-server"
  type: "monitoring"
  namespace: "kube-system"
  description: "Cluster-wide resource usage metrics collection"
  dependencies: []
  default_images:
    - "registry.k8s.io/metrics-server/metrics-server:v0.6.4"
  config_options:
    metric_resolution: "15s"
    kubelet_insecure_tls: true  # Required for Minikube
  resources:
    deployment_pods: 1
  startup_delay: "60s"  # Wait for metrics to populate

# Kubernetes Dashboard
addon_dashboard:
  name: "dashboard"
  type: "ui"
  namespace: "kubernetes-dashboard"
  description: "Web-based UI for cluster management"
  dependencies: []
  default_images:
    - "docker.io/kubernetesui/dashboard:v2.7.0"
    - "docker.io/kubernetesui/metrics-scraper:v1.0.8"
  config_options:
    enable_skip_login: true  # Development only
  resources:
    dashboard_pods: 1
    scraper_pods: 1
  access_method: "minikube dashboard"  # Or kubectl proxy
```

### 2.2 Addon State Machine

**States**:

```
┌──────────┐
│ DISABLED │ (Initial state - addon not installed)
└────┬─────┘
     │ minikube addons enable <name>
     ▼
┌──────────┐
│ ENABLING │ (Installing addon resources)
└────┬─────┘
     │ Pods ready
     ▼
┌──────────┐
│ ENABLED  │ ◄─── Auto-recover from errors
└────┬─────┘
     │
     ├─── Pods Running ──► ┌──────────┐
     │                      │ RUNNING  │ (Healthy and operational)
     │                      └──────────┘
     │
     ├─── Pods Pending ──► ┌──────────┐
     │                      │ PENDING  │ (Waiting for resources)
     │                      └──────────┘
     │
     ├─── Deployment fail ► ┌──────────┐
     │                      │ ERROR    │ (Pods CrashLoopBackOff, ImagePullBackOff)
     │                      └──────────┘
     │
     └─── minikube addons disable <name> ──► ┌──────────┐
                                               │ DISABLED │
                                               └──────────┘
```

**State Transitions**:

| From | To | Trigger | Validation |
|------|-----|---------|------------|
| DISABLED | ENABLING | `minikube addons enable` | Cluster RUNNING, images accessible |
| ENABLING | RUNNING | Pods healthy | All pods Running, services ready |
| ENABLING | PENDING | Resource wait | Insufficient resources, pulling images |
| ENABLING | ERROR | Installation failure | Image pull errors, configuration errors |
| RUNNING | ERROR | Pod failures | CrashLoopBackOff, OOMKilled |
| RUNNING | DISABLED | `minikube addons disable` | - |
| ERROR | RUNNING | Auto-recovery | Kubernetes restarts pods |
| ERROR | DISABLED | `minikube addons disable` | Cleanup resources |
| PENDING | RUNNING | Resources available | Images pulled, resources allocated |
| PENDING | ERROR | Timeout | Max wait time exceeded (5min) |

### 2.3 Addon Dependencies

**Dependency Graph**:

```
None of the core addons have dependencies on each other.
They can be enabled in any order.

┌────────────────┐
│    Ingress     │  (Independent)
└────────────────┘

┌────────────────┐
│ Metrics-Server │  (Independent)
└────────────────┘

┌────────────────┐
│   Dashboard    │  (Independent, but enhanced with metrics-server)
└────────────────┘

Optional enhancement:
Dashboard ──► (optional) ──► Metrics-Server
  (If metrics-server enabled, dashboard shows resource graphs)
```

**Validation Rules**:

```yaml
# Addon enablement validation
addon_validation:
  prerequisites:
    - cluster_status: RUNNING
    - api_server_responsive: true
    - system_pods_ready: true

  resource_requirements:
    ingress:
      min_cpu: 100m
      min_memory: 128Mi
    metrics_server:
      min_cpu: 100m
      min_memory: 200Mi
    dashboard:
      min_cpu: 100m
      min_memory: 200Mi

  timeout:
    enabling: 300s  # 5 minutes max
    health_check: 120s  # 2 minutes for pod ready
```

---

## 3. Resource Allocation Model

### 3.1 Resource Configuration

**Description**: CPU and memory allocation for the Minikube cluster with validation constraints.

**Schema**:

```yaml
resource_allocation:
  cpu:
    type: "integer"
    unit: "cores"
    minimum: 2
    maximum: 32
    recommended: 4
    validation:
      - rule: "must_be_less_than_host_cpu"
        message: "Cannot allocate more CPUs than host has available"
      - rule: "leave_host_buffer"
        recommendation: "Leave at least 2 cores for host OS"
        formula: "allocated_cpu <= (host_cpu - 2)"

  memory:
    type: "integer"
    unit: "MB"
    minimum: 2048  # 2GB
    maximum: 65536  # 64GB
    recommended: 8192  # 8GB
    validation:
      - rule: "must_be_less_than_host_memory"
        message: "Cannot allocate more memory than host has available"
      - rule: "leave_host_buffer"
        recommendation: "Leave at least 4GB for host OS"
        formula: "allocated_memory <= (host_memory - 4096)"
      - rule: "multiple_of_1024"
        message: "Memory should be multiple of 1024MB for optimal allocation"

  disk:
    type: "integer"
    unit: "GB"
    minimum: 20
    maximum: 1000
    recommended: 40
    validation:
      - rule: "must_have_free_space"
        message: "Host must have sufficient free disk space"
        formula: "allocated_disk <= (host_free_disk - 10)"
```

### 3.2 Resource Allocation Calculator

**Decision Matrix**:

```yaml
# Resource allocation based on workload
workload_profiles:
  minimal:
    description: "Single microservice, basic testing"
    cpu: 2
    memory: 4096  # 4GB
    disk: 20
    max_pods: 10
    use_case: "Quick testing, resource-constrained machines"

  standard:
    description: "Full-stack app with multiple services"
    cpu: 4
    memory: 8192  # 8GB
    disk: 40
    max_pods: 30
    use_case: "Backend + Frontend + Database + Ingress + Monitoring"
    services:
      - "FastAPI backend (500MB)"
      - "Next.js frontend (512MB)"
      - "PostgreSQL database (1GB)"
      - "Ingress controller (128MB)"
      - "Metrics server (200MB)"
      - "Kubernetes system (2GB)"
      - "Headroom (4GB)"

  heavy:
    description: "Complex apps, resource-intensive workloads"
    cpu: 6
    memory: 12288  # 12GB
    disk: 60
    max_pods: 50
    use_case: "Multiple microservices, databases, monitoring stack"

  ml_workload:
    description: "AI/ML model training or inference"
    cpu: 8
    memory: 16384  # 16GB
    disk: 100
    max_pods: 20
    use_case: "Model training, large dataset processing"
```

### 3.3 Resource Monitoring Schema

**Metrics Structure**:

```yaml
# Resource usage metrics (from metrics-server)
cluster_metrics:
  node:
    name: "minikube"
    cpu:
      allocatable: "4000m"  # 4 cores
      usage: "1250m"        # Current usage
      usage_percent: 31.25
    memory:
      allocatable: "8192Mi"  # 8GB
      usage: "4096Mi"        # Current usage
      usage_percent: 50.0
    timestamp: "2025-12-30T10:30:00Z"

  pods:
    - namespace: "default"
      name: "backend-api-7d4f8b5c9-xk2m4"
      cpu: "250m"
      memory: "512Mi"
    - namespace: "default"
      name: "frontend-ui-6b8f9a3d1-pl5n8"
      cpu: "200m"
      memory: "256Mi"
    - namespace: "default"
      name: "postgres-0"
      cpu: "100m"
      memory: "1024Mi"
    - namespace: "ingress-nginx"
      name: "ingress-nginx-controller-xyz"
      cpu: "50m"
      memory: "128Mi"
    - namespace: "kube-system"
      name: "metrics-server-abc"
      cpu: "10m"
      memory: "50Mi"
```

**Validation Commands**:

```yaml
verification_commands:
  - name: "Check node allocatable resources"
    command: "kubectl get nodes -o custom-columns=NAME:.metadata.name,CPU:.status.allocatable.cpu,MEMORY:.status.allocatable.memory"
    expected_output:
      cpu: "4"
      memory: "8192Mi"

  - name: "Check current resource usage"
    command: "kubectl top node"
    expected_output:
      cpu_usage: "< 80%"
      memory_usage: "< 80%"

  - name: "Check pod resource usage"
    command: "kubectl top pods -A"
    validation: "All pods should show CPU and memory values (not <unknown>)"
```

---

## 4. Network Configuration

### 4.1 Cluster Networking

**IP Address Schema**:

```yaml
cluster_networking:
  cluster_ip:
    description: "IP address of Minikube node"
    example: "192.168.49.2"
    assignment: "Dynamic (assigned by driver)"
    driver_differences:
      docker:
        access: "Via port forwarding or minikube service"
        direct_ip: false  # On macOS/Windows
      hyperv:
        access: "Direct IP access from host"
        direct_ip: true
      virtualbox:
        access: "Direct IP access from host"
        direct_ip: true

  service_cidr:
    description: "IP range for Kubernetes services"
    default: "10.96.0.0/12"
    example_service_ip: "10.96.45.123"

  pod_cidr:
    description: "IP range for pods"
    default: "10.244.0.0/16"
    example_pod_ip: "10.244.0.15"

  dns:
    cluster_domain: "cluster.local"
    dns_service: "kube-dns"
    dns_service_ip: "10.96.0.10"
```

### 4.2 Ingress Configuration Model

**Ingress Resource Schema**:

```yaml
# Ingress resource data model
ingress_resource:
  apiVersion: "networking.k8s.io/v1"
  kind: "Ingress"

  metadata:
    name: "string"  # Ingress name
    namespace: "string"  # Target namespace
    annotations:
      # Common ingress annotations
      nginx.ingress.kubernetes.io/rewrite-target: "string"
      nginx.ingress.kubernetes.io/ssl-redirect: "boolean"
      nginx.ingress.kubernetes.io/proxy-body-size: "string"  # e.g., "10m"
      cert-manager.io/cluster-issuer: "string"  # Optional TLS

  spec:
    ingressClassName: "nginx"

    rules:
      - host: "string"  # e.g., "todo.local", "api.todo.local"
        http:
          paths:
            - path: "string"  # e.g., "/", "/api", "/api/.*"
              pathType: "Prefix|Exact|ImplementationSpecific"
              backend:
                service:
                  name: "string"  # Target service name
                  port:
                    number: integer  # Service port

    tls:  # Optional HTTPS
      - hosts:
          - "string"  # e.g., "todo.local"
        secretName: "string"  # TLS certificate secret
```

**Example Routing Configuration**:

```yaml
# Todo app ingress routing
routing_configuration:
  frontend:
    host: "todo.local"
    path: "/"
    service: "frontend-service"
    port: 3000
    annotations:
      nginx.ingress.kubernetes.io/rewrite-target: "/"

  backend_api:
    host: "todo.local"
    path: "/api"
    service: "backend-service"
    port: 8000
    annotations:
      nginx.ingress.kubernetes.io/rewrite-target: "/api"
      nginx.ingress.kubernetes.io/proxy-body-size: "10m"

  health_check:
    host: "todo.local"
    path: "/health"
    service: "backend-service"
    port: 8000
```

### 4.3 Port Mapping Model

**Service Exposure Methods**:

```yaml
# Service exposure strategies
service_exposure:
  method_1_ingress:
    name: "Ingress (Recommended)"
    use_case: "HTTP/HTTPS traffic with domain-based routing"
    access: "http://todo.local"
    requires:
      - ingress_addon_enabled: true
      - hosts_file_entry: "192.168.49.2 todo.local"
    pros:
      - "Production-like routing"
      - "Clean URLs"
      - "SSL/TLS support"
      - "Path-based routing"
    cons:
      - "Requires hosts file modification"
      - "HTTP/HTTPS only"

  method_2_nodeport:
    name: "NodePort"
    use_case: "Direct port access without ingress"
    access: "http://192.168.49.2:30080"
    port_range: "30000-32767"
    pros:
      - "No additional setup"
      - "Works for any protocol (TCP/UDP)"
    cons:
      - "Non-standard ports"
      - "Less production-like"
      - "Port conflicts possible"

  method_3_port_forward:
    name: "Port Forwarding (kubectl)"
    use_case: "Development/debugging"
    command: "kubectl port-forward service/frontend 8080:3000"
    access: "http://localhost:8080"
    pros:
      - "No cluster configuration needed"
      - "Works on any driver"
      - "Temporary and flexible"
    cons:
      - "Manual command required"
      - "Single session (dies when terminal closes)"
      - "Not production-like"

  method_4_minikube_service:
    name: "Minikube Service"
    use_case: "Quick testing on Docker driver"
    command: "minikube service frontend-service --url"
    access: "http://127.0.0.1:54321"  # Random port
    pros:
      - "Works on Docker driver (macOS/Windows)"
      - "Auto-creates tunnel"
    cons:
      - "Random ports"
      - "Minikube-specific (not portable)"
      - "Manual command required"
```

### 4.4 Host File Configuration

**Schema**:

```yaml
# /etc/hosts configuration for ingress
hosts_file_entries:
  - ip: "192.168.49.2"  # Minikube IP (get via: minikube ip)
    hostnames:
      - "todo.local"
      - "api.todo.local"
      - "dashboard.local"
    comment: "Minikube ingress for todo app"

  verification:
    command: "ping todo.local"
    expected: "Reply from 192.168.49.2"

  platform_specific:
    linux: "/etc/hosts"
    macos: "/etc/hosts"
    windows: "C:\\Windows\\System32\\drivers\\etc\\hosts"

  modification:
    requires_admin: true
    format: "<IP> <hostname1> <hostname2> # <comment>"
    example: "192.168.49.2 todo.local api.todo.local # Minikube todo app"
```

---

## 5. Configuration Persistence

### 5.1 Minikube Configuration File

**Location**: `~/.minikube/config/config.json`

**Schema**:

```json
{
  "driver": "docker",
  "cpus": 4,
  "memory": 8192,
  "disk-size": "40g",
  "container-runtime": "docker",
  "kubernetes-version": "v1.28.3"
}
```

**Profile Configuration**: `~/.minikube/profiles/<profile-name>/config.json`

```json
{
  "Name": "todo-dev",
  "Driver": "docker",
  "CPUs": 4,
  "Memory": 8192,
  "DiskSize": 40960,
  "KubernetesConfig": {
    "KubernetesVersion": "v1.28.3",
    "ContainerRuntime": "docker"
  },
  "Addons": {
    "ingress": true,
    "metrics-server": true,
    "dashboard": true
  }
}
```

---

## 6. Error States and Recovery

### 6.1 Common Error States

```yaml
error_conditions:
  insufficient_resources:
    code: "ERR_INSUFFICIENT_RESOURCES"
    message: "Host machine does not have enough CPU/memory"
    detection:
      - cpu: "Requested CPU > Available CPU"
      - memory: "Requested memory > Available memory"
    recovery:
      - "Reduce CPU/memory allocation"
      - "Close other applications"
      - "Use minimal workload profile"

  driver_not_available:
    code: "ERR_DRIVER_UNAVAILABLE"
    message: "Selected driver is not installed or not running"
    detection:
      - docker: "Docker daemon not running"
      - hyperv: "Hyper-V not enabled (Windows Pro+ required)"
      - virtualbox: "VirtualBox not installed"
    recovery:
      - "Install/start the driver"
      - "Switch to alternative driver"
      - "Check driver compatibility"

  port_conflict:
    code: "ERR_PORT_CONFLICT"
    message: "Required ports already in use"
    common_ports: [80, 443, 8443, 22]
    detection: "Port binding fails during cluster start"
    recovery:
      - "Stop conflicting services"
      - "Use port forwarding instead of direct binding"
      - "Configure Minikube to use alternative ports"

  image_pull_failure:
    code: "ERR_IMAGE_PULL"
    message: "Cannot pull container images"
    causes:
      - "No network connectivity"
      - "Registry unavailable"
      - "Proxy configuration needed"
    recovery:
      - "Check network connectivity"
      - "Configure registry mirrors"
      - "Set HTTP proxy in Minikube"
      - "Pre-pull images manually"

  addon_installation_failure:
    code: "ERR_ADDON_INSTALL"
    message: "Addon installation failed"
    causes:
      - "Insufficient cluster resources"
      - "Image pull errors"
      - "Configuration errors"
    recovery:
      - "Check addon status: minikube addons list"
      - "View addon logs: kubectl logs -n <addon-namespace>"
      - "Disable and re-enable addon"
      - "Increase cluster resources"
```

---

## 7. Relationships and Dependencies

**Entity Relationship Diagram**:

```
┌─────────────────────┐
│  Minikube Cluster   │
│  - profile_name     │
│  - driver           │
│  - cpu_count        │
│  - memory_mb        │
│  - status           │
└──────────┬──────────┘
           │ 1
           │ contains
           │ 0..*
           ▼
┌─────────────────────┐         ┌─────────────────────┐
│     Addon           │         │   Node              │
│  - name             │         │  - name             │
│  - type             │         │  - status           │
│  - status           │◄────────┤  - cpu_allocatable  │
│  - namespace        │ runs on │  - memory_allocate  │
└─────────────────────┘         └──────────┬──────────┘
                                           │ 1
                                           │ runs
                                           │ 0..*
                                           ▼
                                ┌─────────────────────┐
                                │    Pod              │
                                │  - name             │
                                │  - namespace        │
                                │  - status           │
                                └─────────────────────┘

┌─────────────────────┐         ┌─────────────────────┐
│  Ingress Resource   │         │    Service          │
│  - host             │ routes  │  - name             │
│  - path             ├────────►│  - port             │
│  - service_name     │   to    │  - selector         │
└─────────────────────┘         └─────────────────────┘
```

---

## 8. Summary

This data model defines:

1. **Cluster Configuration**: Profile-based cluster setup with driver, CPU, memory, and disk allocation
2. **State Management**: Comprehensive state machines for cluster and addon lifecycle
3. **Resource Allocation**: Validated CPU/memory/disk allocation with workload profiles
4. **Addon Management**: Core addons (ingress, metrics-server, dashboard) with dependency tracking
5. **Network Configuration**: IP addressing, ingress routing, and service exposure methods
6. **Error Handling**: Common error states and recovery procedures
7. **Persistence**: Configuration storage and profile management

All entities include validation rules, state transitions, and relationships to ensure reliable cluster operations.

---

**Document Owner**: DevOps/Infrastructure Team
**Last Updated**: 2025-12-30
**Next Review**: 2025-01-15
