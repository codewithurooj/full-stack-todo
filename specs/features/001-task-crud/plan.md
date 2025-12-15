# Implementation Plan: Task CRUD Operations

**Branch**: `001-task-crud` | **Date**: 2025-12-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/features/001-task-crud/spec.md`

## Summary

Implement a complete task CRUD system for a full-stack todo application with FastAPI backend and Next.js frontend. Users will be able to create, read, update, delete, and toggle completion status of tasks. All operations require JWT authentication via Better Auth, with strict user data isolation. The system uses Neon PostgreSQL for persistence, SQLModel for ORM, and follows RESTful API design principles.

**Primary Requirement**: Enable authenticated users to manage their personal task lists with full CRUD capabilities.

**Technical Approach**: Monorepo structure with separate frontend (Next.js 16+) and backend (FastAPI) directories. Backend provides RESTful API with JWT middleware, frontend consumes API with Better Auth integration. Database schema enforces user isolation via foreign keys and row-level security.

---

## Technical Context

**Language/Version**:
- Backend: Python 3.13+
- Frontend: TypeScript (Next.js 16+)

**Primary Dependencies**:
- Backend: FastAPI, SQLModel, Pydantic, python-jose (JWT), passlib, Alembic
- Frontend: Next.js 16+, React 18+, Better Auth, Tailwind CSS, TypeScript

**Storage**:
- Neon Serverless PostgreSQL (cloud-hosted)
- Two tables: `users` (Better Auth managed), `tasks` (app-specific)

**Testing**:
- Backend: pytest, pytest-asyncio, httpx (for testing FastAPI)
- Frontend: Jest, React Testing Library (optional for Phase 2)

**Target Platform**:
- Backend: Linux server (Render/Railway)
- Frontend: Vercel Edge Runtime
- Database: Neon Serverless (multi-region PostgreSQL)

**Project Type**: Web application (full-stack)

**Performance Goals**:
- API response time: < 100ms for list operations (p95)
- API response time: < 50ms for CRUD operations (p95)
- Support 100 concurrent users
- Handle 1000+ tasks per user efficiently

**Constraints**:
- All endpoints require JWT authentication
- User data isolation (queries filtered by user_id)
- No manual code writing (spec-driven with Claude Code)
- Stateless API design (no server-side sessions)
- CORS-enabled for cross-origin requests

**Scale/Scope**:
- Target: 1,000+ users
- 10,000+ tasks per user supported
- 6 API endpoints
- 5-10 frontend components
- Single feature branch (001-task-crud)

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Compliance Status

| Principle | Requirement | Status | Notes |
|-----------|-------------|--------|-------|
| **I. Spec-Driven Development** | All features specified before implementation | ✅ PASS | Feature spec complete in `/specs/features/001-task-crud/spec.md` |
| **II. Architecture & Tech Stack** | Monorepo with Next.js 16+ & FastAPI | ✅ PASS | Follows prescribed stack exactly |
| **III. RESTful API Design** | `/api/{user_id}/` base path with standard HTTP methods | ✅ PASS | API spec defines 6 RESTful endpoints |
| **IV. Data Management** | Neon PostgreSQL with SQLModel | ✅ PASS | Schema defined in `/specs/database/schema.md` |
| **V. Testing & Quality** | All 5 basic features functional | ✅ PASS | Feature spec covers all required scenarios |
| **VI. Code Quality** | Clean code, type hints, DRY principle | ✅ PASS | Will be enforced via skills (fastapi-sqlmodel, nextjs-betterauth) |
| **VII. Documentation** | README, CLAUDE.md, specs, history | ✅ PASS | Documentation structure in place |
| **Security & Authentication** | Better Auth JWT, user isolation | ✅ PASS | JWT middleware, user_id verification required |
| **Deployment** | Vercel (frontend) + Render/Railway (backend) | ✅ PASS | Planned deployment targets |

### Quality Gates

- ✅ **Spec Quality**: Feature spec has detailed acceptance criteria for all user stories
- ✅ **Code Quality**: Will use Claude Code skills to generate clean, type-safe code
- ✅ **Security**: JWT authentication on all endpoints, user_id verification
- ✅ **Data Isolation**: Database schema enforces user_id foreign keys with RLS policies
- ✅ **Documentation**: Specs complete, will generate README via skills

### Violations Requiring Justification

**None** - This implementation fully complies with the constitution.

---

## Project Structure

### Documentation (this feature)

```text
specs/features/001-task-crud/
├── spec.md              # Feature specification (✅ EXISTS)
├── plan.md              # This file (implementation plan)
├── research.md          # Phase 0: Technology decisions & patterns
├── data-model.md        # Phase 1: Entity definitions & relationships
├── quickstart.md        # Phase 1: Developer onboarding guide
├── contracts/           # Phase 1: OpenAPI specs for endpoints
│   ├── tasks.openapi.yml
│   └── schemas.json
├── checklists/          # Quality validation checklists
│   └── requirements.md  # (✅ EXISTS)
└── tasks.md             # Phase 2: Detailed task breakdown (created by /sp.tasks)
```

### Source Code (repository root)

```text
full-stack-todo/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI app initialization, CORS, middleware
│   │   ├── config.py          # Environment variables, settings
│   │   ├── database.py        # SQLModel engine, session management
│   │   ├── models/            # SQLModel database models
│   │   │   ├── __init__.py
│   │   │   ├── user.py        # User model (Better Auth schema)
│   │   │   └── task.py        # Task model
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── task.py        # TaskCreate, TaskUpdate, TaskResponse
│   │   │   └── common.py      # Common response wrappers
│   │   ├── routes/            # API endpoint routers
│   │   │   ├── __init__.py
│   │   │   └── tasks.py       # Task CRUD endpoints
│   │   ├── middleware/        # FastAPI middleware
│   │   │   ├── __init__.py
│   │   │   └── auth.py        # JWT verification middleware
│   │   └── utils/             # Helper functions
│   │       ├── __init__.py
│   │       └── jwt.py         # JWT token verification
│   ├── tests/                 # Backend tests
│   │   ├── __init__.py
│   │   ├── conftest.py        # Pytest fixtures
│   │   ├── test_tasks.py      # Task endpoint tests
│   │   └── test_auth.py       # Auth middleware tests
│   ├── migrations/            # Alembic database migrations
│   │   ├── versions/
│   │   │   └── 001_initial_schema.py
│   │   ├── env.py
│   │   └── alembic.ini
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example          # Environment variable template
│   ├── CLAUDE.md             # Backend-specific instructions
│   └── README.md             # Backend setup guide
│
├── frontend/                  # Next.js application
│   ├── app/                   # Next.js App Router
│   │   ├── layout.tsx         # Root layout with Better Auth provider
│   │   ├── page.tsx           # Home page (redirect to /tasks)
│   │   ├── tasks/             # Task management pages
│   │   │   ├── page.tsx       # Task list view
│   │   │   ├── [id]/
│   │   │   │   └── page.tsx   # Task detail/edit view
│   │   │   └── new/
│   │   │       └── page.tsx   # Create task view
│   │   ├── auth/              # Authentication pages
│   │   │   ├── signin/
│   │   │   │   └── page.tsx
│   │   │   └── signup/
│   │   │       └── page.tsx
│   │   └── api/               # Better Auth API routes
│   │       └── auth/
│   │           └── [...all]/route.ts
│   ├── components/            # React components
│   │   ├── ui/                # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── card.tsx
│   │   │   ├── checkbox.tsx
│   │   │   └── dialog.tsx
│   │   ├── TaskList.tsx       # Task list component
│   │   ├── TaskItem.tsx       # Individual task item
│   │   ├── TaskForm.tsx       # Create/edit task form
│   │   ├── DeleteConfirmDialog.tsx
│   │   └── Navbar.tsx         # Navigation with auth state
│   ├── lib/                   # Utilities and configurations
│   │   ├── api/               # API client functions
│   │   │   ├── client.ts      # Base fetch wrapper with auth
│   │   │   └── tasks.ts       # Task API functions
│   │   ├── auth.ts            # Better Auth configuration
│   │   └── utils.ts           # Helper functions (cn, etc.)
│   ├── types/                 # TypeScript type definitions
│   │   └── task.ts            # Task type interfaces
│   ├── tests/                 # Frontend tests (optional for Phase 2)
│   │   └── __tests__/
│   ├── public/                # Static assets
│   ├── .env.local.example    # Environment variable template
│   ├── next.config.js        # Next.js configuration
│   ├── tailwind.config.ts    # Tailwind CSS configuration
│   ├── tsconfig.json         # TypeScript configuration
│   ├── package.json          # npm dependencies
│   ├── CLAUDE.md             # Frontend-specific instructions
│   └── README.md             # Frontend setup guide
│
├── specs/                     # Specifications (✅ EXISTS)
│   ├── overview.md
│   ├── features/001-task-crud/
│   ├── api/rest-endpoints.md
│   ├── database/schema.md
│   └── ui/
│
├── history/                   # Prompt history records
│   └── prompts/
│       ├── general/
│       └── 001-task-crud/
│
├── .specify/                  # Spec-Kit Plus configuration
│   ├── memory/constitution.md
│   └── templates/
│
├── docker-compose.yml         # Local development (backend + db)
├── .gitignore
├── CLAUDE.md                  # Root project instructions (✅ EXISTS)
└── README.md                  # Project overview and setup
```

**Structure Decision**: Web application structure (Option 2) selected due to clear frontend/backend separation. This enables independent development, testing, and deployment of each component. The monorepo structure keeps all code together while maintaining logical boundaries.

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations detected** - All requirements align with constitution principles.

---

## Phase 0: Research & Technology Decisions

### Research Topics

All technology choices are predetermined by the constitution and existing specs. No research phase required for technology selection.

### Predetermined Decisions

| Decision | Rationale | Source |
|----------|-----------|--------|
| **Backend: FastAPI** | High-performance async Python framework, automatic OpenAPI docs | Constitution Section II |
| **Backend ORM: SQLModel** | Type-safe ORM combining SQLAlchemy + Pydantic | Constitution Section IV |
| **Database: Neon PostgreSQL** | Serverless PostgreSQL with connection pooling, auto-scaling | Constitution Section IV |
| **Frontend: Next.js 16+** | React framework with App Router, server components | Constitution Section II |
| **Auth: Better Auth** | JWT-based auth with Next.js integration | Constitution Section II |
| **Styling: Tailwind CSS** | Utility-first CSS framework | Constitution Section II |
| **Migrations: Alembic** | Database migration tool for SQLAlchemy/SQLModel | Standard Python practice |

### Implementation Patterns

#### Backend Patterns

**1. JWT Authentication Middleware**
```python
# Pattern: Dependency injection for auth verification
from fastapi import Depends, HTTPException
from jose import jwt, JWTError

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401)
        return user_id
    except JWTError:
        raise HTTPException(status_code=401)
```

**2. User Data Isolation Pattern**
```python
# Pattern: Always filter by authenticated user_id
@router.get("/api/{user_id}/tasks")
async def list_tasks(
    user_id: str,
    current_user_id: str = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Verify path user_id matches authenticated user
    if user_id != current_user_id:
        raise HTTPException(status_code=403)

    # Query with user isolation
    tasks = session.exec(
        select(Task).where(Task.user_id == user_id)
    ).all()
    return {"data": tasks}
```

**3. Response Wrapper Pattern**
```python
# Pattern: Consistent response structure
from pydantic import BaseModel
from datetime import datetime

class ResponseMeta(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class DataResponse(BaseModel):
    data: Any
    meta: ResponseMeta = Field(default_factory=ResponseMeta)
```

#### Frontend Patterns

**1. API Client with Auth**
```typescript
// Pattern: Centralized API client with automatic auth headers
async function apiRequest(endpoint: string, options: RequestInit = {}) {
  const token = localStorage.getItem('auth_token');

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json();
}
```

**2. Server Component + Client Component Pattern**
```typescript
// Pattern: Server components for data fetching, client components for interactivity

// app/tasks/page.tsx (Server Component)
export default async function TasksPage() {
  // Server-side data fetch (no client-side loading state needed)
  return <TaskList />; // Client component for interactive UI
}

// components/TaskList.tsx (Client Component)
'use client';
export function TaskList() {
  // Client-side state and event handlers
}
```

**3. Optimistic Updates Pattern**
```typescript
// Pattern: Update UI immediately, rollback on error
async function toggleTask(taskId: string) {
  const originalTasks = tasks;

  // Optimistic update
  setTasks(tasks.map(t =>
    t.id === taskId ? { ...t, completed: !t.completed } : t
  ));

  try {
    await api.toggleTaskComplete(userId, taskId);
  } catch (error) {
    // Rollback on error
    setTasks(originalTasks);
    showError('Failed to update task');
  }
}
```

### Best Practices Reference

**Backend Best Practices:**
- Use FastAPI dependency injection for auth, database sessions
- Implement Pydantic schemas for request/response validation
- Use SQLModel for type-safe database operations
- Implement proper error handling with HTTPException
- Use Alembic for database migrations
- Add CORS middleware for frontend access

**Frontend Best Practices:**
- Use Server Components by default, Client Components only when needed
- Implement loading states with React Suspense
- Use TypeScript strict mode
- Follow Next.js App Router conventions
- Use shadcn/ui for consistent UI components
- Implement error boundaries for graceful error handling

---

## Phase 1: Design & Contracts

### Data Model

See [data-model.md](./data-model.md) (to be generated next).

**Summary**:
- **User Entity**: Managed by Better Auth (id, email, name, timestamps)
- **Task Entity**: Application-specific (id, user_id FK, title, description, completed, timestamps)
- **Relationship**: One User has many Tasks (1:N)

### API Contracts

See [contracts/](./contracts/) (to be generated next).

**Endpoints**:
1. `GET /api/{user_id}/tasks` - List all tasks
2. `POST /api/{user_id}/tasks` - Create task
3. `GET /api/{user_id}/tasks/{id}` - Get task details
4. `PUT /api/{user_id}/tasks/{id}` - Update task
5. `DELETE /api/{user_id}/tasks/{id}` - Delete task
6. `PATCH /api/{user_id}/tasks/{id}/complete` - Toggle completion

### Developer Quickstart

See [quickstart.md](./quickstart.md) (to be generated next).

Will include:
- Environment setup instructions
- Database initialization
- Running backend and frontend locally
- Testing the API
- Common development tasks

---

## Phase 2: Implementation Strategy

### Dependency Order

**Critical Path**:
1. Database schema → SQLModel models → API routes → Frontend components
2. Auth system → Protected routes → UI with auth

**Implementation Sequence**:

#### Stage 1: Foundation (Backend)
1. ✅ Database schema (already defined in specs)
2. Set up Neon database instance
3. Create SQLModel models (User, Task)
4. Configure Alembic migrations
5. Apply initial migration

#### Stage 2: Backend API
6. Set up FastAPI project structure
7. Implement database connection (database.py)
8. Implement JWT middleware (middleware/auth.py)
9. Create Pydantic schemas (schemas/task.py)
10. Implement Task CRUD routes (routes/tasks.py)
11. Add CORS middleware
12. Write backend tests

#### Stage 3: Frontend Foundation
13. Set up Next.js project with TypeScript
14. Configure Tailwind CSS
15. Set up Better Auth
16. Create API client utilities (lib/api/)
17. Set up shadcn/ui components

#### Stage 4: Frontend UI
18. Create authentication pages (signin/signup)
19. Implement task list page
20. Implement create task form
21. Implement edit task functionality
22. Implement delete confirmation
23. Implement toggle completion
24. Add loading and error states

#### Stage 5: Integration & Testing
25. Test end-to-end flows
26. Fix bugs and edge cases
27. Add user feedback (toasts, error messages)
28. Performance testing

#### Stage 6: Deployment
29. Deploy backend to Render/Railway
30. Deploy frontend to Vercel
31. Configure environment variables
32. Test production deployment
33. Create demo video

### Skills Usage Plan

**Backend Implementation**:
```bash
# Use fastapi-sqlmodel skill to generate:
# - models/task.py, models/user.py
# - routes/tasks.py with all CRUD endpoints
# - schemas/task.py with Pydantic models
# - tests/test_tasks.py with pytest test cases
# - middleware/auth.py with JWT verification

"Use fastapi-sqlmodel skill to create Task API from @specs/api/rest-endpoints.md and @specs/database/schema.md"
```

**Frontend Implementation**:
```bash
# Use nextjs-betterauth skill to generate:
# - app/tasks/page.tsx (task list)
# - components/TaskForm.tsx (create/edit form)
# - components/TaskList.tsx (list component)
# - components/TaskItem.tsx (individual task)
# - lib/api/tasks.ts (API client)
# - lib/auth.ts (Better Auth config)

"Use nextjs-betterauth skill to create Task UI from @specs/ui/task-management-ui.md"
```

**UI Components**:
```bash
# Use shadcn-ui-library skill to add:
# - Button, Input, Card, Checkbox, Dialog components

"Use shadcn-ui-library skill to add Button Input Card Checkbox Dialog components"
```

### Testing Strategy

**Backend Tests** (pytest):
- Test each endpoint with valid JWT token
- Test unauthorized access (no token, invalid token)
- Test user isolation (user A cannot access user B's tasks)
- Test input validation (empty title, too long, etc.)
- Test CRUD operations end-to-end
- Test concurrent requests

**Frontend Tests** (optional for Phase 2):
- Component rendering tests
- User interaction tests (form submission, clicking buttons)
- API error handling

**Integration Tests**:
- End-to-end user flows (signup → create task → list → edit → delete)
- Authentication flow (signin → access protected route)

### Rollback Plan

**If implementation fails**:
1. Review generated code for spec compliance
2. Refine specifications if ambiguous
3. Re-run skill with updated spec
4. Do NOT manually fix code - iterate on specs

**Common Issues & Solutions**:
- **JWT verification fails**: Check BETTER_AUTH_SECRET matches between frontend/backend
- **CORS errors**: Ensure ALLOWED_ORIGINS includes frontend URL
- **Database connection fails**: Verify DATABASE_URL and Neon connection string
- **User isolation broken**: Ensure all queries include user_id filter

---

## Success Criteria

### Functional Requirements Met

- ✅ FR-001 to FR-015: All functional requirements from spec will be validated
- ✅ All 5 user stories (Create, Read, Update, Delete, Toggle) working end-to-end
- ✅ JWT authentication enforced on all endpoints
- ✅ User data isolation (users cannot see others' tasks)
- ✅ Input validation (title required, length limits)
- ✅ Error handling with clear messages

### Performance Metrics

- Task list loads in < 2 seconds (up to 1000 tasks)
- CRUD operations complete in < 1 second
- API responses < 100ms (list), < 50ms (CRUD)
- Supports 100 concurrent users

### Deployment Checklist

- [ ] Backend deployed to Render/Railway with public URL
- [ ] Frontend deployed to Vercel with public URL
- [ ] Environment variables configured in deployment platforms
- [ ] Database accessible from backend
- [ ] CORS configured for production frontend URL
- [ ] Better Auth domain allowlist includes production URL
- [ ] Manual testing of all features in production
- [ ] Demo video created (< 90 seconds)

---

## Next Steps

1. **Generate research.md**: Document technology choices and patterns (already complete above)
2. **Generate data-model.md**: Detailed entity definitions with validation rules
3. **Generate contracts/**: OpenAPI specification for all endpoints
4. **Generate quickstart.md**: Developer onboarding guide
5. **Run /sp.tasks**: Break down implementation into actionable tasks
6. **Begin implementation**: Use skills to generate code from specs

---

**Plan Status**: ✅ COMPLETE - Ready for task generation (`/sp.tasks`)
**Next Command**: `/sp.tasks` to generate detailed task breakdown
**Estimated Implementation Time**: 8-12 hours (with skills)
