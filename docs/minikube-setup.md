# Minikube Setup Guide

**Feature**: 006-minikube-setup
**Purpose**: Local Kubernetes cluster for development and testing
**Last Updated**: 2025-12-30

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Detailed Setup](#detailed-setup)
5. [Addon Configuration](#addon-configuration)
6. [Verification](#verification)
7. [Daily Workflow](#daily-workflow)
8. [Troubleshooting](#troubleshooting)
9. [Cleanup](#cleanup)
10. [Advanced Configuration](#advanced-configuration)

---

## Overview

This guide walks you through setting up a local Kubernetes development environment using Minikube. The setup includes:

- **Minikube Cluster**: Single-node Kubernetes cluster with 4 CPUs and 8GB RAM
- **NGINX Ingress Controller**: HTTP/HTTPS routing with domain-based traffic distribution
- **Metrics Server**: Resource monitoring and Horizontal Pod Autoscaling (HPA) support
- **Kubernetes Dashboard**: Web UI for cluster management and visualization

**System Requirements**:
- **CPU**: 6+ cores (4 for cluster + 2 for host OS)
- **RAM**: 12GB+ (8GB for cluster + 4GB for host OS)
- **Disk**: 20GB+ free space
- **OS**: Windows 10+, macOS 11+, or Linux (Ubuntu 18.04+)

---

## Prerequisites

### Required Software

Install the following tools before proceeding:

#### 1. Minikube (v1.32.0+)

**Windows** (PowerShell as Administrator):
```powershell
# Using Chocolatey
choco install minikube

# Or using winget
winget install Kubernetes.minikube
```

**macOS**:
```bash
# Using Homebrew
brew install minikube
```

**Linux**:
```bash
# Direct download
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
```

Verify installation:
```bash
minikube version
```

#### 2. kubectl (v1.28.0+)

**Windows** (PowerShell as Administrator):
```powershell
# Using Chocolatey
choco install kubernetes-cli

# Or using winget
winget install Kubernetes.kubectl
```

**macOS**:
```bash
# Using Homebrew
brew install kubectl
```

**Linux**:
```bash
# Direct download
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

Verify installation:
```bash
kubectl version --client
```

#### 3. Docker (v20.10+)

**Windows/macOS**:
- Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop)
- Start Docker Desktop and ensure it's running

**Linux**:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to docker group (logout/login after)
sudo usermod -aG docker $USER
```

Verify installation:
```bash
docker --version
docker ps
```

---

## Quick Start

### One-Command Setup

For the impatient, run the cluster initialization script:

```bash
./scripts/minikube/start-cluster.sh
```

This script will:
1. Verify all prerequisites (Minikube, kubectl, Docker)
2. Check system resources (CPU, memory)
3. Start Minikube cluster with 4 CPUs and 8GB RAM
4. Wait for cluster to become ready
5. Display cluster status and next steps

**Estimated time**: 2-3 minutes

---

## Detailed Setup

(This section will be expanded during Phase 8 - Polish)

### Step-by-Step Cluster Initialization

To be completed...

---

## Addon Configuration

(This section will be expanded during implementation of US2, US3, US4)

### Enable NGINX Ingress Controller

To be completed...

### Enable Metrics Server

To be completed...

### Enable Kubernetes Dashboard

To be completed...

---

## Verification

(This section will be expanded during Phase 7 - Verification & Cleanup)

### Health Check Script

To be completed...

---

## Daily Workflow

(This section will be expanded during Phase 8 - Polish)

### Common Commands

To be completed...

---

## Troubleshooting

(This section will be expanded during Phase 8 - Polish)

### Common Issues

To be completed...

---

## Cleanup

(This section will be expanded during Phase 7 - Verification & Cleanup)

### Stop Cluster

To be completed...

### Delete Cluster

To be completed...

---

## Advanced Configuration

(This section will be expanded during Phase 8 - Polish)

### Environment Variables

See `scripts/minikube/.env.example` for all available configuration options.

To customize your setup:

```bash
cd scripts/minikube
cp .env.example .env
# Edit .env with your preferences
nano .env
```

Common customizations:
- `MINIKUBE_CPU`: Adjust CPU allocation (default: 4)
- `MINIKUBE_MEMORY`: Adjust memory allocation in MB (default: 8192)
- `MINIKUBE_DRIVER`: Change driver (docker, virtualbox, hyperv, kvm2)
- `K8S_VERSION`: Pin specific Kubernetes version

---

## Related Documentation

- [Minikube Official Documentation](https://minikube.sigs.k8s.io/docs/)
- [Kubectl Reference](https://kubernetes.io/docs/reference/kubectl/)
- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [Metrics Server](https://github.com/kubernetes-sigs/metrics-server)

---

**Document Owner**: DevOps/Infrastructure Team
**Feedback**: Open an issue in the repository for improvements or corrections
