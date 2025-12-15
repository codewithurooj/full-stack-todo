# Full-Stack Todo Application - Hackathon II Phase 2

## Project Overview
A full-stack todo application built using spec-driven development with Claude Code and Spec-Kit Plus.

**Phase:** Phase 2 - Full-Stack Web Application
**Due Date:** December 14, 2025
**Points:** 150

## Technology Stack

### Frontend
- **Framework:** Next.js 16+ (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Auth:** Better Auth (JWT)
- **Deployment:** Vercel

### Backend
- **Framework:** FastAPI
- **Language:** Python 3.13+
- **ORM:** SQLModel
- **Database:** Neon Serverless PostgreSQL
- **Deployment:** Render/Railway

### Development Tools
- **Spec-Driven:** Claude Code + Spec-Kit Plus
- **Containerization:** Docker Compose
- **Version Control:** Git + GitHub

## Project Structure

```
├── frontend/       # Next.js 16+ application
├── backend/        # FastAPI server
├── specs/          # Feature specifications
├── history/        # PHRs and ADRs
└── .claude/        # Claude Code configuration
```

## Spec-Kit Plus Organization

### Specifications Directory (`/specs`)
- **`/specs/features/`** - What to build (user stories, requirements)
- **`/specs/api/`** - API contracts and endpoints
- **`/specs/database/`** - Schema and data models
- **`/specs/ui/`** - UI components and pages

### History Directory (`/history`)
- **`/history/prompts/`** - Prompt History Records (PHRs)
- **`/history/adr/`** - Architecture Decision Records

## Development Workflow

### Spec-Driven Development Process
1. **Write Specification**
   ```bash
   # Use spec-writer skill
   "Use spec-writer skill to create task CRUD spec"
   ```

2. **Generate Backend Code**
   ```bash
   # Use fastapi-sqlmodel skill
   "Use fastapi-sqlmodel skill to create Task API from @specs/features/task-crud.md"
   ```

3. **Generate Frontend Code**
   ```bash
   # Use nextjs-auth skill
   "Use nextjs-betterauth skill to create Task UI from @specs/ui/task-management.md"
   ```

4. **Test Implementation**
   ```bash
   # Backend tests
   cd backend && pytest

   # Frontend tests
   cd frontend && npm test
   ```

5. **Create PHR**
   ```bash
   # Document your work
   /sp.phr
   ```

## Quick Start Commands

### Development Servers

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:3000
```

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# Runs on http://localhost:8000
# API docs: http://localhost:8000/docs
```

**Both (Docker):**
```bash
docker-compose up
```

### Testing

**Backend:**
```bash
cd backend
pytest                    # Run all tests
pytest --cov             # With coverage
pytest -v                # Verbose output
```

**Frontend:**
```bash
cd frontend
npm test                 # Run tests
npm run test:watch      # Watch mode
```

**E2E Testing Agent (Autonomous):**
```bash
cd testing-agent
python e2e-tester.py     # Run autonomous E2E test suite
cat reports/test-report.md  # View test results
```

## E2E Testing Agent

An autonomous AI agent that tests your entire application end-to-end using the Claude Agent SDK.

### Features

- **Autonomous Testing:** AI-powered agent runs comprehensive test suites
- **Custom MCP Tools:** 4 specialized testing tools for API validation
- **Complete Coverage:** Tests CRUD, auth, validation, security
- **Smart Reporting:** Generates detailed JSON and markdown reports
- **Session Management:** Maintains context across test phases

### Quick Start

```bash
# 1. Install dependencies
cd testing-agent
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY and API_URL

# 3. Run tests
python e2e-tester.py

# 4. View results
cat reports/test-report.md
```

### Custom Testing Tools

The agent includes 4 specialized MCP tools:

1. **`run_api_test`** - Execute API requests with validation
2. **`validate_response_schema`** - Verify JSON response structures
3. **`log_test_result`** - Record test outcomes with timestamps
4. **`generate_test_report`** - Create summary reports

### Test Coverage

- Health checks and API connectivity
- User authentication (signup, signin, JWT)
- Task CRUD operations (Create, Read, Update, Delete)
- Data validation and error handling
- Security testing (SQL injection, XSS)
- Response schema validation

### Directory Structure

```
testing-agent/
├── e2e-tester.py           # Main agent with custom tools
├── requirements.txt        # Python dependencies
├── .env.example           # Configuration template
├── tests/
│   ├── fixtures.json      # Test data
│   └── test-cases.json    # Test scenarios
└── reports/               # Generated test reports
    ├── test-results.json
    └── test-report.md
```

### Documentation

See `testing-agent/README.md` for complete documentation including:
- Custom tool development
- Test customization
- CI/CD integration
- Troubleshooting guide

## Environment Setup

### Required Environment Variables

**Frontend** (`.env.local`):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
BETTER_AUTH_SECRET=your-secret-key-min-32-chars
NEXT_PUBLIC_OPENAI_DOMAIN_KEY=your-openai-domain-key
```

**Backend** (`.env`):
```env
DATABASE_URL=postgresql://user:pass@host.neon.tech/dbname
BETTER_AUTH_SECRET=your-secret-key-min-32-chars
OPENAI_API_KEY=sk-your-openai-api-key
```

## Claude Code Skills

Available skills in `.claude/skills/`:

### 1. Spec-Writer
Generates comprehensive specifications from natural language.
```bash
"Use spec-writer skill to create [feature] specification"
```

### 2. FastAPI + SQLModel
Generates complete backend with models, routes, and tests.
```bash
"Use fastapi-sqlmodel skill to create [Resource] API"
```

### 3. Next.js + Better Auth
Generates frontend components with authentication.
```bash
"Use nextjs-betterauth skill to create [Component] UI"
```

## Slash Commands

- `/sp.specify` - Create/update feature specification
- `/sp.plan` - Generate implementation plan
- `/sp.tasks` - Generate task list
- `/sp.implement` - Execute implementation
- `/sp.phr` - Record prompt history
- `/sp.adr` - Create architecture decision record

## Phase 2 Requirements

### Features to Implement
- ✅ Task CRUD operations (Create, Read, Update, Delete)
- ✅ User authentication (signup/signin)
- ✅ JWT-based API security
- ✅ Responsive UI with Tailwind CSS
- ✅ PostgreSQL database with Neon

### API Endpoints Required
```
GET    /api/{user_id}/tasks          # List all tasks
POST   /api/{user_id}/tasks          # Create task
GET    /api/{user_id}/tasks/{id}     # Get task
PUT    /api/{user_id}/tasks/{id}     # Update task
DELETE /api/{user_id}/tasks/{id}     # Delete task
PATCH  /api/{user_id}/tasks/{id}/complete  # Toggle completion
```

### Submission Requirements
1. ✅ Public GitHub repository
2. ✅ Deployed frontend (Vercel)
3. ✅ Deployed backend (Render/Railway)
4. ✅ Demo video (< 90 seconds)
5. ✅ All specs in `/specs` directory
6. ✅ PHRs in `/history/prompts`

## Helpful References

- **Hackathon PDF:** `Hackathon II - Todo Spec-Driven Development.pdf`
- **Constitution:** `.specify/memory/constitution.md`
- **Frontend Patterns:** `frontend/CLAUDE.md`
- **Backend Patterns:** `backend/CLAUDE.md`
- **Spec Examples:** `/specs/features/`

## Getting Help

### Read Relevant Specs First
```bash
# Before implementing, read:
@specs/features/[feature].md
@specs/api/rest-endpoints.md
@specs/database/schema.md
```

### Reference Code Patterns
```bash
# Frontend patterns
@frontend/CLAUDE.md

# Backend patterns
@backend/CLAUDE.md
```

### Use Skills
```bash
# Generate code quickly
"Use [skill-name] skill to [action]"
```

## Success Metrics

- ✅ All 5 basic CRUD features working
- ✅ User authentication functional
- ✅ All tests passing (90%+ coverage)
- ✅ Deployed and accessible online
- ✅ Demo video submitted
- ✅ Specs and PHRs documented

## Next Steps

1. **Set up environment variables** (see above)
2. **Create task CRUD specification** using spec-writer skill
3. **Generate backend** using fastapi-sqlmodel skill
4. **Generate frontend** using nextjs-betterauth skill
5. **Test locally**
6. **Deploy to Vercel + Render**
7. **Record demo video**
8. **Submit by December 14, 2025**

---

**Let's build this with spec-driven development!** 🚀
