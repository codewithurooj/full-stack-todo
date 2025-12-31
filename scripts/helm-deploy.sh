#!/bin/bash

# Helm Deployment Script for Todo Application
# Deploys frontend and backend to Minikube using Helm charts

set -e  # Exit on error

echo "=========================================="
echo "Todo App - Helm Deployment Script"
echo "=========================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check prerequisites
echo "Step 1: Checking prerequisites..."
command -v minikube >/dev/null 2>&1 || { print_error "minikube is not installed. Aborting."; exit 1; }
command -v kubectl >/dev/null 2>&1 || { print_error "kubectl is not installed. Aborting."; exit 1; }
command -v helm >/dev/null 2>&1 || { print_error "helm is not installed. Aborting."; exit 1; }
command -v docker >/dev/null 2>&1 || { print_error "docker is not installed. Aborting."; exit 1; }
print_success "All prerequisites installed"
echo ""

# Check Minikube status
echo "Step 2: Checking Minikube status..."
if minikube status | grep -q "Running"; then
    print_success "Minikube is running"
else
    print_warning "Minikube is not running. Starting Minikube..."
    minikube start --cpus=2 --memory=3072 --disk-size=20g
    print_success "Minikube started"
fi
echo ""

# Build and load Docker images
echo "Step 3: Building and loading Docker images..."
read -p "Do you want to rebuild Docker images? (y/n): " rebuild_images

if [ "$rebuild_images" = "y" ] || [ "$rebuild_images" = "Y" ]; then
    echo "Building frontend image..."
    docker build -t todo-frontend:latest ./frontend
    print_success "Frontend image built"

    echo "Building backend image..."
    docker build -t todo-backend:latest ./backend
    print_success "Backend image built"

    echo "Loading images into Minikube..."
    minikube image load todo-frontend:latest
    minikube image load todo-backend:latest
    print_success "Images loaded into Minikube"
else
    print_warning "Skipping image rebuild. Ensure images are already loaded."
fi
echo ""

# Deploy backend
echo "Step 4: Deploying backend..."
if helm list | grep -q "todo-api"; then
    print_warning "Backend already deployed. Upgrading..."
    helm upgrade todo-api ./charts/backend
    print_success "Backend upgraded"
else
    helm install todo-api ./charts/backend
    print_success "Backend deployed"
fi
echo ""

# Deploy frontend
echo "Step 5: Deploying frontend..."
if helm list | grep -q "todo-app"; then
    print_warning "Frontend already deployed. Upgrading..."
    helm upgrade todo-app ./charts/frontend
    print_success "Frontend upgraded"
else
    helm install todo-app ./charts/frontend
    print_success "Frontend deployed"
fi
echo ""

# Wait for pods to be ready
echo "Step 6: Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=todo-backend --timeout=120s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=todo-frontend --timeout=120s
print_success "All pods are ready"
echo ""

# Display deployment status
echo "=========================================="
echo "Deployment Status"
echo "=========================================="
kubectl get pods
echo ""
kubectl get services
echo ""

# Check if ingress should be enabled
read -p "Do you want to enable ingress for external access? (y/n): " enable_ingress

if [ "$enable_ingress" = "y" ] || [ "$enable_ingress" = "Y" ]; then
    echo ""
    echo "Step 7: Enabling ingress..."

    # Enable ingress addon
    if minikube addons list | grep -q "ingress: enabled"; then
        print_success "Ingress addon already enabled"
    else
        minikube addons enable ingress
        print_success "Ingress addon enabled"
    fi

    # Upgrade frontend with ingress enabled
    helm upgrade todo-app ./charts/frontend --set ingress.enabled=true
    print_success "Ingress enabled for frontend"

    # Wait for ingress
    echo "Waiting for ingress to be ready..."
    sleep 10

    echo ""
    print_warning "To access via ingress, add this to /etc/hosts:"
    echo "127.0.0.1 todo.local"
    echo ""
    print_warning "Then run 'minikube tunnel' in a separate terminal"
    print_warning "Access frontend at: http://todo.local/"
    print_warning "Access backend API at: http://todo.local/api/health"
else
    echo ""
    print_warning "Ingress not enabled. Use port-forward to access:"
    echo ""
    echo "Frontend:"
    echo "  kubectl port-forward svc/todo-app-todo-frontend 3000:3000"
    echo "  Visit: http://localhost:3000"
    echo ""
    echo "Backend:"
    echo "  kubectl port-forward svc/todo-api-todo-backend 8000:8000"
    echo "  Visit: http://localhost:8000/health"
fi

echo ""
echo "=========================================="
echo "Deployment Complete! 🎉"
echo "=========================================="
echo ""
print_success "Frontend: 2 replicas running"
print_success "Backend: 2 replicas running"
echo ""
echo "Useful commands:"
echo "  helm list                  # View releases"
echo "  kubectl get pods           # View pods"
echo "  kubectl logs -f <pod>      # View logs"
echo "  helm uninstall todo-app    # Remove frontend"
echo "  helm uninstall todo-api    # Remove backend"
echo ""
