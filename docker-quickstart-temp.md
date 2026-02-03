
**Option 2: Run with Docker Compose** 🐳

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode (background)
docker-compose up -d

# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Backend Docs: http://localhost:8000/docs
```

### 🐳 Docker Commands

**Prerequisites:**
- Docker Engine 20.10+
- Docker Compose v2+

**Environment Setup for Docker:**

1. Copy `.env.example` to `.env` in project root:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your actual values:
   ```env
   DATABASE_URL=postgresql://user:pass@host.neon.tech/dbname
   BETTER_AUTH_SECRET=your-secret-32-chars  # Generate: openssl rand -hex 32
   OPENAI_API_KEY=sk-your-openai-api-key
   ```

**Basic Commands:**

```bash
# Build images
docker-compose build

# Start services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f          # All services
docker-compose logs -f backend  # Backend only
docker-compose logs -f frontend # Frontend only

# Check service health
docker-compose ps

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v --remove-orphans

# Rebuild specific service
docker-compose up --build backend
docker-compose up --build frontend
```

**Run commands in containers:**

```bash
# Backend commands
docker-compose exec backend python -m pytest
docker-compose exec backend python -m pytest --cov

# Frontend commands
docker-compose exec frontend npm test
docker-compose exec frontend npm run lint
```

**Build individual containers:**

```bash
# Frontend only
docker build -t todo-frontend:latest ./frontend
docker run -d -p 3000:3000 --env-file .env todo-frontend:latest

# Backend only
docker build -t todo-backend:latest ./backend
docker run -d -p 8000:8000 --env-file .env todo-backend:latest
```

**Image Information:**

```bash
# View image sizes
docker images | grep todo

# Expected sizes:
# todo-frontend:latest  ~180 MB  (85% reduction from unoptimized)
# todo-backend:latest   ~150 MB  (81% reduction from unoptimized)

# Inspect images
docker inspect todo-frontend:latest
docker inspect todo-backend:latest
```

**Troubleshooting Docker:**

```bash
# Health check endpoints
curl http://localhost:3000/api/health  # Frontend health
curl http://localhost:8000/health      # Backend health

# View detailed logs
docker-compose logs --tail=100 backend
docker-compose logs --tail=100 frontend

# Restart specific service
docker-compose restart backend
docker-compose restart frontend

# Clean up everything and rebuild
docker-compose down -v
docker system prune -a
docker-compose up --build
```

**Container Details:**
- Both containers run as non-root user (UID 1001) for security
- Health checks run every 30 seconds
- Auto-restart enabled (unless manually stopped)
- Resource limits: 512MB RAM, 1 CPU per service
- Frontend uses standalone Next.js build (optimized for containers)
- Backend uses Python 3.13 slim base image

For more detailed Docker documentation, see `specs/005-docker-containerization/quickstart.md`
