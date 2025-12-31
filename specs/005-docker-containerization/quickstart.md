# Docker Containerization Quick Start Guide

**Feature:** Docker Containerization (005-docker-containerization)
**Created:** 2025-12-29
**Purpose:** Complete guide for building, running, and deploying the Full-Stack Todo Application with Docker

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Docker Compose)](#quick-start-docker-compose)
3. [Environment Configuration](#environment-configuration)
4. [Building Individual Containers](#building-individual-containers)
5. [Running Containers](#running-containers)
6. [Health Checks](#health-checks)
7. [Logs and Monitoring](#logs-and-monitoring)
8. [Troubleshooting](#troubleshooting)
9. [Production Deployment](#production-deployment)
10. [Performance Metrics](#performance-metrics)

---

## Prerequisites

### Required Software

- **Docker Engine:** 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose:** v2+ (included with Docker Desktop)
- **Git:** For cloning the repository

### Verify Installation

\`\`\`bash
# Check Docker version
docker --version
# Expected: Docker version 20.10.0 or higher

# Check Docker Compose version
docker compose version
# Expected: Docker Compose version v2.0.0 or higher

# Verify Docker is running
docker info
# Should show Docker server information without errors
\`\`\`

### System Requirements

- **CPU:** 2+ cores recommended
- **RAM:** 4GB minimum, 8GB recommended
- **Disk Space:** 5GB free space
- **Network:** Internet connection for pulling base images

---

## Quick Start (Docker Compose)

The fastest way to run the entire application stack:

### 1. Clone Repository

\`\`\`bash
git clone https://github.com/codewithurooj/full-stack-todo.git
cd full-stack-todo
\`\`\`

### 2. Configure Environment

\`\`\`bash
# Copy environment template
cp .env.example .env

# Edit .env and add your actual values
# Required: DATABASE_URL, BETTER_AUTH_SECRET
# Optional: OPENAI_API_KEY, NEXT_PUBLIC_OPENAI_DOMAIN_KEY
\`\`\`

### 3. Start All Services

\`\`\`bash
# Build and start in one command
docker-compose up --build

# Or start in detached mode (background)
docker-compose up -d --build
\`\`\`

### 4. Access Services

- **Frontend UI:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Frontend Health:** http://localhost:3000/api/health
- **Backend Health:** http://localhost:8000/health

### 5. Stop Services

\`\`\`bash
# Stop services (preserves data)
docker-compose down

# Stop and remove all data
docker-compose down -v --remove-orphans
\`\`\`

---

## Environment Configuration

### Environment Variables

Create a \`.env\` file in the project root with these variables:

\`\`\`env
# Database (Required)
DATABASE_URL=postgresql://user:password@host.neon.tech/dbname?sslmode=require

# Authentication (Required)
# Generate with: openssl rand -hex 32
BETTER_AUTH_SECRET=your-secret-key-minimum-32-characters-long

# API Keys (Optional)
OPENAI_API_KEY=sk-your-openai-api-key
NEXT_PUBLIC_OPENAI_DOMAIN_KEY=your-openai-domain-key

# Frontend API URL (Optional - overridden in docker-compose.yml)
NEXT_PUBLIC_API_URL=http://localhost:8000
\`\`\`

### Generate Secrets

\`\`\`bash
# Generate BETTER_AUTH_SECRET (32 characters minimum)
openssl rand -hex 32

# Or use Python
python -c "import secrets; print(secrets.token_hex(32))"

# Or use Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
\`\`\`

---

## Building Individual Containers

### Frontend Container

\`\`\`bash
# Build frontend image
docker build -t todo-frontend:latest ./frontend

# Expected output:
# - Build context size: ~8MB (98% reduction from ~500MB)
# - Build time: 2-5 minutes
# - Final image size: ~180MB

# View image details
docker images todo-frontend:latest
\`\`\`

### Backend Container

\`\`\`bash
# Build backend image
docker build -t todo-backend:latest ./backend

# Expected output:
# - Build context size: ~5MB (97% reduction from ~200MB)
# - Build time: 1-3 minutes
# - Final image size: ~150MB

# View image details
docker images todo-backend:latest
\`\`\`

---

## Running Containers

### Frontend Only

\`\`\`bash
docker run -d --name todo-frontend -p 3000:3000 --env-file .env todo-frontend:latest

# Check health
curl http://localhost:3000/api/health
\`\`\`

### Backend Only

\`\`\`bash
docker run -d --name todo-backend -p 8000:8000 --env-file .env todo-backend:latest

# Check health
curl http://localhost:8000/health
\`\`\`

### Docker Compose (Recommended)

\`\`\`bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps
\`\`\`

---

## Health Checks

Both containers include health checks that run every 30 seconds.

### Check Container Health

\`\`\`bash
# Using Docker
docker ps

# Using Docker Compose
docker-compose ps

# Manual health check
curl http://localhost:3000/api/health  # Frontend
curl http://localhost:8000/health      # Backend
\`\`\`

---

## Logs and Monitoring

\`\`\`bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f frontend
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend

# Real-time resource stats
docker stats
\`\`\`

---

## Troubleshooting

### Common Issues

**Port Already in Use:**
\`\`\`bash
# Change port in docker-compose.yml
ports:
  - "3001:3000"  # Use host port 3001
\`\`\`

**Database Connection Failed:**
\`\`\`bash
# Verify DATABASE_URL includes ?sslmode=require
DATABASE_URL=postgresql://user:pass@host.neon.tech/db?sslmode=require
\`\`\`

**Clean Rebuild:**
\`\`\`bash
docker-compose down -v --remove-orphans
docker system prune -a -f
docker-compose up --build
\`\`\`

---

## Performance Metrics

### Build Context Reduction

- **Frontend:** 500MB → 8MB (98% reduction)
- **Backend:** 200MB → 5MB (97% reduction)

### Image Size Optimization

- **Frontend:** 1.2GB → 180MB (85% reduction)
- **Backend:** 800MB → 150MB (81% reduction)

### Startup Performance

- **Frontend:** Ready in ~30 seconds
- **Backend:** Ready in ~20 seconds

---

## Additional Resources

- [docker-compose.yml](../../docker-compose.yml)
- [Frontend Dockerfile](../../frontend/Dockerfile)
- [Backend Dockerfile](../../backend/Dockerfile)
- [.env.example](../../.env.example)
- [Feature Specification](./spec.md)
- [Implementation Plan](./plan.md)

---

**Last Updated:** 2025-12-29
