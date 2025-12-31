# Backend Dockerfile Contract
# Complete FastAPI + SQLModel Multi-Stage Production Dockerfile Template
# Base Image: python:3.13-slim (NOT Alpine due to psycopg2 compatibility)
# Target: Production-ready container (~150MB)
# Research: specs/001-docker-containerization/research.md

# ==============================================================================
# Stage 1: Builder
# Purpose: Install dependencies in virtual environment with build tools
# Output: /opt/venv (complete virtual environment)
# ==============================================================================
FROM python:3.13-slim AS builder

WORKDIR /app

# Install build dependencies (gcc for compiling C extensions, libpq-dev for PostgreSQL)
# --no-install-recommends saves ~50MB by skipping "recommended" packages
# rm -rf /var/lib/apt/lists/* saves ~20MB by removing apt cache
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment at /opt/venv
# Virtual environment provides clean separation and easy copying to runner stage
RUN python -m venv /opt/venv

# Activate virtual environment by adding to PATH
# This ensures pip installs to /opt/venv, not system Python
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements file for dependency installation
COPY requirements.txt .

# Install Python dependencies into virtual environment
# --no-cache-dir saves ~100-200MB by not caching downloaded packages
# --upgrade pip ensures latest pip (faster downloads, better dependency resolution)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==============================================================================
# Stage 2: Runner
# Purpose: Minimal production runtime with only required dependencies
# Output: Production-ready container (~150MB)
# ==============================================================================
FROM python:3.13-slim AS runner

WORKDIR /app

# Install runtime dependencies (PostgreSQL client library only, no dev headers)
# libpq5 is the shared library required by psycopg2-binary (~200KB)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security (UID 1001)
# Debian uses groupadd/useradd commands
RUN groupadd -g 1001 fastapi && \
    useradd -u 1001 -g fastapi -s /bin/bash -m fastapi

# Copy virtual environment from builder stage
# This includes all installed packages and binaries
COPY --from=builder /opt/venv /opt/venv

# Activate virtual environment by adding to PATH
ENV PATH="/opt/venv/bin:$PATH"

# Python environment variables for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy application code with correct ownership
# --chown ensures files are owned by fastapi user (no separate chown RUN needed)
COPY --chown=fastapi:fastapi ./app ./app

# Switch to non-root user
USER fastapi

# Expose port 8000 (FastAPI/Uvicorn default)
EXPOSE 8000

# Health check using Python's built-in urllib (no external dependencies)
# Checks /health endpoint every 30 seconds
# start-period=40s gives container time to start before health checks count
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').getcode()" || exit 1

# Start Uvicorn server in production mode
# --host 0.0.0.0 required for Docker networking (not 127.0.0.1)
# Single worker recommended for Kubernetes (horizontal pod scaling)
# Uses exec form (not shell form) for proper signal handling
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ==============================================================================
# Build Instructions:
#
# 1. Ensure requirements.txt includes all dependencies
# 2. Build image:
#    docker build -t todo-backend:latest -f Dockerfile ./backend
# 3. Run container:
#    docker run -p 8000:8000 \
#      -e DATABASE_URL=postgresql://user:pass@host.neon.tech/db \
#      -e BETTER_AUTH_SECRET=your-secret-key \
#      -e OPENAI_API_KEY=sk-your-key \
#      todo-backend:latest
#
# Expected Results:
# - Image size: ~150MB (81% reduction from ~800MB)
# - Build time: ~2-3 minutes (first build), ~30-60s (code changes)
# - Startup time: ~15 seconds
# - Running as: fastapi (UID 1001)
# ==============================================================================

# ==============================================================================
# Required Files:
#
# 1. backend/requirements.txt:
#    fastapi==0.115.0
#    sqlmodel==0.0.22
#    uvicorn[standard]==0.32.0
#    psycopg2-binary==2.9.9
#    pydantic==2.5.0
#    python-dotenv==1.0.0
#
# 2. backend/app/main.py with /health endpoint:
#    @app.get("/health")
#    async def health_check():
#        return {"status": "healthy"}
#
# 3. backend/.dockerignore (see backend.dockerignore.contract)
# ==============================================================================

# ==============================================================================
# Why python:3.13-slim instead of Alpine:
#
# Alpine Challenges:
# - Uses musl libc instead of glibc (many Python packages expect glibc)
# - Requires compiling psycopg2 from source (5-10 minute builds)
# - Potential runtime issues with compiled packages
# - Final image size similar after adding build tools (~120MB)
#
# Slim Benefits:
# - Uses glibc (standard C library)
# - Pre-compiled wheels available (psycopg2-binary)
# - Fast builds (no compilation needed)
# - Better compatibility with SQLModel, FastAPI, uvicorn
# - Only 30MB larger than Alpine (acceptable trade-off)
# ==============================================================================

# ==============================================================================
# Why psycopg2-binary:
#
# psycopg2 (source):
# - Requires compilation during pip install
# - Needs gcc and libpq-dev in runner stage
# - Slower builds
# - Links to system libpq
#
# psycopg2-binary (recommended):
# - Pre-compiled wheel with bundled libpq
# - No gcc required in runner stage
# - Only needs libpq5 runtime library (~200KB)
# - Faster builds
# - Officially recommended for Docker deployments
# ==============================================================================

# ==============================================================================
# Why single worker (not --workers 4):
#
# Single Worker Benefits:
# - Kubernetes handles horizontal scaling (multiple pods)
# - Simpler health checks and monitoring
# - Better resource allocation per pod
# - Easier debugging (single process)
#
# Multiple Workers Use Case:
# - Only if NOT using Kubernetes
# - Standalone Docker deployment
# - Vertical scaling within single container
# ==============================================================================

# ==============================================================================
# Troubleshooting:
#
# Issue: "psycopg2 not found" error
# Solution: Ensure psycopg2-binary in requirements.txt, not psycopg2
#
# Issue: "libpq.so.5: cannot open shared object file"
# Solution: Ensure libpq5 is installed in runner stage
#
# Issue: Health check failing
# Solution: Ensure /health route exists and returns 200 status
#
# Issue: Permission denied errors
# Solution: Ensure app/ directory owned by fastapi user (--chown in COPY)
#
# Issue: Cannot connect from frontend
# Solution: Ensure --host 0.0.0.0 (not 127.0.0.1)
# ==============================================================================
