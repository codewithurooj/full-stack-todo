# Full-Stack Todo Application Constitution
<!-- Phase II: Full-Stack Web Application with Basic Level Functionality -->

## Core Principles

### I. Spec-Driven Development (NON-NEGOTIABLE)
**Every feature must be specified before implementation.**
- Write detailed specifications in Markdown before any code
- Specifications must include user stories, acceptance criteria, and API contracts
- Use Claude Code to generate implementation from refined specifications
- **Constraint**: Manual code writing is prohibited - refine specs until Claude Code generates correct output
- All specs stored in `/specs` directory with clear organization
- Specs must be versioned and updated when requirements change

### II. Architecture & Technology Stack
**Monorepo structure with clear separation of concerns.**

**Frontend**:
- Next.js 16+ (App Router only)
- TypeScript for type safety
- Tailwind CSS for styling (no inline styles)
- Server components by default, client components only when necessary
- Better Auth for authentication

**Backend**:
- Python FastAPI for REST API
- SQLModel for ORM
- Neon Serverless PostgreSQL for database
- Stateless API design

**Authentication & Security**:
- Better Auth with JWT tokens
- User isolation enforced at API level
- All endpoints require valid JWT token
- Environment variables for secrets (never hardcoded)

### III. RESTful API Design
**Consistent, predictable API contracts.**
- Base path: `/api/{user_id}/`
- Standard HTTP methods: GET, POST, PUT, DELETE, PATCH
- JSON request/response format
- Pydantic models for validation
- HTTPException for error handling
- JWT token in `Authorization: Bearer <token>` header

**API Endpoints**:
```
GET    /api/{user_id}/tasks           - List all tasks
POST   /api/{user_id}/tasks           - Create new task
GET    /api/{user_id}/tasks/{id}      - Get task details
PUT    /api/{user_id}/tasks/{id}      - Update task
DELETE /api/{user_id}/tasks/{id}      - Delete task
PATCH  /api/{user_id}/tasks/{id}/complete - Toggle completion
```

### IV. Data Management
**Database-first with clear schema definitions.**
- Neon Serverless PostgreSQL as source of truth
- SQLModel for type-safe database operations
- Migration scripts for schema changes
- User data isolation (tasks filtered by user_id)

**Database Schema**:
- `users` table: managed by Better Auth (id, email, name, created_at)
- `tasks` table: user_id (FK), id, title, description, completed, created_at, updated_at
- Indexes on user_id and completed fields

### V. Testing & Quality Assurance
**Working application with demonstrated functionality.**
- All Basic Level features must be functional:
  - Add Task (title required, description optional)
  - Delete Task (by ID)
  - Update Task (title and/or description)
  - View Task List (with status indicators)
  - Mark as Complete/Incomplete (toggle)
- Manual testing required before submission
- Error handling for edge cases
- Input validation on both frontend and backend

### VI. Code Quality Standards
**Clean, maintainable, production-ready code.**
- Follow clean code principles
- Proper Python project structure (main.py, models.py, routes/, db.py)
- Proper Next.js structure (/components, /app, /lib)
- No hardcoded values - use environment variables
- Meaningful variable and function names
- No duplicate code - DRY principle
- Type hints in Python, TypeScript types in frontend
- Proper error messages for debugging

### VII. Documentation & Repository Standards
**Clear, comprehensive documentation.**

**Required Files**:
- `README.md`: Setup instructions, tech stack, features
- `CLAUDE.md`: Claude Code instructions (root, frontend/, backend/)
- `/specs`: All specification files organized by feature
- `history/` folder: Prompt history records
- `.env.example`: Environment variable template
- `requirements.txt` (backend) and `package.json` (frontend)

**Folder Structure**:
```
full-stack-todo/
├── .specify/
│   ├── memory/constitution.md
│   └── templates/
├── specs/
│   ├── overview.md
│   ├── features/
│   ├── api/
│   ├── database/
│   └── ui/
├── history/
│   └── prompts/
├── frontend/
│   ├── CLAUDE.md
│   └── [Next.js app structure]
├── backend/
│   ├── CLAUDE.md
│   └── [FastAPI app structure]
├── CLAUDE.md (root)
├── README.md
└── docker-compose.yml
```

## Security & Authentication Requirements

### User Authentication
- Better Auth integration required
- JWT tokens for API authentication
- Shared secret (BETTER_AUTH_SECRET) between frontend and backend
- Token expiry enforcement (default 7 days)
- Secure password handling (managed by Better Auth)

### API Security
- JWT verification middleware on all protected routes
- User ID from token must match user_id in URL
- No cross-user data access
- SQL injection prevention via SQLModel/Pydantic
- CORS configuration for production
- Environment-based configuration (dev/prod)

### Data Privacy
- User isolation enforced at database query level
- No shared data between users
- Proper error messages (no sensitive data leakage)
- Secure connection strings (environment variables only)

## Development Workflow

### Phase II Implementation Steps
1. **Specification**: Write detailed specs for each feature in `/specs`
2. **Database Setup**: Configure Neon DB, define schema
3. **Backend Development**:
   - Set up FastAPI project structure
   - Implement data models (SQLModel)
   - Create API endpoints
   - Add JWT authentication middleware
4. **Frontend Development**:
   - Set up Next.js project
   - Implement Better Auth
   - Create UI components
   - Build API client
5. **Integration**: Connect frontend to backend
6. **Testing**: Verify all Basic Level features work
7. **Deployment**: Deploy to Vercel (frontend) and appropriate backend host
8. **Documentation**: Update README with setup and usage instructions

### Spec-Driven Workflow
- Read hackathon requirements → Write feature spec
- Refine spec with acceptance criteria
- Use Claude Code: "Implement @specs/features/[feature].md"
- Test generated code
- Iterate on spec if needed (don't manually fix code)
- Document decisions in ADRs when architecturally significant

## Deployment & DevOps

### Frontend Deployment
- Deploy to Vercel (free tier)
- Environment variables configured in Vercel dashboard
- Public URL required for submission
- Better Auth domain allowlist configured

### Backend Deployment
- FastAPI server deployed (Railway, Render, or similar)
- Public API URL required
- Environment variables configured
- CORS enabled for frontend domain
- Database connection to Neon DB

### Environment Variables
**Frontend**:
- `NEXT_PUBLIC_API_URL`: Backend API base URL
- `BETTER_AUTH_SECRET`: Shared secret for JWT
- `NEXT_PUBLIC_OPENAI_DOMAIN_KEY`: (for Phase III)

**Backend**:
- `DATABASE_URL`: Neon PostgreSQL connection string
- `BETTER_AUTH_SECRET`: Shared secret for JWT verification
- `ALLOWED_ORIGINS`: CORS allowed origins

## Constraints & Non-Negotiables

### Mandatory Requirements
- ✅ All 5 Basic Level features must work
- ✅ Spec-driven development (no manual coding)
- ✅ Better Auth for user authentication
- ✅ JWT-based API security
- ✅ User data isolation
- ✅ Monorepo structure with /specs folder
- ✅ Public GitHub repository
- ✅ Deployed and accessible application
- ✅ README with setup instructions
- ✅ Demo video (max 90 seconds)

### Prohibited Practices
- ❌ Manual code writing (must use Claude Code + specs)
- ❌ Hardcoded secrets or credentials
- ❌ Inline styles (use Tailwind only)
- ❌ Shared data between users
- ❌ Missing authentication/authorization
- ❌ Direct database access from frontend
- ❌ Skipping specification phase

## Feature Requirements: Basic Level

### 1. Add Task
- **User Story**: As a user, I can create a new task with a title and optional description
- **Acceptance Criteria**:
  - Title is required (1-200 characters)
  - Description is optional (max 1000 characters)
  - Task is associated with authenticated user
  - Newly created task appears in task list
  - Default status is "incomplete"

### 2. Delete Task
- **User Story**: As a user, I can remove tasks I no longer need
- **Acceptance Criteria**:
  - User can delete task by ID
  - Only task owner can delete
  - Confirmation before deletion
  - Task removed from database
  - UI updates after deletion

### 3. Update Task
- **User Story**: As a user, I can modify task details
- **Acceptance Criteria**:
  - Can update title and/or description
  - Only task owner can update
  - Changes persist in database
  - UI reflects updates immediately
  - Validation same as create

### 4. View Task List
- **User Story**: As a user, I can see all my tasks
- **Acceptance Criteria**:
  - Display all tasks for current user only
  - Show title, status, created date
  - Clear visual distinction between complete/incomplete
  - Responsive design
  - Empty state when no tasks

### 5. Mark as Complete
- **User Story**: As a user, I can toggle task completion status
- **Acceptance Criteria**:
  - Toggle between complete/incomplete
  - Visual feedback (checkbox, strikethrough, etc.)
  - Status persists in database
  - Only task owner can toggle
  - Immediate UI update

## Governance

### Constitution Authority
- This constitution supersedes all other development practices
- All code, specs, and architectural decisions must comply
- Amendments require documentation and version update
- Non-compliance blocks submission acceptance

### Quality Gates
- **Spec Quality**: All specs must have acceptance criteria
- **Code Quality**: Generated code must pass manual review
- **Security**: JWT authentication required on all endpoints
- **Data Isolation**: User data must be properly segregated
- **Documentation**: README must enable others to run project
- **Deployment**: Application must be publicly accessible

### Review Checklist
Before submission, verify:
- [ ] All 5 Basic Level features work end-to-end
- [ ] Specs written for every feature
- [ ] User authentication working (Better Auth)
- [ ] API requires JWT tokens
- [ ] User data isolation enforced
- [ ] No hardcoded secrets
- [ ] Frontend deployed to Vercel
- [ ] Backend deployed and accessible
- [ ] README has clear setup instructions
- [ ] CLAUDE.md files present
- [ ] Demo video created (< 90 seconds)
- [ ] GitHub repository is public

### Continuous Improvement
- Document learnings in history/prompts/
- Create ADRs for significant architectural decisions
- Update specs when requirements change
- Maintain version history in git
- Iterative refinement encouraged

**Version**: 2.0.0 | **Ratified**: 2025-12-11 | **Phase**: II (Full-Stack Web Application)
