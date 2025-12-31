#!/usr/bin/env bash
#
# Minikube Cluster Cleanup Script
# Feature: 006-minikube-setup / Phase 7 - Verification & Cleanup
# Purpose: Safe cluster cleanup operations (stop, pause, delete, reset)

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

# =============================================================================
# CLEANUP FUNCTIONS
# =============================================================================

stop_cluster() {
    print_header "Stop Cluster"

    if ! validate_profile_exists "$PROFILE"; then
        print_error "Cluster '$PROFILE' does not exist"
        return 1
    fi

    if confirm "Stop cluster '$PROFILE'? (Preserves all data)" "y"; then
        print_step "Stopping cluster..."
        if minikube stop -p "$PROFILE"; then
            print_success "Cluster stopped successfully"
            print_info "Resume with: minikube start -p $PROFILE"
        else
            print_error "Failed to stop cluster"
            return 1
        fi
    else
        print_info "Operation cancelled"
    fi
}

pause_cluster() {
    print_header "Pause Cluster"

    if ! validate_profile_exists "$PROFILE"; then
        print_error "Cluster '$PROFILE' does not exist"
        return 1
    fi

    if confirm "Pause cluster '$PROFILE'? (Freezes cluster state)" "y"; then
        print_step "Pausing cluster..."
        if minikube pause -p "$PROFILE"; then
            print_success "Cluster paused successfully"
            print_info "Resume with: minikube unpause -p $PROFILE"
        else
            print_error "Failed to pause cluster"
            return 1
        fi
    else
        print_info "Operation cancelled"
    fi
}

delete_cluster() {
    print_header "Delete Cluster"

    if ! validate_profile_exists "$PROFILE"; then
        print_error "Cluster '$PROFILE' does not exist"
        return 1
    fi

    echo ""
    print_warning "⚠️  WARNING: This will permanently delete the cluster and all data!"
    echo ""

    if confirm_typed "Type cluster name to confirm deletion" "$PROFILE"; then
        print_step "Deleting cluster..."
        if minikube delete -p "$PROFILE"; then
            print_success "Cluster deleted successfully"
            print_info "Create new cluster with: ./scripts/minikube/start-cluster.sh"
        else
            print_error "Failed to delete cluster"
            return 1
        fi
    else
        print_info "Deletion cancelled"
    fi
}

delete_all_clusters() {
    print_header "Delete All Clusters"

    local cluster_count
    cluster_count=$(minikube profile list 2>/dev/null | grep -c "^|" || echo 0)

    if [ "$cluster_count" -eq 0 ]; then
        print_info "No clusters found"
        return 0
    fi

    echo ""
    print_warning "⚠️  WARNING: This will delete ALL Minikube clusters on this machine!"
    echo ""

    minikube profile list

    echo ""
    if confirm_typed "Type 'DELETE ALL' to confirm" "DELETE ALL"; then
        print_step "Deleting all clusters..."
        if minikube delete --all --purge; then
            print_success "All clusters deleted successfully"
        else
            print_error "Failed to delete all clusters"
            return 1
        fi
    else
        print_info "Operation cancelled"
    fi
}

clean_docker_resources() {
    print_header "Clean Docker Resources"

    echo "This will remove unused Docker images, containers, and volumes"
    echo "used by Minikube (if using Docker driver)"
    echo ""

    if ! command_exists docker; then
        print_error "Docker is not installed or not in PATH"
        return 1
    fi

    if ! docker ps >/dev/null 2>&1; then
        print_error "Docker daemon is not running"
        return 1
    fi

    if confirm "Clean Docker resources (prune images, containers, volumes)?" "n"; then
        print_step "Pruning Docker system..."

        # Prune containers
        print_step "Removing stopped containers..."
        docker container prune -f || print_warning "Container prune failed"

        # Prune images
        print_step "Removing unused images..."
        docker image prune -a -f || print_warning "Image prune failed"

        # Prune volumes
        print_step "Removing unused volumes..."
        docker volume prune -f || print_warning "Volume prune failed"

        # Prune networks
        print_step "Removing unused networks..."
        docker network prune -f || print_warning "Network prune failed"

        print_success "Docker cleanup complete"

        # Show disk space saved
        print_step "Current Docker disk usage:"
        docker system df
    else
        print_info "Docker cleanup cancelled"
    fi
}

reset_minikube_config() {
    print_header "Reset Minikube Configuration"

    echo "This will delete Minikube cache and configuration files"
    echo "Includes: downloaded images, cached binaries, configuration"
    echo ""

    if confirm "Reset Minikube configuration? (Requires re-download of images)" "n"; then
        local minikube_home="${MINIKUBE_HOME:-$HOME/.minikube}"

        print_step "Deleting cache directory..."
        rm -rf "$minikube_home/cache" 2>/dev/null || print_warning "Cache deletion failed"

        print_step "Deleting config files..."
        rm -f "$minikube_home/config/config.json" 2>/dev/null || print_warning "Config deletion failed"

        print_success "Minikube configuration reset"
        print_info "Next cluster start will re-download required files"
    else
        print_info "Reset cancelled"
    fi
}

# =============================================================================
# INTERACTIVE MENU
# =============================================================================

interactive_menu() {
    while true; do
        clear
        print_header "Minikube Cleanup Menu - $PROFILE"

        echo ""
        echo "Select an operation:"
        echo ""
        echo "  1. Stop cluster (preserves data)"
        echo "  2. Pause cluster (freeze state)"
        echo "  3. Delete cluster (permanent deletion)"
        echo "  4. Delete all clusters (ALL clusters on machine)"
        echo "  5. Clean Docker resources (prune images/containers)"
        echo "  6. Reset Minikube configuration (cache and config)"
        echo "  7. Show cluster status"
        echo "  0. Exit"
        echo ""

        read -rp "Enter choice (0-7): " choice

        case "$choice" in
            1)
                stop_cluster
                read -rp "Press Enter to continue..."
                ;;
            2)
                pause_cluster
                read -rp "Press Enter to continue..."
                ;;
            3)
                delete_cluster
                read -rp "Press Enter to continue..."
                ;;
            4)
                delete_all_clusters
                read -rp "Press Enter to continue..."
                ;;
            5)
                clean_docker_resources
                read -rp "Press Enter to continue..."
                ;;
            6)
                reset_minikube_config
                read -rp "Press Enter to continue..."
                ;;
            7)
                display_cluster_status "$PROFILE" || print_error "Cluster not found"
                read -rp "Press Enter to continue..."
                ;;
            0)
                print_info "Exiting..."
                exit 0
                ;;
            *)
                print_error "Invalid choice: $choice"
                read -rp "Press Enter to continue..."
                ;;
        esac
    done
}

# =============================================================================
# MAIN EXECUTION WITH ARGUMENT PARSING
# =============================================================================

show_usage() {
    cat << EOF
Usage: $0 [OPERATION] [OPTIONS]

Minikube cluster cleanup operations

OPERATIONS:
  stop          Stop cluster (preserves data, can resume later)
  pause         Pause cluster (freeze state, quick resume)
  delete        Delete cluster permanently
  delete-all    Delete all Minikube clusters on this machine
  clean-docker  Clean unused Docker resources
  reset-config  Reset Minikube cache and configuration
  interactive   Interactive menu for cleanup operations (default)

OPTIONS:
  -p, --profile   Minikube profile name (default: $PROFILE)
  -h, --help      Show this help message

EXAMPLES:
  $0 stop                     # Stop cluster
  $0 delete                   # Delete cluster with confirmation
  $0 clean-docker             # Prune Docker resources
  $0 interactive              # Show interactive menu (default)
  $0                          # Show interactive menu

For more information, see: docs/minikube-setup.md
EOF
}

main() {
    local operation="${1:-interactive}"

    case "$operation" in
        stop)
            stop_cluster
            ;;
        pause)
            pause_cluster
            ;;
        delete)
            delete_cluster
            ;;
        delete-all)
            delete_all_clusters
            ;;
        clean-docker)
            clean_docker_resources
            ;;
        reset-config)
            reset_minikube_config
            ;;
        interactive)
            interactive_menu
            ;;
        -h|--help|help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown operation: $operation"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
