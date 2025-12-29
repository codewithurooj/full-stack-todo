# Phase 0 Research: MCP Server Technology Decisions

**Feature**: 002-mcp-server
**Date**: 2025-12-27
**Status**: Complete

---

## Research Task 1: MCP SDK Selection

**Question**: Which Python MCP library should we use for implementing the MCP server?

**Options Evaluated**:

1. **`mcp` (Official Python MCP SDK)** ⭐ SELECTED
   - Source: https://github.com/modelcontextprotocol/python-sdk
   - Version: 0.9.0+
   - Pros: Official library, active maintenance, complete protocol implementation, good documentation
   - Cons: Relatively new project

2. **`anthropic-mcp`**
   - Pros: Anthropic-backed
   - Cons: Less documented, unclear if it's the official recommendation

3. **Custom Implementation**
   - Pros: Full control
   - Cons: Protocol complexity, maintenance burden, security risks

**Decision**: Use official `mcp` Python SDK (version 0.9.0+)

**Rationale**:
- Official support ensures protocol compatibility
- Active development and community
- Handles protocol details (request/response serialization, error handling)
- Reduces implementation complexity

**Installation**:
```bash
pip install mcp>=0.9.0
```

---

## Research Task 2: OpenAI Integration Approach

**Question**: Should we use OpenAI Agents SDK or standard OpenAI SDK with function calling?

**Options Evaluated**:

1. **Standard OpenAI SDK with Function Calling** ⭐ SELECTED
   - Library: `openai` (v1.0+)
   - Pattern: Chat completions with `tools` parameter
   - Pros: Simple, well-documented, no additional SDK, proven pattern
   - Cons: Manual tool registration

2. **OpenAI Agents SDK**
   - Status: DEPRECATED (as of late 2024)
   - Cons: No longer recommended by OpenAI

3. **LangChain with OpenAI**
   - Pros: Rich ecosystem, agent orchestration
   - Cons: Additional dependency, over-engineering for our use case

**Decision**: Use standard OpenAI SDK with function calling

**Rationale**:
- OpenAI Agents SDK is deprecated
- Function calling is simpler and more maintainable
- Direct control over tool invocation flow
- No additional abstraction layers

**Implementation Pattern**:
```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

tools = [
    {
        "type": "function",
        "function": {
            "name": "add_task",
            "description": "Create a new task",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["user_id", "title"]
            }
        }
    }
]

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[...],
    tools=tools,
    tool_choice="auto"
)
```

---

## Research Task 3: JWT Verification in MCP Tools

**Question**: How should we extract and verify JWT tokens in MCP tool context?

**Options Evaluated**:

1. **FastAPI Dependency Injection** ⭐ SELECTED
   - Pattern: `Depends(get_current_user)`
   - Pros: Reuses existing auth middleware, type-safe, testable
   - Cons: Requires tools to be FastAPI routes (acceptable)

2. **MCP Middleware**
   - Pattern: Custom MCP server middleware
   - Pros: Centralized authentication
   - Cons: MCP SDK middleware support unclear

3. **Custom Decorators**
   - Pattern: `@require_auth` decorator
   - Pros: Flexible
   - Cons: Duplicates existing FastAPI auth logic

**Decision**: Use FastAPI dependency injection with existing auth middleware

**Rationale**:
- Reuses proven authentication code
- Consistent with existing API endpoints
- Type-safe with Pydantic models
- Easy to test and maintain

**Implementation Pattern**:
```python
from fastapi import Depends, HTTPException
from app.auth import get_current_user  # Existing middleware

async def add_task_tool(
    user_id: str,
    title: str,
    description: str = None,
    current_user: User = Depends(get_current_user)
):
    # Verify user_id matches authenticated user
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="user_id mismatch")

    # Tool logic...
```

---

## Research Task 4: Rate Limiting Strategy

**Question**: Which library should we use for per-user rate limiting?

**Options Evaluated**:

1. **`slowapi`** ⭐ SELECTED
   - Integration: FastAPI native
   - Storage: In-memory (default) or Redis
   - Pros: Simple, FastAPI-specific, good documentation, works with Depends()
   - Cons: In-memory limits lost on restart (acceptable for MVP)

2. **`fastapi-limiter`**
   - Integration: FastAPI + Redis required
   - Pros: Persistent across restarts
   - Cons: Requires Redis deployment

3. **Custom Redis-based Limiter**
   - Pros: Full control
   - Cons: Implementation complexity, maintenance

**Decision**: Use `slowapi` with in-memory storage for MVP, migrate to Redis if needed

**Rationale**:
- Simpler deployment (no Redis dependency for MVP)
- FastAPI-native integration
- Per-user limiting via custom key function
- Can upgrade to Redis backend later without code changes

**Installation**:
```bash
pip install slowapi
```

**Implementation Pattern**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

# Custom key function to limit by user_id from JWT
def get_user_id_from_jwt():
    # Extract from Depends(get_current_user)
    return current_user.id

limiter = Limiter(key_func=get_user_id_from_jwt)

@app.post("/mcp/tools/add_task")
@limiter.limit("100/hour")  # FR-015: 100 creates/hour
async def add_task_endpoint(...):
    ...
```

---

## Research Task 5: Error Response Standards

**Question**: What error response format should MCP tools use to be compatible with OpenAI and HTTP standards?

**Options Evaluated**:

1. **Standardized JSON Error Format** ⭐ SELECTED
   - Format: `{"error": {"code": string, "message": string, "tool": string}, "timestamp": ISO8601}`
   - HTTP Status: 400 (ValidationError), 403 (AuthorizationError), 404 (NotFoundError), 500 (DatabaseError)
   - Pros: Clear, consistent, AI-friendly, HTTP-compliant
   - Cons: Requires custom exception handling

2. **FastAPI Default Errors**
   - Format: `{"detail": string}`
   - Pros: Built-in
   - Cons: Less structured, missing metadata for AI

3. **RFC 7807 Problem Details**
   - Format: JSON with `type`, `title`, `status`, `detail`
   - Pros: Standard
   - Cons: Over-engineered for our use case

**Decision**: Use custom standardized JSON error format with HTTP status codes

**Rationale**:
- Provides rich context for AI agent (code, message, tool name)
- HTTP status codes enable proper error handling in clients
- Timestamp helps with debugging and logging
- Consistent structure across all 5 tools

**Error Format Specification**:
```json
{
  "error": {
    "code": "ValidationError" | "AuthorizationError" | "NotFoundError" | "DatabaseError",
    "message": "Human-readable error description",
    "tool": "add_task",
    "field": "title" (optional, for ValidationError)
  },
  "timestamp": "2025-12-27T15:00:00Z"
}
```

**HTTP Status Code Mapping**:
- `ValidationError` → 400 Bad Request
- `AuthorizationError` → 403 Forbidden
- `NotFoundError` → 404 Not Found
- `DatabaseError` → 500 Internal Server Error

**Implementation Pattern**:
```python
from datetime import datetime
from fastapi import HTTPException

class MCPError:
    @staticmethod
    def validation_error(message: str, tool: str, field: str = None):
        return {
            "error": {
                "code": "ValidationError",
                "message": message,
                "tool": tool,
                "field": field
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    @staticmethod
    def authorization_error(message: str, tool: str):
        return {
            "error": {
                "code": "AuthorizationError",
                "message": message,
                "tool": tool
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    # ... similar for NotFoundError, DatabaseError
```

---

## Technology Stack Summary

### Core Dependencies
```
# requirements.txt additions
mcp>=0.9.0
openai>=1.0.0
slowapi>=0.1.9
```

### Architecture Decisions
1. **MCP SDK**: Official `mcp` Python library
2. **AI Integration**: Standard OpenAI SDK with function calling
3. **Authentication**: FastAPI dependency injection (reuse existing middleware)
4. **Rate Limiting**: slowapi with in-memory storage (MVP), Redis later
5. **Error Format**: Custom JSON with HTTP status codes

### No NEEDS CLARIFICATION Remaining

All research tasks resolved. Ready to proceed to Phase 1 (Design).

---

**Research Complete** - All technology choices validated and documented
