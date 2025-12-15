# Quickstart Guide: Task CRUD Feature

**Feature**: 001-task-crud | **Last Updated**: 2025-12-12

## Overview

This guide helps you quickly set up and run the task CRUD feature locally for development and testing.

---

## Prerequisites

### Required Software

- **Python 3.13+**: Backend runtime
- **Node.js 18+**: Frontend runtime
- **npm or yarn**: Package manager
- **Git**: Version control
- **PostgreSQL client** (optional): For manual database inspection

### Required Accounts

- **Neon Account**: Free PostgreSQL database ([https://neon.tech](https://neon.tech))
- **Vercel Account** (for deployment): Free hosting ([https://vercel.com](https://vercel.com))
- **Render/Railway Account** (for deployment): Free backend hosting

---

## Quick Setup (5 Minutes)

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/full-stack-todo.git
cd full-stack-todo
git checkout 001-task-crud
```

### 2. Set Up Database (Neon)

1. Go to [https://neon.tech](https://neon.tech) and create a free account
2. Create a new project: "full-stack-todo"
3. Copy the connection string (looks like `postgresql://user:pass@host.neon.tech/dbname`)
4. Save it for the next step

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env and add:
# DATABASE_URL=<your-neon-connection-string>
# BETTER_AUTH_SECRET=<generate-a-32-char-random-string>

# Run migrations
alembic upgrade head

# Start backend server
uvicorn app.main:app --reload
```

Backend should now be running at **http://localhost:8000**

Check it: http://localhost:8000/docs (FastAPI automatic documentation)

### 4. Frontend Setup

Open a **new terminal** (keep backend running):

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local file
cp .env.local.example .env.local

# Edit .env.local and add:
# NEXT_PUBLIC_API_URL=http://localhost:8000
# BETTER_AUTH_SECRET=<same-secret-as-backend>

# Start frontend dev server
npm run dev
```

Frontend should now be running at **http://localhost:3000**

### 5. Test the Application

1. Open browser to **http://localhost:3000**
2. Click "Sign Up" and create an account
3. After signup, you should be redirected to the tasks page
4. Try creating a task:
   - Title: "Test task"
   - Description: "This is a test"
5. Verify the task appears in the list
6. Try toggling completion, editing, and deleting

---

## Detailed Setup

### Backend Configuration

#### Environment Variables (`.env`)

```env
# Database
DATABASE_URL=postgresql://user:password@host.neon.tech/dbname?sslmode=require

# Authentication (must match frontend)
BETTER_AUTH_SECRET=your-32-character-secret-key-here

# CORS (for frontend access)
ALLOWED_ORIGINS=http://localhost:3000,https://your-app.vercel.app

# Optional: Database connection pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
```

#### Generate Random Secret

```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL
openssl rand -base64 32

# Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

#### Database Migrations

```bash
# Check current migration status
alembic current

# See migration history
alembic history

# Upgrade to latest
alembic upgrade head

# Downgrade one version
alembic downgrade -1

# Create new migration (if schema changes)
alembic revision --autogenerate -m "description"
```

#### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_tasks.py

# Run specific test
pytest tests/test_tasks.py::test_create_task

# Verbose output
pytest -v
```

### Frontend Configuration

#### Environment Variables (`.env.local`)

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Authentication (must match backend)
BETTER_AUTH_SECRET=your-32-character-secret-key-here

# Optional: OpenAI API key (for Phase 3)
NEXT_PUBLIC_OPENAI_DOMAIN_KEY=sk-your-key-here
```

#### Development Commands

```bash
# Start dev server (with hot reload)
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Type checking
npm run type-check

# Linting
npm run lint

# Format code
npm run format
```

---

## API Testing

### Using cURL

#### 1. Sign Up / Sign In

```bash
# Sign up
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "name": "Test User"
  }'

# Sign in (get JWT token)
curl -X POST http://localhost:8000/api/auth/signin \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'

# Save the token from response:
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
export USER_ID="550e8400-e29b-41d4-a716-446655440000"
```

#### 2. Create Task

```bash
curl -X POST "http://localhost:8000/api/$USER_ID/tasks" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Buy groceries",
    "description": "Milk, eggs, bread"
  }'
```

#### 3. List Tasks

```bash
# All tasks
curl -X GET "http://localhost:8000/api/$USER_ID/tasks" \
  -H "Authorization: Bearer $TOKEN"

# Only incomplete tasks
curl -X GET "http://localhost:8000/api/$USER_ID/tasks?completed=false" \
  -H "Authorization: Bearer $TOKEN"

# Sorted by title
curl -X GET "http://localhost:8000/api/$USER_ID/tasks?sort=title&order=asc" \
  -H "Authorization: Bearer $TOKEN"
```

#### 4. Get Task

```bash
export TASK_ID="660e8400-e29b-41d4-a716-446655440001"

curl -X GET "http://localhost:8000/api/$USER_ID/tasks/$TASK_ID" \
  -H "Authorization: Bearer $TOKEN"
```

#### 5. Update Task

```bash
curl -X PUT "http://localhost:8000/api/$USER_ID/tasks/$TASK_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Buy organic groceries",
    "completed": false
  }'
```

#### 6. Toggle Completion

```bash
curl -X PATCH "http://localhost:8000/api/$USER_ID/tasks/$TASK_ID/complete" \
  -H "Authorization: Bearer $TOKEN"
```

#### 7. Delete Task

```bash
curl -X DELETE "http://localhost:8000/api/$USER_ID/tasks/$TASK_ID" \
  -H "Authorization: Bearer $TOKEN"
```

### Using FastAPI Docs (Recommended)

1. Open **http://localhost:8000/docs**
2. Click "Authorize" button
3. Enter JWT token: `Bearer <your-token>`
4. Try out endpoints interactively

---

## Database Access

### Connect to Neon Database

```bash
# Using psql
psql "postgresql://user:password@host.neon.tech/dbname?sslmode=require"

# List tables
\dt

# Describe table structure
\d tasks
\d users

# Query tasks
SELECT * FROM tasks;

# Query users
SELECT * FROM users;

# Count tasks per user
SELECT user_id, COUNT(*) as task_count
FROM tasks
GROUP BY user_id;
```

### Useful Queries

```sql
-- Check user isolation (ensure each user sees only their tasks)
SELECT
  u.email,
  COUNT(t.id) as task_count
FROM users u
LEFT JOIN tasks t ON u.id = t.user_id
GROUP BY u.id, u.email;

-- Find tasks with empty descriptions
SELECT * FROM tasks WHERE description IS NULL OR description = '';

-- Find completed vs incomplete tasks
SELECT
  completed,
  COUNT(*) as count
FROM tasks
GROUP BY completed;

-- Find recently created tasks (last 24 hours)
SELECT * FROM tasks
WHERE created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;
```

---

## Troubleshooting

### Backend Issues

#### Database Connection Fails

```
Error: could not connect to server
```

**Solution**:
- Verify `DATABASE_URL` in `.env` is correct
- Check Neon dashboard that database is active
- Ensure connection string includes `?sslmode=require`

#### JWT Verification Fails

```
401 Unauthorized: Could not validate credentials
```

**Solution**:
- Verify `BETTER_AUTH_SECRET` matches between frontend and backend
- Ensure token is passed in `Authorization: Bearer <token>` header
- Check token hasn't expired (default: 7 days)

#### Import Errors

```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution**:
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.13+)

### Frontend Issues

#### API Connection Fails

```
Failed to fetch: TypeError: Failed to fetch
```

**Solution**:
- Verify backend is running on http://localhost:8000
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Ensure CORS is enabled in backend for `http://localhost:3000`

#### Authentication Not Working

```
Error: Authentication failed
```

**Solution**:
- Verify `BETTER_AUTH_SECRET` matches backend
- Clear browser cookies and localStorage
- Try signing up with a new email

#### Build Errors

```
Error: Module not found
```

**Solution**:
- Delete `node_modules` and `package-lock.json`
- Run `npm install` again
- Check Node.js version: `node --version` (should be 18+)

---

## Development Workflow

### 1. Start Development Session

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Database (optional)
psql "<connection-string>"
```

### 2. Make Changes

- Edit backend code in `backend/app/`
- Edit frontend code in `frontend/app/` or `frontend/components/`
- Backend auto-reloads on file changes
- Frontend hot-reloads on file changes

### 3. Test Changes

- Use FastAPI docs: http://localhost:8000/docs
- Test frontend: http://localhost:3000
- Run backend tests: `pytest`
- Check database: `psql "<connection-string>"`

### 4. Commit Changes

```bash
git add .
git commit -m "feat: implement task CRUD operations"
git push origin 001-task-crud
```

---

## Deployment

### Backend (Render/Railway)

1. Connect GitHub repository
2. Create new web service
3. Configure environment variables:
   - `DATABASE_URL`: Neon connection string
   - `BETTER_AUTH_SECRET`: Same as development
   - `ALLOWED_ORIGINS`: Include production frontend URL
4. Deploy from `001-task-crud` branch
5. Save the public URL (e.g., `https://your-app.onrender.com`)

### Frontend (Vercel)

1. Import GitHub repository
2. Configure:
   - Framework: Next.js
   - Root directory: `frontend`
   - Build command: `npm run build`
   - Output directory: `.next`
3. Environment variables:
   - `NEXT_PUBLIC_API_URL`: Backend production URL
   - `BETTER_AUTH_SECRET`: Same as backend
4. Deploy from `001-task-crud` branch
5. Test the deployed app

---

## Next Steps

After setting up:

1. ✅ Verify all 5 features work (Create, Read, Update, Delete, Toggle)
2. ✅ Test user authentication (signup, signin, signout)
3. ✅ Verify user data isolation (create second user, ensure tasks are separate)
4. ✅ Run backend tests: `pytest`
5. ✅ Deploy to production
6. ✅ Create demo video (< 90 seconds)

---

## Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Database Spec**: `/specs/database/schema.md`
- **API Spec**: `/specs/api/rest-endpoints.md`
- **Feature Spec**: `/specs/features/001-task-crud/spec.md`
- **Implementation Plan**: `/specs/features/001-task-crud/plan.md`

---

**Questions?** Check the troubleshooting section or review the specs in `/specs/`.
