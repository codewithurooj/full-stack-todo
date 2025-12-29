# MCP Server Quickstart Guide

## Setup

1. Install dependencies:
```bash
cd backend
pip install mcp>=0.9.0 openai>=1.0.0 slowapi>=0.1.9
```

2. Set environment variable:
```bash
export OPENAI_API_KEY=sk-your-key-here
```

3. Start server:
```bash
uvicorn app.main:app --reload
```

## Testing Tools

### add_task
```bash
curl -X POST http://localhost:8000/mcp/tools/add_task \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "title": "Buy groceries"}'
```

### list_tasks
```bash
curl http://localhost:8000/mcp/tools/list_tasks?user_id=user123&filter=pending \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

### complete_task
```bash
curl -X PATCH http://localhost:8000/mcp/tools/complete_task \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "task_id": "uuid-here"}'
```

### delete_task
```bash
curl -X DELETE http://localhost:8000/mcp/tools/delete_task \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "task_id": "uuid-here"}'
```

### update_task
```bash
curl -X PUT http://localhost:8000/mcp/tools/update_task \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "task_id": "uuid-here", "title": "New title"}'
```

## Natural Language Chat

```bash
curl -X POST http://localhost:8000/api/user123/chat \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"message": "Add a task to buy groceries"}'
```
