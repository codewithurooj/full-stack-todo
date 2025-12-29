# Stateless Chat Endpoint - Quick Start Guide

**Feature**: 003-stateless-chat-endpoint
**Endpoint**: `POST /api/{user_id}/chat`
**Authentication**: JWT Bearer token required

## Quick Start

### 1. Start a New Conversation

```bash
curl -X POST http://localhost:8000/api/user123/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need to buy groceries tomorrow"
  }'
```

**Response**:
```json
{
  "conversation_id": 1,
  "assistant_message": "I've added 'Buy groceries' to your task list for tomorrow.",
  "tool_calls": ["add_task"],
  "created_at": "2025-12-27T14:30:00Z"
}
```

### 2. Continue Existing Conversation

```bash
curl -X POST http://localhost:8000/api/user123/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What tasks do I have?",
    "conversation_id": 1
  }'
```

**Response**:
```json
{
  "conversation_id": 1,
  "assistant_message": "You have 1 pending task: 'Buy groceries' (due tomorrow).",
  "tool_calls": ["list_tasks"],
  "created_at": "2025-12-27T14:31:00Z"
}
```

### 3. Natural Language Task Management

**Create Task**:
```bash
curl -X POST http://localhost:8000/api/user123/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Add a task to call mom"
  }'
```

**List Tasks**:
```bash
curl -X POST http://localhost:8000/api/user123/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me my pending tasks",
    "conversation_id": 1
  }'
```

**Complete Task**:
```bash
curl -X POST http://localhost:8000/api/user123/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I finished buying groceries",
    "conversation_id": 1
  }'
```

**Update Task**:
```bash
curl -X POST http://localhost:8000/api/user123/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Change the grocery task to buy milk and eggs",
    "conversation_id": 1
  }'
```

**Delete Task**:
```bash
curl -X POST http://localhost:8000/api/user123/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Remove the grocery task",
    "conversation_id": 1
  }'
```

## API Details

### Request Schema

```typescript
{
  message: string;           // Required, 1-5000 characters
  conversation_id?: number;  // Optional, null for new conversation
}
```

### Response Schema

```typescript
{
  conversation_id: number;   // Conversation ID
  assistant_message: string; // AI response
  tool_calls: string[];      // Names of tools invoked (e.g., ["add_task"])
  created_at: string;        // ISO 8601 timestamp
}
```

### Error Responses

**400 Bad Request** - Message too long:
```json
{
  "detail": [
    {
      "type": "string_too_long",
      "loc": ["body", "message"],
      "msg": "String should have at most 5000 characters"
    }
  ]
}
```

**401 Unauthorized** - Invalid JWT:
```json
{
  "detail": "Invalid authentication credentials"
}
```

**403 Forbidden** - User mismatch:
```json
{
  "error": {
    "message": "Unauthorized access",
    "code": "AUTHORIZATION_ERROR"
  }
}
```

**404 Not Found** - Conversation doesn't exist:
```json
{
  "detail": "Conversation not found"
}
```

**500 Internal Server Error**:
```json
{
  "error": {
    "message": "Internal server error",
    "code": "INTERNAL_ERROR"
  }
}
```

## Features

### Stateless Design
- No server-side session state
- All conversation context fetched from database on each request
- Horizontal scalability ready
- Instant recovery from server restarts

### Tool Integration
The AI automatically invokes MCP tools when needed:
- `add_task` - Creates new tasks
- `list_tasks` - Retrieves user's tasks
- `complete_task` - Toggles task completion
- `delete_task` - Removes tasks
- `update_task` - Modifies task details

### Conversation Context
- Maintains full conversation history
- AI references previous messages
- Last 50 messages included in context
- Multi-turn conversations supported

### Security
- JWT authentication required
- User isolation enforced
- Conversation ownership validated
- All tool calls authorized

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-your-openai-api-key
DATABASE_URL=postgresql://user:pass@host/db

# Optional (with defaults)
OPENAI_MODEL=gpt-4o
CHAT_SYSTEM_PROMPT="You are a helpful AI assistant..."
CHAT_HISTORY_LIMIT=50
```

### Performance Targets

- Database fetch: < 100ms
- Total request: < 3s p95
- Concurrent requests: 100+

## Testing

### Manual Testing

1. Get JWT token from auth endpoint
2. Start conversation with "Hello"
3. Add tasks via natural language
4. Verify tasks in database
5. Continue conversation to test context
6. Restart server and verify context preserved

### Integration Testing

```bash
# Run pytest tests
cd backend
pytest tests/test_chat.py -v
```

## Troubleshooting

### "Conversation not found"
- Verify conversation_id exists
- Ensure conversation belongs to authenticated user

### "Unauthorized access"
- Check JWT token is valid
- Verify user_id matches token

### "OpenAI API timeout"
- Check OPENAI_API_KEY is set
- Verify network connectivity
- Check OpenAI API status

### No tool calls executed
- Verify MCP server is running
- Check get_all_tool_schemas() returns schemas
- Review AI response in assistant_message

## Next Steps

1. Test basic chat flow
2. Test multi-turn conversations
3. Verify tool invocations
4. Check conversation persistence
5. Test error scenarios
6. Deploy to production

---

**Stateless Chat Endpoint - Feature 003** ✅
