# Implementation Plan: Stateless Chat Endpoint with OpenAI Agents SDK

**Branch**: `003-stateless-chat-endpoint` | **Date**: 2025-12-27 | **Spec**: [spec.md](./spec.md)

## Summary

Implement a stateless REST endpoint (`POST /api/{user_id}/chat`) that provides AI-powered conversational task management using OpenAI Agents SDK and MCP tool integration. The endpoint maintains conversation context by fetching complete history from PostgreSQL on each request, enabling horizontal scalability and instant recovery from server restarts. AI assistant can invoke 5 existing MCP tools (add_task, list_tasks, complete_task, delete_task, update_task) to perform task operations through natural language commands.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: openai>=1.0.0, FastAPI 0.115+, SQLModel 0.0.22, httpx 0.27+
**Storage**: Neon PostgreSQL (existing conversations and messages tables from Feature 001)
**Testing**: pytest 8.3+, pytest-asyncio 0.24+, httpx TestClient
**Target Platform**: Linux server (Render/Railway deployment)
**Project Type**: web (backend API endpoint extension)
**Performance Goals**: <3s p95 response time (including DB fetch + OpenAI call + DB write), <100ms conversation history retrieval
**Constraints**: Stateless design (zero in-memory session state), 30-second OpenAI timeout, 5,000 character message limit, 50-message history window
**Scale/Scope**: 100 concurrent chat requests, 10-30 average messages per conversation, 99.9% MCP tool success rate

## Constitution Check

✅ **Spec-Driven Development**: Complete specification in `spec.md` (5 user stories, 20 FRs, 10 success criteria)
✅ **Architecture & Technology Stack**: Extends existing FastAPI + SQLModel backend with OpenAI Agents SDK (Phase III requirement)
✅ **RESTful API Design**: Single POST endpoint follows REST conventions, uses existing JWT auth middleware
✅ **Data Management**: Leverages existing Conversation and Message models (Feature 001), enforces user_id isolation
✅ **Testing**: Defines comprehensive test scenarios with mocked OpenAI responses, pytest fixtures for database
✅ **Code Quality**: Type hints required (Python), async/await for all I/O, error handling for all failure modes
✅ **Security**: JWT verification on every request, conversation ownership validation, input sanitization
✅ **Deployment**: No infrastructure changes required, deploys alongside existing backend

❌ **NO VIOLATIONS**

## Project Structure

### Documentation (this feature)

```
specs/003-stateless-chat-endpoint/
├── plan.md              # This file
├── research.md          # Phase 0 output (OpenAI SDK patterns, error handling)
├── data-model.md        # Phase 1 output (ChatRequest/Response schemas)
├── quickstart.md        # Phase 1 output (API usage examples)
├── contracts/           # Phase 1 output (OpenAPI schema for chat endpoint)
│   └── chat-endpoint.json
└── spec.md              # Completed specification
```

### Source Code (repository root)

```
backend/
├── app/
│   ├── routes/
│   │   └── chat.py              # NEW: Chat endpoint implementation
│   ├── models/
│   │   ├── conversation.py      # EXISTS: From Feature 001
│   │   └── message.py           # EXISTS: From Feature 001
│   ├── mcp_server/
│   │   ├── server.py            # EXISTS: From Feature 002
│   │   └── tools/               # EXISTS: All 5 tools from Feature 002
│   ├── middleware/
│   │   └── auth.py              # EXISTS: JWT verification
│   └── main.py                  # MODIFY: Include chat router
└── tests/
    └── test_chat.py             # NEW: Chat endpoint tests
```

**Structure Decision**: Web application (Option 2) - extends existing backend/app/ structure with new chat.py route module. No frontend changes required for this feature (frontend integration is separate task). Reuses all existing infrastructure (models, auth, MCP tools).

---

## Phase III: AI & MCP Server Design

### MCP Server Architecture

**MCP Tools to Implement**: ✅ **ALL EXIST** (Feature 002)
- ✅ `add_task` - Create new task (user_id, title, description) → task object
- ✅ `list_tasks` - Get user tasks (user_id, filter, sort_by, sort_order) → task array
- ✅ `complete_task` - Toggle completion (user_id, task_id) → updated task
- ✅ `delete_task` - Remove task (user_id, task_id) → deletion confirmation
- ✅ `update_task` - Modify task (user_id, task_id, title, description) → updated task

**Stateless Design Pattern**:
```python
# 8-Step Stateless Chat Flow (backend/app/routes/chat.py)
@router.post("/api/{user_id}/chat")
async def chat_endpoint(
    user_id: str,
    chat_request: ChatRequest,
    credentials: HTTPAuthCredentials = Depends(security),
    session: Session = Depends(get_session)
):
    # Step 1: Verify JWT and authorization
    token_user_id = verify_jwt_token(credentials.credentials)
    if user_id != token_user_id:
        raise HTTPException(status_code=403)

    # Step 2: Get or create conversation
    conversation_id = chat_request.conversation_id
    if conversation_id:
        conversation = session.get(Conversation, conversation_id)
        if not conversation or conversation.user_id != user_id:
            raise HTTPException(status_code=404)
    else:
        conversation = Conversation(user_id=user_id, ...)
        session.add(conversation)
        session.commit()
        session.refresh(conversation)

    # Step 3: Fetch conversation history from database (stateless!)
    statement = select(Message).where(
        Message.conversation_id == conversation.id
    ).order_by(Message.created_at).limit(50)  # Last 50 messages
    history = session.exec(statement).all()

    # Step 4: Build message array for OpenAI
    messages = [
        {"role": "system", "content": "You are a task management assistant..."}
    ]
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": chat_request.message})

    # Step 5: Store user message in database
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=chat_request.message,
        created_at=datetime.utcnow()
    )
    session.add(user_message)
    session.commit()

    # Step 6: Call OpenAI with MCP tool schemas
    tool_schemas = get_all_tool_schemas()  # From MCP server
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tool_schemas,
        tool_choice="auto"
    )

    # Step 7: Handle tool calls if present
    if response.choices[0].message.tool_calls:
        for tool_call in response.choices[0].message.tool_calls:
            # Execute MCP tool with user's JWT token
            handler = get_tool_handler(tool_call.function.name)
            result = handler(
                request=parse_tool_args(tool_call),
                token_user_id=token_user_id,
                session=session
            )
            # Add tool result to messages
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result.model_dump_json()
            })

        # Call OpenAI again with tool results
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )

    # Step 8: Store assistant response and return
    assistant_content = response.choices[0].message.content
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=assistant_content,
        created_at=datetime.utcnow()
    )
    session.add(assistant_message)
    conversation.last_message_at = datetime.utcnow()
    session.commit()

    return ChatResponse(
        conversation_id=conversation.id,
        assistant_message=assistant_content,
        tool_calls=[tc.function.name for tc in response.choices[0].message.tool_calls or []],
        created_at=assistant_message.created_at
    )
    # Server holds NO state - next request starts fresh!
```

**Conversation Database Schema**: ✅ **EXISTS** (Feature 001)
```sql
-- conversations table (ALREADY DEPLOYED)
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    started_at TIMESTAMP DEFAULT NOW(),
    last_message_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);

-- messages table (ALREADY DEPLOYED)
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
```

**OpenAI Agent Configuration**:
- **OpenAI SDK**: `openai>=1.0.0` (official Python SDK)
- **Model**: `gpt-4o` (production) / `gpt-4o-mini` (development)
- **System Prompt**: "You are a helpful AI assistant for task management. You can create, list, update, complete, and delete tasks for users. Be concise and friendly."
- **Tool Invocation Pattern**: Sequential (tools invoked during conversation, second API call with results)
- **Timeout**: 30 seconds per OpenAI API call
- **Max Tokens**: 4096 (default for gpt-4o)
- **Temperature**: 0.7 (balanced creativity)

**Natural Language Understanding Requirements**:
- ✅ "I need to buy groceries" → invokes `add_task` with title "Buy groceries"
- ✅ "What tasks do I have?" → invokes `list_tasks` with filter="all"
- ✅ "Mark task 3 as done" → invokes `complete_task` with task_id=3
- ✅ "Delete the grocery task" → invokes `list_tasks` first, then `delete_task` for matching task
- ✅ "Change task 5 to call mom tomorrow" → invokes `update_task` with new title
- ✅ "Show me pending tasks only" → invokes `list_tasks` with filter="pending"

---

## Implementation Phases

### Phase 0: Research

**Research Topics** (Output: `research.md`):

1. **OpenAI SDK Best Practices**
   - Task: Research OpenAI Python SDK function calling patterns
   - Investigate: Error handling for rate limits, timeouts, API failures
   - Document: Retry strategies, exponential backoff, circuit breaker patterns

2. **Stateless Architecture Patterns**
   - Task: Research stateless HTTP API design for conversational interfaces
   - Investigate: Session management alternatives, database query optimization for history retrieval
   - Document: Tradeoffs between stateless (scalable) vs stateful (faster) designs

3. **MCP Tool Integration**
   - Task: Research how to expose existing MCP tools to OpenAI function calling
   - Investigate: Schema translation (MCP Pydantic models → OpenAI function schemas)
   - Document: Example mappings for all 5 tools

4. **Error Recovery Strategies**
   - Task: Research graceful degradation when OpenAI API unavailable
   - Investigate: Fallback responses, error message clarity, message persistence on failure
   - Document: User-facing error messages for each failure mode

**Deliverable**: `research.md` with decisions on SDK usage, error handling, and integration patterns

### Phase 1: Design & Contracts

**Prerequisites**: research.md complete

1. **Data Models** (Output: `data-model.md`):

   **ChatRequest Model**:
   ```python
   class ChatRequest(BaseModel):
       message: str = Field(min_length=1, max_length=5000, description="User message")
       conversation_id: Optional[int] = Field(None, description="Existing conversation ID")
   ```

   **ChatResponse Model**:
   ```python
   class ChatResponse(BaseModel):
       conversation_id: int
       assistant_message: str
       tool_calls: List[str] = []
       created_at: datetime
   ```

   **OpenAI Tool Schema Generator**:
   ```python
   def get_all_tool_schemas() -> List[Dict]:
       """Generate OpenAI function schemas from MCP tools"""
       return [
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
           },
           # ... 4 more tool schemas
       ]
   ```

2. **API Contracts** (Output: `contracts/chat-endpoint.json`):

   **Endpoint**: `POST /api/{user_id}/chat`

   **Request**:
   ```json
   {
       "message": "I need to buy groceries",
       "conversation_id": 123  // optional
   }
   ```

   **Response** (200 OK):
   ```json
   {
       "conversation_id": 123,
       "assistant_message": "I've added 'Buy groceries' to your task list.",
       "tool_calls": ["add_task"],
       "created_at": "2025-12-27T14:30:00Z"
   }
   ```

   **Errors**:
   - `400 Bad Request` - Message too long or empty
   - `401 Unauthorized` - Invalid JWT token
   - `403 Forbidden` - user_id doesn't match token or conversation doesn't belong to user
   - `404 Not Found` - Conversation ID doesn't exist
   - `500 Internal Server Error` - OpenAI API failure
   - `503 Service Unavailable` - Database unavailable

3. **Quickstart Guide** (Output: `quickstart.md`):
   ```markdown
   # Stateless Chat Endpoint Quickstart

   ## Usage

   ### Start New Conversation
   ```bash
   curl -X POST http://localhost:8000/api/user123/chat \
     -H "Authorization: Bearer $JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"message": "I need to buy groceries"}'
   ```

   ### Continue Existing Conversation
   ```bash
   curl -X POST http://localhost:8000/api/user123/chat \
     -H "Authorization: Bearer $JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"message": "What tasks do I have?", "conversation_id": 123}'
   ```

   ## Natural Language Commands

   - **Create task**: "Add a task to call mom"
   - **List tasks**: "Show me my pending tasks"
   - **Complete task**: "Mark task 5 as done"
   - **Update task**: "Change task 3 to buy milk and eggs"
   - **Delete task**: "Remove the grocery task"
   ```

4. **Update Agent Context**:
   ```bash
   .specify/scripts/bash/update-agent-context.sh claude
   ```

   Adds to `CLAUDE.md`:
   - OpenAI Python SDK usage patterns
   - Stateless chat endpoint pattern
   - MCP tool schema generation
   - Error handling for AI services

**Deliverables**: data-model.md, contracts/chat-endpoint.json, quickstart.md, updated CLAUDE.md

### Phase 2: Task Generation

**Input**: plan.md (this file)
**Command**: `/sp.tasks` (separate command, NOT part of /sp.plan)
**Output**: `tasks.md` with complete implementation checklist

**Example Task Breakdown**:
- T001: Create ChatRequest and ChatResponse Pydantic models
- T002: Implement conversation ownership validation helper
- T003: Create OpenAI tool schema generator from MCP tools
- T004: Implement 8-step stateless flow in chat_endpoint
- T005: Add error handling for OpenAI API failures
- T006: Implement conversation history windowing (50-message limit)
- T007: Add chat router to main.py
- T008: Write pytest tests with mocked OpenAI responses
- T009: Test multi-turn conversations with tool calls
- T010: Test authorization and user isolation

**Ready for**: `/sp.tasks` command to generate complete task breakdown

---

## Stop Here: Plan Complete

**Branch**: `003-stateless-chat-endpoint`
**Plan Path**: `specs/003-stateless-chat-endpoint/plan.md`
**Generated Artifacts**:
- ✅ `plan.md` - This implementation plan
- ⏳ `research.md` - Pending Phase 0 execution
- ⏳ `data-model.md` - Pending Phase 1 execution
- ⏳ `contracts/` - Pending Phase 1 execution
- ⏳ `quickstart.md` - Pending Phase 1 execution

**Next Steps**:
1. Execute Phase 0 research (if needed)
2. Execute Phase 1 design (if needed)
3. Run `/sp.tasks` to generate task breakdown
4. Run `/sp.implement` to execute implementation

---

## Notes

**Key Design Decisions**:
- **Stateless over Stateful**: Chose database-backed state for horizontal scalability
- **Sequential Tool Calls**: OpenAI invokes tools one at a time, reducing complexity
- **50-Message Window**: Balances context quality vs OpenAI token limits
- **Conversation Ownership**: Strict validation prevents cross-user data leaks
- **Error Persistence**: User messages saved even if OpenAI fails (prevents data loss)

**Risks & Mitigations**:
| Risk | Mitigation |
|------|------------|
| OpenAI API slow (>5s) | Set 30s timeout, return clear error if exceeded |
| Database slow (>500ms) | Index conversation_id and created_at columns |
| Token limit exceeded | Limit history to 50 messages, truncate if needed |
| Concurrent message corruption | Use database transaction isolation |
| Cross-user data leak | Verify conversation.user_id == token_user_id on every request |

**Performance Optimizations**:
- Use database connection pooling (already configured)
- Fetch conversation history with single SELECT query
- Limit OpenAI response tokens (max_tokens parameter)
- Log response times for monitoring

**Testing Strategy**:
- Mock OpenAI API responses (avoid real API calls in tests)
- Test all tool invocation scenarios
- Test conversation creation and continuation
- Test error handling for all failure modes
- Test authorization and user isolation
