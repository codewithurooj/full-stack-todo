# Backend Development Guidelines

## Stack
- **Framework:** FastAPI
- **Language:** Python 3.13+
- **ORM:** SQLModel
- **Database:** Neon Serverless PostgreSQL
- **Authentication:** JWT tokens (shared secret with frontend)

## Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app entry point
│   ├── config.py         # Configuration management
│   ├── database.py       # Database session & engine
│   ├── models/           # SQLModel models
│   │   ├── __init__.py
│   │   ├── user.py       # User model (Better Auth)
│   │   └── task.py       # Task model
│   ├── routes/           # API route handlers
│   │   ├── __init__.py
│   │   └── tasks.py      # Task CRUD endpoints
│   ├── services/         # Business logic
│   │   ├── __init__.py
│   │   └── task_service.py
│   ├── middleware/       # Custom middleware
│   │   ├── __init__.py
│   │   └── auth.py       # JWT verification
│   └── utils/            # Utility functions
│       └── __init__.py
├── tests/                # Pytest tests
│   ├── __init__.py
│   ├── conftest.py       # Test fixtures
│   └── test_tasks.py
├── requirements.txt      # Dependencies
├── pyproject.toml        # Project metadata
└── .env.example          # Environment template
```

## Development Patterns

### Database Models with SQLModel
```python
# app/models/task.py
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class TaskBase(SQLModel):
    title: str
    description: Optional[str] = None
    completed: bool = False

class Task(TaskBase, table=True):
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)  # JWT user ID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TaskCreate(TaskBase):
    pass

class TaskUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

class TaskRead(TaskBase):
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
```

### Database Session Management
```python
# app/database.py
from sqlmodel import create_engine, Session
from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=True,  # SQL logging in development
    pool_pre_ping=True  # Verify connections before using
)

def get_session():
    """Dependency for database sessions"""
    with Session(engine) as session:
        yield session
```

### API Route Patterns
```python
# app/routes/tasks.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.database import get_session
from app.models.task import Task, TaskCreate, TaskUpdate, TaskRead
from app.middleware.auth import get_current_user_id

router = APIRouter(prefix="/api/{user_id}/tasks", tags=["tasks"])

@router.get("", response_model=list[TaskRead])
async def list_tasks(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """List all tasks for authenticated user"""
    # Verify user_id matches JWT
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    statement = select(Task).where(Task.user_id == user_id)
    tasks = session.exec(statement).all()
    return tasks

@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    user_id: str,
    task: TaskCreate,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """Create a new task"""
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    db_task = Task(**task.model_dump(), user_id=user_id)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    user_id: str,
    task_id: int,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """Get a specific task"""
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    task = session.get(Task, task_id)
    if not task or task.user_id != user_id:
        raise HTTPException(status_code=404, detail="Task not found")

    return task

@router.put("/{task_id}", response_model=TaskRead)
async def update_task(
    user_id: str,
    task_id: int,
    task_update: TaskUpdate,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """Update a task"""
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    db_task = session.get(Task, task_id)
    if not db_task or db_task.user_id != user_id:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)

    db_task.updated_at = datetime.utcnow()
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    user_id: str,
    task_id: int,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """Delete a task"""
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    task = session.get(Task, task_id)
    if not task or task.user_id != user_id:
        raise HTTPException(status_code=404, detail="Task not found")

    session.delete(task)
    session.commit()

@router.patch("/{task_id}/complete", response_model=TaskRead)
async def toggle_complete(
    user_id: str,
    task_id: int,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """Toggle task completion status"""
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    db_task = session.get(Task, task_id)
    if not db_task or db_task.user_id != user_id:
        raise HTTPException(status_code=404, detail="Task not found")

    db_task.completed = not db_task.completed
    db_task.updated_at = datetime.utcnow()
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task
```

### JWT Authentication Middleware
```python
# app/middleware/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
import jwt
from app.config import settings

security = HTTPBearer()

async def get_current_user_id(
    credentials: HTTPAuthCredentials = Depends(security)
) -> str:
    """Extract and validate JWT token, return user_id"""
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.BETTER_AUTH_SECRET,
            algorithms=["HS256"]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
```

### Configuration Management
```python
# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str
    BETTER_AUTH_SECRET: str
    OPENAI_API_KEY: str = ""

    # CORS settings
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
```

### FastAPI Application Setup
```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import tasks
from app.database import engine
from sqlmodel import SQLModel

# Create database tables
SQLModel.metadata.create_all(engine)

app = FastAPI(
    title="Todo API",
    description="Full-Stack Todo Application API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tasks.router)

@app.get("/")
async def root():
    return {"message": "Todo API - Phase 2"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

## Error Handling

### Standard Error Responses
```python
from fastapi import HTTPException, status

# 400 Bad Request
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Invalid input data"
)

# 401 Unauthorized
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Authentication required"
)

# 403 Forbidden
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Unauthorized access"
)

# 404 Not Found
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Resource not found"
)

# 500 Internal Server Error (handled automatically)
```

## Testing with Pytest

### Test Configuration
```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool
from app.main import app
from app.database import get_session

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
```

### Test Examples
```python
# tests/test_tasks.py
def test_create_task(client, mock_jwt):
    response = client.post(
        "/api/user123/tasks",
        json={"title": "Test Task", "description": "Test"},
        headers={"Authorization": f"Bearer {mock_jwt}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["user_id"] == "user123"

def test_list_tasks(client, mock_jwt):
    response = client.get(
        "/api/user123/tasks",
        headers={"Authorization": f"Bearer {mock_jwt}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

## Running & Building

```bash
# Development
uvicorn app.main:app --reload

# With custom host/port
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Testing
pytest
pytest --cov=app
pytest -v

# Type checking
mypy app/

# Linting
ruff check app/
```

## Environment Variables
Required in `.env`:
```env
DATABASE_URL=postgresql://user:password@host.neon.tech/dbname
BETTER_AUTH_SECRET=your-secret-key-min-32-chars
OPENAI_API_KEY=sk-your-openai-api-key
```

## Best Practices
- ✅ Use SQLModel for all database models
- ✅ Always verify user_id matches JWT on all endpoints
- ✅ Use Pydantic models for request/response validation
- ✅ Include proper HTTP status codes
- ✅ Handle database sessions with context managers
- ✅ Write tests for all endpoints
- ✅ Use async/await for I/O operations
- ✅ Never log secrets or tokens
- ✅ Use environment variables for configuration
- ✅ Implement proper error handling

## Security Checklist
- ✅ JWT verification on all protected endpoints
- ✅ User ID validation (path param matches JWT)
- ✅ Database queries filtered by user_id
- ✅ Secrets in environment variables, never hardcoded
- ✅ CORS properly configured
- ✅ SQL injection prevention (SQLModel parameterized queries)
- ✅ Input validation with Pydantic models

---

## MCP Server Patterns (Feature 002)

### Overview
MCP (Model Context Protocol) server enables AI-powered task management through OpenAI function calling with 5 stateless tools.

### Architecture
```
app/
├── mcp_server/
│   ├── server.py          # Tool registry & rate limiting
│   ├── errors.py          # Custom exceptions (MCPError, ValidationError, etc.)
│   ├── validation.py      # Shared validation utilities
│   ├── auth.py            # JWT verification for MCP tools
│   └── tools/
│       ├── add_task.py
│       ├── list_tasks.py
│       ├── complete_task.py
│       ├── delete_task.py
│       └── update_task.py
├── routes/
│   ├── mcp.py            # MCP tool HTTP endpoints
│   └── chat.py           # AI chat endpoint with OpenAI integration
```

### MCP Tool Pattern
```python
# app/mcp_server/tools/add_task.py
from pydantic import BaseModel, Field
from sqlmodel import Session
from app.mcp_server.validation import validate_user_id, validate_title
from app.mcp_server.auth import verify_user_authorization
from app.mcp_server.errors import DatabaseError

class AddTaskRequest(BaseModel):
    """Request model following OpenAI function schema"""
    user_id: str = Field(..., description="User identifier")
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)

class AddTaskResponse(BaseModel):
    """Response model"""
    task_id: str
    title: str
    completed: bool
    created_at: datetime

def add_task(
    request: AddTaskRequest,
    token_user_id: str,
    session: Session
) -> AddTaskResponse:
    """Stateless tool handler"""
    # 1. Validate inputs
    validate_user_id(request.user_id)
    validate_title(request.title)

    # 2. Verify authorization
    verify_user_authorization(request.user_id, token_user_id)

    # 3. Execute database operation
    try:
        db_task = Task(user_id=request.user_id, title=request.title, ...)
        session.add(db_task)
        session.commit()
        session.refresh(db_task)
        return AddTaskResponse(task_id=str(db_task.id), ...)
    except Exception as e:
        session.rollback()
        raise DatabaseError(message="Failed to create task", details={"error": str(e)})
```

### Tool Registration
```python
# app/mcp_server/server.py
from app.mcp_server.tools.add_task import add_task

register_tool(
    name="add_task",
    handler=add_task,
    rate_limit="100/hour",
    description="Create a new task for the authenticated user"
)
```

### MCP HTTP Endpoint Pattern
```python
# app/routes/mcp.py
from app.mcp_server.server import limiter, get_tool_handler

@router.post("/add_task")
@limiter.limit("100/hour")
async def add_task_endpoint(
    request: Request,
    task_request: AddTaskRequest,
    credentials: HTTPAuthCredentials = Depends(security),
    session: Session = Depends(get_session)
):
    """MCP tool endpoint with rate limiting"""
    try:
        # Verify JWT
        token = credentials.credentials
        token_user_id = verify_jwt_token(token)

        # Execute tool
        handler = get_tool_handler("add_task")
        result = handler(request=task_request, token_user_id=token_user_id, session=session)

        logger.info(f"add_task: user={token_user_id}, task_id={result.task_id}")
        return result

    except MCPError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
```

### Chat Endpoint with OpenAI Integration
```python
# app/routes/chat.py
from openai import OpenAI
from app.mcp_server.server import get_all_tool_schemas

@router.post("")
async def chat_endpoint(user_id: str, chat_request: ChatRequest, ...):
    """
    Stateless 8-step chat flow:
    1. Fetch conversation history from DB
    2. Build messages array (system + history + user message)
    3. Store user message
    4. Call OpenAI with tool schemas
    5. If tool calls: invoke tools and get results
    6. If tool calls: call OpenAI again with results
    7. Store assistant message
    8. Return response
    """
    # Fetch history
    messages = [{"role": "system", "content": "You are a task management assistant..."}]
    # ... add history from DB
    messages.append({"role": "user", "content": chat_request.message})

    # Call OpenAI
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=get_all_tool_schemas(),
        tool_choice="auto"
    )

    # Handle tool calls if present
    if response.choices[0].message.tool_calls:
        for tool_call in response.choices[0].message.tool_calls:
            # Execute tool and add result to messages
            handler = get_tool_handler(tool_call.function.name)
            result = handler(...)
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result.model_dump_json()})

        # Call OpenAI again with tool results
        response = openai_client.chat.completions.create(model="gpt-4o", messages=messages)

    # Store and return assistant message
    assistant_message = response.choices[0].message.content
    # ... store in DB
    return ChatResponse(assistant_message=assistant_message, ...)
```

### Error Handling
```python
# app/mcp_server/errors.py
class MCPError(Exception):
    """Base MCP exception with JSON serialization"""
    def __init__(self, message: str, code: str, status_code: int, details: dict):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details

    def to_dict(self):
        return {"error": {"message": self.message, "code": self.code, "details": self.details}}

class ValidationError(MCPError):
    """400 - Input validation failed"""
    def __init__(self, message: str, details=None):
        super().__init__(message, "VALIDATION_ERROR", 400, details or {})

class AuthorizationError(MCPError):
    """403 - User not authorized"""
    def __init__(self, message="Unauthorized access", details=None):
        super().__init__(message, "AUTHORIZATION_ERROR", 403, details or {})

class NotFoundError(MCPError):
    """404 - Resource not found"""
    def __init__(self, message="Resource not found", details=None):
        super().__init__(message, "NOT_FOUND", 404, details or {})
```

### Rate Limiting with slowapi
```python
# app/mcp_server/server.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# In main.py
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

### MCP Best Practices
- ✅ **Stateless design**: No server-side session state, all context from DB
- ✅ **User isolation**: Verify user_id parameter matches JWT token on every tool call
- ✅ **Validation first**: Validate all inputs before authorization checks
- ✅ **Rate limiting**: Per-tool limits (100/hour creates, 1000/hour reads, 200/hour updates)
- ✅ **Structured errors**: Use MCPError hierarchy with JSON serialization
- ✅ **Logging**: Log all tool invocations with user_id and result summary
- ✅ **Pydantic models**: Define Request/Response models matching OpenAI function schemas
- ✅ **Database rollback**: Always rollback on errors to maintain consistency

### Testing MCP Tools
```bash
# Test add_task tool directly
curl -X POST http://localhost:8000/mcp/tools/add_task \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "title": "Buy groceries"}'

# Test via chat endpoint
curl -X POST http://localhost:8000/api/user123/chat \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "I need to buy groceries tomorrow"}'
```

---

**Build robust, type-safe APIs with FastAPI!** 🚀
