# Phase 0 Research - Docker Containerization Best Practices

**Date**: 2025-12-29
**Feature**: 005-docker-containerization
**Objective**: Research optimal Docker containerization patterns for Next.js 15+ and FastAPI with Python 3.13+

---

## Executive Summary

This research document provides comprehensive answers to all containerization questions identified in the implementation plan. Key findings:

- **Next.js**: Use Node.js 20 Alpine with standalone output mode for 80%+ size reduction
- **FastAPI**: Use Python 3.13 Slim (not Alpine) for better compatibility with PostgreSQL drivers
- **Security**: Non-root user execution (UID 1001) with minimal base images reduces attack surface
- **Performance**: Multi-stage builds with layer caching enable <5 minute builds and <200 MB images
- **Health Checks**: HTTP-based checks on `/health` endpoints with 30-second intervals

---

## Research Questions Answered

### 1. Next.js 15+ Containerization

#### Q1.1: How to configure Next.js standalone output mode for minimal Docker images?

**Decision**: Enable standalone output mode in `next.config.js`

**Configuration Required**:
```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  // ... other config
}

module.exports = nextConfig
```

**How It Works**:
- Next.js builds a self-contained `server.js` file with only required dependencies
- Eliminates `node_modules` from final image (bundled dependencies are <50 MB)
- Includes only code actually used by the application (tree-shaking)
- Reduces final image from ~1.2 GB to ~180 MB (85% reduction)

**File Structure After Build**:
```
.next/
├── standalone/
│   ├── server.js           # Self-contained server
│   ├── node_modules/       # Only runtime dependencies
│   └── package.json        # Minimal manifest
├── static/                 # Static assets (must be copied separately)
└── ...
```

**Docker Implementation**:
```dockerfile
# Build stage generates standalone output
RUN npm run build

# Runner stage copies only necessary files
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

CMD ["node", "server.js"]
```

**Rationale**:
- Standalone mode is designed specifically for containerized deployments
- Eliminates hundreds of megabytes of unused dependencies
- Faster startup times (no dependency resolution)
- Officially recommended by Next.js for Docker deployments

**Alternatives Considered**:
- ❌ **Standard build**: Requires full `node_modules` (~800 MB), slow startup
- ❌ **Static export**: Loses API routes and server-side features
- ✅ **Standalone output**: Best balance of size, functionality, and performance

---

#### Q1.2: What are the best practices for multi-stage builds with Next.js 15+?

**Decision**: Use 3-stage build pattern (deps → builder → runner)

**Multi-Stage Strategy**:

**Stage 1: Dependencies** (install all packages including devDependencies)
```dockerfile
FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat  # Required for some npm packages
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci  # Clean install from lock file
```

**Stage 2: Builder** (build Next.js application)
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build  # Generates standalone output
```

**Stage 3: Runner** (minimal runtime image)
```dockerfile
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
```

**Rationale**:
- **Separation of concerns**: Each stage has a single responsibility
- **Layer caching**: Changing source code doesn't invalidate dependency installation
- **Security**: Only runtime files in final image (no build tools, no source files)
- **Size optimization**: Final image only contains production runtime

**Layer Caching Optimization**:
```
1. Copy package files → Install dependencies (cached unless dependencies change)
2. Copy source code → Build application (cached unless code changes)
3. Copy only built artifacts → Final image (always fresh)
```

**Performance Impact**:
- **First build**: 4-5 minutes (all stages)
- **Code change rebuild**: 1-2 minutes (only builder stage + runner copy)
- **Dependency change rebuild**: 3-4 minutes (deps stage + subsequent stages)

---

#### Q1.3: How to handle static assets and public files in containerized Next.js?

**Decision**: Copy `public/` and `.next/static/` directories separately to runner stage

**Implementation**:
```dockerfile
# Copy public directory (user-uploaded static files, favicon, etc.)
COPY --from=builder /app/public ./public

# Copy Next.js generated static assets
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
```

**File Location Requirements**:
```
/app/
├── server.js               # Entry point (from standalone)
├── public/                 # Public static files (images, fonts, etc.)
│   ├── favicon.ico
│   └── images/
└── .next/
    └── static/             # Build-time generated assets (JS, CSS chunks)
        ├── chunks/
        └── css/
```

**Why Both Directories Are Required**:
- **`public/`**: Contains pre-existing static files (favicon, images, robots.txt)
- **`.next/static/`**: Contains build-generated assets (code splitting chunks, CSS)
- Next.js server expects both to be present at specific paths

**Common Mistakes to Avoid**:
- ❌ Forgetting to copy `.next/static` → 404 errors for JavaScript bundles
- ❌ Forgetting to copy `public/` → Missing favicons and static images
- ❌ Not setting correct ownership → Permission errors with non-root user

---

#### Q1.4: What Node.js Alpine image version is compatible with Next.js 15?

**Decision**: Use `node:20-alpine` (Node.js 20 LTS with Alpine Linux 3.18+)

**Version Compatibility Matrix**:

| Next.js Version | Node.js Minimum | Recommended | Alpine Base |
|----------------|-----------------|-------------|-------------|
| Next.js 15.x   | Node.js 18.18+  | Node.js 20  | `node:20-alpine` |
| Next.js 14.x   | Node.js 18.17+  | Node.js 20  | `node:20-alpine` |
| Next.js 13.x   | Node.js 16.14+  | Node.js 18  | `node:18-alpine` |

**Why Node.js 20**:
- ✅ Long-term support (LTS) until April 2026
- ✅ Performance improvements (V8 engine 11.3)
- ✅ Native test runner and improved ESM support
- ✅ Officially tested with Next.js 15

**Why Alpine Linux**:
- ✅ Minimal size (~40 MB base vs ~200 MB Debian)
- ✅ Security-focused distribution (fewer packages = smaller attack surface)
- ✅ apk package manager for adding required dependencies
- ✅ Industry standard for Node.js containers

**Required Alpine Packages**:
```dockerfile
RUN apk add --no-cache libc6-compat
```
- **libc6-compat**: Provides glibc compatibility for npm packages with native bindings
- Required by some npm packages that expect glibc (Alpine uses musl libc)

**Image Size Comparison**:
- `node:20-alpine`: ~170 MB (base) → ~180 MB (final with Next.js)
- `node:20-slim`: ~240 MB (base) → ~280 MB (final with Next.js)
- `node:20`: ~1.1 GB (base) → ~1.3 GB (final with Next.js)

**Pinning Strategy**:
```dockerfile
# ✅ Recommended: Pin major version
FROM node:20-alpine

# ⚠️ Better: Pin minor version for reproducibility
FROM node:20.11-alpine

# ❌ Not recommended: Using latest
FROM node:alpine
```

---

#### Q1.5: How to implement health checks for Next.js applications in Docker?

**Decision**: HTTP-based health check using Node.js built-in `http` module

**Dockerfile Implementation**:
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/api/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"
```

**Health Check Configuration Explained**:
- **interval=30s**: Check every 30 seconds (standard for web apps)
- **timeout=3s**: Health check must complete within 3 seconds
- **start-period=40s**: Give container 40 seconds to start before health checks count against retries
- **retries=3**: Mark unhealthy after 3 consecutive failures (90 seconds total)

**Health Endpoint Implementation** (Next.js App Router):
```typescript
// frontend/app/api/health/route.ts
import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    service: 'frontend',
    uptime: process.uptime()
  }, { status: 200 });
}
```

**Why This Approach**:
- ✅ No external dependencies (uses built-in Node.js http module)
- ✅ Fast execution (<100ms response time)
- ✅ Works in minimal Alpine images
- ✅ Kubernetes-compatible (same endpoint can be used for liveness/readiness probes)

**Alternative Approaches Considered**:
- ❌ **curl-based**: Requires installing curl in Alpine (`apk add curl` adds ~2 MB)
- ❌ **wget-based**: Requires installing wget (similar size penalty)
- ✅ **Node.js http module**: Built-in, zero dependencies, minimal overhead

**Advanced Health Check (Optional)**:
```typescript
// Check database connectivity
export async function GET() {
  try {
    // Optional: Ping database to verify full stack health
    // await db.execute('SELECT 1');

    return NextResponse.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      checks: {
        server: 'ok',
        // database: 'ok'
      }
    }, { status: 200 });
  } catch (error) {
    return NextResponse.json({
      status: 'unhealthy',
      error: error.message
    }, { status: 503 });
  }
}
```

---

### 2. FastAPI Containerization

#### Q2.1: What are the optimal Python 3.13 base images (slim vs alpine)?

**Decision**: Use `python:3.13-slim` (Debian-based), NOT Alpine

**Base Image Comparison**:

| Base Image | Size | Pros | Cons | Recommendation |
|-----------|------|------|------|----------------|
| `python:3.13` | ~1.0 GB | All packages included | Massive size | ❌ Avoid |
| `python:3.13-slim` | ~130 MB | Good compatibility, reasonable size | Larger than Alpine | ✅ **Recommended** |
| `python:3.13-alpine` | ~50 MB | Smallest size | glibc issues, compilation required | ❌ Avoid for production |

**Why Slim, Not Alpine**:

**Problem with Alpine**:
```bash
# Alpine requires compiling psycopg2 from source
RUN apk add --no-cache postgresql-dev gcc python3-dev musl-dev
RUN pip install psycopg2  # 5+ minute compilation
```

**Benefits of Slim**:
```bash
# Slim uses pre-compiled wheels
RUN apt-get update && apt-get install -y libpq5
RUN pip install psycopg2-binary  # 10 second installation
```

**Detailed Comparison**:

**Alpine Challenges**:
- ❌ Uses musl libc instead of glibc (many Python packages expect glibc)
- ❌ Requires compiling packages with C extensions (psycopg2, pillow, numpy, etc.)
- ❌ Longer build times (5-10 minutes vs 1-2 minutes)
- ❌ Potential runtime issues with compiled packages

**Slim Benefits**:
- ✅ Uses glibc (standard C library expected by most Python packages)
- ✅ Pre-compiled wheels available on PyPI (fast installation)
- ✅ Better compatibility with SQLModel, psycopg2, uvicorn
- ✅ Faster build times (no compilation needed)
- ✅ More predictable behavior in production

**Size Impact**:
- Final image with Alpine: ~120 MB (after adding build tools)
- Final image with Slim: ~150 MB (30 MB difference is acceptable)

**Industry Consensus**:
- FastAPI official docs recommend Debian-based images
- Most production deployments use slim variants
- Alpine is better suited for Go, Rust, or static binaries

---

#### Q2.2: How to structure multi-stage builds for FastAPI with SQLModel dependencies?

**Decision**: Use 2-stage build with virtual environment (builder → runner)

**Multi-Stage Strategy**:

**Stage 1: Builder** (install dependencies in virtual environment)
```dockerfile
FROM python:3.13-slim AS builder
WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
```

**Stage 2: Runner** (minimal runtime with only venv)
```dockerfile
FROM python:3.13-slim AS runner
WORKDIR /app

# Install runtime dependencies only (PostgreSQL client, no gcc)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

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

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Why Virtual Environment in Docker**:

Many developers ask: "Why use venv in Docker? The container is already isolated!"

**Benefits of venv in Docker**:
1. **Clean separation**: Isolates app dependencies from system Python packages
2. **Easy copying**: Single `/opt/venv` directory contains all dependencies
3. **Build optimization**: Only venv is copied to runner stage (not build tools)
4. **Consistency**: Same environment locally and in container
5. **Security**: System Python remains untouched

**Alternative: System-wide pip install**:
```dockerfile
# ❌ Not recommended: Installs to system Python
RUN pip install -r requirements.txt

# Problems:
# - Harder to copy to runner stage (dependencies scattered)
# - Mixes system and app dependencies
# - Larger final image (includes system packages)
```

**SQLModel-Specific Dependencies**:
```
# requirements.txt
fastapi==0.115.0
sqlmodel==0.0.22
uvicorn[standard]==0.32.0
psycopg2-binary==2.9.9  # PostgreSQL adapter
pydantic==2.5.0
python-dotenv==1.0.0
```

**Build Tools vs Runtime Libraries**:

**Builder stage needs**:
- `gcc`: Compile packages with C extensions
- `libpq-dev`: PostgreSQL development headers

**Runner stage needs**:
- `libpq5`: PostgreSQL client library (no headers)
- No gcc (compilation already done)

**Size Savings**:
- Builder stage: ~400 MB (includes gcc, headers, wheels)
- Runner stage: ~150 MB (only venv + runtime libs)
- Savings: ~250 MB (62% reduction)

---

#### Q2.3: How to handle PostgreSQL client library (psycopg2) in minimal images?

**Decision**: Use `psycopg2-binary` in Slim image with `libpq5` runtime library

**Dependency Strategy**:

**Option 1: psycopg2-binary (Recommended for Docker)**:
```python
# requirements.txt
psycopg2-binary==2.9.9
```

```dockerfile
# Dockerfile runner stage
RUN apt-get install -y --no-install-recommends libpq5
```

**Option 2: psycopg2 from source (Not recommended)**:
```python
# requirements.txt
psycopg2==2.9.9  # Requires compilation
```

```dockerfile
# Dockerfile builder stage
RUN apt-get install -y gcc libpq-dev  # Build dependencies
```

**Recommendation Matrix**:

| Use Case | Package | Docker Stage | Debian Package | Rationale |
|----------|---------|--------------|----------------|-----------|
| Production Docker | `psycopg2-binary` | Runner | `libpq5` | Pre-compiled, faster builds |
| Development | `psycopg2-binary` | N/A | N/A | Easy pip install |
| System deployment | `psycopg2` | N/A | `libpq-dev` | Compiled against system PostgreSQL |

**Why psycopg2-binary for Docker**:
- ✅ Pre-compiled wheel (no gcc required in runner stage)
- ✅ Smaller runtime dependencies (`libpq5` only, not `libpq-dev`)
- ✅ Faster builds (no compilation step)
- ✅ Officially recommended for containerized deployments

**PostgreSQL Client Library Breakdown**:

**Build-time** (builder stage):
```dockerfile
RUN apt-get install -y libpq-dev  # ~10 MB, includes headers and dev files
```

**Runtime** (runner stage):
```dockerfile
RUN apt-get install -y libpq5  # ~200 KB, shared library only
```

**psycopg2 vs psycopg2-binary**:
- **psycopg2**: Source distribution, compiled during `pip install`, links to system libpq
- **psycopg2-binary**: Pre-compiled wheel with bundled libpq, drop-in replacement

**SQLModel + psycopg2 Integration**:
```python
# SQLModel uses SQLAlchemy under the hood
from sqlmodel import create_engine

# PostgreSQL connection string
DATABASE_URL = "postgresql://user:pass@host.neon.tech/dbname"

# create_engine automatically uses psycopg2 for PostgreSQL URLs
engine = create_engine(DATABASE_URL)
```

**Common Issues and Solutions**:

**Issue**: "psycopg2 not found" error in container
```bash
ModuleNotFoundError: No module named 'psycopg2'
```
**Solution**: Ensure `psycopg2-binary` is in `requirements.txt`

**Issue**: "libpq.so.5: cannot open shared object file"
```bash
ImportError: libpq.so.5: cannot open shared object file
```
**Solution**: Install `libpq5` in runner stage

---

#### Q2.4: What are the best practices for Python virtual environments in containers?

**Decision**: Create venv in builder, copy entire venv to runner stage

**Virtual Environment Pattern**:

**Builder Stage**:
```dockerfile
FROM python:3.13-slim AS builder

# Create virtual environment
RUN python -m venv /opt/venv

# Activate virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies into venv
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
```

**Runner Stage**:
```dockerfile
FROM python:3.13-slim AS runner

# Copy entire virtual environment
COPY --from=builder /opt/venv /opt/venv

# Activate virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Now Python uses packages from /opt/venv
CMD ["uvicorn", "app.main:app"]  # Uses venv's uvicorn
```

**Why /opt/venv Location**:
- ✅ Standard Linux location for optional software
- ✅ Outside /app (separates code from dependencies)
- ✅ Easy to copy as single directory
- ✅ Consistent across different projects

**Environment Variable Activation**:
```dockerfile
# ✅ Recommended: Modify PATH
ENV PATH="/opt/venv/bin:$PATH"

# ❌ Not recommended: Activate script
RUN . /opt/venv/bin/activate  # Doesn't persist across RUN commands
```

**Why Not Use WORKDIR for venv**:
```dockerfile
# ❌ Bad practice
WORKDIR /app
RUN python -m venv venv  # Creates /app/venv
# Problem: Mixing code and dependencies in same directory
```

**Pip Installation Best Practices**:
```dockerfile
# ✅ Recommended pattern
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --no-cache-dir: Don't save downloaded packages (saves ~100 MB)
# --upgrade pip: Use latest pip (faster downloads, better resolver)
# -r requirements.txt: Install from lock file
```

**Requirements.txt Best Practices**:
```txt
# ✅ Pin exact versions for reproducibility
fastapi==0.115.0
sqlmodel==0.0.22
uvicorn[standard]==0.32.0

# ❌ Avoid unpinned versions
fastapi  # Can install different versions on different builds
```

**Virtual Environment in Multi-stage Builds**:

**Why copy entire venv directory**:
1. **Simplicity**: Single COPY command
2. **Completeness**: Includes all installed packages and binaries
3. **Consistency**: Same structure as builder
4. **Performance**: Copying directory is faster than pip install

**What gets copied**:
```
/opt/venv/
├── bin/              # Executables (uvicorn, python, etc.)
├── lib/              # Python packages
│   └── python3.13/
│       └── site-packages/
└── pyvenv.cfg        # Virtual environment metadata
```

**Environment Variables for Python in Docker**:
```dockerfile
ENV PATH="/opt/venv/bin:$PATH"           # Use venv binaries
ENV PYTHONUNBUFFERED=1                   # Don't buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1            # Don't create .pyc files
ENV PIP_NO_CACHE_DIR=1                   # Don't cache pip downloads
ENV PIP_DISABLE_PIP_VERSION_CHECK=1      # Skip pip version check
```

---

#### Q2.5: How to run uvicorn in production mode within Docker?

**Decision**: Run uvicorn with production-optimized settings (no reload, proper host binding)

**Production Uvicorn Configuration**:
```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Command Breakdown**:
- `uvicorn`: ASGI server for FastAPI
- `app.main:app`: Import path to FastAPI application instance
- `--host 0.0.0.0`: Listen on all network interfaces (required for Docker networking)
- `--port 8000`: Standard port for backend API

**Why --host 0.0.0.0**:
```bash
# ❌ Default: 127.0.0.1 (localhost only)
uvicorn app.main:app
# Cannot access from outside container

# ✅ Required: 0.0.0.0 (all interfaces)
uvicorn app.main:app --host 0.0.0.0
# Accessible from other containers and host machine
```

**Production vs Development Settings**:

| Setting | Development | Production (Docker) |
|---------|-------------|---------------------|
| Host | `127.0.0.1` | `0.0.0.0` |
| Port | `8000` | `8000` |
| Reload | `--reload` | ❌ Disabled |
| Workers | `1` | `1` (horizontal scaling in K8s) |
| Log Level | `info` | `info` |
| Access Log | Enabled | Enabled |

**Development Command** (local machine):
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Production Command** (Docker):
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Worker Configuration**:

**Single Worker** (Recommended for Docker/Kubernetes):
```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# Let Kubernetes handle horizontal scaling (multiple containers)
```

**Multiple Workers** (Alternative for standalone Docker):
```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
# Only if NOT using Kubernetes for scaling
```

**Why Single Worker for Kubernetes**:
- ✅ Kubernetes pods should have single process (easier monitoring)
- ✅ Horizontal pod autoscaling manages replicas
- ✅ Better resource allocation (CPU/memory per pod)
- ✅ Simpler health checks and logging

**Uvicorn Standard Extras**:
```txt
# requirements.txt
uvicorn[standard]==0.32.0
```

**What [standard] includes**:
- `uvloop`: Fast asyncio event loop (2-4x faster)
- `httptools`: Fast HTTP parser
- `websockets`: WebSocket protocol support
- `watchfiles`: File watching for reload (dev only)

**Alternative ASGI Servers**:

| Server | Use Case | Recommendation |
|--------|----------|----------------|
| Uvicorn | Development, lightweight production | ✅ **Recommended** for Docker |
| Gunicorn + Uvicorn | Heavy production traffic | ⚠️ Use only if not using K8s |
| Hypercorn | HTTP/2, HTTP/3 support | ⚠️ Experimental |

**Gunicorn + Uvicorn (Advanced)**:
```dockerfile
# Only if NOT using Kubernetes
CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

**FastAPI Application Structure**:
```python
# app/main.py
from fastapi import FastAPI

app = FastAPI(
    title="Todo API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# uvicorn looks for the 'app' variable
```

**Command Formats in Dockerfile**:

**✅ Exec form** (Recommended):
```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# Runs directly, no shell, receives signals correctly
```

**❌ Shell form** (Not recommended):
```dockerfile
CMD uvicorn app.main:app --host 0.0.0.0 --port 8000
# Runs in shell (/bin/sh -c), doesn't receive signals properly
```

**Graceful Shutdown**:
```dockerfile
# Uvicorn handles SIGTERM for graceful shutdown
STOPSIGNAL SIGTERM
```

---

### 3. Security Best Practices

#### Q3.1: How to configure non-root user execution (UID 1001)?

**Decision**: Create dedicated user with UID 1001 in both containers

**Frontend (Alpine-based)**:
```dockerfile
# Alpine uses addgroup and adduser commands
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Set ownership of application files
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./

# Switch to non-root user
USER nextjs
```

**Backend (Debian-based)**:
```dockerfile
# Debian uses groupadd and useradd commands
RUN groupadd -g 1001 fastapi && \
    useradd -u 1001 -g fastapi -s /bin/bash -m fastapi

# Set ownership of application files
COPY --chown=fastapi:fastapi ./app ./app

# Switch to non-root user
USER fastapi
```

**Why UID 1001**:
- ✅ Well above system user range (0-999)
- ✅ Standard convention for application users
- ✅ Consistent across both containers
- ✅ Avoids conflicts with host system users
- ✅ Kubernetes-friendly (some clusters require UID >1000)

**User Creation Comparison**:

| Distribution | Group Command | User Command | Shell |
|--------------|---------------|--------------|-------|
| Alpine | `addgroup --system --gid 1001 nodejs` | `adduser --system --uid 1001 nextjs` | `/sbin/nologin` |
| Debian/Ubuntu | `groupadd -g 1001 fastapi` | `useradd -u 1001 -g fastapi fastapi` | `/bin/bash` |

**File Ownership Best Practices**:

**✅ Set ownership during COPY**:
```dockerfile
COPY --chown=nextjs:nodejs /app/.next/standalone ./
# Efficient: Ownership set during copy operation
```

**❌ Set ownership after COPY**:
```dockerfile
COPY /app/.next/standalone ./
RUN chown -R nextjs:nodejs ./
# Inefficient: Creates additional layer, doubles size
```

**Security Benefits of Non-Root**:

1. **Principle of Least Privilege**:
   - Application doesn't need root permissions
   - Limits damage from container escape vulnerabilities
   - Reduces attack surface

2. **Kubernetes Security Contexts**:
   ```yaml
   # Kubernetes enforces non-root in security policies
   securityContext:
     runAsNonRoot: true
     runAsUser: 1001
   ```

3. **Filesystem Protection**:
   - User cannot modify system files
   - Cannot install packages or modify binaries
   - Limited to application directory only

**Verification**:
```bash
# Check running user in container
docker exec <container> whoami
# Output: nextjs (or fastapi)

# Check user ID
docker exec <container> id
# Output: uid=1001(nextjs) gid=1001(nodejs)
```

**Common Pitfalls**:

**Issue**: Permission denied errors
```bash
Error: EACCES: permission denied, open '/app/file.log'
```
**Solution**: Ensure all files are owned by application user
```dockerfile
COPY --chown=nextjs:nodejs /app/.next/standalone ./
```

**Issue**: USER directive placed too early
```dockerfile
# ❌ Wrong: USER before COPY
USER nextjs
COPY /app/.next/standalone ./  # Owned by root!

# ✅ Correct: USER after COPY
COPY --chown=nextjs:nodejs /app/.next/standalone ./
USER nextjs
```

**Read-Only Filesystem (Advanced)**:
```yaml
# Kubernetes security enhancement
securityContext:
  readOnlyRootFilesystem: true
  runAsUser: 1001
```

---

#### Q3.2: What are the minimal required system packages for each runtime?

**Decision**: Only install packages absolutely required for runtime

**Frontend (Node.js Alpine)**:

**Required Packages**:
```dockerfile
RUN apk add --no-cache libc6-compat
```

**Package Breakdown**:
- `libc6-compat`: glibc compatibility layer (~2 MB)
  - Required by npm packages with native bindings
  - Provides compatibility for packages expecting glibc on musl libc system

**Total Additional Packages**: 1 (~2 MB)

**Backend (Python Slim)**:

**Required Packages**:
```dockerfile
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*
```

**Package Breakdown**:
- `libpq5`: PostgreSQL client library (~200 KB)
  - Required by psycopg2-binary to connect to PostgreSQL
  - Shared library for database connectivity

**Cleanup Commands**:
- `--no-install-recommends`: Skip "recommended" packages (saves ~50 MB)
- `rm -rf /var/lib/apt/lists/*`: Remove apt cache (saves ~20 MB)

**Total Additional Packages**: 1 (~200 KB + cleanup)

**What NOT to Install**:

**Frontend**:
- ❌ `curl`, `wget`: Not needed (health check uses Node.js http module)
- ❌ `git`: Not needed (code already copied)
- ❌ `build-essential`: Not needed in runner (only builder)

**Backend**:
- ❌ `gcc`, `g++`: Not needed in runner (only builder)
- ❌ `libpq-dev`: Not needed in runner (only libpq5 runtime library)
- ❌ `python3-dev`: Not needed in runner (only builder)
- ❌ `curl`, `wget`: Not needed (health check uses Python urllib)

**Package Installation Best Practices**:

**Alpine (apk)**:
```dockerfile
# ✅ Good: No cache flag
RUN apk add --no-cache package1 package2

# ❌ Bad: Cache retained
RUN apk add package1
```

**Debian (apt-get)**:
```dockerfile
# ✅ Good: Update, install, cleanup in one layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends package1 && \
    rm -rf /var/lib/apt/lists/*

# ❌ Bad: Separate layers, cache retained
RUN apt-get update
RUN apt-get install -y package1
```

**Size Impact of Common Packages**:

| Package | Size | Purpose | Needed? |
|---------|------|---------|---------|
| `curl` | ~2 MB | HTTP client | ❌ No (use native HTTP) |
| `wget` | ~1 MB | Download files | ❌ No |
| `git` | ~10 MB | Version control | ❌ No (code in image) |
| `gcc` | ~50 MB | C compiler | ❌ No in runner |
| `libpq-dev` | ~10 MB | PostgreSQL dev files | ❌ No in runner |
| `libpq5` | ~200 KB | PostgreSQL runtime | ✅ Yes (backend) |
| `libc6-compat` | ~2 MB | glibc compatibility | ✅ Yes (frontend) |

**Verification**:
```bash
# List installed packages (Alpine)
docker exec <container> apk list --installed

# List installed packages (Debian)
docker exec <container> dpkg -l
```

---

#### Q3.3: How to scan Docker images for vulnerabilities?

**Decision**: Use Trivy for local scanning, Docker Scout for CI/CD

**Trivy (Recommended for Local Development)**:

**Installation**:
```bash
# macOS
brew install aquasecurity/trivy/trivy

# Linux
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install trivy

# Windows
choco install trivy
```

**Scanning Images**:
```bash
# Scan frontend image
trivy image frontend:latest

# Scan backend image
trivy image backend:latest

# Output to JSON
trivy image --format json --output results.json frontend:latest

# Only show HIGH and CRITICAL vulnerabilities
trivy image --severity HIGH,CRITICAL frontend:latest
```

**Sample Trivy Output**:
```
frontend:latest (alpine 3.18.4)
===================================
Total: 12 (UNKNOWN: 0, LOW: 4, MEDIUM: 6, HIGH: 2, CRITICAL: 0)

┌─────────────┬───────────────┬──────────┬────────┬───────────────────┬─────────────┐
│   Library   │ Vulnerability │ Severity │ Status │ Installed Version │ Fixed Ver.  │
├─────────────┼───────────────┼──────────┼────────┼───────────────────┼─────────────┤
│ libcrypto3  │ CVE-2024-XXXX │ HIGH     │ fixed  │ 3.1.0-r1          │ 3.1.0-r2    │
│ libssl3     │ CVE-2024-XXXX │ HIGH     │ fixed  │ 3.1.0-r1          │ 3.1.0-r2    │
└─────────────┴───────────────┴──────────┴────────┴───────────────────┴─────────────┘
```

**Docker Scout (Recommended for CI/CD)**:

**Usage**:
```bash
# Enable Docker Scout (free for public images)
docker scout enroll

# Quick scan
docker scout quickview frontend:latest

# Detailed scan
docker scout cves frontend:latest

# Compare with base image
docker scout compare frontend:latest --to node:20-alpine
```

**CI/CD Integration**:
```yaml
# .github/workflows/docker-scan.yml
name: Docker Security Scan

on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build image
        run: docker build -t frontend:latest ./frontend

      - name: Scan with Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: frontend:latest
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'  # Fail on critical/high vulnerabilities

      - name: Upload results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
```

**Severity Levels**:

| Severity | Action | Example |
|----------|--------|---------|
| CRITICAL | Block deployment | Remote code execution vulnerabilities |
| HIGH | Block deployment | SQL injection, XSS vulnerabilities |
| MEDIUM | Review and patch | Information disclosure |
| LOW | Monitor | Minor issues, low exploitability |
| UNKNOWN | Investigate | CVEs without severity rating |

**Best Practices**:
- ✅ Scan images before deployment
- ✅ Update base images regularly (monthly)
- ✅ Pin base image versions for reproducibility
- ✅ Set CI/CD to fail on CRITICAL/HIGH vulnerabilities
- ✅ Use minimal base images (fewer packages = fewer vulnerabilities)

**Alternative Scanners**:
- **Snyk**: Commercial, good developer experience
- **Clair**: Open-source, RedHat project
- **Anchore**: Open-source, policy-based scanning
- **Grype**: Faster alternative to Trivy

---

#### Q3.4: What are the security implications of different base images?

**Decision**: Use official images with minimal packages (Alpine for frontend, Slim for backend)

**Base Image Security Comparison**:

| Base Image | Size | Packages | Vulnerabilities* | Update Frequency | Recommendation |
|-----------|------|----------|------------------|------------------|----------------|
| `node:20-alpine` | ~170 MB | ~30 | Low (5-10) | Weekly | ✅ **Recommended** |
| `node:20-slim` | ~240 MB | ~100 | Medium (20-30) | Weekly | ⚠️ Acceptable |
| `node:20` | ~1.1 GB | ~400+ | High (50-100+) | Weekly | ❌ Avoid |
| `python:3.13-alpine` | ~50 MB | ~20 | Low (5-10) | Weekly | ⚠️ Compatibility issues |
| `python:3.13-slim` | ~130 MB | ~80 | Medium (15-25) | Weekly | ✅ **Recommended** |
| `python:3.13` | ~1.0 GB | ~300+ | High (50-100+) | Weekly | ❌ Avoid |

*Vulnerability counts are approximate and change over time

**Security Attack Surface**:

**Minimal Images (Alpine/Slim)**:
- ✅ Fewer packages = fewer CVEs
- ✅ Smaller attack surface
- ✅ Faster security patching (fewer packages to update)
- ✅ Smaller image = faster vulnerability scans

**Full Images (Debian/Ubuntu)**:
- ❌ Hundreds of unnecessary packages
- ❌ Large attack surface (compilers, dev tools, documentation)
- ❌ More CVEs to monitor and patch
- ❌ Slower scans and updates

**CVE Statistics Example** (as of 2025):

**node:20-alpine**:
```
Total: 8 vulnerabilities
├─ CRITICAL: 0
├─ HIGH: 2
├─ MEDIUM: 4
└─ LOW: 2

Attack Surface: 32 packages
```

**node:20** (Debian full):
```
Total: 87 vulnerabilities
├─ CRITICAL: 1
├─ HIGH: 12
├─ MEDIUM: 43
└─ LOW: 31

Attack Surface: 412 packages
```

**Security Best Practices by Image Type**:

**Alpine Linux**:
- ✅ Security-focused distribution
- ✅ Minimal default installation
- ✅ musl libc (smaller, simpler than glibc)
- ✅ apk package manager (fast, efficient)
- ⚠️ Compatibility issues with some packages

**Debian Slim**:
- ✅ Balance between size and compatibility
- ✅ glibc compatibility (wider package support)
- ✅ Official Debian base (well-maintained)
- ⚠️ Larger than Alpine (~100 MB more)

**Update Strategies**:

**Pin Major Versions**:
```dockerfile
# ✅ Recommended: Pin major version, get security updates
FROM node:20-alpine

# Builds use latest 20.x.x version
# Security patches applied automatically
```

**Pin Exact Versions**:
```dockerfile
# ⚠️ More reproducible, but requires manual updates
FROM node:20.11.0-alpine3.18

# Always builds same image
# Requires manual updates for security patches
```

**Use Latest Tag**:
```dockerfile
# ❌ Not recommended: Unpredictable versions
FROM node:alpine

# Could be Node 18, 19, 20, or newer
# Breaks reproducibility
```

**Distroless Images** (Advanced):

**What are Distroless**:
- Container images without package manager, shell, or utilities
- Only runtime and application files
- Google maintains distroless images for multiple languages

**Example** (Python):
```dockerfile
FROM python:3.13-slim AS builder
# ... install dependencies ...

FROM gcr.io/distroless/python3
COPY --from=builder /opt/venv /opt/venv
COPY app ./app
CMD ["app/main.py"]
```

**Pros**:
- ✅ Absolute minimal attack surface
- ✅ No shell (prevents shell-based attacks)
- ✅ ~20 MB smaller than Alpine

**Cons**:
- ❌ No shell (harder to debug)
- ❌ No package manager
- ❌ Limited language support
- ❌ Requires more complex multi-stage builds

**Recommendation**: Use Alpine/Slim for development, consider Distroless for high-security production environments.

---

### 4. Performance Optimization

#### Q4.1: How to optimize Docker layer caching for faster rebuilds?

**Decision**: Order Dockerfile instructions from least to most frequently changing

**Layer Caching Principles**:

1. **Docker caches each layer** (each RUN, COPY, ADD instruction)
2. **Cache invalidated** when instruction changes or previous layer changes
3. **All subsequent layers** are rebuilt when cache is invalidated
4. **Optimize order** to maximize cache hits

**Optimal Instruction Order**:

```dockerfile
# 1. Base image (changes rarely)
FROM node:20-alpine AS deps

# 2. System packages (changes rarely)
RUN apk add --no-cache libc6-compat

# 3. Dependency files (changes occasionally)
COPY package.json package-lock.json ./

# 4. Install dependencies (cached unless dependencies change)
RUN npm ci

# 5. Source code (changes frequently)
COPY . .

# 6. Build application (only runs when code changes)
RUN npm run build
```

**Why This Order**:
- Base image changes: Once per year
- System packages change: Once per month
- Dependencies change: Once per week
- Source code changes: Multiple times per day

**Layer Caching Impact**:

**Scenario 1: Code change only**
```bash
# Cache hit: Base image
# Cache hit: System packages
# Cache hit: Dependency files
# Cache hit: npm ci (30 seconds saved!)
# Cache miss: Source code copy
# Cache miss: npm run build
```

**Scenario 2: Dependency change**
```bash
# Cache hit: Base image
# Cache hit: System packages
# Cache miss: Dependency files changed
# Cache miss: npm ci (must reinstall)
# Cache miss: Source code copy
# Cache miss: npm run build
```

**Bad Example** (Frequently Invalidated Cache):
```dockerfile
# ❌ Wrong: Copy everything first
COPY . .

# ❌ Every code change invalidates npm ci
RUN npm ci

# ❌ No caching benefit
RUN npm run build
```

**Good Example** (Optimized Caching):
```dockerfile
# ✅ Correct: Copy dependencies first
COPY package.json package-lock.json ./

# ✅ Cached unless dependencies change
RUN npm ci

# ✅ Copy source code after dependencies
COPY . .

# ✅ Only rebuilds when code changes
RUN npm run build
```

**Advanced Caching: .dockerignore**:

```
# Exclude files that change but aren't needed
.git
.gitignore
README.md
*.md
.env
.env.*
node_modules  # Will be installed by npm ci
coverage
.vscode
```

**Why .dockerignore Improves Caching**:
- Excludes files that change frequently but aren't needed
- Reduces build context size
- Prevents cache invalidation from README updates
- Faster context transfer to Docker daemon

**Build Context Size Impact**:

**Without .dockerignore**:
```
Sending build context to Docker daemon: 450 MB
# Includes node_modules, .git, coverage, etc.
```

**With .dockerignore**:
```
Sending build context to Docker daemon: 12 MB
# Only includes source code
```

**BuildKit Caching** (Docker 18.09+):

**Enable BuildKit**:
```bash
# Environment variable
export DOCKER_BUILDKIT=1
docker build -t frontend:latest ./frontend

# Or inline
DOCKER_BUILDKIT=1 docker build -t frontend:latest ./frontend
```

**BuildKit Benefits**:
- ✅ Parallel layer builds
- ✅ Better cache invalidation logic
- ✅ Skips unused stages in multi-stage builds
- ✅ Faster dependency resolution

**Mounted Caches** (Advanced):

```dockerfile
# Cache npm packages across builds
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Cache pip packages across builds
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

**Benefits**:
- ✅ Cache persists across builds
- ✅ Faster dependency installation
- ✅ Reduces network usage

**Verification**:
```bash
# Build with verbose output
docker build --progress=plain -t frontend:latest ./frontend

# Look for "CACHED" lines
#1 [deps 1/4] FROM node:20-alpine
#1 CACHED

#2 [deps 2/4] RUN apk add --no-cache libc6-compat
#2 CACHED
```

---

#### Q4.2: What are the best practices for .dockerignore patterns?

**Decision**: Use comprehensive .dockerignore with category-based organization

**Frontend .dockerignore**:

```
# === Dependencies ===
# Will be installed via npm ci
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*
package-lock.json  # Copied separately

# === Build Output ===
# Will be generated during build
.next/
out/
dist/
build/

# === Environment Files ===
# Contains secrets, never include
.env
.env*.local
.env.development
.env.production
.env.staging

# === Version Control ===
# Not needed in container
.git/
.gitignore
.gitattributes

# === IDE and Editor ===
# Development tools only
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# === Testing ===
# Tests not needed in production
coverage/
.nyc_output/
*.test.ts
*.test.tsx
*.spec.ts
*.spec.tsx
__tests__/
__mocks__/
jest.config.js

# === Documentation ===
# Not needed in runtime
README.md
CHANGELOG.md
LICENSE
*.md
docs/

# === Docker Files ===
# Don't include Docker files in build
Dockerfile
Dockerfile.*
.dockerignore
docker-compose.yml
docker-compose.*.yml

# === Development ===
# Dev-only files
.eslintrc.js
.eslintrc.json
.prettierrc
.editorconfig
tsconfig.json
next.config.js  # Will be copied separately if needed

# === Logs ===
logs/
*.log

# === OS Files ===
Thumbs.db
.DS_Store
```

**Backend .dockerignore**:

```
# === Python Cache ===
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# === Virtual Environments ===
# Will be created in builder stage
venv/
env/
ENV/
.venv

# === Environment Files ===
.env
.env.*
.env.local
.env.development
.env.production

# === Version Control ===
.git/
.gitignore
.gitattributes

# === IDE and Editor ===
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# === Testing ===
.pytest_cache/
.coverage
htmlcov/
*.test.py
*_test.py
test_*.py
tests/
.tox/

# === Documentation ===
README.md
CHANGELOG.md
LICENSE
*.md
docs/

# === Docker Files ===
Dockerfile
Dockerfile.*
.dockerignore
docker-compose.yml
docker-compose.*.yml

# === Database ===
# Migrations handled separately
*.db
*.sqlite
*.sqlite3

# === Jupyter Notebooks ===
.ipynb_checkpoints/
*.ipynb

# === Distribution ===
dist/
build/
*.egg-info/

# === Logs ===
logs/
*.log
```

**Pattern Explanation**:

**Wildcards**:
```
*.log       # All .log files in current directory
**/*.log    # All .log files recursively (any depth)
logs/       # Entire logs directory
```

**Negation**:
```
# Ignore all .env files
.env*

# But include .env.example
!.env.example
```

**Why Exclude Each Category**:

**Dependencies** (`node_modules/`):
- ✅ Will be installed fresh via `npm ci`
- ✅ Ensures consistent versions
- ✅ Reduces context size by ~300 MB

**Build Output** (`.next/`, `__pycache__/`):
- ✅ Generated during build process
- ✅ Prevents stale build artifacts
- ✅ Reduces context size by ~50 MB

**Environment Files** (`.env*`):
- ✅ Contains secrets (database URLs, API keys)
- ✅ Prevents accidental secret leakage
- ✅ Environment-specific (not portable)

**Version Control** (`.git/`):
- ✅ Git history not needed in container
- ✅ Reduces context size by ~50-200 MB
- ✅ Prevents accidental credential leakage (git config)

**Testing** (`coverage/`, `*.test.ts`):
- ✅ Tests not needed in production
- ✅ Reduces image size
- ✅ Faster builds

**Build Context Impact**:

**Without .dockerignore**:
```bash
$ docker build -t frontend:latest ./frontend
Sending build context to Docker daemon: 523 MB
```

**With .dockerignore**:
```bash
$ docker build -t frontend:latest ./frontend
Sending build context to Docker daemon: 8.5 MB
```

**98% reduction in build context size!**

**Verification**:
```bash
# Show files sent to Docker daemon
docker build --progress=plain -t frontend:latest ./frontend 2>&1 | grep "Sending build context"

# Test .dockerignore patterns
docker build --no-cache -t test:latest ./frontend 2>&1 | grep "COPY"
```

---

#### Q4.3: How to minimize image size without sacrificing functionality?

**Decision**: Use multi-stage builds, minimal base images, and aggressive cleanup

**Image Size Reduction Techniques**:

### 1. Multi-Stage Builds (80%+ Reduction)

**Before** (single-stage):
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY . .
RUN npm ci
RUN npm run build
CMD ["npm", "start"]
```
**Size**: ~1.2 GB (includes build tools, source, node_modules)

**After** (multi-stage):
```dockerfile
# Builder stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Runner stage
FROM node:20-alpine AS runner
WORKDIR /app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
CMD ["node", "server.js"]
```
**Size**: ~180 MB (only runtime files)

**Savings**: ~1 GB (83% reduction)

### 2. Minimal Base Images

**Image Size Comparison**:
```
node:20           → 1.1 GB  (Debian full)
node:20-slim      → 240 MB  (Debian minimal)
node:20-alpine    → 170 MB  (Alpine Linux)

python:3.13       → 1.0 GB  (Debian full)
python:3.13-slim  → 130 MB  (Debian minimal)
python:3.13-alpine→  50 MB  (Alpine Linux)
```

**Recommendation**:
- Frontend: `node:20-alpine` (minimal + compatible)
- Backend: `python:3.13-slim` (minimal + psycopg2 support)

### 3. Package Manager Cleanup

**Alpine (apk)**:
```dockerfile
# ✅ No cache flag
RUN apk add --no-cache libc6-compat
# Savings: ~5-10 MB
```

**Debian (apt)**:
```dockerfile
# ✅ Cleanup in same layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*
# Savings: ~20-30 MB
```

**Python pip**:
```dockerfile
# ✅ No cache flag
RUN pip install --no-cache-dir -r requirements.txt
# Savings: ~100-200 MB
```

### 4. Combine RUN Commands

**Before** (multiple layers):
```dockerfile
RUN apt-get update
RUN apt-get install -y libpq5
RUN rm -rf /var/lib/apt/lists/*
```
**Size**: Each RUN creates a layer, cache persists

**After** (single layer):
```dockerfile
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*
```
**Savings**: ~30-50 MB (cache not retained in image)

### 5. Exclude Unnecessary Files (.dockerignore)

```
# .dockerignore
node_modules/     # Saves ~300 MB
.git/             # Saves ~50-200 MB
coverage/         # Saves ~10-50 MB
*.md              # Saves ~1-5 MB
.vscode/          # Saves ~1-2 MB
```
**Total Savings**: ~400-600 MB

### 6. Next.js Standalone Output

**Before** (standard build):
```dockerfile
COPY node_modules ./node_modules
COPY .next ./.next
```
**Size**: ~800 MB (all dependencies)

**After** (standalone):
```dockerfile
COPY --from=builder /app/.next/standalone ./
```
**Size**: ~50 MB (only required runtime)

**Savings**: ~750 MB (93% reduction in app files)

### 7. Remove Development Dependencies

**Python**:
```txt
# requirements.txt (production only)
fastapi==0.115.0
uvicorn==0.32.0

# requirements-dev.txt (not copied to Docker)
pytest==7.4.0
black==23.9.0
```

**Node.js**:
```dockerfile
# Use npm ci (ignores devDependencies in production)
ENV NODE_ENV=production
RUN npm ci --only=production
```

### 8. Optimize Application Code

**Remove unused dependencies**:
```bash
# Check for unused packages
npx depcheck

# Remove unused packages
npm uninstall unused-package
```

**Size Optimization Checklist**:

```
✅ Multi-stage builds (builder + runner)
✅ Minimal base images (Alpine/Slim)
✅ Package manager no-cache flags
✅ Cleanup in same layer (&&, rm -rf)
✅ Comprehensive .dockerignore
✅ Next.js standalone output
✅ Production-only dependencies
✅ Combine RUN commands
✅ Remove development tools
✅ Pin dependency versions
```

**Final Image Sizes**:

| Service | Unoptimized | Optimized | Savings |
|---------|-------------|-----------|---------|
| Frontend | ~1.2 GB | ~180 MB | 85% |
| Backend | ~800 MB | ~150 MB | 81% |
| **Total** | **~2 GB** | **~330 MB** | **84%** |

**Verification**:
```bash
# Check image size
docker images

REPOSITORY   TAG      SIZE
frontend     latest   178 MB
backend      latest   152 MB
```

---

#### Q4.4: How to optimize container startup time?

**Decision**: Use standalone builds, lazy loading, and proper resource allocation

**Container Startup Optimization**:

### 1. Next.js Standalone Output (50% Faster)

**Before** (standard build):
```dockerfile
CMD ["npm", "start"]
```
**Startup**: ~60 seconds
- npm resolves dependencies
- Loads entire node_modules
- Parses package.json

**After** (standalone):
```dockerfile
CMD ["node", "server.js"]
```
**Startup**: ~25 seconds
- Direct Node.js execution
- Pre-bundled dependencies
- No package resolution

**Improvement**: 58% faster startup

### 2. Python Optimizations

**Disable bytecode compilation**:
```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1
```
- Skips `.pyc` file creation
- Saves ~2-5 seconds on startup

**Unbuffered output**:
```dockerfile
ENV PYTHONUNBUFFERED=1
```
- Immediate log output
- Better debugging
- No performance impact

### 3. Uvicorn Startup Configuration

**Production settings**:
```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
**Startup**: ~15 seconds

**With workers** (slower startup):
```dockerfile
CMD ["uvicorn", "app.main:app", "--workers", "4", "--host", "0.0.0.0"]
```
**Startup**: ~30 seconds (each worker initializes)

**Recommendation**: Use single worker in Kubernetes (horizontal pod scaling)

### 4. Health Check Start Period

**Configuration**:
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/api/health')"
```

**start-period=40s**:
- Gives container time to start
- Health checks don't count against retries during start period
- Prevents premature "unhealthy" status

**Tuning**:
- Too short: Container marked unhealthy before ready
- Too long: Slow failure detection
- **Recommended**: 1.5x typical startup time

### 5. Resource Allocation

**Docker Compose**:
```yaml
services:
  frontend:
    image: frontend:latest
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

**Impact**:
- Sufficient CPU: Faster startup (JavaScript parsing)
- Sufficient memory: No swapping during startup

### 6. Lazy Loading Dependencies

**FastAPI**:
```python
# ❌ Import all dependencies at module level
import heavy_module_1
import heavy_module_2

@app.get("/endpoint")
def handler():
    return heavy_module_1.process()
```
**Startup**: ~20 seconds (loads all modules)

**✅ Import dependencies on demand**:
```python
# Only import when needed
@app.get("/endpoint")
def handler():
    import heavy_module_1
    return heavy_module_1.process()
```
**Startup**: ~10 seconds (deferred loading)

### 7. Database Connection Pooling

**Eager connection** (slower):
```python
# Creates connection pool at startup
engine = create_engine(DATABASE_URL, pool_size=10)

# Startup waits for database
```

**Lazy connection** (faster):
```python
# Creates connection pool on first request
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connection before use
    pool_size=5,         # Smaller initial pool
    max_overflow=10      # Scale up as needed
)
```

### 8. Precompile Static Assets

**Next.js**:
```dockerfile
# Precompile during build (not startup)
RUN npm run build
```
- All JavaScript/CSS compiled at build time
- Startup only loads pre-built files

### 9. Startup Metrics

**Frontend Startup Timeline**:
```
[0s]    Container created
[2s]    Node.js process starts
[5s]    Server.js loaded
[10s]   Next.js server initializes
[15s]   Route handlers registered
[20s]   Database connections ready (if applicable)
[25s]   Health check passes
[25s]   Container READY
```

**Backend Startup Timeline**:
```
[0s]    Container created
[2s]    Python process starts
[4s]    FastAPI app imports
[6s]    Route handlers registered
[8s]    Database connection pool created
[10s]   Middleware initialized
[15s]   Health check passes
[15s]   Container READY
```

**Startup Time Targets**:

| Service | Target | Acceptable | Poor |
|---------|--------|------------|------|
| Frontend | <25s | <30s | >40s |
| Backend | <15s | <20s | >30s |
| Full Stack | <30s | <40s | >60s |

**Verification**:
```bash
# Measure startup time
time docker-compose up --wait

# Check container logs for startup duration
docker logs frontend 2>&1 | grep "Ready"
docker logs backend 2>&1 | grep "Uvicorn running"
```

---

### 5. Docker Compose

#### Q5.1: How to configure networking between frontend and backend containers?

**Decision**: Use Docker Compose default bridge network with service names as hostnames

**Docker Compose Networking**:

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    container_name: todo-backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - CORS_ORIGINS=["http://localhost:3000", "http://frontend:3000"]
    networks:
      - todo-network
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 3s
      start_period: 40s
      retries: 3

  frontend:
    build: ./frontend
    container_name: todo-frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
      - BETTER_AUTH_SECRET=${BETTER_AUTH_SECRET}
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - todo-network
    healthcheck:
      test: ["CMD", "node", "-e", "require('http').get('http://localhost:3000/api/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"]
      interval: 30s
      timeout: 3s
      start_period: 40s
      retries: 3

networks:
  todo-network:
    driver: bridge
```

**How Container Networking Works**:

**Service Discovery**:
- Docker Compose creates internal DNS
- Service name = hostname
- `backend` resolves to backend container IP
- `frontend` resolves to frontend container IP

**Example Communication**:
```javascript
// Frontend container makes request
fetch('http://backend:8000/api/tasks')

// Docker DNS resolves 'backend' to 172.18.0.2 (example)
// Request sent to backend container on port 8000
```

**Network Isolation**:
```
Host Machine (your computer)
  ├── Port 3000 → Frontend Container (172.18.0.3:3000)
  ├── Port 8000 → Backend Container (172.18.0.2:8000)
  └── Docker Network: todo-network (172.18.0.0/16)
```

**Why Use Service Names**:
- ✅ Dynamic IP addresses (IPs change on restart)
- ✅ DNS-based discovery (no hardcoded IPs)
- ✅ Works in any environment (dev, staging, prod)
- ✅ Kubernetes-compatible (same pattern)

**Communication Patterns**:

**1. Frontend → Backend (Server-Side)**:
```javascript
// Next.js API route (server-side)
export async function GET() {
  // Uses internal Docker network
  const res = await fetch('http://backend:8000/api/tasks');
  return NextResponse.json(await res.json());
}
```

**2. Browser → Frontend → Backend (Client-Side)**:
```javascript
// React component (browser)
useEffect(() => {
  // Browser cannot access 'backend' hostname
  // Must use public API through frontend
  fetch('/api/tasks')  // Proxied through Next.js
    .then(res => res.json());
}, []);
```

**CORS Configuration**:

**Backend allows frontend origins**:
```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Browser access (dev)
        "http://frontend:3000",       # Container access
        "https://yourdomain.com"      # Production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**depends_on with Health Checks**:

```yaml
frontend:
  depends_on:
    backend:
      condition: service_healthy  # Wait for health check
```

**Startup Order**:
1. Backend container starts
2. Backend health check runs (every 30s)
3. When backend healthy, frontend starts
4. Frontend health check runs
5. All services ready

**Without health check**:
```yaml
frontend:
  depends_on:
    - backend  # Only waits for container start, not readiness
```
- Frontend starts before backend is ready
- May cause connection errors

**Port Mapping**:

**Internal Port** (container):
```yaml
ports:
  - "3000:3000"
#   ↑       ↑
#   Host    Container
```

**Access Patterns**:
- **From host**: `http://localhost:3000`
- **From frontend container**: `http://backend:8000`
- **From backend container**: `http://frontend:3000`
- **Between containers**: Use service name, internal port

---

#### Q5.2: What are the best practices for environment variable management?

**Decision**: Use .env file for development, environment variables for production

**Environment Variable Strategy**:

### 1. .env File (Development)

**.env** (gitignored):
```bash
# Database
DATABASE_URL=postgresql://user:pass@host.neon.tech/dbname

# Auth
BETTER_AUTH_SECRET=your-secret-key-minimum-32-characters-long

# API Keys
OPENAI_API_KEY=sk-your-openai-api-key
NEXT_PUBLIC_OPENAI_DOMAIN_KEY=your-openai-domain-key

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**.env.example** (checked into git):
```bash
# Database - Get from Neon dashboard
DATABASE_URL=postgresql://user:pass@host.neon.tech/dbname

# Auth - Generate with: openssl rand -hex 32
BETTER_AUTH_SECRET=your-secret-key-minimum-32-characters-long

# API Keys - Get from OpenAI dashboard
OPENAI_API_KEY=sk-your-openai-api-key
NEXT_PUBLIC_OPENAI_DOMAIN_KEY=your-openai-domain-key

# Frontend - Backend API URL
NEXT_PUBLIC_API_URL=http://backend:8000
```

### 2. Docker Compose (env_file)

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    env_file:
      - .env  # Load all variables from .env
    environment:
      # Override specific variables
      PYTHONUNBUFFERED: 1

  frontend:
    build: ./frontend
    env_file:
      - .env
    environment:
      # Override for container networking
      NEXT_PUBLIC_API_URL: http://backend:8000
```

### 3. Build-time vs Runtime Variables

**Build-time** (baked into image):
```dockerfile
# Dockerfile
ARG NODE_ENV=production
ENV NODE_ENV=${NODE_ENV}
ENV NEXT_TELEMETRY_DISABLED=1

# Built into image, cannot change later
```

**Runtime** (passed when container starts):
```yaml
# docker-compose.yml
services:
  backend:
    environment:
      - DATABASE_URL=${DATABASE_URL}
      # Can change without rebuilding image
```

**Recommendation**:
- ✅ Use runtime variables for secrets and environment-specific config
- ✅ Use build-time variables for static configuration only
- ❌ Never bake secrets into image with ARG/ENV

### 4. Next.js Environment Variables

**Public vs Private**:

**Public** (exposed to browser):
```bash
# Prefixed with NEXT_PUBLIC_
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_OPENAI_DOMAIN_KEY=pk-your-public-key

# Available in browser and server
```

**Private** (server-only):
```bash
# No prefix
DATABASE_URL=postgresql://...
BETTER_AUTH_SECRET=secret-key

# Only available in Next.js API routes and server components
```

**Security Warning**:
```bash
# ❌ NEVER expose secrets to browser
NEXT_PUBLIC_DATABASE_URL=postgresql://...  # Visible in browser!

# ✅ Keep secrets private (no NEXT_PUBLIC_ prefix)
DATABASE_URL=postgresql://...  # Server-only
```

### 5. Variable Precedence

**Docker Compose Priority** (highest to lowest):
1. `environment:` in docker-compose.yml
2. `env_file:` variables
3. Dockerfile `ENV` instructions
4. Shell environment variables

**Example**:
```yaml
# docker-compose.yml
services:
  backend:
    env_file:
      - .env  # DATABASE_URL=postgresql://dev.neon.tech
    environment:
      - DATABASE_URL=postgresql://prod.neon.tech  # Overrides .env
```

### 6. Secret Management Best Practices

**Development**:
```yaml
# docker-compose.yml
services:
  backend:
    env_file: .env  # Simple .env file
```

**Production (Docker Swarm)**:
```yaml
services:
  backend:
    secrets:
      - database_url
      - auth_secret

secrets:
  database_url:
    external: true
  auth_secret:
    external: true
```

**Production (Kubernetes)**:
```yaml
# ConfigMap for non-sensitive
apiVersion: v1
kind: ConfigMap
metadata:
  name: backend-config
data:
  PYTHONUNBUFFERED: "1"

---
# Secret for sensitive
apiVersion: v1
kind: Secret
metadata:
  name: backend-secrets
type: Opaque
data:
  DATABASE_URL: <base64-encoded>
  AUTH_SECRET: <base64-encoded>
```

### 7. Validation and Documentation

**Backend validation**:
```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    better_auth_secret: str
    openai_api_key: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = False

# Raises error if required variables missing
settings = Settings()
```

**Frontend validation**:
```typescript
// lib/env.ts
const requiredEnvVars = [
  'NEXT_PUBLIC_API_URL',
  'BETTER_AUTH_SECRET'
] as const;

for (const envVar of requiredEnvVars) {
  if (!process.env[envVar]) {
    throw new Error(`Missing required environment variable: ${envVar}`);
  }
}
```

### 8. Security Checklist

```
✅ Add .env to .gitignore
✅ Provide .env.example with placeholder values
✅ Use NEXT_PUBLIC_ prefix only for public variables
✅ Validate required variables on startup
✅ Use runtime environment variables (not build-time)
✅ Rotate secrets regularly
✅ Use external secret managers in production
✅ Never log secret values
✅ Use strong random secrets (32+ characters)
✅ Document all required variables
```

---

#### Q5.3: How to implement health checks and dependency management?

**Decision**: Use Docker HEALTHCHECK with HTTP endpoints and depends_on with service_healthy condition

**Complete Health Check Implementation**:

### 1. Frontend Health Endpoint

**Create health route**:
```typescript
// frontend/app/api/health/route.ts
import { NextResponse } from 'next/server';

export async function GET() {
  try {
    return NextResponse.json({
      status: 'healthy',
      service: 'frontend',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      version: process.env.npm_package_version || '1.0.0'
    }, { status: 200 });
  } catch (error) {
    return NextResponse.json({
      status: 'unhealthy',
      error: error.message
    }, { status: 503 });
  }
}
```

### 2. Backend Health Endpoint

**Verify existing endpoint**:
```python
# backend/app/main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "backend",
        "timestamp": datetime.now().isoformat()
    }
```

### 3. Dockerfile Health Checks

**Frontend Dockerfile**:
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/api/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"
```

**Backend Dockerfile**:
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').getcode()" || exit 1
```

**Health Check Parameters**:
- **--interval=30s**: Check every 30 seconds
- **--timeout=3s**: Health check must complete within 3 seconds
- **--start-period=40s**: Grace period before retries count (container startup time)
- **--retries=3**: Mark unhealthy after 3 consecutive failures

### 4. Docker Compose Health Checks

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 3s
      start_period: 40s
      retries: 3
    # Health status available to depends_on

  frontend:
    build: ./frontend
    depends_on:
      backend:
        condition: service_healthy  # Wait for backend health check
    healthcheck:
      test: ["CMD", "node", "-e", "require('http').get('http://localhost:3000/api/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"]
      interval: 30s
      timeout: 3s
      start_period: 40s
      retries: 3
```

### 5. Dependency Management Patterns

**Pattern 1: depends_on with service_healthy**:
```yaml
frontend:
  depends_on:
    backend:
      condition: service_healthy  # Waits for backend health check
```

**Startup Order**:
1. Backend starts
2. Backend health check runs (every 30s)
3. After 40s (start_period), health checks count toward retries
4. When backend reports healthy, frontend starts

**Pattern 2: depends_on without health check**:
```yaml
frontend:
  depends_on:
    - backend  # Only waits for container to start
```
- ⚠️ Frontend starts before backend is ready
- ⚠️ May cause connection errors
- ❌ Not recommended

**Pattern 3: restart policies**:
```yaml
backend:
  restart: unless-stopped
  healthcheck:
    # ... health check config
```
- Container restarts if health check fails
- Recovers from temporary failures

### 6. Advanced Health Checks

**Database connectivity check**:
```python
# backend/app/main.py
from sqlmodel import select, Session
from app.database import engine

@app.get("/health")
async def health_check():
    checks = {"status": "healthy"}

    # Check database connection
    try:
        with Session(engine) as session:
            session.exec(select(1))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = "error"
        checks["status"] = "degraded"

    status_code = 200 if checks["status"] == "healthy" else 503
    return JSONResponse(checks, status_code=status_code)
```

**Liveness vs Readiness**:

**Liveness** (is container alive?):
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health/live"]
  # Failure = restart container
```

**Readiness** (is container ready for traffic?):
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health/ready"]
  # Failure = remove from load balancer
```

**Implementation**:
```python
@app.get("/health/live")
async def liveness():
    return {"status": "alive"}  # Always returns 200

@app.get("/health/ready")
async def readiness():
    # Check database, cache, dependencies
    if database_ready and cache_ready:
        return {"status": "ready"}
    raise HTTPException(status_code=503, detail="Not ready")
```

### 7. Monitoring Health Status

**Check health status**:
```bash
# View container health
docker ps
# CONTAINER ID   IMAGE       STATUS
# abc123         frontend    Up 5 min (healthy)
# def456         backend     Up 5 min (healthy)

# View health check logs
docker inspect --format='{{json .State.Health}}' backend | jq
```

**Health Status States**:
- **starting**: Within start_period, health checks don't count
- **healthy**: Health check passed
- **unhealthy**: Health check failed after retries

### 8. Kubernetes Health Checks

**Compatibility**:
```yaml
# Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: backend
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 40  # Same as start_period
          periodSeconds: 30        # Same as interval
          timeoutSeconds: 3        # Same as timeout
          failureThreshold: 3      # Same as retries

        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 40
          periodSeconds: 10
```

---

#### Q5.4: How to structure docker-compose for both dev and prod environments?

**Decision**: Use single docker-compose.yml with overrides for development

**Docker Compose Structure**:

### Base Configuration (docker-compose.yml)

**Production-ready base**:
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    image: backend:latest
    container_name: todo-backend
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
    env_file:
      - .env
    networks:
      - todo-network
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 3s
      start_period: 40s
      retries: 3
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    image: frontend:latest
    container_name: todo-frontend
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - NEXT_TELEMETRY_DISABLED=1
      - NEXT_PUBLIC_API_URL=http://backend:8000
    env_file:
      - .env
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - todo-network
    healthcheck:
      test: ["CMD", "node", "-e", "require('http').get('http://localhost:3000/api/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"]
      interval: 30s
      timeout: 3s
      start_period: 40s
      retries: 3
    restart: unless-stopped

networks:
  todo-network:
    driver: bridge
```

### Development Overrides (docker-compose.dev.yml)

**Development-specific configurations**:
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev  # Development Dockerfile with hot-reload
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    volumes:
      - ./backend/app:/app/app:ro  # Mount source code for hot-reload
    environment:
      - PYTHONDONTWRITEBYTECODE=1
    restart: no  # Don't auto-restart in dev

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    command: npm run dev
    volumes:
      - ./frontend/app:/app/app:ro
      - ./frontend/components:/app/components:ro
      - ./frontend/lib:/app/lib:ro
    environment:
      - NODE_ENV=development
    restart: no
```

### Usage

**Production** (default):
```bash
docker-compose up
```

**Development** (with overrides):
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

**Alternative: Single File with Profiles**

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: ${BUILD_TARGET:-runner}  # Production by default
    profiles:
      - production
      - development
    environment:
      - ENV=${ENV:-production}

  backend-dev:
    extends: backend
    profiles:
      - development
    build:
      target: development
    command: uvicorn app.main:app --reload
    volumes:
      - ./backend/app:/app/app
```

**Usage**:
```bash
# Production
docker-compose --profile production up

# Development
docker-compose --profile development up
```

### Environment-Specific .env Files

**.env.production**:
```bash
DATABASE_URL=postgresql://prod-user:pass@prod.neon.tech/prod-db
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
BETTER_AUTH_SECRET=<production-secret>
```

**.env.development**:
```bash
DATABASE_URL=postgresql://dev-user:pass@dev.neon.tech/dev-db
NEXT_PUBLIC_API_URL=http://localhost:8000
BETTER_AUTH_SECRET=dev-secret-for-testing-only
```

**Load specific env file**:
```bash
# Production
docker-compose --env-file .env.production up

# Development
docker-compose --env-file .env.development up
```

### Recommended Structure

**For this project**:
- ✅ Use single `docker-compose.yml` (production-ready)
- ✅ No separate dev compose file (keep it simple)
- ✅ Use `.env` for local development
- ✅ Use Kubernetes ConfigMaps/Secrets for production

**Rationale**:
- Development primarily uses `npm run dev` and `uvicorn --reload` locally
- Docker Compose used for testing containerized deployment
- Kubernetes is the production target (not Docker Compose)

---

## Best Practices Summary

### Multi-Stage Builds
- ✅ Separate builder and runner stages
- ✅ Copy only necessary artifacts to runner
- ✅ Install build tools only in builder stage
- ✅ Use smaller base images for runner stage
- ✅ Expected size reduction: 80-85%

### Layer Caching
- ✅ Order Dockerfile instructions by change frequency
- ✅ Copy dependency files before source code
- ✅ Combine RUN commands with && (cleanup in same layer)
- ✅ Use .dockerignore aggressively
- ✅ Enable BuildKit for parallel builds
- ✅ Expected build time: <5 minutes (first), <2 minutes (rebuild)

### Security
- ✅ Run as non-root user (UID 1001)
- ✅ Use minimal base images (Alpine/Slim)
- ✅ Scan images with Trivy before deployment
- ✅ Pin base image versions
- ✅ No secrets in Dockerfile or images
- ✅ Keep system packages minimal
- ✅ Regular security updates

### Performance
- ✅ Use .dockerignore to reduce build context
- ✅ Leverage BuildKit caching
- ✅ Use --no-cache-dir for package managers
- ✅ Cleanup package manager caches
- ✅ Next.js standalone output (750 MB savings)
- ✅ Python virtual environment isolation
- ✅ Expected startup time: <30 seconds

### Health Checks
- ✅ HTTP-based checks (no curl dependency)
- ✅ Interval: 30 seconds
- ✅ Timeout: 3 seconds
- ✅ Start period: 40 seconds
- ✅ Retries: 3
- ✅ Kubernetes-compatible endpoints

### Environment Management
- ✅ Use .env file for development
- ✅ Use .env.example for documentation
- ✅ Runtime variables (not build-time)
- ✅ Validate required variables on startup
- ✅ NEXT_PUBLIC_ prefix for browser variables
- ✅ External secrets in production

---

## Technology Choices Finalized

### Base Images

**Frontend**:
- **Base Image**: `node:20-alpine`
- **Size**: ~170 MB base, ~180 MB final
- **Rationale**: Minimal size, Node.js 20 LTS, Next.js 15 compatible
- **Alternative**: `node:20-slim` (larger but glibc compatibility)

**Backend**:
- **Base Image**: `python:3.13-slim`
- **Size**: ~130 MB base, ~150 MB final
- **Rationale**: psycopg2 compatibility, pre-compiled wheels, glibc support
- **Alternative**: `python:3.13-alpine` (smaller but compilation issues)

### Build Tools

**Frontend**:
- **Package Manager**: `npm ci` (clean install from lock file)
- **Build**: `npm run build` (Next.js standalone output)
- **Runtime**: `node server.js` (direct execution)

**Backend**:
- **Package Manager**: `pip install --no-cache-dir`
- **Virtual Environment**: `/opt/venv` (isolated dependencies)
- **Runtime**: `uvicorn app.main:app` (single worker for Kubernetes)

### Health Checks

**Frontend**:
- **Method**: Node.js http module (no dependencies)
- **Endpoint**: `http://localhost:3000/api/health`
- **Response**: `{"status": "healthy", "timestamp": "..."}`

**Backend**:
- **Method**: Python urllib (no dependencies)
- **Endpoint**: `http://localhost:8000/health`
- **Response**: `{"status": "healthy", "timestamp": "..."}`

### Networking

**Container to Container**:
- **Method**: Docker Compose service names
- **Frontend to Backend**: `http://backend:8000`
- **Network**: Docker bridge network (default)

**Browser to Services**:
- **Frontend**: `http://localhost:3000`
- **Backend API**: Proxied through frontend Next.js API routes

### Environment Variables

**Development**:
- **Method**: .env file loaded by docker-compose
- **Storage**: Local file (gitignored)

**Production (Kubernetes)**:
- **Non-sensitive**: ConfigMaps
- **Sensitive**: Secrets (base64 encoded)

---

## References

### Official Documentation

1. **Next.js Docker**:
   - https://nextjs.org/docs/deployment#docker-image
   - Standalone output configuration
   - Multi-stage build examples

2. **FastAPI Deployment**:
   - https://fastapi.tiangolo.com/deployment/docker/
   - Uvicorn production configuration
   - Dockerfile best practices

3. **Docker Multi-stage Builds**:
   - https://docs.docker.com/build/building/multi-stage/
   - Layer caching optimization
   - Build context management

4. **Docker Health Checks**:
   - https://docs.docker.com/engine/reference/builder/#healthcheck
   - Parameter configuration
   - Kubernetes integration

5. **Node.js Official Images**:
   - https://hub.docker.com/_/node
   - Alpine vs Slim comparison
   - Version compatibility

6. **Python Official Images**:
   - https://hub.docker.com/_/python
   - Slim vs Alpine guidance
   - Best practices

7. **Docker Compose**:
   - https://docs.docker.com/compose/compose-file/
   - Service dependencies
   - Networking configuration

8. **Dockerfile Best Practices**:
   - https://docs.docker.com/develop/develop-images/dockerfile_best-practices/
   - Layer optimization
   - Security guidelines

### Security Resources

9. **OWASP Docker Security**:
   - https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html
   - Non-root user execution
   - Secret management

10. **Trivy Vulnerability Scanner**:
    - https://github.com/aquasecurity/trivy
    - Installation and usage
    - CI/CD integration

### Community Resources

11. **Docker Hub Examples**:
    - Next.js production Dockerfiles
    - FastAPI deployment patterns

12. **GitHub Best Practices**:
    - Container security templates
    - Multi-stage build patterns

---

## Conclusion

This research document provides comprehensive answers to all containerization questions from the implementation plan. Key takeaways:

1. **Next.js**: Use standalone output with Node.js 20 Alpine for minimal images
2. **FastAPI**: Use Python 3.13 Slim for psycopg2 compatibility
3. **Multi-stage**: Separate builder and runner stages (80%+ size reduction)
4. **Security**: Non-root execution, minimal packages, vulnerability scanning
5. **Performance**: Layer caching, .dockerignore, standalone builds
6. **Health Checks**: HTTP-based checks with 30-second intervals
7. **Networking**: Docker Compose service names for inter-container communication

**Next Steps**:
- Proceed to Phase 1: Design (create data-model.md, contracts/, quickstart.md)
- Use this research to inform Dockerfile templates
- Validate configurations against best practices checklist

---

**Research Complete** ✅ | **Date**: 2025-12-29 | **Ready for Phase 1 Design**
