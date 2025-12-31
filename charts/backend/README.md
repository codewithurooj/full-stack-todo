# Todo Backend Helm Chart

Production-ready Helm chart for deploying the FastAPI Todo Backend API to Kubernetes.

## Quick Start

### Prerequisites
- Kubernetes 1.19+
- Helm 3.0+
- kubectl configured
- Docker images built and loaded (for Minikube)
- PostgreSQL database (Neon serverless)

### Installation

```bash
# Install with default values (2 replicas, ClusterIP service)
helm install todo-api ./charts/backend

# Install with custom database URL
helm install todo-api ./charts/backend \
  --set secrets.DATABASE_URL="postgresql://user:pass@host/db"

# Install with custom values file
helm install todo-api ./charts/backend -f custom-values.yaml
```

### For Minikube Development

```bash
# 1. Build and load Docker image
docker build -t todo-backend:latest ./backend
minikube image load todo-backend:latest

# 2. Install chart
helm install todo-api ./charts/backend

# 3. Access via port-forward
kubectl port-forward svc/todo-api-todo-backend 8000:8000

# 4. Test health endpoint
curl http://localhost:8000/health
```

## Configuration

### Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of backend pods | `2` |
| `image.repository` | Docker image repository | `todo-backend` |
| `image.tag` | Docker image tag | `latest` |
| `image.pullPolicy` | Image pull policy | `Never` |
| `service.type` | Kubernetes service type | `ClusterIP` |
| `service.port` | Service port | `8000` |
| `resources.limits.cpu` | CPU limit | `1000m` |
| `resources.limits.memory` | Memory limit | `512Mi` |
| `resources.requests.cpu` | CPU request | `200m` |
| `resources.requests.memory` | Memory request | `256Mi` |

### Environment Variables

Configure via `values.yaml`:

```yaml
config:
  ENVIRONMENT: "production"
  LOG_LEVEL: "info"

secrets:
  DATABASE_URL: "postgresql://user:pass@neon.host/dbname"
  BETTER_AUTH_SECRET: "your-32-char-secret"
  OPENAI_API_KEY: "sk-your-api-key"
```

### Custom Values Example

```bash
# Set specific values
helm install todo-api ./charts/backend \
  --set replicaCount=3 \
  --set image.tag=v1.2.3 \
  --set resources.limits.memory=1Gi
```

## Upgrading

```bash
# Upgrade with new values
helm upgrade todo-api ./charts/backend

# Upgrade with different image tag
helm upgrade todo-api ./charts/backend --set image.tag=v1.1.0

# Upgrade with custom values file
helm upgrade todo-api ./charts/backend -f custom-values.yaml
```

## Rollback

```bash
# View release history
helm history todo-api

# Rollback to previous version
helm rollback todo-api

# Rollback to specific revision
helm rollback todo-api 2
```

## Uninstalling

```bash
helm uninstall todo-api
```

## Validation

```bash
# Lint the chart
helm lint ./charts/backend

# Test rendering templates
helm template todo-api ./charts/backend

# Dry run installation
helm install todo-api ./charts/backend --dry-run --debug
```

## Verification

```bash
# Check deployment status
kubectl get deployments
kubectl get pods
kubectl get services

# View pod logs
kubectl logs -f -l app.kubernetes.io/name=todo-backend

# Check health endpoint
kubectl exec -it $(kubectl get pods -l app.kubernetes.io/name=todo-backend -o jsonpath='{.items[0].metadata.name}') -- curl localhost:8000/health

# Port forward for local access
kubectl port-forward svc/todo-api-todo-backend 8000:8000
curl http://localhost:8000/health
```

## API Endpoints

Once deployed, the backend exposes:

- `GET /health` - Health check endpoint
- `GET /api/{user_id}/tasks` - List tasks
- `POST /api/{user_id}/tasks` - Create task
- `GET /api/{user_id}/tasks/{id}` - Get task
- `PUT /api/{user_id}/tasks/{id}` - Update task
- `DELETE /api/{user_id}/tasks/{id}` - Delete task
- `PATCH /api/{user_id}/tasks/{id}/complete` - Toggle completion

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

### Database connection issues

```bash
# Check secrets
kubectl get secret todo-api-todo-backend-secret
kubectl get secret todo-api-todo-backend-secret -o jsonpath='{.data.DATABASE_URL}' | base64 -d

# Check logs for connection errors
kubectl logs -f -l app.kubernetes.io/name=todo-backend | grep -i database
```

### Health check failures

```bash
# Test health endpoint directly
kubectl exec -it <pod-name> -- curl localhost:8000/health

# Check probe configuration
kubectl describe pod <pod-name> | grep -A 5 Liveness
kubectl describe pod <pod-name> | grep -A 5 Readiness
```

## Health Checks

The chart includes three types of probes:

- **Startup Probe**: Checks if app has started (max 5 minutes)
- **Liveness Probe**: Restarts pod if unhealthy
- **Readiness Probe**: Removes from service if not ready

All probes use `GET /health` on port 8000.

## Resource Management

Default resource limits:

```yaml
resources:
  limits:
    cpu: 1000m
    memory: 512Mi
  requests:
    cpu: 200m
    memory: 256Mi
```

Adjust based on your workload and database query complexity.

## Security

- Service account created per release
- Pod security contexts can be enabled
- Secrets are base64 encoded (use external secret manager in production)
- No privilege escalation by default
- Database credentials stored as Kubernetes Secrets

## Database

This chart requires an external PostgreSQL database (Neon serverless recommended).

**Important**: Update `secrets.DATABASE_URL` in values.yaml with your actual database connection string:

```yaml
secrets:
  DATABASE_URL: "postgresql://username:password@host.neon.tech/database_name?sslmode=require"
```

## Support

For issues or questions:
- Check pod logs: `kubectl logs <pod-name>`
- Describe resources: `kubectl describe <resource> <name>`
- View Helm values: `helm get values todo-api`
- Review manifest: `helm get manifest todo-api`
- Test health: `curl http://localhost:8000/health`

## Chart Version

- Chart Version: 1.0.0
- App Version: 1.0.0
- Kubernetes: 1.19+
- Helm: 3.0+
- FastAPI: 0.100+
- Python: 3.13+
