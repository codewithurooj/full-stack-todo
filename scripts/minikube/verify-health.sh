#!/usr/bin/env bash
#
# Minikube Cluster Health Verification Script
# Feature: 006-minikube-setup / Phase 7 - Verification & Cleanup
# Purpose: Comprehensive health checks for cluster, addons, and networking

set -euo pipefail

# =============================================================================
# SCRIPT SETUP
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/utils.sh"

if [ -f "$SCRIPT_DIR/.env" ]; then
    source "$SCRIPT_DIR/.env"
fi

# =============================================================================
# CONFIGURATION
# =============================================================================

readonly PROFILE="${MINIKUBE_PROFILE:-todo-dev}"

# Test results tracking
PASSED=0
FAILED=0
WARNINGS=0

# =============================================================================
# TEST FUNCTIONS
# =============================================================================

test_cluster_status() {
    print_step "Test: Cluster status..."
    if validate_profile_exists "$PROFILE"; then
        local status
        status=$(minikube status -p "$PROFILE" --format='{{.Host}}' 2>/dev/null || echo "Unknown")
        if [ "$status" = "Running" ]; then
            print_success "Cluster is running"
            ((PASSED++))
        else
            print_error "Cluster status: $status"
            ((FAILED++))
        fi
    else
        print_error "Cluster does not exist"
        ((FAILED++))
    fi
}

test_node_readiness() {
    print_step "Test: Node readiness..."
    if kubectl get nodes 2>/dev/null | grep -q " Ready "; then
        print_success "Node is Ready"
        ((PASSED++))
    else
        print_error "Node is not Ready"
        ((FAILED++))
    fi
}

test_resource_allocation() {
    print_step "Test: Resource allocation..."
    local cpu memory
    cpu=$(kubectl get nodes -o custom-columns=CPU:.status.allocatable.cpu --no-headers 2>/dev/null || echo "0")
    memory=$(kubectl get nodes -o custom-columns=MEMORY:.status.allocatable.memory --no-headers 2>/dev/null || echo "0Ki")

    if [ "$cpu" -ge 4 ] 2>/dev/null; then
        print_success "CPU allocation: ${cpu} (meets requirement: 4)"
        ((PASSED++))
    else
        print_warning "CPU allocation: ${cpu} (expected: 4)"
        ((WARNINGS++))
    fi

    # Convert memory to MB for comparison
    local memory_mb
    memory_mb=$(echo "$memory" | sed 's/Ki//' | awk '{print int($1/1024)}')
    if [ "$memory_mb" -ge 7000 ] 2>/dev/null; then
        print_success "Memory allocation: ${memory_mb}MB (meets requirement: ~8GB)"
        ((PASSED++))
    else
        print_warning "Memory allocation: ${memory_mb}MB (expected: ~8GB)"
        ((WARNINGS++))
    fi
}

test_system_pods() {
    print_step "Test: System pods status..."
    local not_ready
    not_ready=$(kubectl get pods -n kube-system --no-headers 2>/dev/null | grep -v -E '(Running|Completed)' | wc -l || echo 999)

    if [ "$not_ready" -eq 0 ]; then
        print_success "All system pods are Running or Completed"
        ((PASSED++))
    else
        print_error "$not_ready system pods are not ready"
        ((FAILED++))
    fi
}

test_api_server() {
    print_step "Test: API server connectivity..."
    local start end elapsed
    start=$(date +%s%N)
    if kubectl cluster-info >/dev/null 2>&1; then
        end=$(date +%s%N)
        elapsed=$(( (end - start) / 1000000 ))  # Convert to ms
        if [ "$elapsed" -lt 1000 ]; then
            print_success "API server responds in ${elapsed}ms (target: <1000ms)"
            ((PASSED++))
        else
            print_warning "API server responds in ${elapsed}ms (slow)"
            ((WARNINGS++))
        fi
    else
        print_error "Cannot connect to API server"
        ((FAILED++))
    fi
}

test_dns() {
    print_step "Test: DNS functionality..."
    if kubectl run -i --rm --restart=Never dns-test --image=busybox:1.28 --command -- nslookup kubernetes.default >/dev/null 2>&1; then
        print_success "DNS resolution works"
        ((PASSED++))
    else
        print_warning "DNS test failed (may be transient)"
        ((WARNINGS++))
    fi
}

test_ingress_addon() {
    print_step "Test: Ingress addon..."
    local status
    status=$(minikube addons list -p "$PROFILE" 2>/dev/null | grep "^| ingress " | awk '{print $3}' || echo "disabled")

    if [ "$status" = "enabled" ]; then
        if kubectl get pods -n ingress-nginx -l app.kubernetes.io/component=controller 2>/dev/null | grep -q " Running "; then
            print_success "Ingress controller is enabled and running"
            ((PASSED++))
        else
            print_warning "Ingress enabled but controller not running"
            ((WARNINGS++))
        fi
    else
        print_info "Ingress addon is not enabled (optional)"
        ((WARNINGS++))
    fi
}

test_metrics_server_addon() {
    print_step "Test: Metrics-server addon..."
    local status
    status=$(minikube addons list -p "$PROFILE" 2>/dev/null | grep "^| metrics-server " | awk '{print $3}' || echo "disabled")

    if [ "$status" = "enabled" ]; then
        if kubectl top nodes >/dev/null 2>&1; then
            print_success "Metrics-server is enabled and collecting metrics"
            ((PASSED++))
        else
            print_warning "Metrics-server enabled but metrics not available"
            ((WARNINGS++))
        fi
    else
        print_info "Metrics-server addon is not enabled (optional)"
        ((WARNINGS++))
    fi
}

test_dashboard_addon() {
    print_step "Test: Dashboard addon..."
    local status
    status=$(minikube addons list -p "$PROFILE" 2>/dev/null | grep "^| dashboard " | awk '{print $3}' || echo "disabled")

    if [ "$status" = "enabled" ]; then
        if kubectl get pods -n kubernetes-dashboard 2>/dev/null | grep -q " Running "; then
            print_success "Dashboard is enabled and running"
            ((PASSED++))
        else
            print_warning "Dashboard enabled but pods not running"
            ((WARNINGS++))
        fi
    else
        print_info "Dashboard addon is not enabled (optional)"
        ((WARNINGS++))
    fi
}

test_network() {
    print_step "Test: Cluster network connectivity..."
    local cluster_ip
    cluster_ip=$(minikube ip -p "$PROFILE" 2>/dev/null || echo "")

    if [ -n "$cluster_ip" ]; then
        print_success "Cluster IP: $cluster_ip"
        ((PASSED++))
    else
        print_error "Cannot get cluster IP"
        ((FAILED++))
    fi
}

test_ingress_routing() {
    print_step "Test: Ingress routing configuration..."
    local cluster_ip
    cluster_ip=$(minikube ip -p "$PROFILE" 2>/dev/null || echo "")

    if [ -n "$cluster_ip" ]; then
        print_info "For ingress routing, add to hosts file:"
        echo "  $cluster_ip  todo.local"
        ((WARNINGS++))
    fi
}

# =============================================================================
# SUMMARY DISPLAY
# =============================================================================

display_summary() {
    print_header "Health Check Summary"

    local total=$((PASSED + FAILED + WARNINGS))

    echo "Total Tests: $total"
    echo ""
    print_success "Passed:   $PASSED"
    print_error "Failed:   $FAILED"
    print_warning "Warnings: $WARNINGS"
    echo ""

    if [ "$FAILED" -eq 0 ] && [ "$WARNINGS" -lt 5 ]; then
        print_success "✅ CLUSTER VERIFICATION PASSED"
        return 0
    elif [ "$FAILED" -eq 0 ]; then
        print_warning "⚠️  CLUSTER VERIFICATION PASSED WITH WARNINGS"
        return 0
    else
        print_error "❌ CLUSTER VERIFICATION FAILED"
        return 1
    fi
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    print_header "Minikube Cluster Health Check - $PROFILE"
    echo ""

    test_cluster_status
    test_node_readiness
    test_resource_allocation
    test_system_pods
    test_api_server
    test_dns
    test_ingress_addon
    test_metrics_server_addon
    test_dashboard_addon
    test_network
    test_ingress_routing

    echo ""
    display_summary
}

main "$@"
