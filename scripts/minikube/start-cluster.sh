#!/usr/bin/env bash
#
# Minikube Cluster Initialization Script
# Feature: 006-minikube-setup / US1 - Launch Local Kubernetes Cluster
# Purpose: Start Minikube cluster with 4 CPUs, 8GB RAM, and essential configuration

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

# Cluster configuration (with defaults)
readonly PROFILE="${MINIKUBE_PROFILE:-todo-dev}"
readonly DRIVER="${MINIKUBE_DRIVER:-docker}"
readonly CPU="${MINIKUBE_CPU:-4}"
readonly MEMORY="${MINIKUBE_MEMORY:-8192}"
readonly DISK="${MINIKUBE_DISK:-40g}"
readonly K8S_VERSION="${K8S_VERSION:-stable}"
readonly CONTAINER_RUNTIME="${CONTAINER_RUNTIME:-docker}"
readonly START_TIMEOUT="${CLUSTER_START_TIMEOUT:-300}"

# =============================================================================
# PREREQUISITE CHECKS
# =============================================================================

# Check if Minikube is installed
check_minikube_installed() {
    print_step "Checking if Minikube is installed..."

    if ! command_exists minikube; then
        print_error "Minikube is not installed"
        echo ""
        echo "Please install Minikube from:"
        echo "  https://minikube.sigs.k8s.io/docs/start/"
        echo ""
        echo "Installation commands:"
        echo "  Windows: choco install minikube  OR  winget install Kubernetes.minikube"
        echo "  macOS:   brew install minikube"
        echo "  Linux:   curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64"
        echo "           sudo install minikube-linux-amd64 /usr/local/bin/minikube"
        return 1
    fi

    validate_minikube_installed
    return 0
}

# Check if kubectl is installed
check_kubectl_installed() {
    print_step "Checking if kubectl is installed..."

    if ! command_exists kubectl; then
        print_error "kubectl is not installed"
        echo ""
        echo "Please install kubectl from:"
        echo "  https://kubernetes.io/docs/tasks/tools/"
        echo ""
        echo "Installation commands:"
        echo "  Windows: choco install kubernetes-cli  OR  winget install Kubernetes.kubectl"
        echo "  macOS:   brew install kubectl"
        echo "  Linux:   curl -LO https://dl.k8s.io/release/\$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
        echo "           sudo install kubectl /usr/local/bin/kubectl"
        return 1
    fi

    validate_kubectl_installed
    return 0
}

# Check if specified driver is available
check_driver_available() {
    print_step "Checking if driver '$DRIVER' is available..."

    case "$DRIVER" in
        docker)
            if ! command_exists docker; then
                print_error "Docker is not installed"
                echo ""
                echo "Please install Docker from:"
                echo "  https://docs.docker.com/get-docker/"
                return 1
            fi

            if ! docker ps >/dev/null 2>&1; then
                print_error "Docker daemon is not running"
                echo ""
                echo "Please start Docker:"
                echo "  Windows/macOS: Start Docker Desktop"
                echo "  Linux: sudo systemctl start docker"
                return 1
            fi

            print_success "Docker driver is available and running"
            ;;

        hyperv)
            if [[ "$OSTYPE" != "msys" ]] && [[ "$OSTYPE" != "cygwin" ]]; then
                print_error "Hyper-V driver is only available on Windows"
                return 1
            fi
            print_success "Hyper-V driver selected (Windows)"
            ;;

        virtualbox)
            if ! command_exists VBoxManage; then
                print_error "VirtualBox is not installed"
                echo ""
                echo "Please install VirtualBox from:"
                echo "  https://www.virtualbox.org/wiki/Downloads"
                return 1
            fi
            print_success "VirtualBox driver is available"
            ;;

        kvm2)
            if [[ "$OSTYPE" != "linux-gnu"* ]]; then
                print_error "KVM2 driver is only available on Linux"
                return 1
            fi
            if ! command_exists virsh; then
                print_error "KVM/libvirt is not installed"
                echo ""
                echo "Please install KVM:"
                echo "  Ubuntu/Debian: sudo apt-get install qemu-kvm libvirt-daemon-system"
                return 1
            fi
            print_success "KVM2 driver is available"
            ;;

        *)
            print_error "Unknown driver: $DRIVER"
            echo ""
            echo "Supported drivers: docker, hyperv, virtualbox, kvm2"
            return 1
            ;;
    esac

    return 0
}

# Validate system resources
validate_resources() {
    print_step "Validating system resources..."

    # Validate system has sufficient resources
    validate_system_resources "$CPU" "$MEMORY"

    print_info "Cluster will be allocated: ${CPU} CPUs, ${MEMORY}MB RAM, ${DISK} disk"
    return 0
}

# =============================================================================
# CLUSTER MANAGEMENT
# =============================================================================

# Check if cluster already exists and prompt for action
check_existing_cluster() {
    print_step "Checking for existing cluster with profile '$PROFILE'..."

    if validate_profile_exists "$PROFILE"; then
        print_warning "Cluster with profile '$PROFILE' already exists"

        # Get current status
        local status
        status=$(minikube status -p "$PROFILE" --format='{{.Host}}' 2>/dev/null || echo "Unknown")

        echo ""
        echo "Current cluster status: $status"
        echo ""
        echo "Options:"
        echo "  1. Delete and recreate cluster (recommended for clean setup)"
        echo "  2. Reuse existing cluster (faster, may have stale state)"
        echo "  3. Cancel and exit"
        echo ""

        read -rp "Enter your choice (1/2/3): " choice

        case "$choice" in
            1)
                print_step "Deleting existing cluster..."
                minikube delete -p "$PROFILE" || print_warning "Delete failed, will try to recreate anyway"
                print_success "Existing cluster deleted"
                return 0
                ;;
            2)
                print_info "Reusing existing cluster"
                print_warning "This may skip some initialization steps"

                # Try to start if stopped
                local current_status
                current_status=$(minikube status -p "$PROFILE" --format='{{.Host}}' 2>/dev/null || echo "Stopped")
                if [ "$current_status" != "Running" ]; then
                    print_step "Starting existing cluster..."
                    minikube start -p "$PROFILE" || {
                        print_error "Failed to start existing cluster"
                        return 1
                    }
                fi

                # Set kubectl context
                kubectl config use-context "$PROFILE" >/dev/null 2>&1 || true

                # Display status and exit (skip cluster creation)
                display_cluster_info
                display_next_steps "$PROFILE"
                exit 0
                ;;
            3|*)
                print_info "Cancelled by user"
                exit 0
                ;;
        esac
    else
        print_success "No existing cluster found, will create new cluster"
    fi

    return 0
}

# Start Minikube cluster
start_cluster() {
    print_header "Starting Minikube Cluster"

    print_step "Initializing cluster with profile '$PROFILE'..."
    echo ""
    echo "Configuration:"
    echo "  Profile:           $PROFILE"
    echo "  Driver:            $DRIVER"
    echo "  CPUs:              $CPU"
    echo "  Memory:            ${MEMORY}MB"
    echo "  Disk:              $DISK"
    echo "  Kubernetes:        $K8S_VERSION"
    echo "  Container Runtime: $CONTAINER_RUNTIME"
    echo ""

    # Build minikube start command
    local start_cmd=(
        minikube start
        --profile="$PROFILE"
        --driver="$DRIVER"
        --cpus="$CPU"
        --memory="$MEMORY"
        --disk-size="$DISK"
        --kubernetes-version="$K8S_VERSION"
        --container-runtime="$CONTAINER_RUNTIME"
    )

    # Add extra flags if specified
    if [ -n "${EXTRA_MINIKUBE_FLAGS:-}" ]; then
        # shellcheck disable=SC2206
        start_cmd+=($EXTRA_MINIKUBE_FLAGS)
    fi

    print_step "Executing: ${start_cmd[*]}"
    echo ""

    # Record start time
    local start_time
    start_time=$(date +%s)

    # Execute start command
    if "${start_cmd[@]}"; then
        local end_time elapsed
        end_time=$(date +%s)
        elapsed=$((end_time - start_time))

        echo ""
        print_success "Cluster started successfully in ${elapsed}s"

        # Check if startup was within performance target
        if [ "$elapsed" -lt "$START_TIMEOUT" ]; then
            print_success "Startup time within target (${START_TIMEOUT}s)"
        else
            print_warning "Startup took ${elapsed}s (target: <${START_TIMEOUT}s)"
            print_info "Slow startup may indicate resource constraints"
        fi
    else
        print_error "Cluster start failed"
        echo ""
        echo "Troubleshooting steps:"
        echo "  1. Check Docker is running: docker ps"
        echo "  2. Check system resources: free -h && nproc"
        echo "  3. Try deleting cluster: minikube delete -p $PROFILE"
        echo "  4. Check Minikube logs: minikube logs -p $PROFILE"
        return 1
    fi

    return 0
}

# Set active profile for kubectl
set_active_profile() {
    print_step "Setting active kubectl context to '$PROFILE'..."

    if kubectl config use-context "$PROFILE" >/dev/null 2>&1; then
        print_success "kubectl context set to '$PROFILE'"
    else
        print_warning "Failed to set kubectl context (cluster may not be ready)"
    fi

    return 0
}

# Wait for cluster to be fully ready
wait_for_cluster_ready() {
    print_header "Waiting for Cluster Ready"

    # Wait for node to be Ready
    print_step "Waiting for node to be Ready..."
    if wait_for_condition \
        "kubectl get nodes 2>/dev/null | grep -q ' Ready '" \
        120 \
        "Checking node status..."; then
        print_success "Node is Ready"
    else
        print_error "Node did not become Ready within 120s"
        return 1
    fi

    # Wait for system pods to be Running or Completed
    print_step "Waiting for system pods to be Running..."
    local wait_pods=0
    local max_wait=120

    while [ $wait_pods -lt $max_wait ]; do
        local not_ready
        not_ready=$(kubectl get pods -n kube-system --no-headers 2>/dev/null | grep -v -E '(Running|Completed)' | wc -l || echo 999)

        if [ "$not_ready" -eq 0 ]; then
            print_success "All system pods are Running or Completed"
            break
        fi

        sleep 5
        wait_pods=$((wait_pods + 5))

        if [ $((wait_pods % 15)) -eq 0 ]; then
            printf "\r${COLOR_CYAN}▸${COLOR_RESET} Waiting for system pods... ${wait_pods}s / ${max_wait}s (${not_ready} pods not ready)"
        fi
    done

    if [ $wait_pods -ge $max_wait ]; then
        echo ""
        print_warning "Some system pods may not be ready yet"
        print_info "Check pod status with: kubectl get pods -A"
    else
        echo ""
    fi

    return 0
}

# =============================================================================
# DISPLAY FUNCTIONS
# =============================================================================

# Display cluster information
display_cluster_info() {
    print_header "Cluster Information"

    # Cluster status
    print_step "Cluster status:"
    minikube status -p "$PROFILE" || true
    echo ""

    # Node information
    print_step "Node information:"
    kubectl get nodes -o wide || print_warning "Failed to get node information"
    echo ""

    # Resource allocation
    print_step "Resource allocation:"
    kubectl get nodes -o custom-columns=\
NAME:.metadata.name,\
CPU:.status.allocatable.cpu,\
MEMORY:.status.allocatable.memory,\
PODS:.status.allocatable.pods 2>/dev/null || print_warning "Failed to get resource information"
    echo ""

    # System pods
    print_step "System pods:"
    kubectl get pods -n kube-system || print_warning "Failed to get system pods"
    echo ""

    # Cluster IP
    local cluster_ip
    cluster_ip=$(minikube ip -p "$PROFILE" 2>/dev/null || echo "N/A")
    print_info "Cluster IP: $cluster_ip"

    # API server
    local api_server
    api_server=$(kubectl cluster-info 2>/dev/null | head -1 || echo "N/A")
    print_info "API Server: $api_server"
}

# Display helpful next steps
display_next_steps() {
    local profile=$1

    print_header "Next Steps"

    echo "✅ Cluster '$profile' is ready!"
    echo ""
    echo "📋 Verification Commands:"
    echo "   kubectl get nodes                    # Check node status"
    echo "   kubectl get pods -A                  # List all pods"
    echo "   kubectl cluster-info                 # Cluster info"
    echo ""
    echo "🔌 Enable Addons (recommended):"
    echo "   ./scripts/minikube/enable-addons.sh ingress        # HTTP/HTTPS routing"
    echo "   ./scripts/minikube/enable-addons.sh metrics-server # Resource monitoring"
    echo "   ./scripts/minikube/enable-addons.sh dashboard      # Web UI"
    echo ""
    echo "🔍 Health Check:"
    echo "   ./scripts/minikube/verify-health.sh               # Comprehensive health check"
    echo ""
    echo "📊 Dashboard:"
    echo "   minikube dashboard -p $profile                    # Open dashboard in browser"
    echo ""
    echo "🛑 Stop Cluster:"
    echo "   minikube stop -p $profile                         # Stop cluster (preserves data)"
    echo "   ./scripts/minikube/cleanup.sh                     # Stop/delete with menu"
    echo ""
    echo "📚 Documentation:"
    echo "   docs/minikube-setup.md                             # Complete setup guide"
    echo ""
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    print_header "Minikube Cluster Setup - $PROFILE"

    echo "This script will initialize a Minikube cluster with the following configuration:"
    echo "  - Profile: $PROFILE"
    echo "  - CPUs: $CPU"
    echo "  - Memory: ${MEMORY}MB (${MEMORY}MB = $(( MEMORY / 1024 ))GB)"
    echo "  - Disk: $DISK"
    echo "  - Driver: $DRIVER"
    echo ""

    # Step 1: Prerequisite checks
    print_header "Step 1: Prerequisite Checks"
    check_minikube_installed || die "Minikube is required but not installed"
    check_kubectl_installed || die "kubectl is required but not installed"
    check_driver_available || die "Driver '$DRIVER' is not available"
    validate_resources || die "System resources insufficient"
    echo ""

    # Step 2: Check for existing cluster
    print_header "Step 2: Cluster Existence Check"
    check_existing_cluster
    echo ""

    # Step 3: Start cluster
    print_header "Step 3: Cluster Initialization"
    start_cluster || die "Failed to start cluster"
    echo ""

    # Step 4: Set kubectl context
    print_header "Step 4: Configure kubectl"
    set_active_profile
    echo ""

    # Step 5: Wait for cluster ready
    print_header "Step 5: Wait for Cluster Ready"
    wait_for_cluster_ready || print_warning "Cluster may not be fully ready"
    echo ""

    # Step 6: Display cluster info
    display_cluster_info
    echo ""

    # Step 7: Display next steps
    display_next_steps "$PROFILE"
    echo ""

    print_success "Cluster setup complete!"
}

# Run main function
main "$@"
