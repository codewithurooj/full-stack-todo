# Tasks: Docker Containerization

**Feature Branch:** `005-docker-containerization`
**Created:** 2025-12-29
**Input:** Implementation plan from `plan.md` and specification from `spec.md`

---

## Phase 1: Setup

- [ ] T001 Verify Docker Engine 20.10+ is installed and running on development machine - `docker --version && docker info`
- [ ] T002 Verify Docker Compose v2+ is installed - `docker compose version`
- [ ] T003 Review dockerfile-generator skill patterns - `.claude/skills/dockerfile-generator.md`

---

## Phase 2: Foundational

- [ ] T004 [P] Create frontend health check endpoint - `frontend/app/api/health/route.ts`
- [ ] T005 [P] Verify backend health check endpoint exists and returns correct response - `backend/app/main.py` line 55-58
- [ ] T006 [P] Update frontend next.config.js to enable standalone output mode - `frontend/next.config.js`
- [ ] T007 [P] Test frontend health check endpoint locally responds with 200 OK - `npm run dev` then `curl http://localhost:3000/api/health`

---

## Phase 3: US1 - Frontend Container

**User Story:** Build and Run Frontend Container (Priority: P1)

**Independent Test:** `docker build -t todo-frontend:latest ./frontend && docker run -d -p 3000:3000 --name test-frontend -e NEXT_PUBLIC_API_URL=http://localhost:8000 todo-frontend:latest && sleep 40 && curl http://localhost:3000/api/health`

### Stage 1: Dockerfile Creation
- [ ] T008 [P] [US1] Create frontend production Dockerfile with Stage 1 (Dependencies) using Node.js 20 Alpine - `frontend/Dockerfile`
- [ ] T009 [US1] Add Stage 2 (Builder) to frontend Dockerfile with Next.js build and standalone output - `frontend/Dockerfile`
- [ ] T010 [US1] Add Stage 3 (Runner) to frontend Dockerfile with non-root user (UID 1001) and minimal runtime - `frontend/Dockerfile`
- [ ] T011 [US1] Add HEALTHCHECK instruction to frontend Dockerfile targeting /api/health endpoint - `frontend/Dockerfile`

### Stage 2: Build Context Optimization
- [ ] T012 [P] [US1] Create comprehensive .dockerignore file for frontend excluding node_modules, .next, .env files - `frontend/.dockerignore`

### Stage 3: Build and Test
- [ ] T013 [US1] Build frontend Docker image and verify successful completion - `docker build -t todo-frontend:latest ./frontend`
- [ ] T014 [US1] Verify frontend image size is under 200 MB - `docker images todo-frontend:latest`
- [ ] T015 [US1] Test frontend container starts successfully and health check passes within 40 seconds - `docker run` with health validation

---

## Phase 4: US2 - Backend Container

**User Story:** Build and Run Backend Container (Priority: P1)

**Independent Test:** `docker build -t todo-backend:latest ./backend && docker run -d -p 8000:8000 --name test-backend -e DATABASE_URL=$DATABASE_URL -e BETTER_AUTH_SECRET=$BETTER_AUTH_SECRET -e OPENAI_API_KEY=$OPENAI_API_KEY todo-backend:latest && sleep 40 && curl http://localhost:8000/health`

### Stage 1: Dockerfile Creation
- [ ] T016 [P] [US2] Create backend production Dockerfile with Stage 1 (Builder) using Python 3.13 Slim - `backend/Dockerfile`
- [ ] T017 [US2] Add virtual environment creation and dependency installation to backend builder stage - `backend/Dockerfile`
- [ ] T018 [US2] Add Stage 2 (Runner) to backend Dockerfile with non-root user (UID 1001) and minimal runtime dependencies - `backend/Dockerfile`
- [ ] T019 [US2] Add HEALTHCHECK instruction to backend Dockerfile targeting /health endpoint - `backend/Dockerfile`
- [ ] T020 [US2] Configure uvicorn CMD with proper host (0.0.0.0) and port (8000) settings - `backend/Dockerfile`

### Stage 2: Build Context Optimization
- [ ] T021 [P] [US2] Create comprehensive .dockerignore file for backend excluding __pycache__, venv, .pytest_cache, .env files - `backend/.dockerignore`

### Stage 3: Build and Test
- [ ] T022 [US2] Build backend Docker image and verify successful completion - `docker build -t todo-backend:latest ./backend`
- [ ] T023 [US2] Verify backend image size is under 200 MB - `docker images todo-backend:latest`
- [ ] T024 [US2] Test backend container starts successfully with database connection and health check passes within 40 seconds - `docker run` with all required environment variables

---

## Phase 5: US3 - Docker Compose

**User Story:** Local Testing with Docker Compose (Priority: P2)

**Independent Test:** `docker compose up -d && sleep 60 && curl http://localhost:3000 && curl http://localhost:8000/health && docker compose logs`

### Stage 1: Configuration
- [ ] T025 [US3] Create production docker-compose.yml defining frontend and backend services - `docker-compose.yml`
- [ ] T026 [US3] Configure service networking, ports (3000, 8000), and dependencies in docker-compose.yml - `docker-compose.yml`
- [ ] T027 [US3] Configure environment variable injection using env_file and inline environment in docker-compose.yml - `docker-compose.yml`
- [ ] T028 [US3] Add health check configurations and restart policies (unless-stopped) to docker-compose.yml - `docker-compose.yml`

### Stage 2: End-to-End Testing
- [ ] T029 [US3] Test full stack with docker-compose up verifying both containers start, become healthy, and communicate successfully - `docker compose up && docker compose ps`
- [ ] T030 [US3] Verify frontend can make successful API requests to backend through Docker network - End-to-end task CRUD test
- [ ] T031 [US3] Test docker-compose logs shows output from both services for debugging - `docker compose logs -f`

---

## Phase 6: US4 - Security & Optimization

**User Story:** Container Security and Optimization (Priority: P3)

**Independent Test:** `trivy image todo-frontend:latest && trivy image todo-backend:latest && docker inspect todo-frontend:latest && docker inspect todo-backend:latest`

### Stage 1: Security Validation
- [ ] T032 [P] [US4] Run security scan on frontend image and verify no critical/high vulnerabilities - `docker scan todo-frontend:latest` or `trivy image todo-frontend:latest`
- [ ] T033 [P] [US4] Run security scan on backend image and verify no critical/high vulnerabilities - `docker scan todo-backend:latest` or `trivy image todo-backend:latest`
- [ ] T034 [US4] Verify both containers run as non-root user (UID 1001) - `docker exec` user validation or `docker inspect`

### Stage 2: Optimization Validation
- [ ] T035 [P] [US4] Verify frontend .dockerignore excludes unnecessary files by comparing build context size before/after - Review `docker build` output
- [ ] T036 [P] [US4] Verify backend .dockerignore excludes unnecessary files by comparing build context size before/after - Review `docker build` output
- [ ] T037 [US4] Measure and document final image sizes (frontend <180 MB, backend <150 MB) - `docker images` output
- [ ] T038 [US4] Measure and document container startup times (both <30 seconds) - Docker logs timestamp analysis

---

## Phase 7: Polish

- [ ] T039 [P] Update root README.md with Docker quick start instructions including build, run, and docker-compose commands - `README.md`
- [ ] T040 [P] Update .env.example with all required Docker environment variables for both services - `.env.example`
- [ ] T041 [P] Create quickstart.md in specs directory with comprehensive Docker deployment guide - `specs/005-docker-containerization/quickstart.md`
- [ ] T042 Remove development Dockerfile artifacts if they exist - `frontend/Dockerfile.dev`, `backend/Dockerfile.dev`
- [ ] T043 Clean up dangling Docker images and containers from testing - `docker system prune`
- [ ] T044 Final validation: Run complete docker-compose up test from fresh state - `docker compose down -v && docker compose build && docker compose up`

---

## Task Execution Notes

### Parallel Execution Opportunities

**Within US1 (Frontend):**
- T008 and T012 can run in parallel (different files)

**Within US2 (Backend):**
- T016 and T021 can run in parallel (different files)

**Within US4 (Security):**
- T032 and T033 can run in parallel (independent scans)
- T035 and T036 can run in parallel (independent validations)

**Cross-Story Parallelism:**
- US1 (T008-T015) and US2 (T016-T024) can be developed in parallel after foundational tasks complete

**Polish Phase:**
- T039, T040, T041 can run in parallel (different files)

### Critical Dependencies

**Sequential Requirements:**
- T001-T003 (Setup) must complete before T004-T007 (Foundational)
- T004-T007 (Foundational) must complete before US1 and US2
- T008-T012 must complete before T013-T015 (can't test without Dockerfile)
- T016-T021 must complete before T022-T024 (can't test without Dockerfile)
- US1 and US2 must complete before US3 (Docker Compose needs both images)
- T025-T028 must complete before T029-T031 (can't test orchestration without config)
- US1, US2, US3 must complete before US4 (can't scan/optimize non-existent images)

### Testing Strategy

**Per-Story Validation:**
- **US1**: Build frontend image → Run container → Test health endpoint → Verify size
- **US2**: Build backend image → Run container with DB connection → Test health endpoint → Verify size
- **US3**: Run docker-compose → Verify both services start → Test inter-service communication → Check logs
- **US4**: Security scan both images → Verify non-root execution → Validate .dockerignore effectiveness → Measure performance

**Acceptance Criteria per US:**
- **US1**: Frontend container runs standalone, serves on port 3000, health check passes, <200 MB
- **US2**: Backend container runs standalone, serves on port 8000, connects to Neon DB, health check passes, <200 MB
- **US3**: Both services orchestrated, network communication works, docker-compose commands functional
- **US4**: No critical vulnerabilities, non-root execution confirmed, images optimized, startup <30s

### Environment Variables Required

**Frontend Container:**
```bash
NEXT_PUBLIC_API_URL=http://backend:8000  # For docker-compose networking
BETTER_AUTH_SECRET=<32-char-secret>
NEXT_PUBLIC_OPENAI_DOMAIN_KEY=<optional>
```

**Backend Container:**
```bash
DATABASE_URL=postgresql://user:pass@host.neon.tech/dbname
BETTER_AUTH_SECRET=<32-char-secret>
OPENAI_API_KEY=sk-<key>
```

### File Paths Reference

**New Files to Create:**
- `frontend/Dockerfile` (Production multi-stage)
- `frontend/.dockerignore` (Build exclusions)
- `frontend/app/api/health/route.ts` (Health check endpoint)
- `backend/Dockerfile` (Production multi-stage)
- `backend/.dockerignore` (Build exclusions)
- `docker-compose.yml` (Production orchestration at root)

**Files to Modify:**
- `frontend/next.config.js` (Add `output: 'standalone'`)
- `README.md` (Add Docker instructions)
- `.env.example` (Add Docker environment variables)

**Files to Verify:**
- `backend/app/main.py` (Confirm /health endpoint exists)

**Files to Remove (if exist):**
- `frontend/Dockerfile.dev`
- `backend/Dockerfile.dev`

### Expected Image Sizes

| Image | Unoptimized | Target | Stretch Goal |
|-------|------------|--------|--------------|
| Frontend | ~1.2 GB | <200 MB | <180 MB |
| Backend | ~800 MB | <200 MB | <150 MB |

### Build Time Expectations

| Task | Expected Duration | Success Criteria |
|------|------------------|------------------|
| Frontend image build | <5 minutes | Build completes without errors |
| Backend image build | <3 minutes | Build completes without errors |
| Frontend container startup | <30 seconds | Health check passes |
| Backend container startup | <30 seconds | Health check passes |
| Docker Compose full stack | <60 seconds | Both services healthy |

---

## Success Criteria Summary

- ✅ All 44 tasks completed
- ✅ Frontend image <200 MB (target <180 MB)
- ✅ Backend image <200 MB (target <150 MB)
- ✅ Both containers start <30 seconds
- ✅ Health checks pass consistently (>95% success rate)
- ✅ No critical or high-severity vulnerabilities
- ✅ Non-root execution (UID 1001) verified
- ✅ Docker Compose orchestration functional
- ✅ Frontend-backend communication working
- ✅ Comprehensive documentation complete

---

**Ready for Implementation** - All tasks defined with clear acceptance criteria, dependencies mapped, parallel opportunities identified, and testing strategies documented.
