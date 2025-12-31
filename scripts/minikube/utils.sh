#!/usr/bin/env bash
#
# Minikube Utilities - Shared Functions
# Feature: 006-minikube-setup
# Purpose: Reusable functions for color output, validation, and display formatting

set -euo pipefail

# =============================================================================
# COLOR OUTPUT FUNCTIONS
# =============================================================================

# Color codes
readonly COLOR_RESET='\033[0m'
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[0;33m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_MAGENTA='\033[0;35m'
readonly COLOR_CYAN='\033[0;36m'
readonly COLOR_BOLD='\033[1m'

# Print colored messages
print_success() {
    echo -e "${COLOR_GREEN}✓${COLOR_RESET} $1"
}

print_error() {
    echo -e "${COLOR_RED}✗${COLOR_RESET} $1" >&2
}

print_warning() {
    echo -e "${COLOR_YELLOW}⚠${COLOR_RESET} $1"
}

print_info() {
    echo -e "${COLOR_BLUE}ℹ${COLOR_RESET} $1"
}

print_step() {
    echo -e "${COLOR_CYAN}▸${COLOR_RESET} $1"
}

print_header() {
    echo ""
    echo -e "${COLOR_BOLD}${COLOR_MAGENTA}$1${COLOR_RESET}"
    echo -e "${COLOR_MAGENTA}$(printf '=%.0s' {1..60})${COLOR_RESET}"
}

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Validate Minikube installation
validate_minikube_installed() {
    if ! command_exists minikube; then
        print_error "Minikube is not installed"
        print_info "Install from: https://minikube.sigs.k8s.io/docs/start/"
        return 1
    fi

    local version
    version=$(minikube version --short 2>/dev/null | grep -oP 'v\K[0-9]+\.[0-9]+\.[0-9]+' || echo "0.0.0")
    print_success "Minikube installed (version: v$version)"
    return 0
}

# Validate kubectl installation
validate_kubectl_installed() {
    if ! command_exists kubectl; then
        print_error "kubectl is not installed"
        print_info "Install from: https://kubernetes.io/docs/tasks/tools/"
        return 1
    fi

    local version
    version=$(kubectl version --client --short 2>/dev/null | grep -oP 'v\K[0-9]+\.[0-9]+\.[0-9]+' | head -1 || echo "0.0.0")
    print_success "kubectl installed (version: v$version)"
    return 0
}

# Validate Docker installation and daemon status
validate_docker_available() {
    if ! command_exists docker; then
        print_error "Docker is not installed"
        print_info "Install from: https://docs.docker.com/get-docker/"
        return 1
    fi

    if ! docker ps >/dev/null 2>&1; then
        print_error "Docker daemon is not running"
        print_info "Start Docker Desktop or run: sudo systemctl start docker"
        return 1
    fi

    local version
    version=$(docker --version | grep -oP '\d+\.\d+\.\d+' | head -1)
    print_success "Docker installed and running (version: $version)"
    return 0
}

# Validate system resources
validate_system_resources() {
    local required_cpu=$1
    local required_memory_mb=$2

    print_step "Validating system resources..."

    # CPU validation (cross-platform)
    local cpu_count=0
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        cpu_count=$(nproc 2>/dev/null || echo 0)
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        cpu_count=$(sysctl -n hw.ncpu 2>/dev/null || echo 0)
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        cpu_count=$(wmic cpu get NumberOfLogicalProcessors 2>/dev/null | tail -1 | tr -d ' \r\n' || echo 0)
    fi

    if [ "$cpu_count" -lt "$required_cpu" ]; then
        print_warning "System has $cpu_count CPUs (recommended: ${required_cpu}+ for cluster + host)"
        print_info "Cluster may run slowly with fewer CPUs"
    else
        print_success "CPU count: $cpu_count (sufficient for $required_cpu cluster CPUs)"
    fi

    # Memory validation (warning only, not blocking)
    local memory_gb=0
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        memory_gb=$(free -g | awk '/^Mem:/{print $2}')
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        memory_gb=$(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 ))
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        memory_gb=$(wmic OS get TotalVisibleMemorySize /Value 2>/dev/null | grep -oP '\d+' | awk '{print int($1/1024/1024)}')
    fi

    local required_memory_gb=$(( required_memory_mb / 1024 + 4 ))  # Cluster + 4GB for host
    if [ "$memory_gb" -lt "$required_memory_gb" ]; then
        print_warning "System has ${memory_gb}GB RAM (recommended: ${required_memory_gb}GB+ for cluster + host)"
        print_info "Cluster may experience memory pressure"
    else
        print_success "Memory: ${memory_gb}GB (sufficient for ${required_memory_mb}MB cluster + host)"
    fi

    return 0
}

# Validate profile exists
validate_profile_exists() {
    local profile=$1

    if ! minikube profile list 2>/dev/null | grep -q "^| $profile "; then
        return 1
    fi
    return 0
}

# =============================================================================
# DISPLAY FUNCTIONS
# =============================================================================

# Display cluster status with formatting
display_cluster_status() {
    local profile=$1

    print_header "Cluster Status: $profile"

    if validate_profile_exists "$profile"; then
        minikube status -p "$profile" || true
    else
        print_error "Profile '$profile' does not exist"
        return 1
    fi
}

# Display resource information
display_resource_info() {
    local profile=$1

    print_header "Resource Allocation"

    if validate_profile_exists "$profile"; then
        local cpu memory disk
        cpu=$(minikube profile list | grep "^| $profile " | awk '{print $5}' || echo "N/A")
        memory=$(minikube profile list | grep "^| $profile " | awk '{print $6}' || echo "N/A")
        disk=$(minikube profile list | grep "^| $profile " | awk '{print $7}' || echo "N/A")

        echo "CPU:    $cpu"
        echo "Memory: $memory"
        echo "Disk:   $disk"
    else
        print_error "Profile '$profile' not found"
        return 1
    fi
}

# Display helpful next steps
display_next_steps() {
    local profile=$1

    print_header "Next Steps"
    echo "1. Verify cluster:"
    echo "   kubectl get nodes"
    echo ""
    echo "2. View system pods:"
    echo "   kubectl get pods -A"
    echo ""
    echo "3. Enable addons:"
    echo "   ./scripts/minikube/enable-addons.sh ingress"
    echo "   ./scripts/minikube/enable-addons.sh metrics-server"
    echo "   ./scripts/minikube/enable-addons.sh dashboard"
    echo ""
    echo "4. Verify health:"
    echo "   ./scripts/minikube/verify-health.sh"
    echo ""
    echo "5. Access dashboard:"
    echo "   minikube dashboard -p $profile"
    echo ""
}

# Display addon status with color coding
display_addon_status() {
    local profile=$1
    local addon=$2

    local status
    status=$(minikube addons list -p "$profile" 2>/dev/null | grep "^| $addon " | awk '{print $3}' || echo "unknown")

    case "$status" in
        enabled)
            print_success "Addon '$addon' is enabled"
            ;;
        disabled)
            print_warning "Addon '$addon' is disabled"
            ;;
        *)
            print_error "Addon '$addon' status: $status"
            ;;
    esac
}

# Display progress bar (simple text-based)
display_progress() {
    local current=$1
    local total=$2
    local message=$3

    local percent=$(( current * 100 / total ))
    local filled=$(( percent / 5 ))
    local empty=$(( 20 - filled ))

    printf "\r${COLOR_CYAN}▸${COLOR_RESET} %-40s [" "$message"
    printf "%0.s█" $(seq 1 $filled)
    printf "%0.s░" $(seq 1 $empty)
    printf "] %3d%%" "$percent"

    if [ "$current" -eq "$total" ]; then
        echo ""
    fi
}

# =============================================================================
# WAIT FUNCTIONS
# =============================================================================

# Wait for condition with timeout
wait_for_condition() {
    local condition_cmd=$1
    local timeout_seconds=$2
    local message=$3

    print_step "$message"

    local elapsed=0
    local interval=5

    while [ $elapsed -lt $timeout_seconds ]; do
        if eval "$condition_cmd" 2>/dev/null; then
            print_success "Condition met after ${elapsed}s"
            return 0
        fi

        sleep $interval
        elapsed=$((elapsed + interval))

        local remaining=$((timeout_seconds - elapsed))
        printf "\r${COLOR_CYAN}▸${COLOR_RESET} Waiting... ${elapsed}s / ${timeout_seconds}s (${remaining}s remaining)"
    done

    echo ""
    print_error "Timeout after ${timeout_seconds}s"
    return 1
}

# =============================================================================
# ERROR HANDLING
# =============================================================================

# Exit with error message
die() {
    print_error "$1"
    exit 1
}

# Check last command status
check_status() {
    local status=$?
    local message=$1

    if [ $status -ne 0 ]; then
        print_error "$message (exit code: $status)"
        return 1
    fi
    return 0
}

# =============================================================================
# CONFIRMATION PROMPTS
# =============================================================================

# Ask for confirmation (yes/no)
confirm() {
    local prompt=$1
    local default=${2:-n}

    local yn_prompt
    if [ "$default" = "y" ]; then
        yn_prompt="[Y/n]"
    else
        yn_prompt="[y/N]"
    fi

    echo -n -e "${COLOR_YELLOW}?${COLOR_RESET} $prompt $yn_prompt: "
    read -r response

    response=${response:-$default}
    case "$response" in
        [yY]|[yY][eE][sS])
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Ask for typed confirmation (user must type specific text)
confirm_typed() {
    local prompt=$1
    local expected=$2

    echo -e "${COLOR_YELLOW}?${COLOR_RESET} $prompt"
    echo -n "  Type '$expected' to confirm: "
    read -r response

    if [ "$response" = "$expected" ]; then
        return 0
    else
        print_error "Confirmation failed (expected: '$expected', got: '$response')"
        return 1
    fi
}

# =============================================================================
# SCRIPT END
# =============================================================================

# Note: This file should be sourced by other scripts using:
# source "$(dirname "${BASH_SOURCE[0]}")/utils.sh"
