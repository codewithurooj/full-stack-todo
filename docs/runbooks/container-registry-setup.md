# Container Registry Setup Guide

This guide covers setting up container registries for the todo application on different cloud providers.

## Table of Contents

1. [Oracle Container Registry (OCIR)](#oracle-container-registry-ocir)
2. [Azure Container Registry (ACR)](#azure-container-registry-acr)
3. [Google Artifact Registry (GAR)](#google-artifact-registry-gar)
4. [Docker Hub](#docker-hub)
5. [Image Tagging Strategy](#image-tagging-strategy)
6. [Image Retention Policy](#image-retention-policy)

---

## Oracle Container Registry (OCIR)

### Prerequisites
- Oracle Cloud account with OKE cluster
- OCI CLI installed and configured

### Setup Steps

```bash
# 1. Get your tenancy namespace
oci os ns get

# 2. Generate an auth token (OCI Console)
# Identity → Users → Your User → Auth Tokens → Generate Token
# Save the token - it won't be shown again!

# 3. Login to OCIR
docker login <region>.ocir.io
# Username: <tenancy-namespace>/<username>
# Password: <auth-token>

# Example for Ashburn region:
docker login us-ashburn-1.ocir.io
# Username: mytenancy/oracleidentitycloudservice/john@example.com
# Password: <auth-token>
```

### Push Images

```bash
export REGION=us-ashburn-1
export TENANCY=mytenancy
export OCIR_REPO=$REGION.ocir.io/$TENANCY

# Tag images
docker tag todo-backend:latest $OCIR_REPO/todo-backend:latest
docker tag todo-frontend:latest $OCIR_REPO/todo-frontend:latest

# Push images
docker push $OCIR_REPO/todo-backend:latest
docker push $OCIR_REPO/todo-frontend:latest
```

### Create Kubernetes Pull Secret

```bash
kubectl create secret docker-registry ocir-secret \
  --namespace todo-app \
  --docker-server=$REGION.ocir.io \
  --docker-username="$TENANCY/oracleidentitycloudservice/<username>" \
  --docker-password="<auth-token>" \
  --docker-email=your-email@example.com
```

### Repository Naming
- Public: `<region>.ocir.io/<tenancy>/<repo-name>`
- Private (default): Same format, requires pull secret

---

## Azure Container Registry (ACR)

### Prerequisites
- Azure subscription
- Azure CLI installed

### Setup Steps

```bash
# 1. Create resource group (if not exists)
az group create --name todo-rg --location eastus

# 2. Create ACR
az acr create \
  --resource-group todo-rg \
  --name todoregistry \
  --sku Basic \
  --admin-enabled true

# 3. Get credentials
az acr credential show --name todoregistry

# 4. Login to ACR
az acr login --name todoregistry
```

### Attach ACR to AKS (Recommended)

```bash
# This allows AKS to pull images without imagePullSecrets
az aks update \
  --resource-group todo-rg \
  --name todo-cluster \
  --attach-acr todoregistry
```

### Push Images

```bash
export ACR_REPO=todoregistry.azurecr.io

# Tag images
docker tag todo-backend:latest $ACR_REPO/todo-backend:latest
docker tag todo-frontend:latest $ACR_REPO/todo-frontend:latest

# Push images
docker push $ACR_REPO/todo-backend:latest
docker push $ACR_REPO/todo-frontend:latest
```

### Create Kubernetes Pull Secret (if not using attached ACR)

```bash
kubectl create secret docker-registry acr-secret \
  --namespace todo-app \
  --docker-server=todoregistry.azurecr.io \
  --docker-username=todoregistry \
  --docker-password="<password-from-acr-credentials>"
```

---

## Google Artifact Registry (GAR)

### Prerequisites
- Google Cloud project
- gcloud CLI installed

### Setup Steps

```bash
# 1. Enable Artifact Registry API
gcloud services enable artifactregistry.googleapis.com

# 2. Create repository
gcloud artifacts repositories create todo-repo \
  --repository-format=docker \
  --location=us-central1 \
  --description="Todo application container images"

# 3. Configure Docker authentication
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### Push Images

```bash
export PROJECT_ID=$(gcloud config get-value project)
export GAR_REPO=us-central1-docker.pkg.dev/$PROJECT_ID/todo-repo

# Tag images
docker tag todo-backend:latest $GAR_REPO/todo-backend:latest
docker tag todo-frontend:latest $GAR_REPO/todo-frontend:latest

# Push images
docker push $GAR_REPO/todo-backend:latest
docker push $GAR_REPO/todo-frontend:latest
```

### GKE Access

GKE nodes have implicit access to Artifact Registry in the same project. For cross-project access, configure Workload Identity.

---

## Docker Hub

### Setup Steps

```bash
# 1. Login to Docker Hub
docker login
# Enter your Docker Hub username and password/token

# 2. Create repository (via Docker Hub web interface or push creates it)
```

### Push Images

```bash
export DOCKERHUB_USER=yourusername

# Tag images
docker tag todo-backend:latest $DOCKERHUB_USER/todo-backend:latest
docker tag todo-frontend:latest $DOCKERHUB_USER/todo-frontend:latest

# Push images
docker push $DOCKERHUB_USER/todo-backend:latest
docker push $DOCKERHUB_USER/todo-frontend:latest
```

### Create Kubernetes Pull Secret

```bash
kubectl create secret docker-registry regcred \
  --namespace todo-app \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=$DOCKERHUB_USER \
  --docker-password="<docker-hub-token>" \
  --docker-email=your-email@example.com
```

### Rate Limits
- Anonymous: 100 pulls/6 hours
- Authenticated: 200 pulls/6 hours
- Pro/Team: Unlimited

---

## Image Tagging Strategy

### Tag Format

| Tag Type | Format | Example | Use Case |
|----------|--------|---------|----------|
| SHA | `sha-<short-hash>` | `sha-a1b2c3d` | Every build |
| Latest | `latest` | `latest` | Current main branch |
| Semver | `v<major>.<minor>.<patch>` | `v1.2.3` | Releases |
| Branch | `<branch-name>` | `feature-auth` | Feature branches |

### CI/CD Tagging

```yaml
# In GitHub Actions
tags: |
  ${{ env.REGISTRY }}/${{ env.IMAGE }}:sha-${{ github.sha }}
  ${{ env.REGISTRY }}/${{ env.IMAGE }}:latest
  ${{ env.REGISTRY }}/${{ env.IMAGE }}:${{ github.ref_name }}
```

### Recommended Strategy

1. **Development**: `sha-<hash>` for every commit
2. **Staging**: `latest` or `sha-<hash>`
3. **Production**: `v<semver>` for releases

---

## Image Retention Policy

### Recommended Retention

| Image Type | Retention Period |
|------------|------------------|
| `sha-*` tags | 30 days |
| `latest` | Always keep |
| `v*` (semver) | Forever |
| Untagged | 7 days |

### OCIR Retention

```bash
# Oracle doesn't have built-in retention policies
# Use a scheduled cleanup script:

# List images older than 30 days
oci artifacts container image list \
  --compartment-id <compartment-ocid> \
  --repository-name todo-backend \
  --query "data[?\"time-created\"<'$(date -d '-30 days' +%Y-%m-%d)'].\"image-id\""
```

### ACR Retention

```bash
# Create retention policy
az acr config retention update \
  --registry todoregistry \
  --status enabled \
  --days 30 \
  --type UntaggedManifests
```

### GAR Retention

```bash
# Set cleanup policy
gcloud artifacts repositories set-cleanup-policies todo-repo \
  --location=us-central1 \
  --policy=cleanup-policy.json

# cleanup-policy.json:
{
  "name": "delete-old-untagged",
  "action": {"type": "Delete"},
  "condition": {
    "olderThan": "30d",
    "tagState": "untagged"
  }
}
```

---

## Multi-Architecture Builds

For Oracle OKE ARM instances, build multi-arch images:

```bash
# Create buildx builder
docker buildx create --name multiarch --use

# Build and push multi-arch
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t $REGISTRY/todo-backend:latest \
  --push \
  ./backend
```

---

## Troubleshooting

### Image Pull Errors

```bash
# Check secret exists
kubectl get secrets -n todo-app | grep -E "(ocir|acr|regcred)"

# Describe secret
kubectl get secret <secret-name> -n todo-app -o yaml

# Test pull manually
kubectl run test-pull --image=$REGISTRY/todo-backend:latest \
  -n todo-app --rm -it --restart=Never -- echo "Pull successful"
```

### Authentication Issues

```bash
# Verify Docker login works
docker pull $REGISTRY/todo-backend:latest

# Regenerate secret
kubectl delete secret <secret-name> -n todo-app
# Then recreate with correct credentials
```

---

## Quick Reference

| Provider | Registry URL | Secret Name |
|----------|--------------|-------------|
| OCIR | `<region>.ocir.io/<tenancy>` | `ocir-secret` |
| ACR | `<name>.azurecr.io` | `acr-secret` or none (attached) |
| GAR | `<region>-docker.pkg.dev/<project>/<repo>` | None (Workload Identity) |
| Docker Hub | `docker.io` | `regcred` |
