# Implementation Plan: MCP Server with 5 Custom Tools

**Branch**: `002-mcp-server` | **Date**: 2025-12-27 | **Spec**: [spec.md](./spec.md)

## Summary

Implement an MCP (Model Context Protocol) server with 5 stateless tools enabling AI-powered task management through natural language. Tools: add_task, list_tasks, complete_task, delete_task, update_task. All tools enforce user isolation via JWT and maintain stateless architecture with conversation history in database (Feature 001).

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: mcp (MCP SDK), openai, FastAPI 0.100+, SQLModel 0.0.8+, Pydantic 2.0+
**Storage**: Neon PostgreSQL - tables: tasks, users, conversations, messages
**Testing**: pytest, httpx, pytest-asyncio
**Target Platform**: Linux server (FastAPI on Render/Railway)
**Project Type**: web - Backend extension
**Performance Goals**: <100ms p95, 99.9% success rate, 1000 concurrent requests
**Constraints**: Stateless, single DB transaction/tool, 5-second timeout, JSON-only
**Scale/Scope**: 5 tools, 100% user isolation, rate limits: 100 creates/hr, 200 updates/hr, 1000 reads/hr

## Constitution Check

✅ Spec-Driven Development: Complete (spec.md, 304 lines, 5 stories, 15 FRs)
✅ Architecture & Tech Stack: Extends FastAPI, SQLModel, Neon PostgreSQL, official MCP SDK
✅ RESTful API: MCP via HTTP/JSON, JWT auth, user_id verification, Pydantic validation
✅ Data Management: Existing tables, user isolation (FR-008), no cross-user access
✅ Testing: All 5 tools tested, NL test cases defined, 90%+ coverage
✅ Code Quality: Type hints, no hardcoded values, DRY, async/await
✅ Security: JWT on all tools (FR-006), user isolation (FR-008), XSS sanitization (FR-009)
❌ NO VIOLATIONS

## Project Structure

### Documentation
```
specs/002-mcp-server/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/ (add_task.json, list_tasks.json, etc.)
├── spec.md
└── tasks.md (/sp.tasks output)
```

### Source Code
```
backend/app/
├── routes/chat.py (NEW)
├── mcp_server/ (NEW)
│   ├── server.py
│   ├── tools/ (add_task.py, list_tasks.py, etc.)
│   ├── auth.py
│   ├── validation.py
│   └── errors.py
└── config.py (NEW)
```

## Phase III: AI & MCP Server Design

### MCP Tools
- add_task: user_id, title(1-200), description(opt, max 1000)
- list_tasks: user_id, filter(all/pending/completed), sort_by, sort_order
- complete_task: user_id, task_id(UUID)
- delete_task: user_id, task_id(UUID)
- update_task: user_id, task_id(UUID), title(opt), description(opt)

### Stateless Pattern
1. Fetch conversation history from DB
2. Build message array (history + new)
3. Store user message
4. Run OpenAI with MCP tools
5. Agent invokes tools
6. Store assistant response
7. Return response
8. No server state

### DB Schema
ALREADY EXISTS from Feature 001 (conversations, messages tables)

### OpenAI Config
- Model: gpt-4o or gpt-4o-mini
- System Prompt: Task management assistant
- Tool Invocation: Sequential (OpenAI SDK)

## Implementation Phases

### Phase 0: Research
1. MCP SDK selection
2. OpenAI integration approach
3. JWT verification pattern
4. Rate limiting library
5. Error response format

**Deliverable**: research.md

### Phase 1: Design
1. Data models (data-model.md)
2. API contracts (contracts/*.json)
3. Chat endpoint design
4. Quickstart guide

**Deliverables**: data-model.md, 5 contracts, quickstart.md

### Phase 2: Tasks
Run /sp.tasks command

## Next Steps
1. Review artifacts
2. /sp.tasks
3. /sp.implement
4. Test
5. Deploy
