# Todo Frontend Helm Chart

Production-ready Helm chart for deploying the Next.js Todo Frontend application to Kubernetes.

## Quick Start

### Prerequisites
- Kubernetes 1.19+
- Helm 3.0+
- kubectl configured
- Docker images built and loaded (for Minikube)

### Installation

```bash
# Install with default values (2 replicas, ClusterIP service)
helm install todo-app ./charts/frontend

# Install with ingress enabled
helm install todo-app ./charts/frontend --set ingress.enabled=true

# Install with custom values file
helm install todo-app ./charts/frontend -f custom-values.yaml
```

### For Minikube Development

```bash
# 1. Build and load Docker image
docker build -t todo-frontend:latest ./frontend
minikube image load todo-frontend:latest

# 2. Install chart
helm install todo-app ./charts/frontend

# 3. Access via port-forward
kubectl port-forward svc/todo-app-todo-frontend 3000:3000

# 4. Or enable ingress
minikube addons enable ingress
helm upgrade todo-app ./charts/frontend --set ingress.enabled=true
minikube tunnel  # In separate terminal
# Add to /etc/hosts: 127.0.0.1 todo.local
# Access at: http://todo.local/
```

## Configuration

### Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of frontend pods | `2` |
| `image.repository` | Docker image repository | `todo-frontend` |
| `image.tag` | Docker image tag | `latest` |
| `image.pullPolicy` | Image pull policy | `Never` |
| `service.type` | Kubernetes service type | `ClusterIP` |
| `service.port` | Service port | `3000` |
| `ingress.enabled` | Enable ingress | `false` |
| `ingress.hosts[0].host` | Ingress hostname | `todo.local` |
| `resources.limits.cpu` | CPU limit | `500m` |
| `resources.limits.memory` | Memory limit | `256Mi` |
| `resources.requests.cpu` | CPU request | `100m` |
| `resources.requests.memory` | Memory request | `128Mi` |

### Environment Variables

Configure via `values.yaml`:

```yaml
config:
  NEXT_PUBLIC_API_URL: "http://todo-backend:8000"
  NODE_ENV: "production"

secrets:
  BETTER_AUTH_SECRET: "your-32-char-secret"
  NEXT_PUBLIC_OPENAI_DOMAIN_KEY: "your-key"
```

### Custom Values Example

```bash
# Set specific values
helm install todo-app ./charts/frontend \
  --set replicaCount=3 \
  --set image.tag=v1.2.3 \
  --set ingress.enabled=true
```

## Upgrading

```bash
# Upgrade with new values
helm upgrade todo-app ./charts/frontend

# Upgrade with different image tag
helm upgrade todo-app ./charts/frontend --set image.tag=v1.1.0

# Upgrade with custom values file
helm upgrade todo-app ./charts/frontend -f custom-values.yaml
```

## Rollback

```bash
# View release history
helm history todo-app

# Rollback to previous version
helm rollback todo-app

# Rollback to specific revision
helm rollback todo-app 2
```

## Uninstalling

```bash
helm uninstall todo-app
```

## Validation

```bash
# Lint the chart
helm lint ./charts/frontend

# Test rendering templates
helm template todo-app ./charts/frontend

# Dry run installation
helm install todo-app ./charts/frontend --dry-run --debug
```

## Verification

```bash
# Check deployment status
kubectl get deployments
kubectl get pods
kubectl get services

# View pod logs
kubectl logs -f -l app.kubernetes.io/name=todo-frontend

# Check health probes
kubectl describe pod <pod-name>

# Port forward for local access
kubectl port-forward svc/todo-app-todo-frontend 3000:3000
```

## Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl get pods
kubectl describe pod <pod-name>
kubectl logs <pod-name>

# Check image availability
kubectl get pods -o jsonpath='{.items[*].spec.containers[*].image}'
```

### Ingress not working

```bash
# Check ingress status
kubectl get ingress
kubectl describe ingress todo-app-todo-frontend

# Verify ingress controller
kubectl get pods -n ingress-nginx

# Check /etc/hosts entry
cat /etc/hosts | grep todo.local
```

### ConfigMap/Secret issues

```bash
# View ConfigMap
kubectl get configmap
kubectl describe configmap todo-app-todo-frontend-config

# View Secret (base64 encoded)
kubectl get secret
kubectl describe secret todo-app-todo-frontend-secret
```

## Health Checks

The chart includes three types of probes:

- **Startup Probe**: Checks if app has started (max 5 minutes)
- **Liveness Probe**: Restarts pod if unhealthy
- **Readiness Probe**: Removes from service if not ready

All probes use `GET /` on port 3000.

## Resource Management

Default resource limits prevent pods from consuming excessive resources:

```yaml
resources:
  limits:
    cpu: 500m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

Adjust based on your workload requirements.

## Security

- Service account created per release
- Pod security contexts can be enabled
- Secrets are base64 encoded
- No privilege escalation by default

## Support

For issues or questions:
- Check pod logs: `kubectl logs <pod-name>`
- Describe resources: `kubectl describe <resource> <name>`
- View Helm values: `helm get values todo-app`
- Review manifest: `helm get manifest todo-app`

## Chart Version

- Chart Version: 1.0.0
- App Version: 1.0.0
- Kubernetes: 1.19+
- Helm: 3.0+
