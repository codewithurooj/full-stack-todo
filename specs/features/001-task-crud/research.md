# Research & Technology Decisions: Task CRUD Operations

**Feature**: 001-task-crud | **Date**: 2025-12-12

## Summary

All technology choices for this feature are predetermined by the project constitution (`/.specify/memory/constitution.md`). This document records the decisions and their rationale for reference.

---

## Technology Stack Decisions

### Backend Stack

#### Decision 1: FastAPI Framework

**Chosen**: FastAPI 0.104+

**Rationale**:
- High-performance async Python web framework
- Automatic OpenAPI documentation generation
- Built-in Pydantic validation
- Native async/await support for database operations
- Type hints throughout for better IDE support
- Constitution mandated (Section II)

**Alternatives Considered**: None (constitution requirement)

**Implementation Notes**:
- Use dependency injection for database sessions and auth
- Enable CORS middleware for frontend access
- Use HTTPException for consistent error responses

---

#### Decision 2: SQLModel ORM

**Chosen**: SQLModel 0.0.14+

**Rationale**:
- Combines SQLAlchemy (mature ORM) with Pydantic (validation)
- Type-safe database operations
- Compatible with FastAPI's dependency injection
- Single model definition for both DB and API schemas
- Constitution mandated (Section IV)

**Alternatives Considered**: None (constitution requirement)

**Implementation Notes**:
- Use `Field` for validation and constraints
- Define relationships with `Relationship` (optional)
- Use `select` statements for queries (SQLAlchemy 2.0 style)

---

#### Decision 3: Neon PostgreSQL

**Chosen**: Neon Serverless PostgreSQL 15+

**Rationale**:
- Serverless PostgreSQL with connection pooling
- Auto-scaling and automatic backups
- Free tier sufficient for Phase 2
- Point-in-time recovery (PITR)
- Compatible with standard PostgreSQL tools
- Constitution mandated (Section IV)

**Alternatives Considered**: None (constitution requirement)

**Implementation Notes**:
- Connection string includes `?sslmode=require`
- Use connection pooling (20-50 connections)
- Enable row-level security (RLS) for user isolation

---

#### Decision 4: Alembic Migrations

**Chosen**: Alembic 1.13+

**Rationale**:
- Standard migration tool for SQLAlchemy/SQLModel
- Version control for database schema
- Supports upgrade and downgrade paths
- Auto-generation of migrations from model changes

**Alternatives Considered**: None (industry standard)

**Implementation Notes**:
- Store migrations in `backend/migrations/versions/`
- Use `alembic revision --autogenerate` for new migrations
- Always review auto-generated migrations before applying

---

### Frontend Stack

#### Decision 5: Next.js 16+ (App Router)

**Chosen**: Next.js 16+ with App Router

**Rationale**:
- React framework with server-side rendering (SSR)
- App Router for file-based routing
- Server components by default (better performance)
- Built-in optimization (images, fonts, code splitting)
- Vercel deployment integration
- Constitution mandated (Section II)

**Alternatives Considered**: None (constitution requirement)

**Implementation Notes**:
- Use server components for data fetching (no client-side loading states)
- Use client components only for interactivity (`'use client'` directive)
- Implement loading.tsx and error.tsx for better UX

---

#### Decision 6: Better Auth

**Chosen**: Better Auth 1.0+

**Rationale**:
- JWT-based authentication library
- Next.js integration
- Supports email/password authentication
- Provides hooks for auth state management
- Shared secret with backend for JWT verification
- Constitution mandated (Section II)

**Alternatives Considered**: None (constitution requirement)

**Implementation Notes**:
- Configure in `lib/auth.ts`
- Use `BETTER_AUTH_SECRET` environment variable (must match backend)
- Store JWT token in localStorage or httpOnly cookies
- Implement auth middleware for protected routes

---

#### Decision 7: Tailwind CSS

**Chosen**: Tailwind CSS 3.4+

**Rationale**:
- Utility-first CSS framework
- No runtime overhead (build-time CSS generation)
- Responsive design with mobile-first approach
- Customizable via `tailwind.config.ts`
- Constitution mandated (Section II)

**Alternatives Considered**: None (constitution requirement)

**Implementation Notes**:
- No inline styles (use Tailwind classes only)
- Use `cn` utility for conditional classes
- Extend default theme for custom colors/spacing

---

#### Decision 8: shadcn/ui Components

**Chosen**: shadcn/ui (Radix UI primitives)

**Rationale**:
- High-quality, accessible React components
- Built on Radix UI (primitives)
- Styled with Tailwind CSS
- Copy/paste components (not NPM package)
- Full control over component code

**Alternatives Considered**: Headless UI, Chakra UI (shadcn/ui preferred for Tailwind integration)

**Implementation Notes**:
- Install components individually as needed
- Components in `components/ui/`
- Use `button`, `input`, `card`, `checkbox`, `dialog` for task UI

---

## Implementation Patterns

### Backend Patterns

#### Pattern 1: JWT Middleware for Authentication

**Decision**: Use FastAPI dependency injection for JWT verification

**Rationale**:
- Centralized authentication logic
- Reusable across all protected endpoints
- Clear separation of concerns

**Implementation**:
```python
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

@router.get("/api/{user_id}/tasks")
async def list_tasks(
    user_id: str,
    current_user_id: str = Depends(get_current_user)
):
    if user_id != current_user_id:
        raise HTTPException(status_code=403)
    # ... query tasks
```

---

#### Pattern 2: User Data Isolation

**Decision**: Always filter queries by authenticated user_id

**Rationale**:
- Prevents cross-user data access
- Enforced at application level
- Complements database-level RLS

**Implementation**:
```python
# ALWAYS include user_id filter
tasks = session.exec(
    select(Task).where(Task.user_id == current_user_id)
).all()

# Verify user owns resource before update/delete
task = session.exec(
    select(Task).where(
        Task.id == task_id,
        Task.user_id == current_user_id
    )
).first()
if not task:
    raise HTTPException(status_code=404)
```

---

#### Pattern 3: Consistent Response Wrapper

**Decision**: Use standard response structure for all endpoints

**Rationale**:
- Predictable API contract
- Includes metadata (timestamp, pagination)
- Clear distinction between success and error responses

**Implementation**:
```python
from pydantic import BaseModel
from datetime import datetime

class ResponseMeta(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class DataResponse(BaseModel):
    data: Any
    meta: ResponseMeta = Field(default_factory=ResponseMeta)

# Usage
return DataResponse(data=tasks)
```

---

### Frontend Patterns

#### Pattern 4: Centralized API Client

**Decision**: Create reusable API client with automatic auth headers

**Rationale**:
- DRY principle (don't repeat auth logic)
- Centralized error handling
- Easy to add logging, retry logic, etc.

**Implementation**:
```typescript
// lib/api/client.ts
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
    const error = await response.json();
    throw new Error(error.error.message);
  }

  return response.status === 204 ? null : response.json();
}
```

---

#### Pattern 5: Server Component + Client Component

**Decision**: Use server components for data fetching, client components for interactivity

**Rationale**:
- Reduces JavaScript sent to client
- Server components can access backend directly (in future)
- Client components only where needed (forms, buttons, etc.)

**Implementation**:
```typescript
// app/tasks/page.tsx (Server Component)
export default async function TasksPage() {
  // Could fetch data here server-side in future
  return <TaskList />;
}

// components/TaskList.tsx (Client Component)
'use client';
export function TaskList() {
  const [tasks, setTasks] = useState([]);
  // Client-side state and event handlers
}
```

---

#### Pattern 6: Optimistic Updates

**Decision**: Update UI immediately, rollback on error

**Rationale**:
- Better perceived performance
- Users see instant feedback
- Network latency doesn't block UI

**Implementation**:
```typescript
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

---

## Security Decisions

### Decision: JWT Token Storage

**Chosen**: localStorage

**Rationale**:
- Simple implementation for Phase 2
- Works across tabs
- Better Auth default

**Trade-offs**:
- Vulnerable to XSS attacks (mitigated by Next.js CSP headers)
- Cannot be httpOnly (unlike cookies)

**Future Enhancement**: Use httpOnly cookies for production

---

### Decision: User ID in URL Path

**Chosen**: Include user_id in API path (`/api/{user_id}/tasks`)

**Rationale**:
- Explicit user context in URL
- Easier to verify authorization (path user_id vs token user_id)
- Follows constitution requirement (Section III)

**Security**: Always verify path user_id matches authenticated user_id

---

### Decision: CORS Configuration

**Chosen**: Whitelist specific origins

**Rationale**:
- Prevents unauthorized frontend access
- Development: `http://localhost:3000`
- Production: Vercel deployment URL

**Implementation**:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Performance Decisions

### Decision: Database Indexes

**Chosen**: Strategic indexes on common query patterns

**Rationale**:
- O(log n) query performance
- Composite indexes for filtered + sorted queries
- Minimal storage overhead

**Indexes**:
- `idx_tasks_user_id`: Filter by user
- `idx_tasks_user_completed`: Filter by user + completion status
- `idx_tasks_created_at`: Sort by creation date
- `idx_tasks_user_completed_created`: Composite for filtered + sorted

---

### Decision: Connection Pooling

**Chosen**: 20 connections minimum, 10 max overflow

**Rationale**:
- Balances concurrency with resource usage
- Neon recommends 20-50 connections for serverless
- Prevents connection exhaustion

**Implementation**:
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True  # Verify connections before use
)
```

---

## Testing Decisions

### Decision: pytest for Backend Tests

**Chosen**: pytest with fixtures for test data

**Rationale**:
- Industry standard for Python testing
- Powerful fixture system
- Async test support (pytest-asyncio)

**Implementation**:
```python
@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_create_task(client, auth_token):
    response = client.post(
        f"/api/{user_id}/tasks",
        json={"title": "Test task"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
```

---

## Deployment Decisions

### Decision: Render for Backend

**Chosen**: Render (free tier)

**Rationale**:
- Free tier available
- Automatic deployments from GitHub
- PostgreSQL addon if needed (using Neon instead)
- Environment variable management

**Alternative**: Railway (also viable)

---

### Decision: Vercel for Frontend

**Chosen**: Vercel (free tier)

**Rationale**:
- Built by Next.js team (best integration)
- Automatic deployments from GitHub
- Edge network (global CDN)
- Environment variable management
- Preview deployments for PRs

---

## Rejected Alternatives

### Why Not GraphQL?

**Rejected**: GraphQL API instead of REST

**Reason**:
- Constitution mandates REST (Section III)
- REST is simpler for CRUD operations
- GraphQL adds unnecessary complexity for Phase 2

---

### Why Not Server Actions?

**Rejected**: Next.js Server Actions for mutations

**Reason**:
- Backend is separate FastAPI service
- Server Actions only work with Next.js backend
- Need RESTful API for future mobile clients

---

### Why Not Prisma?

**Rejected**: Prisma ORM instead of SQLModel

**Reason**:
- Prisma is for Node.js/TypeScript (backend is Python)
- SQLModel is Python-native and constitution-mandated

---

## Key Takeaways

1. **All major technology choices predetermined by constitution** - no research needed
2. **Implementation patterns follow industry best practices** - JWT auth, user isolation, consistent responses
3. **Security prioritized** - JWT verification, CORS, user data isolation
4. **Performance optimized** - Strategic indexes, connection pooling
5. **Deployment platforms selected** - Render (backend), Vercel (frontend)

---

**Status**: ✅ COMPLETE
**Next**: Proceed to implementation using `/sp.tasks` to generate task breakdown
