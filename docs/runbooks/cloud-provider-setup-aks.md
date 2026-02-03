# Azure AKS Setup Runbook

This runbook provides step-by-step instructions for setting up Azure Kubernetes Service (AKS) for the full-stack todo application.

## Prerequisites

- Azure account with active subscription
- Azure CLI installed and configured
- kubectl installed (v1.28+)
- Helm installed (v3.13+)

## Step 1: Login to Azure

```bash
# Login to Azure
az login

# Set your subscription (if you have multiple)
az account set --subscription "Your Subscription Name"

# Verify
az account show
```

## Step 2: Create Resource Group

```bash
# Create resource group
az group create \
  --name todo-rg \
  --location eastus

# Verify
az group show --name todo-rg
```

## Step 3: Create AKS Cluster

```bash
# Create AKS cluster with managed identity
az aks create \
  --resource-group todo-rg \
  --name todo-cluster \
  --node-count 2 \
  --node-vm-size Standard_B2s \
  --enable-managed-identity \
  --generate-ssh-keys \
  --network-plugin azure \
  --enable-addons monitoring

# Get credentials
az aks get-credentials --resource-group todo-rg --name todo-cluster

# Verify
kubectl get nodes
```

## Step 4: Create Azure Container Registry (ACR)

```bash
# Create ACR
az acr create \
  --resource-group todo-rg \
  --name todoregistry$(date +%s) \
  --sku Basic

# Store the registry name
export ACR_NAME=$(az acr list --resource-group todo-rg --query "[0].name" -o tsv)

# Attach ACR to AKS (enables seamless pulls without secrets)
az aks update \
  --resource-group todo-rg \
  --name todo-cluster \
  --attach-acr $ACR_NAME

# Login to ACR
az acr login --name $ACR_NAME
```

## Step 5: Build and Push Images

```bash
# Set registry URL
export ACR_URL=$ACR_NAME.azurecr.io

# Build and push backend
cd backend
az acr build --registry $ACR_NAME --image todo-backend:latest .
cd ..

# Build and push frontend
cd frontend
az acr build --registry $ACR_NAME --image todo-frontend:latest .
cd ..
```

Or with Docker:

```bash
docker build -t $ACR_URL/todo-backend:latest ./backend
docker build -t $ACR_URL/todo-frontend:latest ./frontend
docker push $ACR_URL/todo-backend:latest
docker push $ACR_URL/todo-frontend:latest
```

## Step 6: Create Kubernetes Secrets

```bash
# Create namespace
kubectl create namespace todo-app

# Application secrets
kubectl create secret generic todo-backend-secret \
  --namespace todo-app \
  --from-literal=DATABASE_URL='postgresql://user:pass@host.neon.tech/dbname?sslmode=require' \
  --from-literal=BETTER_AUTH_SECRET='your-32-char-secret' \
  --from-literal=OPENAI_API_KEY='sk-your-openai-key'

kubectl create secret generic todo-frontend-secret \
  --namespace todo-app \
  --from-literal=BETTER_AUTH_SECRET='your-32-char-secret' \
  --from-literal=NEXT_PUBLIC_OPENAI_DOMAIN_KEY='your-domain-key'
```

## Step 7: Install Prerequisites

### NGINX Ingress Controller

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Wait for LoadBalancer IP
kubectl get svc -n ingress-nginx ingress-nginx-controller --watch
```

### cert-manager

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Wait for pods
kubectl wait --for=condition=Ready pods -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=120s
```

## Step 8: Deploy Application

```bash
# Apply ClusterIssuers
kubectl apply -f k8s/cert-manager/cluster-issuer-letsencrypt-staging.yaml
kubectl apply -f k8s/cert-manager/cluster-issuer-letsencrypt-prod.yaml

# Deploy backend
helm upgrade --install todo-backend ./charts/backend \
  --namespace todo-app \
  -f charts/backend/values-aks.yaml \
  --set image.repository=$ACR_URL/todo-backend

# Deploy frontend
helm upgrade --install todo-frontend ./charts/frontend \
  --namespace todo-app \
  -f charts/frontend/values-aks.yaml \
  --set image.repository=$ACR_URL/todo-frontend
```

## Step 9: Configure DNS

```bash
# Get LoadBalancer IP
INGRESS_IP=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "Configure DNS A record: todo.yourdomain.com -> $INGRESS_IP"

# Or use nip.io for testing
echo "Access at: http://todo.$INGRESS_IP.nip.io"
```

## Step 10: Enable Monitoring (Optional)

```bash
# Container Insights is enabled via --enable-addons monitoring

# Access Azure Monitor
az aks show --resource-group todo-rg --name todo-cluster --query "addonProfiles.omsagent"
```

## Troubleshooting

### ACR Pull Failures

```bash
# Verify ACR attachment
az aks check-acr --resource-group todo-rg --name todo-cluster --acr $ACR_NAME

# Re-attach if needed
az aks update --resource-group todo-rg --name todo-cluster --attach-acr $ACR_NAME
```

### Node Pool Issues

```bash
# Check node status
kubectl describe nodes

# Scale node pool
az aks scale --resource-group todo-rg --name todo-cluster --node-count 3
```

### View Cluster Logs

```bash
# Get diagnostic settings
az monitor diagnostic-settings list --resource /subscriptions/.../resourceGroups/todo-rg/providers/Microsoft.ContainerService/managedClusters/todo-cluster
```

## Cost Management

Azure AKS pricing:
- Control plane: Free
- Nodes: Pay for VM compute
- LoadBalancer: ~$18/month
- ACR Basic: ~$5/month

To minimize costs:
- Use B-series VMs for non-production
- Stop cluster when not in use: `az aks stop --resource-group todo-rg --name todo-cluster`
- Delete unused resources

## Cleanup

```bash
# Delete entire resource group (includes all resources)
az group delete --name todo-rg --yes --no-wait
```
