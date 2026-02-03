# Oracle Cloud OKE Setup Runbook

This runbook provides step-by-step instructions for setting up Oracle Cloud Infrastructure (OCI) Kubernetes Engine (OKE) for the full-stack todo application.

## Prerequisites

- Oracle Cloud account with access to OKE
- OCI CLI installed and configured
- kubectl installed (v1.28+)
- Helm installed (v3.13+)

## Step 1: Create OKE Cluster

### Via Console (Recommended for First-Time Setup)

1. Log in to the Oracle Cloud Console: https://cloud.oracle.com
2. Navigate to: **Developer Services > Kubernetes Clusters (OKE)**
3. Click **Create Cluster**
4. Select **Quick Create**
5. Configure:
   - **Name**: `todo-cluster`
   - **Kubernetes Version**: `1.28.x` or latest
   - **Shape**: `VM.Standard.A1.Flex` (ARM - Always Free eligible)
   - **Number of nodes**: `2`
   - **OCPUs per node**: `2`
   - **Memory per node**: `12 GB`
6. Click **Create**
7. Wait for cluster to become Active (10-15 minutes)

### Via OCI CLI

```bash
# Set variables
export COMPARTMENT_ID="ocid1.compartment.oc1..xxx"
export VCN_ID="ocid1.vcn.oc1.xxx"

# Create cluster
oci ce cluster create \
  --compartment-id $COMPARTMENT_ID \
  --name todo-cluster \
  --kubernetes-version v1.28.0 \
  --vcn-id $VCN_ID
```

## Step 2: Configure kubectl Access

```bash
# Download kubeconfig from OCI Console
# Navigate to: Cluster Details > Access Cluster > Local Access

# Set KUBECONFIG environment variable
export KUBECONFIG=~/.kube/oke-config

# Verify connection
kubectl get nodes
kubectl cluster-info
```

## Step 3: Set Up Oracle Container Registry (OCIR)

### Get Tenancy Namespace

```bash
oci os ns get
# Output: {"data": "your-namespace"}
export TENANCY_NAMESPACE=your-namespace
export REGION=us-ashburn-1  # Change to your region
```

### Create Auth Token

1. Navigate to: **Identity > Users > Your User**
2. Click **Auth Tokens**
3. Click **Generate Token**
4. Copy the token (shown only once)

### Log In to OCIR

```bash
docker login $REGION.ocir.io
# Username: <tenancy-namespace>/<username>
# Password: <auth-token>
```

### Build and Push Images

```bash
export OCIR_REPO=$REGION.ocir.io/$TENANCY_NAMESPACE

# Build multi-arch images for ARM support
docker buildx create --name multiarch --use
docker buildx build --platform linux/amd64,linux/arm64 \
  -t $OCIR_REPO/todo-backend:latest --push ./backend
docker buildx build --platform linux/amd64,linux/arm64 \
  -t $OCIR_REPO/todo-frontend:latest --push ./frontend
```

## Step 4: Create Kubernetes Secrets

### Registry Pull Secret

```bash
kubectl create namespace todo-app

kubectl create secret docker-registry ocir-secret \
  --namespace todo-app \
  --docker-server=$REGION.ocir.io \
  --docker-username="$TENANCY_NAMESPACE/<username>" \
  --docker-password="<auth-token>" \
  --docker-email="your-email@example.com"
```

### Application Secrets

```bash
kubectl create secret generic todo-backend-secret \
  --namespace todo-app \
  --from-literal=DATABASE_URL='postgresql://user:pass@host.neon.tech/dbname?sslmode=require' \
  --from-literal=BETTER_AUTH_SECRET='your-32-char-secret' \
  --from-literal=OPENAI_API_KEY='sk-your-openai-key'
```

## Step 5: Install Prerequisites

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

## Step 6: Deploy Application

```bash
# Apply ClusterIssuers
kubectl apply -f k8s/cert-manager/cluster-issuer-letsencrypt-staging.yaml
kubectl apply -f k8s/cert-manager/cluster-issuer-letsencrypt-prod.yaml

# Deploy backend
helm upgrade --install todo-backend ./charts/backend \
  --namespace todo-app \
  -f charts/backend/values-oke.yaml \
  --set image.repository=$OCIR_REPO/todo-backend

# Deploy frontend
helm upgrade --install todo-frontend ./charts/frontend \
  --namespace todo-app \
  -f charts/frontend/values-oke.yaml \
  --set image.repository=$OCIR_REPO/todo-frontend
```

## Step 7: Configure DNS

```bash
# Get LoadBalancer IP
INGRESS_IP=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "Configure DNS A record: todo.yourdomain.com -> $INGRESS_IP"

# Or use nip.io for testing
echo "Access at: http://todo.$INGRESS_IP.nip.io"
```

## Troubleshooting

### Pods in ImagePullBackOff

```bash
# Check secret exists
kubectl get secret ocir-secret -n todo-app

# Verify image path
kubectl describe pod <pod-name> -n todo-app | grep -A 5 "Container"
```

### ARM vs AMD64 Issues

Oracle OKE free tier uses ARM (A1) instances. Ensure multi-arch builds:

```bash
# Verify image architecture
docker manifest inspect $OCIR_REPO/todo-backend:latest
```

### LoadBalancer Pending

Oracle OKE creates OCI Load Balancers. Check:

```bash
# View service events
kubectl describe svc ingress-nginx-controller -n ingress-nginx
```

## Cost Optimization

Oracle Cloud Always Free includes:
- Up to 4 ARM-based A1 OCPUs and 24 GB memory
- 200 GB total block storage
- 10 TB outbound data transfer/month

To stay within free limits:
- Use 2 nodes with 2 OCPUs and 12 GB each
- Use ARM (A1.Flex) shape only
- Clean up unused load balancers
