# Secrets Management Guide

This guide documents all environment variables and secrets required for the todo application.

---

## Required Secrets

### Backend Service

| Secret Name | Key | Description | Example |
|-------------|-----|-------------|---------|
| `todo-backend-secret` | `DATABASE_URL` | Neon PostgreSQL connection string | `postgresql://user:pass@host.neon.tech/db?sslmode=require` |
| `todo-backend-secret` | `BETTER_AUTH_SECRET` | JWT signing key (32+ chars) | `a-very-long-secret-key-at-least-32-chars` |
| `todo-backend-secret` | `OPENAI_API_KEY` | OpenAI API key | `sk-proj-...` |

### Frontend Service

| Secret Name | Key | Description | Example |
|-------------|-----|-------------|---------|
| `todo-frontend-secret` | `BETTER_AUTH_SECRET` | JWT signing key (must match backend) | Same as backend |
| `todo-frontend-secret` | `NEXT_PUBLIC_OPENAI_DOMAIN_KEY` | OpenAI domain key | `your-domain-key` |

### Container Registry

| Secret Name | Description | Used By |
|-------------|-------------|---------|
| `ocir-secret` | Oracle OCIR credentials | OKE deployments |
| `acr-secret` | Azure ACR credentials | AKS deployments (if not using attached ACR) |
| `regcred` | Docker Hub credentials | Multi-cloud deployments |

---

## Creating Secrets

### Backend Secrets

```bash
# Create backend secret
kubectl create secret generic todo-backend-secret \
  --namespace todo-app \
  --from-literal=DATABASE_URL='postgresql://user:password@host.neon.tech/dbname?sslmode=require' \
  --from-literal=BETTER_AUTH_SECRET='your-32-character-or-longer-secret-key' \
  --from-literal=OPENAI_API_KEY='sk-proj-your-openai-api-key'
```

### Frontend Secrets

```bash
# Create frontend secret
kubectl create secret generic todo-frontend-secret \
  --namespace todo-app \
  --from-literal=BETTER_AUTH_SECRET='your-32-character-or-longer-secret-key' \
  --from-literal=NEXT_PUBLIC_OPENAI_DOMAIN_KEY='your-openai-domain-key'
```

### Container Registry Secrets

```bash
# Docker Hub
kubectl create secret docker-registry regcred \
  --namespace todo-app \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=<username> \
  --docker-password=<password-or-token>

# Oracle OCIR
kubectl create secret docker-registry ocir-secret \
  --namespace todo-app \
  --docker-server=<region>.ocir.io \
  --docker-username='<tenancy>/<username>' \
  --docker-password='<auth-token>'

# Azure ACR
kubectl create secret docker-registry acr-secret \
  --namespace todo-app \
  --docker-server=<registry>.azurecr.io \
  --docker-username=<username> \
  --docker-password='<password>'
```

---

## Updating Secrets

### Update Single Key

```bash
# Delete and recreate (simplest method)
kubectl delete secret todo-backend-secret -n todo-app
kubectl create secret generic todo-backend-secret \
  --namespace todo-app \
  --from-literal=DATABASE_URL='<new-value>' \
  --from-literal=BETTER_AUTH_SECRET='<existing-value>' \
  --from-literal=OPENAI_API_KEY='<existing-value>'

# Restart pods to pick up new secrets
kubectl rollout restart deployment todo-backend -n todo-app
```

### Update via Patch

```bash
# Encode new value
NEW_VALUE=$(echo -n 'new-value' | base64)

# Patch secret
kubectl patch secret todo-backend-secret -n todo-app \
  -p '{"data":{"DATABASE_URL":"'$NEW_VALUE'"}}'
```

---

## GitHub Actions Secrets

Required secrets in GitHub repository settings:

| Secret Name | Description |
|-------------|-------------|
| `REGISTRY_USERNAME` | Container registry username |
| `REGISTRY_PASSWORD` | Container registry password/token |
| `KUBE_CONFIG` | Base64-encoded kubeconfig |
| `DATABASE_URL` | Neon PostgreSQL connection string |
| `BETTER_AUTH_SECRET` | JWT signing key |
| `OPENAI_API_KEY` | OpenAI API key |
| `NEXT_PUBLIC_OPENAI_DOMAIN_KEY` | OpenAI domain key |
| `SLACK_WEBHOOK_URL` | (Optional) Slack notifications |

### Encoding Kubeconfig

```bash
# Get kubeconfig and encode
cat ~/.kube/config | base64 -w 0

# For OKE
cat ~/.kube/oke-config | base64 -w 0
```

---

## Viewing Secrets

### List Secrets

```bash
kubectl get secrets -n todo-app
```

### View Secret Contents

```bash
# View secret metadata
kubectl describe secret todo-backend-secret -n todo-app

# Decode specific key
kubectl get secret todo-backend-secret -n todo-app \
  -o jsonpath='{.data.DATABASE_URL}' | base64 -d
```

---

## Security Best Practices

### DO

- [ ] Use Kubernetes secrets, never hardcode
- [ ] Use different secrets for each environment
- [ ] Rotate secrets regularly (every 90 days)
- [ ] Use RBAC to limit secret access
- [ ] Encrypt secrets at rest (enable cluster-level encryption)

### DON'T

- [ ] Commit secrets to git
- [ ] Log secret values
- [ ] Share secrets via insecure channels
- [ ] Use weak secrets (less than 32 characters)

### Secret Rotation Checklist

1. Generate new secret value
2. Create new Kubernetes secret (or update existing)
3. Restart pods to pick up new value
4. Verify application works with new secret
5. Revoke/delete old secret value where applicable

---

## Generating Secrets

### Random String (JWT Secret)

```bash
# Generate 32-character random string
openssl rand -base64 32

# Or using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Database URL

Format: `postgresql://USER:PASSWORD@HOST:PORT/DATABASE?sslmode=require`

Get from Neon dashboard: Connection Details → Connection string

---

## Troubleshooting

### Secret Not Found

```bash
# Check secret exists in correct namespace
kubectl get secrets -n todo-app | grep todo-backend

# Check secret is referenced correctly in deployment
kubectl get deployment todo-backend -n todo-app -o yaml | grep -A 5 envFrom
```

### Secret Value Incorrect

```bash
# Decode and verify value
kubectl get secret todo-backend-secret -n todo-app \
  -o jsonpath='{.data.DATABASE_URL}' | base64 -d

# Test database connection manually
kubectl exec -it <pod> -n todo-app -- python -c "
import os
print(os.environ.get('DATABASE_URL', 'NOT SET'))
"
```

### Pods Not Getting Updated Secrets

```bash
# Secrets are NOT automatically reloaded - must restart pods
kubectl rollout restart deployment todo-backend -n todo-app
```

---

## Quick Reference

| Action | Command |
|--------|---------|
| List secrets | `kubectl get secrets -n todo-app` |
| View secret | `kubectl describe secret <name> -n todo-app` |
| Decode value | `kubectl get secret <name> -n todo-app -o jsonpath='{.data.<key>}' \| base64 -d` |
| Delete secret | `kubectl delete secret <name> -n todo-app` |
| Restart pods | `kubectl rollout restart deployment <name> -n todo-app` |
