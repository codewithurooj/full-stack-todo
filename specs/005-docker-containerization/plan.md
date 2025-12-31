# Implementation Plan: Docker Containerization

**Branch**: `005-docker-containerization` | **Date**: 2025-12-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-docker-containerization/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Package the Next.js 15+ frontend and FastAPI backend applications into production-ready Docker containers with multi-stage builds, optimized for minimal image size (<200 MB each), fast startup (<30 seconds), and security (non-root user execution). Deliverables include production Dockerfiles for both services, .dockerignore files, production docker-compose.yml, and comprehensive testing of containerized deployment using dockerfile-generator skill patterns.

## Technical Context

**Language/Version**: Node.js 20 (frontend), Python 3.13 (backend)
**Primary Dependencies**: Next.js 15, React 19, FastAPI 0.115, SQLModel 0.0.22, uvicorn 0.32, Docker Engine 20.10+, Docker Compose v2
**Storage**: N/A (containerization layer only, connects to existing Neon PostgreSQL)
**Testing**: `docker build`, `docker run`, `docker-compose up`, health check validation, container startup tests
**Target Platform**: Docker containers (Linux-based Alpine and Slim variants), compatible with Minikube for Phase 4 Kubernetes deployment
**Project Type**: web (frontend + backend microservices)
**Performance Goals**: Image build <5 min per service, container startup <30 sec, final image sizes <200 MB each, health check response <2 sec
**Constraints**: Multi-stage builds mandatory, non-root user (UID 1001) required, health checks must be included, Alpine/Slim base images only, no secrets in images
**Scale/Scope**: 2 production containers (frontend, backend), 1 production docker-compose.yml, 2 .dockerignore files, 2 production Dockerfiles

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: PASS

**Validation**:
- ✅ Follows Phase IV containerization requirements from Hackathon II roadmap
- ✅ Uses dockerfile-generator skill (spec-driven development methodology)
- ✅ Maintains single repository structure (no new projects added)
- ✅ Follows minimalist principle (only necessary containerization artifacts)
- ✅ No architectural complexity added (stateless containerization layer)
- ✅ Security-first design (non-root execution, no secrets in images)
- ✅ Performance constraints documented (image size, startup time)

**No violations detected** - Feature aligns with all constitutional principles.

## Project Structure

### Documentation (this feature)

```text
specs/005-docker-containerization/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output - Docker best practices for Next.js & FastAPI
├── data-model.md        # Phase 1 output - Container configuration model
├── quickstart.md        # Phase 1 output - Docker setup and deployment guide
├── contracts/           # Phase 1 output - Dockerfile templates and schemas
│   ├── frontend.dockerfile.template
│   ├── backend.dockerfile.template
│   ├── docker-compose.yml.template
│   ├── frontend.dockerignore.template
│   └── backend.dockerignore.template
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
# Root Level
docker-compose.yml                # Production orchestration (replaces existing dev version)
.env.example                     # Updated with Docker-specific variables

# Frontend Container
frontend/
├── Dockerfile                   # Production multi-stage Dockerfile (NEW)
├── .dockerignore                # Build context exclusions (NEW)
├── next.config.js               # Updated for standalone output mode
├── package.json                 # Existing dependencies
├── package-lock.json            # Existing lock file
├── app/                         # Existing Next.js app
├── components/                  # Existing components
├── lib/                         # Existing utilities
└── public/                      # Existing static assets

# Backend Container
backend/
├── Dockerfile                   # Production multi-stage Dockerfile (NEW)
├── .dockerignore                # Build context exclusions (NEW)
├── requirements.txt             # Existing dependencies (unchanged)
├── app/                         # Existing FastAPI app
│   ├── main.py                  # Entry point (health check verified)
│   ├── config.py                # Configuration management
│   ├── database.py              # Database session
│   ├── models/                  # SQLModel models
│   ├── routes/                  # API routes
│   ├── middleware/              # Auth middleware
│   └── mcp_server/              # MCP tools (Feature 002)
└── tests/                       # Existing tests

# Development Artifacts (will be removed)
frontend/Dockerfile.dev          # To be replaced by production Dockerfile
backend/Dockerfile.dev           # To be replaced by production Dockerfile
```

**Structure Decision**: Web application (Option 2) with separate frontend and backend directories. Containerization adds production Dockerfiles and .dockerignore files to each service directory, plus production docker-compose.yml at root. Existing development docker-compose.yml will be replaced with production-ready version that can serve both dev and prod environments through separate compose files.

## Complexity Tracking

> **Not Applicable** - No constitutional violations detected.

---

## Phase IV: Containerization & Kubernetes

> **This section is REQUIRED for this feature as it implements Phase IV containerization**

### Docker Strategy

**Containers to Build**:
- ✅ **`frontend`** - Next.js 15 application with standalone output, Node.js 20 Alpine base, multi-stage build
- ✅ **`backend`** - FastAPI application with uvicorn server, Python 3.13 Slim base, multi-stage build
- ❌ **`mcp-server`** - Not separated (integrated into backend container as part of Feature 002)

**Multi-Stage Build Pattern**:

**Frontend Strategy** (Node.js 20 Alpine):
```dockerfile
# Stage 1: Dependencies - Install all dependencies including devDependencies
FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Stage 2: Builder - Build Next.js standalone output
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Stage 3: Runner - Minimal runtime image with only production files
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy only necessary files from builder
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/api/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

CMD ["node", "server.js"]
```

**Backend Strategy** (Python 3.13 Slim):
```dockerfile
# Stage 1: Builder - Install dependencies and create virtual environment
FROM python:3.13-slim AS builder
WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runner - Minimal runtime image
FROM python:3.13-slim AS runner
WORKDIR /app

# Install runtime dependencies only (PostgreSQL client)
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -g 1001 fastapi && \
    useradd -u 1001 -g fastapi -s /bin/bash -m fastapi

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Copy application code
COPY --chown=fastapi:fastapi ./app ./app

USER fastapi
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').getcode()" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**dockerfile-generator Skill Usage**:
- ✅ Use `dockerfile-generator` skill to create initial Dockerfile templates
- ✅ Skill will analyze package.json and requirements.txt for optimal base images
- ✅ Skill will generate .dockerignore patterns based on gitignore and build artifacts
- ✅ Manual refinement needed for Next.js standalone output configuration
- ✅ Validate generated Dockerfiles against security best practices

**Health Check Configurations**:

| Service | Endpoint | Interval | Timeout | Retries | Start Period |
|---------|----------|----------|---------|---------|--------------|
| Frontend | `http://localhost:3000/api/health` | 30s | 3s | 3 | 40s |
| Backend | `http://localhost:8000/health` | 30s | 3s | 3 | 40s |

**Health Check Implementation Requirements**:
- Frontend: Create `/app/api/health/route.ts` returning `{"status": "healthy", "timestamp": "..."}`
- Backend: Verify existing `/health` endpoint in `app/main.py` (should exist from Phase 2)
- Both must return HTTP 200 status code
- Both must respond within timeout period
- Failed health checks trigger container restart in orchestration

**Environment Variable Management**:

**Frontend Environment Variables**:
```bash
# Build-time (baked into image)
NEXT_TELEMETRY_DISABLED=1
NODE_ENV=production

# Runtime (passed via docker-compose or kubernetes)
NEXT_PUBLIC_API_URL=http://backend:8000  # Internal service name for container networking
BETTER_AUTH_SECRET=<secret-32-chars>     # Shared secret with backend
NEXT_PUBLIC_OPENAI_DOMAIN_KEY=<key>      # Optional for MCP features
```

**Backend Environment Variables**:
```bash
# Build-time (baked into image)
PYTHONUNBUFFERED=1

# Runtime (passed via docker-compose or kubernetes)
DATABASE_URL=postgresql://user:pass@host.neon.tech/dbname
BETTER_AUTH_SECRET=<secret-32-chars>     # Shared secret with frontend
OPENAI_API_KEY=sk-<key>                  # For MCP server (Feature 002)
CORS_ORIGINS=["http://localhost:3000", "http://frontend:3000"]
```

**Secret Management Strategy**:
- ❌ **Never** hardcode secrets in Dockerfiles or commit .env files
- ✅ Use `.env.example` with placeholder values for documentation
- ✅ Pass secrets via `docker-compose` environment variables or env_file
- ✅ For Kubernetes: Use ConfigMaps (non-sensitive) and Secrets (sensitive)
- ✅ Local development: Use `.env` file (gitignored) loaded by docker-compose
- ✅ Production: Use external secret managers (covered in Phase 5)

**.dockerignore Pattern Strategy**:

**Frontend .dockerignore**:
```
# Dependencies (will be installed via npm ci)
node_modules
npm-debug.log*
yarn-debug.log*
yarn-error.log*
package-lock.json

# Next.js build output (will be generated)
.next/
out/

# Environment files (secrets)
.env
.env*.local
.env.production

# Git and IDE
.git
.gitignore
.vscode
.idea

# Testing
coverage
*.test.ts
*.test.tsx
**/__tests__

# Documentation
README.md
*.md
docs/

# Development files
Dockerfile.dev
docker-compose.yml
.eslintrc.json
tsconfig.json
```

**Backend .dockerignore**:
```
# Python cache and bytecode
__pycache__
*.py[cod]
*$py.class
*.so
.Python

# Virtual environments
venv/
env/
ENV/

# Environment files (secrets)
.env
.env.*

# Testing
.pytest_cache
.coverage
htmlcov/
*.test.py

# Git and IDE
.git
.gitignore
.vscode
.idea

# Documentation
README.md
*.md
docs/

# Development files
Dockerfile.dev
docker-compose.yml

# Database migrations (handled separately)
alembic/versions/*.py
```

**Image Size Optimization Techniques**:
1. **Multi-stage builds**: Separate build and runtime stages
2. **Alpine/Slim base images**: Minimal OS footprint
3. **Layer caching**: Copy dependency files before source code
4. **Combine RUN commands**: Reduce layer count with `&&` chaining
5. **Clean package manager cache**: `--no-cache-dir` for pip, `rm -rf /var/lib/apt/lists/*` for apt
6. **Exclude unnecessary files**: Aggressive .dockerignore patterns
7. **Next.js standalone output**: Only bundle required Node.js runtime
8. **Python virtual environment**: Isolate dependencies from system Python

**Expected Image Sizes**:
- Frontend (unoptimized): ~1.2 GB
- Frontend (optimized): <180 MB (target: <200 MB)
- Backend (unoptimized): ~800 MB
- Backend (optimized): <150 MB (target: <200 MB)

### Helm Chart Design

> **NOT IN SCOPE for this feature** - Helm charts will be created in Step 3 (helm-chart-builder) using the helm-chart-builder skill after Docker containerization is complete and tested.

**Deferred to Future Phase**:
- Chart structure design: Deferred to `002-helm-charts` feature
- Kubernetes resource definitions: Deferred to `002-helm-charts` feature
- kubectl-ai and kagent usage: Deferred to Phase IV Step 4 (Kubernetes deployment)

---

## Implementation Phases

### Phase 0: Research - Docker Best Practices

**Objective**: Gather comprehensive knowledge about Docker containerization patterns for Next.js 15+ and FastAPI with Python 3.13+ to inform optimal Dockerfile design.

**Research Questions**:
1. **Next.js 15+ Containerization**:
   - How to configure Next.js standalone output mode for minimal Docker images?
   - What are the best practices for multi-stage builds with Next.js 15+?
   - How to handle static assets and public files in containerized Next.js?
   - What Node.js Alpine image version is compatible with Next.js 15?
   - How to implement health checks for Next.js applications in Docker?

2. **FastAPI Containerization**:
   - What are the optimal Python 3.13 base images (slim vs alpine)?
   - How to structure multi-stage builds for FastAPI with SQLModel dependencies?
   - How to handle PostgreSQL client library (psycopg2) in minimal images?
   - What are the best practices for Python virtual environments in containers?
   - How to run uvicorn in production mode within Docker?

3. **Security Best Practices**:
   - How to configure non-root user execution (UID 1001)?
   - What are the minimal required system packages for each runtime?
   - How to scan Docker images for vulnerabilities?
   - What are the security implications of different base images?

4. **Performance Optimization**:
   - How to optimize Docker layer caching for faster rebuilds?
   - What are the best practices for .dockerignore patterns?
   - How to minimize image size without sacrificing functionality?
   - How to optimize container startup time?

5. **Docker Compose**:
   - How to configure networking between frontend and backend containers?
   - What are the best practices for environment variable management?
   - How to implement health checks and dependency management?
   - How to structure docker-compose for both dev and prod environments?

**Research Deliverables** (output to `research.md`):
- Next.js standalone output configuration guide
- Python virtual environment best practices
- Security hardening checklist
- Image size optimization techniques
- Docker Compose networking patterns
- Health check implementation patterns
- .dockerignore pattern library
- Base image comparison (Alpine vs Slim vs Distroless)

**Research Sources**:
- Next.js official Docker documentation (https://nextjs.org/docs/deployment#docker-image)
- FastAPI deployment best practices (https://fastapi.tiangolo.com/deployment/docker/)
- Docker official documentation (multi-stage builds, health checks)
- Python Docker official images guide (https://hub.docker.com/_/python)
- Node.js Docker official images guide (https://hub.docker.com/_/node)
- Community best practices (Docker Hub, GitHub examples)

**Success Criteria**:
- ✅ Documented Next.js standalone build configuration
- ✅ Identified optimal base images for both services
- ✅ Security best practices checklist created
- ✅ Performance optimization techniques documented
- ✅ Docker Compose patterns identified

---

### Phase 1: Design - Container Architecture

**Objective**: Design the complete containerization architecture including Dockerfile structures, configuration models, and deployment workflows based on Phase 0 research findings.

**Design Activities**:

1. **Container Configuration Model** (output to `data-model.md`):
   - Document container configuration schema (environment variables, ports, volumes)
   - Define health check specifications for both services
   - Design build arguments and runtime arguments
   - Document resource limits and constraints
   - Define container networking model

2. **Dockerfile Templates** (output to `contracts/`):
   - Create `frontend.dockerfile.template` with multi-stage build
   - Create `backend.dockerfile.template` with virtual environment
   - Document build stages and layer optimization strategies
   - Include inline documentation for each instruction

3. **Docker Compose Configuration** (output to `contracts/`):
   - Design `docker-compose.yml.template` with service definitions
   - Configure service dependencies and health checks
   - Design environment variable injection strategy
   - Document networking and volume configurations

4. **Build Context Exclusions** (output to `contracts/`):
   - Create `frontend.dockerignore.template` with comprehensive patterns
   - Create `backend.dockerignore.template` with Python-specific patterns
   - Document rationale for each exclusion pattern

5. **Quickstart Guide** (output to `quickstart.md`):
   - Step-by-step Docker setup instructions
   - Environment variable configuration guide
   - Build and run commands for local testing
   - Troubleshooting common issues
   - Minikube preparation steps

**Design Deliverables**:
- `data-model.md`: Container configuration schema and specifications
- `contracts/frontend.dockerfile.template`: Annotated frontend Dockerfile
- `contracts/backend.dockerfile.template`: Annotated backend Dockerfile
- `contracts/docker-compose.yml.template`: Production orchestration template
- `contracts/frontend.dockerignore.template`: Frontend build exclusions
- `contracts/backend.dockerignore.template`: Backend build exclusions
- `quickstart.md`: Docker deployment guide

**Design Principles**:
- **Security First**: Non-root execution, minimal attack surface
- **Performance Optimized**: Layer caching, minimal image sizes
- **Developer Friendly**: Clear documentation, easy local testing
- **Production Ready**: Health checks, graceful shutdown, logging
- **Kubernetes Compatible**: Standard labels, portable configurations

**Success Criteria**:
- ✅ All design artifacts created and reviewed
- ✅ Dockerfile templates validate against best practices
- ✅ Configuration model supports both dev and prod environments
- ✅ Quickstart guide enables developer onboarding in <15 minutes

---

### Phase 2: Implementation - Generate Tasks

**Objective**: Use `/sp.tasks` command to generate detailed, dependency-ordered implementation tasks based on this plan and Phase 0-1 artifacts.

**Note**: This phase is **NOT executed by `/sp.plan`**. The `/sp.tasks` command will be run separately after Phase 0 and Phase 1 are complete.

**Expected Task Categories** (preview only, actual tasks generated by `/sp.tasks`):
1. **Frontend Containerization**:
   - Update next.config.js for standalone output
   - Create production Dockerfile
   - Create .dockerignore
   - Create frontend health check endpoint
   - Test frontend container build and run

2. **Backend Containerization**:
   - Create production Dockerfile
   - Create .dockerignore
   - Verify health check endpoint exists
   - Test backend container build and run

3. **Orchestration**:
   - Create production docker-compose.yml
   - Update .env.example
   - Configure container networking
   - Test full stack with docker-compose

4. **Testing & Validation**:
   - Verify image sizes (<200 MB each)
   - Verify startup times (<30 seconds)
   - Verify health checks pass
   - Test frontend-to-backend communication
   - Security scan images

5. **Documentation & Cleanup**:
   - Update root README.md with Docker instructions
   - Remove development Dockerfiles
   - Document Minikube loading steps
   - Create troubleshooting guide

**Task Generation Input**:
- This plan document
- Phase 0 research findings (research.md)
- Phase 1 design artifacts (data-model.md, contracts/, quickstart.md)
- Feature specification (spec.md)

**Success Criteria**:
- ✅ All tasks are actionable and specific
- ✅ Tasks have clear dependencies
- ✅ Tasks include acceptance criteria
- ✅ Tasks map to user stories from spec.md

---

## Risk Analysis

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Next.js standalone output incompatible with existing app structure | Low | High | Research phase validates compatibility, fallback to standard build if needed |
| Python 3.13 slim missing required system libraries | Medium | Medium | Document all required system packages in research phase, test thoroughly |
| Container networking issues between frontend and backend | Low | Medium | Use Docker Compose networking, test connectivity with health checks |
| Image size exceeds 200 MB target | Medium | Low | Aggressive .dockerignore patterns, multi-stage builds, monitor size during builds |
| Health check endpoints slow or missing | Low | Medium | Verify endpoints exist in Phase 2, implement if missing, optimize response time |
| Environment variable configuration complexity | Low | Low | Clear documentation in quickstart.md, .env.example with all required variables |

### Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Developers unfamiliar with Docker workflows | Medium | Low | Comprehensive quickstart guide, clear error messages, troubleshooting section |
| Secret management errors (committed .env files) | Medium | High | Update .gitignore, documentation warnings, use .env.example pattern |
| Build failures due to network issues | Medium | Low | Document retry strategies, use build caching, layer optimization |
| Incompatibility with Minikube | Low | High | Test Minikube loading early, document workarounds, use standard Kubernetes patterns |

---

## Success Metrics

### Build Performance Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Frontend image build time | <5 minutes | `time docker build` on standard dev machine |
| Backend image build time | <3 minutes | `time docker build` on standard dev machine |
| Frontend image size | <200 MB | `docker images` after build |
| Backend image size | <200 MB | `docker images` after build |
| Docker Compose startup time | <60 seconds | `time docker-compose up` until all healthy |

### Runtime Performance Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Frontend container startup | <30 seconds | Docker logs timestamp from start to health check pass |
| Backend container startup | <30 seconds | Docker logs timestamp from start to health check pass |
| Frontend memory usage (idle) | <256 MB | `docker stats` after startup |
| Backend memory usage (idle) | <256 MB | `docker stats` after startup |
| Health check response time | <2 seconds | Health check timeout configuration |
| Health check success rate | >95% | Monitor over 10-minute period |

### Quality Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Security vulnerabilities (critical) | 0 | `docker scan` or Trivy scan |
| Security vulnerabilities (high) | 0 | `docker scan` or Trivy scan |
| Non-root user execution | 100% | Verify with `docker exec` user check |
| .dockerignore coverage | >90% unnecessary files excluded | Manual review of build context size |
| Developer onboarding time | <15 minutes | Time to run containers from quickstart guide |

### Functional Validation

| Validation | Method |
|------------|--------|
| Frontend serves all routes correctly | Manual browser testing of all pages |
| Backend API endpoints respond correctly | Manual API testing with curl or Postman |
| Frontend-to-backend communication works | Test task CRUD operations end-to-end |
| Environment variables loaded correctly | Verify config values in container logs |
| Health checks pass consistently | Monitor Docker health status over time |
| Containers restart on failure | Kill process and verify auto-restart |

---

## Dependencies

### External Dependencies

- **Docker Engine** 20.10+ installed on development machines
- **Docker Compose** v2+ installed for orchestration
- **Node.js 20** compatible with Next.js 15 (verified in package.json)
- **Python 3.13** compatible with FastAPI and SQLModel (verified in requirements.txt)
- **Neon PostgreSQL** cloud service accessible from containers
- **dockerfile-generator skill** available in Claude Code

### Internal Dependencies

- **Frontend application** exists at `/frontend` with package.json
- **Backend application** exists at `/backend` with requirements.txt
- **Health check endpoints** implemented or implementable in both services
- **next.config.js** supports standalone output configuration
- **Environment variables** documented and available for configuration

### Feature Dependencies

- **Phase 2 completion**: All CRUD features, authentication, and MCP server must be working
- **Testing infrastructure**: Pytest and Jest tests pass before containerization
- **Database migrations**: Alembic migrations compatible with container deployment

---

## Out of Scope

### Explicitly Not Included in This Feature

- ❌ **Container Registry**: Pushing images to Docker Hub, ACR, GCR (covered in Phase 5)
- ❌ **Helm Charts**: Kubernetes deployment manifests (covered in Step 3: helm-chart-builder)
- ❌ **CI/CD Pipeline**: Automated builds and deployments (covered in Phase 5)
- ❌ **Monitoring**: Prometheus, Grafana, logging aggregation (covered in Phase 5)
- ❌ **Database Container**: PostgreSQL containerization (using Neon cloud service)
- ❌ **SSL/TLS**: Certificate management (handled at ingress level in Kubernetes)
- ❌ **Automated Security Scanning**: Pipeline integration (covered in Phase 5)
- ❌ **Multi-environment Configs**: Separate dev/staging/prod compose files (Phase 5)
- ❌ **Load Balancing**: Beyond Docker Compose (covered in Kubernetes phase)
- ❌ **Backup/Restore**: Container data persistence strategies (Phase 5)

### Future Enhancements

These features may be added in later phases but are not required for Phase IV containerization:

- Advanced health check logic (database connectivity verification)
- Container resource limits and quotas (memory, CPU)
- Horizontal scaling with Docker Swarm
- Development Dockerfile with hot-reload
- Container image signing and verification
- Advanced logging configurations (JSON structured logs)
- Container metrics collection
- Graceful shutdown handlers

---

## Appendix

### Glossary

- **Multi-stage Build**: Docker build pattern that uses multiple FROM statements to create intermediate images, copying only necessary artifacts to final image
- **Standalone Output**: Next.js build mode that bundles only required Node.js runtime and dependencies for minimal deployment size
- **Non-root User**: Container security practice running application processes as non-privileged user (UID 1001) instead of root
- **Health Check**: Docker/Kubernetes feature that periodically tests if container is responding correctly, enabling auto-restart on failure
- **.dockerignore**: File that specifies patterns to exclude from Docker build context, reducing image size and build time
- **Alpine Linux**: Minimal Linux distribution (~5 MB) commonly used for Docker base images
- **Slim Image**: Debian-based Python image variant that's larger than Alpine but more compatible (~40 MB)
- **Layer Caching**: Docker optimization that reuses unchanged layers from previous builds to speed up rebuilds
- **Build Context**: Files and directories sent to Docker daemon during build process (controlled by .dockerignore)

### Reference Links

- [Next.js Docker Documentation](https://nextjs.org/docs/deployment#docker-image)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/docker/)
- [Docker Multi-stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [Docker Health Checks](https://docs.docker.com/engine/reference/builder/#healthcheck)
- [Node.js Official Images](https://hub.docker.com/_/node)
- [Python Official Images](https://hub.docker.com/_/python)
- [Docker Compose File Reference](https://docs.docker.com/compose/compose-file/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)

### Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-29 | Claude Code | Initial plan created from spec.md using plan template |

---

**Ready for Phase 0 Research** - All planning sections complete. Next step: Execute research phase to gather Docker best practices for Next.js 15+ and FastAPI with Python 3.13+.
