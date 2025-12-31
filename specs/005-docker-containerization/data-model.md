# Phase 1 Design - Container Configuration Model

**Feature**: 005-docker-containerization
**Date**: 2025-12-29
**Type**: Infrastructure Design

---

## Overview

This document defines the container configuration model for the full-stack todo application. Unlike traditional data models that define database entities, this model specifies the structure, configuration, and runtime characteristics of our Docker containers and their orchestration.

---

## Container Entities

### 1. Frontend Container Entity

**Image Identity**:
```yaml
image_name: todo-frontend
image_tag: latest
base_image: node:20-alpine
registry: local (development) / ghcr.io (production)
```

**Build Configuration**:
```yaml
build:
  context: ./frontend
  dockerfile: Dockerfile
  stages:
    - deps:
        purpose: Install dependencies
        base: node:20-alpine
        system_packages: [libc6-compat]
        output: /app/node_modules

    - builder:
        purpose: Build Next.js application
        base: node:20-alpine
        input: node_modules from deps stage
        environment:
          NEXT_TELEMETRY_DISABLED: "1"
          NODE_ENV: production
        build_command: npm run build
        output: .next/standalone, .next/static, public/

    - runner:
        purpose: Production runtime
        base: node:20-alpine
        input: standalone, static, public from builder
        user: nextjs:nodejs
        uid: 1001
        gid: 1001
```

**Runtime Configuration**:
```yaml
runtime:
  port: 3000
  protocol: HTTP
  command: ["node", "server.js"]
  working_directory: /app
  user: nextjs
  entrypoint: null  # Use default

  environment_variables:
    required:
      - NEXT_PUBLIC_API_URL
      - BETTER_AUTH_SECRET
    optional:
      - NEXT_PUBLIC_OPENAI_DOMAIN_KEY
    build_time:
      - NEXT_TELEMETRY_DISABLED=1
      - NODE_ENV=production
    runtime:
      - NEXT_PUBLIC_API_URL (from .env)
      - BETTER_AUTH_SECRET (from .env)
```

**Health Check Configuration**:
```yaml
health_check:
  type: HTTP
  method: node_http_module
  endpoint: /api/health
  command: |
    node -e "require('http').get('http://localhost:3000/api/health', (r) => {
      process.exit(r.statusCode === 200 ? 0 : 1)
    })"
  interval: 30s
  timeout: 3s
  start_period: 40s
  retries: 3
  expected_response:
    status_code: 200
    body_contains: "healthy"
```

**Resource Configuration**:
```yaml
resources:
  limits:
    cpu: "1.0"
    memory: 512M
  reservations:
    cpu: "0.5"
    memory: 256M

  image_size:
    unoptimized: ~1.2GB
    optimized: ~180MB
    savings: 85%

  startup_time:
    target: <25s
    acceptable: <30s
    poor: >40s
```

**Network Configuration**:
```yaml
networking:
  expose_ports: [3000]
  publish_ports:
    - host: 3000
      container: 3000
      protocol: tcp

  internal_communication:
    - to: backend
      method: http
      url: http://backend:8000
      purpose: API requests from server components

  external_access:
    - from: browser
      port: 3000
      protocol: http
      url: http://localhost:3000
```

---

### 2. Backend Container Entity

**Image Identity**:
```yaml
image_name: todo-backend
image_tag: latest
base_image: python:3.13-slim
registry: local (development) / ghcr.io (production)
```

**Build Configuration**:
```yaml
build:
  context: ./backend
  dockerfile: Dockerfile
  stages:
    - builder:
        purpose: Install dependencies in virtual environment
        base: python:3.13-slim
        system_packages:
          - gcc (build tool)
          - libpq-dev (PostgreSQL headers)
        virtual_environment: /opt/venv
        requirements: requirements.txt
        pip_flags: [--no-cache-dir, --upgrade pip]
        output: /opt/venv/*

    - runner:
        purpose: Production runtime
        base: python:3.13-slim
        system_packages:
          - libpq5 (PostgreSQL client library)
        input: /opt/venv from builder
        user: fastapi:fastapi
        uid: 1001
        gid: 1001
```

**Runtime Configuration**:
```yaml
runtime:
  port: 8000
  protocol: HTTP
  command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
  working_directory: /app
  user: fastapi

  environment_variables:
    required:
      - DATABASE_URL
      - BETTER_AUTH_SECRET
    optional:
      - OPENAI_API_KEY
    build_time:
      - PYTHONUNBUFFERED=1
      - PYTHONDONTWRITEBYTECODE=1
      - PIP_NO_CACHE_DIR=1
    runtime:
      - DATABASE_URL (from .env)
      - BETTER_AUTH_SECRET (from .env)
      - OPENAI_API_KEY (from .env)
```

**Health Check Configuration**:
```yaml
health_check:
  type: HTTP
  method: python_urllib
  endpoint: /health
  command: |
    python -c "import urllib.request;
    urllib.request.urlopen('http://localhost:8000/health').getcode()" || exit 1
  interval: 30s
  timeout: 3s
  start_period: 40s
  retries: 3
  expected_response:
    status_code: 200
    body_contains: "healthy"
```

**Resource Configuration**:
```yaml
resources:
  limits:
    cpu: "1.0"
    memory: 512M
  reservations:
    cpu: "0.5"
    memory: 256M

  image_size:
    unoptimized: ~800MB
    optimized: ~150MB
    savings: 81%

  startup_time:
    target: <15s
    acceptable: <20s
    poor: >30s
```

**Network Configuration**:
```yaml
networking:
  expose_ports: [8000]
  publish_ports:
    - host: 8000
      container: 8000
      protocol: tcp

  internal_communication:
    - to: database
      method: postgresql
      url: ${DATABASE_URL}
      purpose: Data persistence

  external_access:
    - from: frontend
      port: 8000
      protocol: http
      url: http://backend:8000
    - from: browser
      port: 8000
      protocol: http
      url: http://localhost:8000
```

---

### 3. Docker Compose Service Entity

**Service Orchestration**:
```yaml
compose:
  version: "3.8"

  services:
    backend:
      metadata:
        container_name: todo-backend
        restart_policy: unless-stopped
        profile: [production, development]

      build:
        context: ./backend
        dockerfile: Dockerfile
        cache_from: [backend:latest]

      dependencies:
        startup_order: 1
        depends_on: []
        health_check_required: true

      networking:
        networks: [todo-network]
        internal_hostname: backend
        dns_resolution: automatic

      configuration:
        env_file: .env
        environment_overrides: {}

    frontend:
      metadata:
        container_name: todo-frontend
        restart_policy: unless-stopped
        profile: [production, development]

      build:
        context: ./frontend
        dockerfile: Dockerfile
        cache_from: [frontend:latest]

      dependencies:
        startup_order: 2
        depends_on:
          - backend:
              condition: service_healthy
        health_check_required: true

      networking:
        networks: [todo-network]
        internal_hostname: frontend
        dns_resolution: automatic

      configuration:
        env_file: .env
        environment_overrides:
          NEXT_PUBLIC_API_URL: http://backend:8000
```

**Network Definition**:
```yaml
networks:
  todo-network:
    driver: bridge
    ipam:
      driver: default
      config:
        - subnet: 172.18.0.0/16
    internal: false
    attachable: true

    service_discovery:
      method: dns
      resolution: automatic
      hostnames:
        - backend → 172.18.0.2
        - frontend → 172.18.0.3
```

**Volume Definition** (if needed in future):
```yaml
volumes:
  backend_cache:
    driver: local
    driver_opts:
      type: none
      device: ./backend/.cache
      o: bind
```

---

## Configuration Schema Models

### 1. Build Configuration Schema

```yaml
BuildConfiguration:
  context: string           # Relative path to build context
  dockerfile: string        # Dockerfile name
  target: string | null     # Multi-stage target (null = final stage)
  args: map<string, string> # Build arguments
  cache_from: list<string>  # Images for cache resolution
  labels: map<string, string>

  stages: list<BuildStage>
    - name: string
      base_image: string
      system_packages: list<string>
      package_manager:
        type: enum[apk, apt-get, yum]
        flags: list<string>
        cleanup: boolean
      commands: list<string>
      artifacts: list<string>
```

### 2. Runtime Configuration Schema

```yaml
RuntimeConfiguration:
  image: string
  command: list<string>     # exec form
  entrypoint: list<string> | null
  working_dir: string
  user: string              # username:group or uid:gid

  environment:
    variables: map<string, string>
    files: list<string>     # .env files
    secrets: list<string>   # Docker secrets

  ports:
    expose: list<int>       # Internal ports
    publish: list<PortMapping>
      - host: int
        container: int
        protocol: enum[tcp, udp]

  volumes:
    mounts: list<VolumeMount>
      - type: enum[bind, volume, tmpfs]
        source: string
        target: string
        read_only: boolean
```

### 3. Health Check Schema

```yaml
HealthCheckConfiguration:
  type: enum[http, tcp, exec]

  # For HTTP checks
  http:
    method: enum[GET, POST]
    endpoint: string
    expected_status: int
    expected_body: string | null

  # For exec checks
  exec:
    command: list<string>
    shell: boolean

  # Common parameters
  interval: duration        # e.g., "30s"
  timeout: duration         # e.g., "3s"
  start_period: duration    # e.g., "40s"
  retries: int              # e.g., 3

  # States
  states:
    - starting: "Within start_period, checks don't count"
    - healthy: "Check passed"
    - unhealthy: "Check failed after retries"
```

### 4. Network Configuration Schema

```yaml
NetworkConfiguration:
  driver: enum[bridge, host, overlay, macvlan, none]

  # For bridge networks
  bridge:
    subnet: cidr            # e.g., "172.18.0.0/16"
    gateway: ip             # e.g., "172.18.0.1"
    ip_range: cidr | null

  # DNS and service discovery
  dns:
    servers: list<ip>
    search: list<domain>
    options: list<string>

  service_discovery:
    enabled: boolean
    method: enum[dns, external]

  # Network policies
  policies:
    internal: boolean       # No external access
    attachable: boolean     # Other containers can attach
    ingress: boolean        # Swarm ingress network
```

### 5. Resource Limits Schema

```yaml
ResourceConfiguration:
  cpu:
    limit: string           # e.g., "1.0" (1 CPU)
    reservation: string     # e.g., "0.5" (0.5 CPU)
    shares: int | null      # Relative weight

  memory:
    limit: string           # e.g., "512M"
    reservation: string     # e.g., "256M"
    swap_limit: string | null

  pids:
    limit: int | null       # Max number of processes

  storage:
    read_bps: string | null   # e.g., "10mb"
    write_bps: string | null
    read_iops: int | null
    write_iops: int | null
```

---

## Security Configuration Models

### 1. User Configuration

```yaml
UserConfiguration:
  # Alpine (adduser/addgroup)
  alpine:
    group_command: addgroup --system --gid {gid} {group}
    user_command: adduser --system --uid {uid} {user}
    shell: /sbin/nologin

  # Debian (useradd/groupadd)
  debian:
    group_command: groupadd -g {gid} {group}
    user_command: useradd -u {uid} -g {group} -s /bin/bash -m {user}
    shell: /bin/bash

  # Common configuration
  common:
    uid: 1001               # Well above system range (0-999)
    gid: 1001
    home_dir: /home/{user}
    create_home: boolean
    no_login: boolean
```

### 2. File Permissions

```yaml
FilePermissions:
  ownership:
    user: string            # e.g., "nextjs"
    group: string           # e.g., "nodejs"
    uid: int                # e.g., 1001
    gid: int                # e.g., 1001

  permissions:
    files: "644"            # rw-r--r--
    directories: "755"      # rwxr-xr-x
    executables: "755"      # rwxr-xr-x

  # Set during COPY
  copy_with_chown:
    command: COPY --chown={user}:{group} {source} {dest}
    benefits:
      - Single layer (no extra chown RUN)
      - Correct ownership from start
```

### 3. Security Context

```yaml
SecurityContext:
  # Docker configuration
  docker:
    user: "1001:1001"
    read_only_rootfs: boolean
    no_new_privileges: boolean
    cap_drop: [ALL]
    cap_add: [] # Add only required capabilities

  # Kubernetes configuration (future)
  kubernetes:
    runAsUser: 1001
    runAsGroup: 1001
    runAsNonRoot: true
    readOnlyRootFilesystem: true
    allowPrivilegeEscalation: false
    seccompProfile:
      type: RuntimeDefault
```

---

## Dependency Configuration Models

### 1. Build Dependencies

**Frontend (Node.js)**:
```yaml
frontend_build_dependencies:
  system:
    - package: libc6-compat
      purpose: glibc compatibility for npm packages
      size: ~2MB
      stage: deps

  npm:
    - package: next
      version: "15.x"
      purpose: Framework
    - package: typescript
      version: "5.x"
      purpose: Type checking
    - package: tailwindcss
      version: "3.x"
      purpose: Styling
```

**Backend (Python)**:
```yaml
backend_build_dependencies:
  system:
    - package: gcc
      purpose: Compile C extensions
      size: ~50MB
      stage: builder
    - package: libpq-dev
      purpose: PostgreSQL development headers
      size: ~10MB
      stage: builder

  python:
    - package: fastapi
      version: "0.115.0"
      purpose: Web framework
    - package: sqlmodel
      version: "0.0.22"
      purpose: ORM
    - package: uvicorn[standard]
      version: "0.32.0"
      purpose: ASGI server
```

### 2. Runtime Dependencies

**Frontend (Node.js)**:
```yaml
frontend_runtime_dependencies:
  system:
    - package: libc6-compat
      purpose: glibc compatibility
      size: ~2MB
      required: true

  bundled:
    description: Next.js standalone bundles all runtime deps
    location: .next/standalone/node_modules
    size: ~50MB
```

**Backend (Python)**:
```yaml
backend_runtime_dependencies:
  system:
    - package: libpq5
      purpose: PostgreSQL client library
      size: ~200KB
      required: true

  python:
    location: /opt/venv
    size: ~100MB
    packages:
      - psycopg2-binary (pre-compiled wheel)
      - fastapi (runtime only)
      - sqlmodel (runtime only)
      - uvicorn[standard] (with uvloop, httptools)
```

---

## Build Artifact Models

### 1. Frontend Build Artifacts

```yaml
frontend_artifacts:
  standalone_output:
    location: .next/standalone/
    contents:
      - server.js (self-contained server)
      - node_modules/ (minimal runtime deps)
      - package.json (minimal manifest)
    size: ~50MB
    purpose: Production server

  static_assets:
    location: .next/static/
    contents:
      - chunks/ (code splitting bundles)
      - css/ (compiled stylesheets)
      - media/ (optimized images)
    size: ~10-20MB
    purpose: Client-side assets

  public_files:
    location: public/
    contents:
      - favicon.ico
      - images/
      - robots.txt
    size: ~1-5MB
    purpose: Static files

  total_size: ~70-80MB
  compression_ratio: 93% (vs ~1.2GB unoptimized)
```

### 2. Backend Build Artifacts

```yaml
backend_artifacts:
  virtual_environment:
    location: /opt/venv/
    contents:
      - bin/ (executables: uvicorn, python)
      - lib/python3.13/site-packages/ (all packages)
      - pyvenv.cfg (venv metadata)
    size: ~100MB
    purpose: Isolated Python environment

  application_code:
    location: /app/
    contents:
      - app/main.py
      - app/routers/
      - app/models/
      - app/database.py
    size: ~500KB - 2MB
    purpose: Application logic

  total_size: ~102-105MB
  compression_ratio: 81% (vs ~800MB unoptimized)
```

---

## Performance Metrics Models

### 1. Build Performance

```yaml
build_metrics:
  frontend:
    first_build:
      duration: 4-5 minutes
      stages:
        - deps: 60-90s (npm ci)
        - builder: 120-180s (npm run build)
        - runner: 10-20s (copy artifacts)

    code_change_rebuild:
      duration: 1-2 minutes
      cached_stages:
        - deps (node_modules cached)
      rebuild_stages:
        - builder (only build changed)
        - runner (copy new artifacts)

    dependency_change_rebuild:
      duration: 3-4 minutes
      rebuild_stages:
        - deps (npm ci again)
        - builder (rebuild all)
        - runner (copy artifacts)

  backend:
    first_build:
      duration: 2-3 minutes
      stages:
        - builder: 90-120s (pip install)
        - runner: 30-60s (copy venv)

    code_change_rebuild:
      duration: 30-60s
      cached_stages:
        - builder (venv cached)
      rebuild_stages:
        - runner (copy new code)

    dependency_change_rebuild:
      duration: 2-3 minutes
      rebuild_stages:
        - builder (pip install again)
        - runner (copy new venv)
```

### 2. Runtime Performance

```yaml
runtime_metrics:
  frontend:
    startup_time:
      target: <25s
      acceptable: <30s
      poor: >40s

    memory_usage:
      idle: ~100-150MB
      active: ~200-300MB
      peak: ~400-500MB

    response_time:
      p50: <100ms
      p95: <300ms
      p99: <500ms

  backend:
    startup_time:
      target: <15s
      acceptable: <20s
      poor: >30s

    memory_usage:
      idle: ~80-120MB
      active: ~150-250MB
      peak: ~300-400MB

    response_time:
      p50: <50ms
      p95: <150ms
      p99: <300ms
```

---

## Environment Variables Model

### 1. Variable Types

```yaml
environment_variable_types:
  build_time:
    description: Baked into image, cannot change
    examples:
      - NEXT_TELEMETRY_DISABLED=1
      - NODE_ENV=production
      - PYTHONUNBUFFERED=1
    usage: ENV directive in Dockerfile

  runtime:
    description: Passed when container starts
    examples:
      - DATABASE_URL (from .env)
      - BETTER_AUTH_SECRET (from .env)
      - OPENAI_API_KEY (from .env)
    usage: docker run -e or docker-compose environment

  public:
    description: Exposed to browser (Next.js)
    prefix: NEXT_PUBLIC_
    examples:
      - NEXT_PUBLIC_API_URL
      - NEXT_PUBLIC_OPENAI_DOMAIN_KEY
    security: No secrets allowed

  private:
    description: Server-only (Next.js)
    prefix: none
    examples:
      - DATABASE_URL
      - BETTER_AUTH_SECRET
    security: Never exposed to browser
```

### 2. Variable Configuration

```yaml
frontend_environment:
  required:
    - name: NEXT_PUBLIC_API_URL
      type: public
      default: http://backend:8000
      description: Backend API URL
      example: http://localhost:8000

    - name: BETTER_AUTH_SECRET
      type: private
      default: null
      description: JWT signing secret (32+ chars)
      example: "openssl rand -hex 32"

  optional:
    - name: NEXT_PUBLIC_OPENAI_DOMAIN_KEY
      type: public
      default: null
      description: OpenAI domain API key
      example: pk-your-key

backend_environment:
  required:
    - name: DATABASE_URL
      type: private
      default: null
      description: PostgreSQL connection string
      example: postgresql://user:pass@host.neon.tech/db

    - name: BETTER_AUTH_SECRET
      type: private
      default: null
      description: JWT signing secret (must match frontend)
      example: "openssl rand -hex 32"

  optional:
    - name: OPENAI_API_KEY
      type: private
      default: null
      description: OpenAI API key for AI features
      example: sk-your-key
```

---

## Image Optimization Targets

```yaml
optimization_targets:
  frontend:
    unoptimized_size: 1.2GB
    optimized_size: 180MB
    target_size: <200MB
    reduction: 85%

    techniques_applied:
      - Multi-stage builds (3 stages)
      - Next.js standalone output
      - Alpine base image
      - .dockerignore (exclude 400MB+)
      - No npm cache
      - Production-only dependencies

  backend:
    unoptimized_size: 800MB
    optimized_size: 150MB
    target_size: <200MB
    reduction: 81%

    techniques_applied:
      - Multi-stage builds (2 stages)
      - Virtual environment isolation
      - Slim base image (not Alpine)
      - .dockerignore (exclude 200MB+)
      - No pip cache
      - psycopg2-binary (pre-compiled)

  total:
    unoptimized_size: 2.0GB
    optimized_size: 330MB
    target_size: <400MB
    reduction: 84%
```

---

## Validation Checklist

### Build Configuration Validation

- [ ] Base images pinned to major versions
- [ ] Multi-stage builds implemented (builder + runner)
- [ ] System packages minimized (only required)
- [ ] Package manager caches cleaned up
- [ ] Build context optimized (.dockerignore)
- [ ] Layer caching optimized (dependency files first)

### Runtime Configuration Validation

- [ ] Non-root user execution (UID 1001)
- [ ] Port bindings correct (3000, 8000)
- [ ] Environment variables validated on startup
- [ ] Health checks implemented (HTTP)
- [ ] Resource limits configured
- [ ] Restart policies set

### Security Configuration Validation

- [ ] No secrets in Dockerfile or image
- [ ] No root user execution
- [ ] Minimal system packages
- [ ] Vulnerability scanning enabled
- [ ] File permissions correct (644/755)
- [ ] Read-only root filesystem (optional)

### Performance Configuration Validation

- [ ] Image size < 200MB per service
- [ ] Build time < 5 minutes (first build)
- [ ] Startup time < 30 seconds
- [ ] Layer caching effective (< 2 min rebuild)
- [ ] Memory usage < 512MB per service

---

## References

- Research findings: `specs/005-docker-containerization/research.md`
- Next.js Docker documentation: https://nextjs.org/docs/deployment#docker-image
- FastAPI Docker documentation: https://fastapi.tiangolo.com/deployment/docker/
- Docker multi-stage builds: https://docs.docker.com/build/building/multi-stage/
- Docker Compose specification: https://docs.docker.com/compose/compose-file/

---

**Status**: Design Complete | **Next Phase**: Implementation
