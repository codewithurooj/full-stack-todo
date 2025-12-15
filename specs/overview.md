# Full-Stack Todo Application - Project Overview

## Project Information

**Project Name:** Full-Stack Todo Application
**Phase:** Phase 2 - Full-Stack Web Application
**Due Date:** December 14, 2025
**Points:** 150

## Purpose

Build a modern, spec-driven todo application that demonstrates:
- Full-stack development with Next.js and FastAPI
- Spec-driven development methodology
- RESTful API design
- User authentication and authorization
- Database-backed persistence

## Current Phase: Phase 2

### Tech Stack
- **Frontend:** Next.js 16+ (App Router), TypeScript, Tailwind CSS
- **Backend:** FastAPI, SQLModel, Python 3.13+
- **Database:** Neon Serverless PostgreSQL
- **Auth:** Better Auth with JWT tokens
- **Development:** Claude Code + Spec-Kit Plus

## Features (Basic Level)

### 1. Add Task
Create new todo items with title and optional description.

### 2. Delete Task
Remove tasks from the list by ID.

### 3. Update Task
Modify existing task details (title and/or description).

### 4. View Task List
Display all tasks for the authenticated user.

### 5. Mark as Complete
Toggle task completion status.

## Features (To Be Implemented in Later Phases)

**Phase 3:**
- AI-powered chatbot interface
- Natural language task management
- MCP server architecture

**Phase 4:**
- Local Kubernetes deployment (Minikube)
- Docker containerization
- Helm charts

**Phase 5:**
- Cloud deployment (DigitalOcean/GKE/AKS)
- Event-driven architecture with Kafka
- Dapr integration

## Architecture

### Frontend
- Server Components by default
- Client Components for interactivity
- API client abstraction layer
- Better Auth for authentication

### Backend
- RESTful API with FastAPI
- SQLModel for database operations
- JWT middleware for authentication
- User data isolation

### Database Schema
- `users` table (managed by Better Auth)
- `tasks` table with foreign key to users

## API Design

### Base Path
`/api/{user_id}/`

### Endpoints
```
GET    /api/{user_id}/tasks           - List all tasks
POST   /api/{user_id}/tasks           - Create task
GET    /api/{user_id}/tasks/{id}      - Get task details
PUT    /api/{user_id}/tasks/{id}      - Update task
DELETE /api/{user_id}/tasks/{id}      - Delete task
PATCH  /api/{user_id}/tasks/{id}/complete - Toggle completion
```

## Security

- JWT-based authentication
- User ID verification on all requests
- Database query filtering by user_id
- Environment variable-based secrets
- CORS configuration for production

## Development Approach

### Spec-Driven Development
1. Write detailed specifications for each feature
2. Use Claude Code to generate implementation
3. Refine specs until code is correct
4. Test thoroughly
5. Document with PHRs

### Constraints
- No manual code writing
- Specifications must come first
- All features require acceptance criteria
- User authentication required on all endpoints

## Success Criteria

- ✅ All 5 basic features working end-to-end
- ✅ User authentication functional
- ✅ JWT tokens enforced on API
- ✅ User data properly isolated
- ✅ Frontend deployed to Vercel
- ✅ Backend deployed (Render/Railway)
- ✅ Demo video created (< 90 seconds)
- ✅ All specs documented in `/specs`
- ✅ PHRs created in `/history/prompts`

## Next Steps

1. Create detailed feature specifications
2. Set up database schema
3. Implement backend API
4. Build frontend UI
5. Integrate authentication
6. Deploy to production
7. Create demo video
8. Submit before December 14, 2025

---

**Last Updated:** 2025-12-11
**Status:** In Progress - Setting up monorepo structure
