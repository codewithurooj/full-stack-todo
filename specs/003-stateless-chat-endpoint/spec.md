# Feature Specification: Stateless Chat Endpoint with OpenAI Agents SDK

**Feature Branch**: `003-stateless-chat-endpoint`
**Created**: 2025-12-27
**Status**: Draft
**Input**: User description: "Chat endpoint with stateless design using OpenAI Agents SDK and MCP tools"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Contextual AI Conversations (Priority: P1)

As a user, I want to send messages to an AI assistant and receive intelligent responses that understand the full context of our conversation history, so that I can have natural, multi-turn conversations about my tasks without the system forgetting what we discussed.

**Why this priority**: This is the core value proposition of the AI chat feature. Without conversation context, the AI would respond to each message in isolation, making it impossible to have meaningful multi-turn interactions. This enables the entire AI assistant experience.

**Independent Test**: Can be fully tested by sending a message like "I need to buy groceries", then a follow-up "When should I do that?", and verifying the AI's response references the groceries task from the first message. Delivers complete conversational AI capability.

**Acceptance Scenarios**:

1. **Given** I have an existing conversation with 5 messages, **When** I send a new message "What was the first thing we talked about?", **Then** the system retrieves all 5 previous messages from the database, includes them in the AI context, and the AI can accurately reference our first topic
2. **Given** I start a brand new conversation, **When** I send my first message "Help me organize my day", **Then** the system creates a new conversation record, stores my message, calls the AI with system instructions and my message, stores the AI's response, and returns it to me
3. **Given** I'm in the middle of a conversation about groceries, **When** I say "Add that to my task list", **Then** the AI understands "that" refers to buying groceries from our conversation context and creates the appropriate task using the MCP tool
4. **Given** I send a message to a conversation, **When** the AI generates a response, **Then** both my message (role: user) and the AI's response (role: assistant) are permanently stored in the messages table with correct conversation_id and timestamps

---

### User Story 2 - Tool-Augmented AI Responses (Priority: P1)

As a user, I want the AI assistant to automatically perform actions on my behalf (like creating tasks, listing tasks, completing tasks) when I ask it to, so that I can manage my todo list through natural conversation instead of manual UI interactions.

**Why this priority**: Core differentiator of an AI-powered todo app. Without MCP tool integration, the AI would only provide conversational responses with no ability to take action. Tool integration is essential for the AI to be genuinely useful.

**Independent Test**: Can be fully tested by saying "Create a task to call mom tomorrow" and verifying: (1) AI invokes add_task tool, (2) task appears in database, (3) AI confirms task creation in its response. Demonstrates end-to-end AI action capability.

**Acceptance Scenarios**:

1. **Given** I'm chatting with the AI, **When** I say "I need to buy groceries and walk the dog", **Then** the AI invokes the add_task tool twice (once for each task), both tasks are created in the database with my user_id, and the AI confirms both tasks were created
2. **Given** I have 3 pending tasks and 2 completed tasks, **When** I ask "What tasks do I have?", **Then** the AI invokes the list_tasks tool with my user_id, retrieves all 5 tasks, and presents them in natural language grouped by status
3. **Given** I have a task "Buy groceries" and I say "I finished the grocery shopping", **When** the AI processes my message, **Then** it invokes the complete_task tool with the correct task_id, toggles the completion status in the database, and confirms the task is now complete
4. **Given** the AI needs to invoke a tool, **When** it makes the tool call, **Then** the system passes my JWT token with the request, the tool verifies user_id matches the token, and the tool executes successfully with proper authorization

---

### User Story 3 - Concurrent User Isolation (Priority: P1)

As a user, I want my conversations and AI interactions to be completely private and isolated from other users, so that my chat history and task actions never leak to other users or get mixed up with their data.

**Why this priority**: Critical security and privacy requirement. Multi-user systems must guarantee complete data isolation. Without this, the system would be unusable in production.

**Independent Test**: Can be tested by creating conversations for User A and User B, sending messages to both, and verifying User A's AI responses only reference User A's conversation history and tasks (never User B's). Demonstrates security isolation.

**Acceptance Scenarios**:

1. **Given** User A and User B both have active conversations, **When** User A sends a message, **Then** the system fetches only User A's conversation history from the database (filtered by user_id), and the AI context includes zero messages from User B's conversations
2. **Given** User A asks the AI to list tasks, **When** the AI invokes list_tasks tool, **Then** the tool receives User A's user_id from the JWT token, queries the database filtering by User A's user_id, and returns only User A's tasks (never User B's)
3. **Given** User A and User B are both chatting simultaneously, **When** both send messages at the same time, **Then** the server processes both requests independently with no shared state, each fetching their own conversation history, and responses never get mixed up
4. **Given** User A tries to reference User B's conversation_id in a request, **When** the system validates the request, **Then** it rejects the request with a 403 Forbidden error because the conversation doesn't belong to User A

---

### User Story 4 - Stateless Scalability (Priority: P2)

As a system operator, I want the chat endpoint to be completely stateless with no server-side session memory, so that the application can scale horizontally without session affinity requirements and can recover instantly from server restarts.

**Why this priority**: Important for production scalability and reliability, but not essential for initial MVP. Users can still have conversations even if the system doesn't scale horizontally yet.

**Independent Test**: Can be tested by sending a message, restarting the server, sending another message in the same conversation, and verifying the AI still has full context. Demonstrates true statelessness.

**Acceptance Scenarios**:

1. **Given** a user is mid-conversation, **When** the backend server restarts between messages, **Then** the next message still receives full conversation context because all history is fetched from the database (no in-memory state lost)
2. **Given** a user sends multiple messages rapidly, **When** each request is handled by different server instances (load balanced), **Then** all responses maintain correct conversation context because each request independently fetches history from the shared database
3. **Given** the AI is processing a message, **When** examining server memory, **Then** there is zero conversation state stored in memory beyond the current request scope (all state lives in database)

---

### User Story 5 - Error Recovery and Graceful Degradation (Priority: P3)

As a user, I want clear, helpful error messages when something goes wrong (like if the AI service is unavailable or my request is invalid), so that I understand what happened and can take appropriate action.

**Why this priority**: Nice-to-have for user experience, but not critical for core functionality. Users can retry requests even without perfect error messages.

**Independent Test**: Can be tested by simulating an OpenAI API failure and verifying the endpoint returns a clear error message like "AI service temporarily unavailable, please try again" instead of a generic 500 error.

**Acceptance Scenarios**:

1. **Given** the OpenAI API is temporarily unavailable, **When** I send a chat message, **Then** the system catches the API error, stores my message in the database (so it's not lost), and returns a clear error message explaining the AI service is unavailable
2. **Given** I send a message with an invalid conversation_id, **When** the system validates my request, **Then** it returns a 404 error with message "Conversation not found" and doesn't crash
3. **Given** the database is temporarily unavailable, **When** I send a chat message, **Then** the system returns a 503 Service Unavailable error with message "Database temporarily unavailable" instead of exposing internal error details

---

### Edge Cases

- What happens when a user sends an extremely long message (10,000+ characters)? (Validate max message length, return 400 error if exceeded)
- How does the system handle a conversation with 1,000+ messages? (Implement message history limit, e.g., only fetch last 50 messages for AI context to avoid token limits)
- What happens if the AI tries to invoke a non-existent MCP tool? (Return error to AI, AI explains tool isn't available)
- How does the system behave if OpenAI takes 30+ seconds to respond? (Set timeout, return error after threshold)
- What happens when concurrent requests try to add messages to the same conversation simultaneously? (Database handles concurrent writes with proper transaction isolation)
- How does the system handle malicious prompts trying to extract other users' data? (AI has no access to other users' data; MCP tools enforce user_id validation)
- What happens if a user sends a message to a deleted conversation? (Return 404 Not Found)
- How does the AI handle ambiguous tool calls (e.g., "complete the task" when there are 5 pending tasks)? (AI should ask for clarification)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a POST endpoint `/api/{user_id}/chat` that accepts a message and conversation_id, and returns an AI-generated response
- **FR-002**: System MUST fetch complete conversation history from the database before processing each message (stateless design - no in-memory caching)
- **FR-003**: System MUST store the user's message in the messages table with role='user' BEFORE calling the OpenAI API
- **FR-004**: System MUST store the AI's response in the messages table with role='assistant' AFTER receiving response from OpenAI
- **FR-005**: System MUST update the conversation's last_message_at timestamp after storing the assistant's response
- **FR-006**: System MUST build message array in order: system prompt, conversation history (chronological), new user message
- **FR-007**: System MUST integrate OpenAI Agents SDK and pass all available MCP tool schemas to the AI for function calling
- **FR-008**: System MUST invoke MCP tools when requested by OpenAI, passing the user's JWT token for authentication
- **FR-009**: System MUST handle OpenAI tool calls by: (1) executing tool, (2) adding tool result to message history, (3) calling OpenAI again with results
- **FR-010**: System MUST enforce user authorization by verifying conversation belongs to authenticated user (conversation.user_id matches JWT token user_id)
- **FR-011**: System MUST create a new conversation if conversation_id is not provided (first message scenario)
- **FR-012**: System MUST validate conversation_id exists and belongs to user if provided
- **FR-013**: System MUST limit message content to maximum 5,000 characters (prevent abuse and token overflow)
- **FR-014**: System MUST implement conversation history windowing (fetch only last 50 messages to stay within OpenAI token limits)
- **FR-015**: System MUST return complete response including: assistant's message text, conversation_id, message_id, and timestamp
- **FR-016**: System MUST handle OpenAI API errors gracefully and return user-friendly error messages
- **FR-017**: System MUST set OpenAI API timeout to 30 seconds to prevent hanging requests
- **FR-018**: System MUST use transaction rollback if storing assistant message fails after receiving OpenAI response
- **FR-019**: System MUST sanitize message content to prevent injection attacks (already handled by OpenAI SDK, but validate inputs)
- **FR-020**: System MUST log all chat requests with user_id, conversation_id, message_id, AI model used, and response time for debugging

### Key Entities

- **Chat Request**: User input containing message text, optional conversation_id. If conversation_id is null, indicates starting a new conversation.

- **Chat Response**: AI output containing assistant's message text, conversation_id (created or provided), message_id of assistant's response, and timestamp.

- **Message Array**: Ordered sequence of messages sent to OpenAI API. Format: [system_message, ...history_messages, new_user_message]. System message defines AI behavior, history provides context, new message is what AI responds to.

- **Tool Call**: OpenAI's request for the AI to invoke a specific MCP tool with parameters. Includes tool name, tool call ID, and JSON arguments. System must execute tool and return result to OpenAI.

- **Tool Result**: Response from executed MCP tool, formatted as JSON. Added to message array with role='tool' and tool_call_id to give AI context about action outcome.

- **Conversation Context**: Complete state for a conversation rebuilt on each request from database. Includes: conversation metadata (id, user_id, timestamps), full message history (up to limit), user authentication info.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Chat endpoint responds to user messages within 3 seconds at 95th percentile (including database fetch, OpenAI API call, and database write)
- **SC-002**: System successfully maintains conversation context across 20+ message turns with 100% accuracy (AI can reference earlier messages)
- **SC-003**: MCP tool invocations through AI have 99.9% success rate when valid parameters provided (tools execute correctly)
- **SC-004**: User isolation is enforced with 100% effectiveness (zero cross-user data leaks in conversation history or tool calls)
- **SC-005**: System handles 100 concurrent chat requests without degradation or data corruption (stateless design enables parallelism)
- **SC-006**: Conversation history retrieval completes in under 100ms for conversations with 50 messages (database query performance)
- **SC-007**: System gracefully handles OpenAI API failures with 100% error recovery (stores user message even if AI response fails)
- **SC-008**: New conversations are created successfully on first message 100% of the time with correct user_id association
- **SC-009**: Message storage has 100% durability (messages never lost after successful API response to client)
- **SC-010**: System enforces authorization checks on 100% of requests (all endpoints verify user owns conversation)

### Constraints & Assumptions

**Constraints**:
- Must be compatible with existing SQLModel Conversation and Message models
- Must integrate with existing MCP server tool infrastructure
- Must use existing JWT authentication middleware
- Must work with OpenAI API (GPT-4o model)
- Must be stateless (no server-side session storage)
- Must not modify existing task management functionality
- Response time limited to 30 seconds (OpenAI timeout)
- Message content limited to 5,000 characters
- Conversation history limited to last 50 messages per AI request

**Assumptions**:
- OpenAI API key is configured and valid
- Database schema (conversations, messages tables) is already deployed
- MCP server with 5 tools is already implemented and functional
- JWT authentication is working and provides reliable user_id
- Users understand AI responses may take 2-5 seconds
- Average conversation will have 10-30 messages
- OpenAI API has 99%+ uptime
- Database can handle 100+ concurrent reads/writes
- Network latency to OpenAI API is under 500ms
- Users send messages sequentially (not 10 messages simultaneously)

### Dependencies

- **Database Schema**: Requires conversations and messages tables (Feature 001)
- **MCP Server**: Requires 5 tools implemented and deployed (Feature 002)
- **OpenAI API**: Requires valid API key and GPT-4o access
- **Authentication**: Requires JWT token generation/validation
- **SQLModel**: Requires Conversation and Message models
- **OpenAI Agents SDK**: Python library for agent function calling
- **Neon PostgreSQL**: Database for storing conversations and messages

### Out of Scope

The following are explicitly NOT included:

- Real-time messaging with WebSockets (REST API only)
- Message editing or deletion by users
- Message reactions or likes
- Conversation sharing between users
- Conversation export (PDF, text file)
- Voice input/output for chat
- Image or file attachments in messages
- Custom AI model selection (GPT-4o only)
- AI personality customization
- Message search or full-text indexing
- Conversation folders or organization
- Message read receipts
- Typing indicators
- Conversation archival UI
- Multi-language support (English only)
- Profanity filtering
- AI response regeneration
- Conversation branching or alternate responses
- Analytics dashboard for chat metrics

---

## Technical Architecture *(informative)*

### Stateless Request Flow

The chat endpoint follows this 9-step stateless flow on EVERY request:

```
1. Receive Request
   ↓
   Input: { user_id, conversation_id (optional), message, JWT token }

2. Authenticate & Authorize
   ↓
   - Verify JWT token
   - Extract user_id from token
   - If conversation_id provided: verify conversation belongs to user
   - If conversation_id null: prepare to create new conversation

3. Fetch Conversation History
   ↓
   - Query database: SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC LIMIT 50
   - Build message array: system prompt + history
   - NO state stored in server memory

4. Store User Message
   ↓
   - If conversation_id null: CREATE conversation first
   - INSERT INTO messages (conversation_id, role='user', content=message, ...)
   - UPDATE conversations SET last_message_at = NOW()
   - COMMIT transaction

5. Call OpenAI Agent
   ↓
   - Append user message to message array
   - Call openai.chat.completions.create(model="gpt-4o", messages=array, tools=mcp_tools)
   - Timeout: 30 seconds

6. Handle Tool Calls (if any)
   ↓
   - If AI requests tool calls:
     - For each tool: invoke MCP tool handler with JWT token
     - Collect tool results
     - Append tool results to message array
     - Call OpenAI again with tool results
   - If no tool calls: skip to step 7

7. Store Assistant Response
   ↓
   - Extract assistant message from OpenAI response
   - INSERT INTO messages (conversation_id, role='assistant', content=response, ...)
   - UPDATE conversations SET last_message_at = NOW()
   - COMMIT transaction

8. Return Response
   ↓
   - Output: { assistant_message, conversation_id, message_id, created_at }

9. Discard State
   ↓
   - Request completes
   - All conversation context discarded from memory
   - Next request rebuilds state from database
```

### Data Flow Diagram

```
┌─────────────┐
│   Client    │
│  (Frontend) │
└──────┬──────┘
       │
       │ POST /api/{user_id}/chat
       │ { message, conversation_id? }
       │ Authorization: Bearer <JWT>
       ▼
┌─────────────────────┐
│  Chat Endpoint      │
│  /routes/chat.py    │
└──────┬──────────────┘
       │
       ├─────────────────────────────────┐
       │                                 │
       ▼                                 ▼
┌──────────────┐              ┌──────────────────┐
│  Database    │              │  OpenAI API      │
│              │              │  (GPT-4o)        │
│  1. Fetch    │              │                  │
│  conversation│              │  System Prompt + │
│  history     │              │  History +       │
│              │              │  User Message    │
│  2. Store    │              │                  │
│  user message│              │  Tools: 5 MCP    │
│              │◄─────────┐   │  function schemas│
│  3. Store    │          │   │                  │
│  assistant   │          │   └────────┬─────────┘
│  message     │          │            │
│              │          │            │ Tool Calls?
└──────────────┘          │            ▼
                          │   ┌─────────────────┐
                          │   │  MCP Server     │
                          │   │  /mcp_server/   │
                          │   │                 │
                          └───┤  Tool Handlers  │
                              │  - add_task     │
                              │  - list_tasks   │
                              │  - complete_task│
                              │  - update_task  │
                              │  - delete_task  │
                              └─────────────────┘
```

### API Contract

**Endpoint**: `POST /api/{user_id}/chat`

**Request Headers**:
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

**Request Body**:
```json
{
  "conversation_id": 123,  // Optional: null for new conversation
  "message": "I need to buy groceries and call mom tomorrow"
}
```

**Response (200 OK)**:
```json
{
  "conversation_id": 123,
  "message_id": 456,
  "assistant_message": "I've created two tasks for you: 'Buy groceries' and 'Call mom'. Both are now in your task list. Would you like me to set any details for these tasks?",
  "created_at": "2025-12-27T14:30:00Z",
  "tool_calls_executed": [
    {
      "tool": "add_task",
      "result": "Created task 'Buy groceries'"
    },
    {
      "tool": "add_task",
      "result": "Created task 'Call mom'"
    }
  ]
}
```

**Error Responses**:

```json
// 400 Bad Request - Invalid input
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Message exceeds maximum length of 5000 characters"
  }
}

// 401 Unauthorized - Invalid JWT
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or expired authentication token"
  }
}

// 403 Forbidden - Wrong user
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Conversation does not belong to authenticated user"
  }
}

// 404 Not Found - Invalid conversation
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Conversation not found"
  }
}

// 500 Internal Server Error - OpenAI API failure
{
  "error": {
    "code": "AI_SERVICE_ERROR",
    "message": "AI service temporarily unavailable, please try again"
  }
}

// 503 Service Unavailable - Database down
{
  "error": {
    "code": "DATABASE_ERROR",
    "message": "Database temporarily unavailable"
  }
}
```

### System Prompt Template

The system message defines AI behavior and available capabilities:

```
You are a helpful task management assistant. You help users organize their tasks and manage their todo list through natural conversation.

You have access to the following tools:
- add_task: Create a new task for the user
- list_tasks: Retrieve all tasks for the user
- complete_task: Mark a task as complete or incomplete
- update_task: Modify a task's title or description
- delete_task: Permanently remove a task

When users mention things they need to do, proactively offer to create tasks for them. Always confirm actions you take (like creating or completing tasks) in your response.

Be concise, friendly, and helpful. If you're not sure which task the user is referring to, ask for clarification.

Current date: {current_date}
```

### Message History Windowing

To stay within OpenAI token limits, implement sliding window:

```python
# Fetch last 50 messages only
messages_query = (
    select(Message)
    .where(Message.conversation_id == conversation_id)
    .order_by(Message.created_at.desc())
    .limit(50)
)
messages = session.exec(messages_query).all()
messages.reverse()  # Chronological order for AI context
```

### OpenAI Agent Integration Pattern

```python
from openai import OpenAI

client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Build message array
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    *[{"role": msg.role, "content": msg.content} for msg in history],
    {"role": "user", "content": new_message}
]

# First AI call with tools
response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=get_mcp_tool_schemas(),  # All 5 MCP tools
    tool_choice="auto",
    timeout=30
)

# Handle tool calls if present
message = response.choices[0].message
if message.tool_calls:
    messages.append(message)  # Add AI's tool call request

    for tool_call in message.tool_calls:
        # Execute MCP tool
        tool_result = execute_mcp_tool(
            tool_name=tool_call.function.name,
            args=json.loads(tool_call.function.arguments),
            user_token=jwt_token
        )

        # Add tool result to messages
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(tool_result)
        })

    # Second AI call with tool results
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        timeout=30
    )

assistant_message = response.choices[0].message.content
```

---

## Testing Strategy *(informative)*

### Unit Tests

1. **Conversation History Retrieval**
   - Fetch messages for conversation with 10 messages
   - Verify messages returned in chronological order
   - Verify only last 50 messages fetched when conversation has 100 messages
   - Verify empty array when conversation has no messages

2. **User Authorization**
   - Reject request when conversation doesn't belong to user (403)
   - Reject request when JWT token invalid (401)
   - Accept request when user owns conversation (200)

3. **New Conversation Creation**
   - Create conversation when conversation_id is null
   - Set user_id from JWT token
   - Set started_at and last_message_at to current time

4. **Message Storage**
   - Store user message with correct role, content, timestamps
   - Store assistant message after OpenAI response
   - Update conversation last_message_at after storing assistant message

5. **Error Handling**
   - Handle OpenAI API timeout gracefully
   - Handle database connection failure
   - Handle invalid message content (too long, empty)

### Integration Tests

1. **End-to-End Chat Flow**
   - Send message to new conversation
   - Verify conversation created in database
   - Verify user message stored
   - Verify OpenAI called with correct message array
   - Verify assistant response stored
   - Verify response returned to client

2. **Multi-Turn Conversation**
   - Send 5 messages to same conversation
   - Verify each response has context from previous messages
   - Verify conversation only has 1 record (not 5 conversations)
   - Verify messages table has 10 records (5 user + 5 assistant)

3. **Tool Integration**
   - Send "Create a task to buy milk"
   - Verify OpenAI invokes add_task tool
   - Verify task created in database
   - Verify AI response confirms task creation

4. **Concurrent Requests**
   - Send 10 requests simultaneously to different conversations
   - Verify all responses correct with no data mixing
   - Verify all messages stored correctly

5. **User Isolation**
   - Create conversations for User A and User B
   - Send message as User A referencing User B's data
   - Verify User A's AI never accesses User B's conversation or tasks

### Performance Tests

1. **Response Time**
   - Measure p50, p95, p99 response times under normal load
   - Target: p95 < 3 seconds

2. **Conversation History Query**
   - Measure query time for 50-message conversation
   - Target: < 100ms

3. **Concurrent Load**
   - Send 100 concurrent requests
   - Verify no degradation or errors
   - Verify database connection pool handles load

### Security Tests

1. **JWT Validation**
   - Attempt request with invalid JWT (reject)
   - Attempt request with expired JWT (reject)
   - Attempt request with valid JWT (accept)

2. **User Authorization**
   - User A tries to access User B's conversation (reject 403)
   - User A accesses their own conversation (accept 200)

3. **SQL Injection Prevention**
   - Send malicious content in message (sanitized)
   - Verify SQLModel parameterized queries prevent injection

4. **Prompt Injection**
   - Send message trying to override system prompt
   - Verify OpenAI's built-in protections prevent jailbreaking

---

## Implementation Notes *(informative)*

### File Structure

```
backend/app/
├── routes/
│   └── chat.py               # Chat endpoint (new)
├── services/
│   └── chat_service.py       # Business logic (new)
├── models/
│   ├── conversation.py       # Existing from Feature 001
│   └── message.py            # Existing from Feature 001
├── mcp_server/
│   ├── server.py             # Existing from Feature 002
│   └── tools/                # 5 existing tools
└── utils/
    └── openai_client.py      # OpenAI SDK wrapper (new)
```

### Configuration

Add to `.env`:
```env
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o
OPENAI_TIMEOUT=30
CHAT_HISTORY_LIMIT=50
MAX_MESSAGE_LENGTH=5000
```

### Logging

Log every chat request:
```python
logger.info(
    "chat_request",
    extra={
        "user_id": user_id,
        "conversation_id": conversation_id,
        "message_length": len(message),
        "has_history": len(history) > 0
    }
)

logger.info(
    "chat_response",
    extra={
        "user_id": user_id,
        "conversation_id": conversation_id,
        "response_length": len(assistant_message),
        "tool_calls": len(tool_calls),
        "duration_ms": duration
    }
)
```

### Database Indexes

Ensure these indexes exist (should already exist from Feature 001):
```sql
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);  -- For ORDER BY optimization
```

### Rate Limiting

Consider adding rate limits to prevent abuse:
- 60 chat requests per minute per user
- 1000 chat requests per hour per user

---

## Business Value *(informative)*

### User Benefits

- **Natural Interaction**: Users can manage tasks through conversation instead of forms and buttons
- **Time Savings**: AI automates task creation, reducing manual data entry
- **Context Awareness**: AI remembers conversation history, no need to repeat information
- **Intelligent Assistance**: AI proactively suggests task management actions

### Technical Benefits

- **Scalability**: Stateless design enables horizontal scaling without session affinity
- **Reliability**: No in-memory state means instant recovery from server restarts
- **Maintainability**: Clear separation between conversation storage (database), AI logic (OpenAI), and actions (MCP tools)
- **Extensibility**: Easy to add new MCP tools without changing chat endpoint code

### Success Metrics

- **Engagement**: % of users who send 5+ chat messages per session
- **Task Creation**: % of tasks created through AI chat vs manual UI
- **Satisfaction**: User rating of AI assistant helpfulness (target: 4+ out of 5)
- **Retention**: % of users who return to use chat feature weekly

---

*This specification defines WHAT the stateless chat endpoint does and WHY it's needed. The HOW (implementation details) is intentionally left to the implementation phase, allowing flexibility in technical approach while ensuring clear business requirements and success criteria.*
