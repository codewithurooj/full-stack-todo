# Google Cloud GKE Setup Runbook

This runbook provides step-by-step instructions for setting up Google Kubernetes Engine (GKE) for the full-stack todo application.

## Prerequisites

- Google Cloud account with billing enabled
- gcloud CLI installed and configured
- kubectl installed (v1.28+)
- Helm installed (v3.13+)

## Step 1: Login to Google Cloud

```bash
# Login to Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Verify
gcloud config get-value project

# Enable required APIs
gcloud services enable container.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

## Step 2: Create GKE Cluster

### Standard Cluster (Recommended)

```bash
# Create GKE cluster
gcloud container clusters create todo-cluster \
  --region us-central1 \
  --num-nodes 2 \
  --machine-type e2-small \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 5 \
  --enable-autorepair \
  --enable-autoupgrade

# Get credentials
gcloud container clusters get-credentials todo-cluster --region us-central1

# Verify
kubectl get nodes
```

### Autopilot Cluster (Serverless Option)

```bash
# Create Autopilot cluster (pay per pod, not per node)
gcloud container clusters create-auto todo-cluster \
  --region us-central1

# Get credentials
gcloud container clusters get-credentials todo-cluster --region us-central1
```

## Step 3: Set Up Artifact Registry

```bash
# Create repository
gcloud artifacts repositories create todo-repo \
  --repository-format docker \
  --location us-central1 \
  --description "Todo application container images"

# Configure Docker to use Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev

# Set registry URL
export GCR_REPO=us-central1-docker.pkg.dev/$(gcloud config get-value project)/todo-repo
```

## Step 4: Build and Push Images

### Using Cloud Build (Recommended)

```bash
# Build and push backend
cd backend
gcloud builds submit --tag $GCR_REPO/todo-backend:latest
cd ..

# Build and push frontend
cd frontend
gcloud builds submit --tag $GCR_REPO/todo-frontend:latest
cd ..
```

### Using Docker

```bash
# Build locally
docker build -t $GCR_REPO/todo-backend:latest ./backend
docker build -t $GCR_REPO/todo-frontend:latest ./frontend

# Push to Artifact Registry
docker push $GCR_REPO/todo-backend:latest
docker push $GCR_REPO/todo-frontend:latest
```

## Step 5: Create Kubernetes Secrets

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

GKE nodes have implicit access to Artifact Registry in the same project - no pull secrets needed.

## Step 6: Install Prerequisites

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

## Step 7: Deploy Application

```bash
# Apply ClusterIssuers
kubectl apply -f k8s/cert-manager/cluster-issuer-letsencrypt-staging.yaml
kubectl apply -f k8s/cert-manager/cluster-issuer-letsencrypt-prod.yaml

# Deploy backend
helm upgrade --install todo-backend ./charts/backend \
  --namespace todo-app \
  -f charts/backend/values-gke.yaml \
  --set image.repository=$GCR_REPO/todo-backend

# Deploy frontend
helm upgrade --install todo-frontend ./charts/frontend \
  --namespace todo-app \
  -f charts/frontend/values-gke.yaml \
  --set image.repository=$GCR_REPO/todo-frontend
```

## Step 8: Configure DNS

```bash
# Get LoadBalancer IP
INGRESS_IP=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "Configure DNS A record: todo.yourdomain.com -> $INGRESS_IP"

# Or use nip.io for testing
echo "Access at: http://todo.$INGRESS_IP.nip.io"

# Optional: Reserve static IP
gcloud compute addresses create todo-app-ip --global
```

## Step 9: Enable Monitoring (Optional)

```bash
# GKE has built-in Cloud Monitoring
# View metrics in Google Cloud Console > Kubernetes Engine > Clusters > todo-cluster

# Or install kube-prometheus-stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace
```

## Troubleshooting

### Image Pull Issues

```bash
# Verify Artifact Registry permissions
gcloud artifacts repositories get-iam-policy todo-repo --location us-central1

# Check node service account has access
gcloud projects get-iam-policy $(gcloud config get-value project) \
  --flatten="bindings[].members" \
  --filter="bindings.role:roles/artifactregistry.reader"
```

### Cluster Not Responding

```bash
# Check cluster status
gcloud container clusters describe todo-cluster --region us-central1

# Re-fetch credentials
gcloud container clusters get-credentials todo-cluster --region us-central1
```

### Workload Identity (Advanced)

```bash
# For more secure access to GCP services
gcloud container clusters update todo-cluster \
  --region us-central1 \
  --workload-pool=$(gcloud config get-value project).svc.id.goog
```

## Cost Management

GKE pricing:
- Standard cluster management: $0.10/hour per cluster
- Autopilot: Pay per pod resources
- Nodes: Pay for Compute Engine VMs

To minimize costs:
- Use e2-small instances for non-production
- Enable cluster autoscaling
- Use spot/preemptible VMs for non-critical workloads
- Consider Autopilot for variable workloads

Free tier includes:
- $300 credit for new users (90 days)
- 1 free zonal cluster (not Autopilot)

## Cleanup

```bash
# Delete cluster
gcloud container clusters delete todo-cluster --region us-central1 --quiet

# Delete Artifact Registry
gcloud artifacts repositories delete todo-repo --location us-central1 --quiet

# Delete any remaining resources
gcloud compute addresses delete todo-app-ip --global --quiet
```

## Additional Resources

- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [Artifact Registry Guide](https://cloud.google.com/artifact-registry/docs)
- [Cloud Build CI/CD](https://cloud.google.com/build/docs)
