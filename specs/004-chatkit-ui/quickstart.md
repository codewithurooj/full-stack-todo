# Quickstart: ChatKit UI

## Setup

No new dependencies needed. Everything is already installed.

## Development

1. **Start backend** (if not running):
```bash
cd backend
uvicorn app.main:app --reload
```

2. **Start frontend**:
```bash
cd frontend
npm run dev
```

3. **Navigate to chat**:
```
http://localhost:3000/chat
```

## Usage

### Send a Message

**User**: "Add a task to buy groceries"
**AI**: "I've added 'Buy groceries' to your task list."

### View Tasks

**User**: "What tasks do I have?"
**AI**: "You have 3 tasks: 1. Buy groceries, 2. Call mom, 3. Finish project"

### Complete Task

**User**: "Mark task 1 as complete"
**AI**: "Task 'Buy groceries' is now marked as complete."

## API Endpoint

**POST** `/api/{user_id}/chat`

**Request**:
```json
{
  "message": "Add a task to buy groceries",
  "conversation_id": 123  // optional
}
```

**Response**:
```json
{
  "conversation_id": 123,
  "assistant_message": "I've added 'Buy groceries' to your task list.",
  "tool_calls": ["add_task"],
  "created_at": "2025-12-28T12:00:00Z"
}
```

## Authentication

All requests require JWT token:
```typescript
headers: {
  'Authorization': 'Bearer YOUR_JWT_TOKEN'
}
```

## Error Handling

- **401**: Token expired → Redirect to login
- **403**: Unauthorized → Show error
- **404**: Conversation not found → Create new
- **500**: Server error → Show retry

## Testing

```bash
# Manual test with curl
curl -X POST http://localhost:8000/api/user123/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hi"}'
```

## Features

- ✅ Natural language task management
- ✅ Conversation history persistence
- ✅ Streaming responses (optional)
- ✅ Real-time task list updates
- ✅ Mobile responsive design

## Next Steps

1. Implement components (`/sp.implement`)
2. Test functionality
3. Add streaming (optional)
4. Deploy

