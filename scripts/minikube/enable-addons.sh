#!/usr/bin/env bash
#
# Minikube Addon Management Script
# Feature: 006-minikube-setup / US2, US3, US4
# Purpose: Enable and verify Minikube addons (ingress, metrics-server, dashboard)

set -euo pipefail

# =============================================================================
# SCRIPT SETUP
# =============================================================================

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source utilities
# shellcheck source=./utils.sh
source "$SCRIPT_DIR/utils.sh"

# Load environment variables if .env exists
if [ -f "$SCRIPT_DIR/.env" ]; then
    # shellcheck source=./.env.example
    source "$SCRIPT_DIR/.env"
fi

# =============================================================================
# CONFIGURATION
# =============================================================================

# Cluster configuration
readonly PROFILE="${MINIKUBE_PROFILE:-todo-dev}"
readonly ADDON_TIMEOUT="${ADDON_ENABLE_TIMEOUT:-120}"
readonly METRICS_DELAY="${METRICS_COLLECTION_DELAY:-60}"

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

# Check if cluster is running
check_cluster_running() {
    print_step "Checking if cluster '$PROFILE' is running..."

    if ! validate_profile_exists "$PROFILE"; then
        print_error "Cluster with profile '$PROFILE' does not exist"
        echo ""
        echo "Please create the cluster first:"
        echo "  ./scripts/minikube/start-cluster.sh"
        return 1
    fi

    local status
    status=$(minikube status -p "$PROFILE" --format='{{.Host}}' 2>/dev/null || echo "Stopped")

    if [ "$status" != "Running" ]; then
        print_error "Cluster is not running (status: $status)"
        echo ""
        echo "Start the cluster with:"
        echo "  minikube start -p $PROFILE"
        return 1
    fi

    print_success "Cluster '$PROFILE' is running"
    return 0
}

# Check kubectl connectivity
check_kubectl_connectivity() {
    print_step "Checking kubectl connectivity..."

    if ! kubectl cluster-info >/dev/null 2>&1; then
        print_error "Cannot connect to cluster with kubectl"
        echo ""
        echo "Try setting the context:"
        echo "  kubectl config use-context $PROFILE"
        return 1
    fi

    print_success "kubectl can connect to cluster"
    return 0
}

# =============================================================================
# INGRESS ADDON (US2)
# =============================================================================

# Enable NGINX Ingress Controller addon
enable_ingress() {
    print_header "Enabling NGINX Ingress Controller"

    # Check if already enabled
    local status
    status=$(minikube addons list -p "$PROFILE" 2>/dev/null | grep "^| ingress " | awk '{print $3}' || echo "unknown")

    if [ "$status" = "enabled" ]; then
        print_success "Ingress addon is already enabled"
    else
        print_step "Enabling ingress addon..."
        if minikube addons enable ingress -p "$PROFILE"; then
            print_success "Ingress addon enabled"
        else
            print_error "Failed to enable ingress addon"
            return 1
        fi
    fi

    # Wait for ingress controller pods to be ready
    print_step "Waiting for ingress controller to be ready (timeout: ${ADDON_TIMEOUT}s)..."

    if wait_for_condition \
        "kubectl get pods -n ingress-nginx -l app.kubernetes.io/component=controller 2>/dev/null | grep -q ' Running '" \
        "$ADDON_TIMEOUT" \
        "Checking ingress controller pods..."; then
        print_success "Ingress controller is ready"
    else
        print_warning "Ingress controller did not become ready within ${ADDON_TIMEOUT}s"
        print_info "Check pod status with: kubectl get pods -n ingress-nginx"
        return 1
    fi

    # Display ingress status
    display_ingress_status

    # Display configuration tips
    display_ingress_config_tips

    return 0
}

# Display ingress addon status
display_ingress_status() {
    print_header "Ingress Controller Status"

    print_step "Ingress controller pods:"
    kubectl get pods -n ingress-nginx 2>/dev/null || print_error "Failed to get ingress pods"
    echo ""

    print_step "Ingress controller services:"
    kubectl get svc -n ingress-nginx 2>/dev/null || print_error "Failed to get ingress services"
    echo ""
}

# Display ingress configuration tips
display_ingress_config_tips() {
    print_header "Ingress Configuration Tips"

    local cluster_ip
    cluster_ip=$(minikube ip -p "$PROFILE" 2>/dev/null || echo "N/A")

    echo "📝 Hosts File Configuration:"
    echo ""
    echo "To access ingress routes via domain names, add entries to your hosts file:"
    echo ""
    echo "  Cluster IP: $cluster_ip"
    echo ""
    echo "  Windows:"
    echo "    1. Open Notepad as Administrator"
    echo "    2. Open: C:\\Windows\\System32\\drivers\\etc\\hosts"
    echo "    3. Add line: $cluster_ip  your-domain.local"
    echo ""
    echo "  macOS/Linux:"
    echo "    sudo nano /etc/hosts"
    echo "    Add line: $cluster_ip  your-domain.local"
    echo ""
    echo "📄 Example Ingress Resources:"
    echo "  See: kubernetes/examples/hello-world-ingress.yaml"
    echo "  See: kubernetes/examples/ingress-routing.yaml"
    echo ""
    echo "🧪 Test Ingress:"
    echo "  1. Deploy test app:"
    echo "     kubectl apply -f kubernetes/examples/hello-world-deployment.yaml"
    echo "     kubectl apply -f kubernetes/examples/hello-world-service.yaml"
    echo "     kubectl apply -f kubernetes/examples/hello-world-ingress.yaml"
    echo ""
    echo "  2. Add to hosts file:"
    echo "     echo \"$cluster_ip hello.local\" | sudo tee -a /etc/hosts"
    echo ""
    echo "  3. Test with curl:"
    echo "     curl http://hello.local"
    echo ""
}

# =============================================================================
# METRICS SERVER ADDON (US3)
# =============================================================================

# Enable Metrics Server addon
enable_metrics_server() {
    print_header "Enabling Metrics Server"

    # Check if already enabled
    local status
    status=$(minikube addons list -p "$PROFILE" 2>/dev/null | grep "^| metrics-server " | awk '{print $3}' || echo "unknown")

    if [ "$status" = "enabled" ]; then
        print_success "Metrics-server addon is already enabled"
    else
        print_step "Enabling metrics-server addon..."
        if minikube addons enable metrics-server -p "$PROFILE"; then
            print_success "Metrics-server addon enabled"
        else
            print_error "Failed to enable metrics-server addon"
            return 1
        fi
    fi

    # Wait for metrics-server deployment to be ready
    print_step "Waiting for metrics-server deployment to be ready (timeout: ${ADDON_TIMEOUT}s)..."

    if wait_for_condition \
        "kubectl get deployment metrics-server -n kube-system 2>/dev/null | grep -q '1/1'" \
        "$ADDON_TIMEOUT" \
        "Checking metrics-server deployment..."; then
        print_success "Metrics-server deployment is ready"
    else
        print_warning "Metrics-server deployment did not become ready within ${ADDON_TIMEOUT}s"
        print_info "Check deployment status with: kubectl get deployment -n kube-system metrics-server"
    fi

    # Wait for metrics collection to start
    print_step "Waiting ${METRICS_DELAY}s for metrics collection to start..."
    sleep "$METRICS_DELAY"
    print_success "Metrics collection delay complete"

    # Verify metrics availability
    verify_metrics_availability

    # Display metrics status
    display_metrics_status

    # Display usage tips
    display_metrics_usage_tips

    return 0
}

# Verify metrics are available
verify_metrics_availability() {
    print_step "Verifying metrics availability..."

    # Test kubectl top nodes
    if kubectl top nodes >/dev/null 2>&1; then
        print_success "Node metrics are available (kubectl top nodes)"
    else
        print_warning "Node metrics not yet available"
        print_info "Metrics may need more time to collect data"
    fi

    # Test kubectl top pods
    if kubectl top pods -A >/dev/null 2>&1; then
        print_success "Pod metrics are available (kubectl top pods)"
    else
        print_warning "Pod metrics not yet available"
        print_info "Metrics may need more time to collect data"
    fi

    return 0
}

# Display metrics server status
display_metrics_status() {
    print_header "Metrics Server Status"

    print_step "Metrics-server pods:"
    kubectl get pods -n kube-system -l k8s-app=metrics-server 2>/dev/null || print_error "Failed to get metrics-server pods"
    echo ""

    print_step "Sample node metrics:"
    kubectl top nodes 2>/dev/null || print_warning "Node metrics not available yet (try again in 1-2 minutes)"
    echo ""

    print_step "Sample pod metrics (top 10):"
    kubectl top pods -A --sort-by=cpu 2>/dev/null | head -11 || print_warning "Pod metrics not available yet (try again in 1-2 minutes)"
    echo ""
}

# Display metrics usage tips
display_metrics_usage_tips() {
    print_header "Metrics Usage Tips"

    echo "📊 Metrics Commands:"
    echo ""
    echo "  View node metrics:"
    echo "    kubectl top nodes"
    echo ""
    echo "  View pod metrics (all namespaces):"
    echo "    kubectl top pods -A"
    echo ""
    echo "  View pod metrics (specific namespace):"
    echo "    kubectl top pods -n kube-system"
    echo ""
    echo "  Sort pods by CPU:"
    echo "    kubectl top pods -A --sort-by=cpu"
    echo ""
    echo "  Sort pods by memory:"
    echo "    kubectl top pods -A --sort-by=memory"
    echo ""
    echo "🔄 Horizontal Pod Autoscaler (HPA):"
    echo "  Create HPA based on CPU:"
    echo "    kubectl autoscale deployment <name> --cpu-percent=80 --min=2 --max=10"
    echo ""
    echo "  View HPA status:"
    echo "    kubectl get hpa"
    echo ""
    echo "  Describe HPA:"
    echo "    kubectl describe hpa <name>"
    echo ""
}

# =============================================================================
# DASHBOARD ADDON (US4)
# =============================================================================

# Enable Kubernetes Dashboard addon
enable_dashboard() {
    print_header "Enabling Kubernetes Dashboard"

    # Check if already enabled
    local status
    status=$(minikube addons list -p "$PROFILE" 2>/dev/null | grep "^| dashboard " | awk '{print $3}' || echo "unknown")

    if [ "$status" = "enabled" ]; then
        print_success "Dashboard addon is already enabled"
    else
        print_step "Enabling dashboard addon..."
        if minikube addons enable dashboard -p "$PROFILE"; then
            print_success "Dashboard addon enabled"
        else
            print_error "Failed to enable dashboard addon"
            return 1
        fi
    fi

    # Wait for dashboard pods to be ready
    print_step "Waiting for dashboard pods to be ready (timeout: ${ADDON_TIMEOUT}s)..."

    if wait_for_condition \
        "kubectl get pods -n kubernetes-dashboard 2>/dev/null | grep -E 'kubernetes-dashboard|dashboard-metrics-scraper' | grep -q ' Running '" \
        "$ADDON_TIMEOUT" \
        "Checking dashboard pods..."; then
        print_success "Dashboard pods are ready"
    else
        print_warning "Dashboard pods did not become ready within ${ADDON_TIMEOUT}s"
        print_info "Check pod status with: kubectl get pods -n kubernetes-dashboard"
    fi

    # Display dashboard status
    display_dashboard_status

    # Display access instructions
    display_dashboard_access_instructions

    return 0
}

# Display dashboard status
display_dashboard_status() {
    print_header "Dashboard Status"

    print_step "Dashboard pods:"
    kubectl get pods -n kubernetes-dashboard 2>/dev/null || print_error "Failed to get dashboard pods"
    echo ""

    print_step "Dashboard services:"
    kubectl get svc -n kubernetes-dashboard 2>/dev/null || print_error "Failed to get dashboard services"
    echo ""
}

# Display dashboard access instructions
display_dashboard_access_instructions() {
    print_header "Dashboard Access Instructions"

    echo "🌐 Access Kubernetes Dashboard:"
    echo ""
    echo "Method 1: minikube dashboard command (opens browser automatically)"
    echo "  minikube dashboard -p $PROFILE"
    echo ""
    echo "Method 2: minikube dashboard with URL only (no browser)"
    echo "  minikube dashboard -p $PROFILE --url"
    echo "  Then open the URL in your browser manually"
    echo ""
    echo "Method 3: kubectl proxy (advanced)"
    echo "  kubectl proxy"
    echo "  Then open:"
    echo "  http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/"
    echo ""
    echo "🔒 Security Note:"
    echo "  The dashboard is only accessible from localhost by default"
    echo "  Do NOT expose the dashboard to the internet without proper authentication"
    echo ""
}

# =============================================================================
# DISPLAY ALL ADDONS STATUS
# =============================================================================

# Display status of all enabled addons
display_addon_status() {
    print_header "Enabled Addons Summary"

    print_step "All enabled addons:"
    minikube addons list -p "$PROFILE" 2>/dev/null | grep " enabled " || print_info "No addons enabled"
    echo ""

    print_step "Critical addon pods:"
    echo ""
    echo "Ingress Controller:"
    kubectl get pods -n ingress-nginx -l app.kubernetes.io/component=controller 2>/dev/null || print_info "  Not enabled"
    echo ""
    echo "Metrics Server:"
    kubectl get pods -n kube-system -l k8s-app=metrics-server 2>/dev/null || print_info "  Not enabled"
    echo ""
    echo "Dashboard:"
    kubectl get pods -n kubernetes-dashboard 2>/dev/null || print_info "  Not enabled"
    echo ""
}

# =============================================================================
# MAIN EXECUTION WITH ARGUMENT PARSING
# =============================================================================

# Display usage information
show_usage() {
    cat << EOF
Usage: $0 <addon> [options]

Enable and verify Minikube addons

ADDONS:
  ingress         Enable NGINX Ingress Controller (US2)
  metrics-server  Enable Metrics Server (US3)
  dashboard       Enable Kubernetes Dashboard (US4)
  all             Enable all recommended addons (ingress, metrics-server, dashboard)
  status          Show status of all addons

OPTIONS:
  -p, --profile   Minikube profile name (default: $PROFILE)
  -h, --help      Show this help message

EXAMPLES:
  $0 ingress                    # Enable ingress addon
  $0 metrics-server             # Enable metrics-server addon
  $0 dashboard                  # Enable dashboard addon
  $0 all                        # Enable all recommended addons
  $0 status                     # Show addon status

RELATED COMMANDS:
  minikube addons list -p $PROFILE          # List all available addons
  minikube addons disable <addon> -p $PROFILE  # Disable an addon

For more information, see: docs/minikube-setup.md
EOF
}

# Main function with argument parsing
main() {
    # Parse arguments
    if [ $# -eq 0 ]; then
        show_usage
        exit 1
    fi

    local addon="$1"

    # Validate prerequisites
    check_cluster_running || die "Cluster is not running"
    check_kubectl_connectivity || die "Cannot connect to cluster with kubectl"
    echo ""

    # Process addon request
    case "$addon" in
        ingress)
            enable_ingress || die "Failed to enable ingress addon"
            ;;

        metrics-server|metrics)
            enable_metrics_server || die "Failed to enable metrics-server addon"
            ;;

        dashboard)
            enable_dashboard || die "Failed to enable dashboard addon"
            ;;

        all)
            print_header "Enabling All Recommended Addons"
            enable_ingress || print_warning "Ingress enablement failed"
            echo ""
            enable_metrics_server || print_warning "Metrics-server enablement failed"
            echo ""
            enable_dashboard || print_warning "Dashboard enablement failed"
            echo ""
            display_addon_status
            ;;

        status)
            display_addon_status
            ;;

        -h|--help|help)
            show_usage
            exit 0
            ;;

        *)
            print_error "Unknown addon: $addon"
            echo ""
            show_usage
            exit 1
            ;;
    esac

    echo ""
    print_success "Addon operation complete!"
}

# Run main function
main "$@"
