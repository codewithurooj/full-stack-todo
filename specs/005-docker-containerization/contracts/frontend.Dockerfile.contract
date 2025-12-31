# Frontend Dockerfile Contract
# Complete Next.js 15+ Multi-Stage Production Dockerfile Template
# Base Image: node:20-alpine
# Target: Production-ready container (~180MB)
# Research: specs/001-docker-containerization/research.md

# ==============================================================================
# Stage 1: Dependencies
# Purpose: Install all dependencies including devDependencies
# Output: /app/node_modules
# ==============================================================================
FROM node:20-alpine AS deps

# Install libc6-compat for npm packages with native bindings
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copy package files for dependency installation
COPY package.json package-lock.json ./

# Clean install from lock file (reproducible builds)
# npm ci is faster and more reliable than npm install for CI/CD
RUN npm ci

# ==============================================================================
# Stage 2: Builder
# Purpose: Build Next.js application with standalone output
# Output: .next/standalone, .next/static, public/
# ==============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy node_modules from deps stage (faster than reinstalling)
COPY --from=deps /app/node_modules ./node_modules

# Copy application source code
COPY . .

# Disable Next.js telemetry during build
ENV NEXT_TELEMETRY_DISABLED=1

# Build Next.js application
# Standalone output mode generates self-contained server.js (~50MB vs ~800MB)
# Configuration required in next.config.js:
#   module.exports = { output: 'standalone' }
RUN npm run build

# ==============================================================================
# Stage 3: Runner
# Purpose: Minimal production runtime environment
# Output: Production-ready container (~180MB)
# ==============================================================================
FROM node:20-alpine AS runner

WORKDIR /app

# Set production environment
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user for security (UID 1001)
# Alpine uses addgroup/adduser commands
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy public directory (user-uploaded static files, favicon, etc.)
# Must be at /app/public for Next.js to serve files correctly
COPY --from=builder /app/public ./public

# Copy standalone output (self-contained server with minimal dependencies)
# Set ownership to non-root user
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./

# Copy Next.js generated static assets (JS bundles, CSS chunks)
# Must be at /app/.next/static for Next.js to serve assets correctly
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Switch to non-root user
USER nextjs

# Expose port 3000 (Next.js default)
EXPOSE 3000

# Environment variable for port (can be overridden)
ENV PORT=3000

# Health check using Node.js built-in http module (no external dependencies)
# Checks /api/health endpoint every 30 seconds
# start-period=40s gives container time to start before health checks count
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/api/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Start Next.js standalone server
# Uses exec form (not shell form) for proper signal handling
CMD ["node", "server.js"]

# ==============================================================================
# Build Instructions:
#
# 1. Ensure next.config.js has: output: 'standalone'
# 2. Build image:
#    docker build -t todo-frontend:latest -f Dockerfile ./frontend
# 3. Run container:
#    docker run -p 3000:3000 \
#      -e NEXT_PUBLIC_API_URL=http://backend:8000 \
#      -e BETTER_AUTH_SECRET=your-secret-key \
#      todo-frontend:latest
#
# Expected Results:
# - Image size: ~180MB (85% reduction from ~1.2GB)
# - Build time: ~4-5 minutes (first build), ~1-2 minutes (code changes)
# - Startup time: ~25 seconds
# - Running as: nextjs (UID 1001)
# ==============================================================================

# ==============================================================================
# Required Files:
#
# 1. frontend/app/api/health/route.ts:
#    export async function GET() {
#      return NextResponse.json({ status: 'healthy' }, { status: 200 });
#    }
#
# 2. frontend/next.config.js:
#    module.exports = {
#      output: 'standalone',
#      // ... other config
#    }
#
# 3. frontend/.dockerignore (see frontend.dockerignore.contract)
# ==============================================================================

# ==============================================================================
# Troubleshooting:
#
# Issue: "Cannot find module" errors
# Solution: Ensure all dependencies are in package.json, not devDependencies
#
# Issue: 404 errors for JavaScript bundles
# Solution: Ensure .next/static is copied to correct location
#
# Issue: Missing favicon or images
# Solution: Ensure public/ directory is copied
#
# Issue: Health check failing
# Solution: Ensure /api/health route exists and returns 200 status
#
# Issue: Permission denied errors
# Solution: Ensure files are owned by nextjs user (--chown in COPY)
# ==============================================================================
