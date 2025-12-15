# Full-Stack Todo Application

> Hackathon II: The Evolution of Todo - Spec-Driven Development

## 🎯 Project Overview

A modern todo application built using spec-driven development with Claude Code and Spec-Kit Plus for Hackathon II Phase 2.

**Phase:** Phase 2 - Full-Stack Web Application
**Due:** December 14, 2025
**Points:** 150

## ✨ Features

- ✅ Task CRUD operations (Create, Read, Update, Delete, Mark Complete)
- ✅ User authentication with Better Auth
- ✅ JWT-based API security
- ✅ Responsive UI with Tailwind CSS
- ✅ PostgreSQL database with Neon
- ✅ RESTful API design
- ✅ Spec-driven development workflow

## 🛠️ Tech Stack

### Frontend
- **Framework:** Next.js 16+ (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Auth:** Better Auth (JWT)
- **Deployment:** Vercel

### Backend
- **Framework:** FastAPI
- **Language:** Python 3.13+
- **ORM:** SQLModel
- **Database:** Neon Serverless PostgreSQL
- **Deployment:** Render/Railway

### Development
- **Spec-Driven:** Claude Code + Spec-Kit Plus
- **Containerization:** Docker Compose
- **Testing:** Pytest + Jest
- **CI/CD:** GitHub Actions

## 📁 Project Structure

```
full-stack-todo/
├── frontend/           # Next.js application
│   ├── app/           # Pages (App Router)
│   ├── components/    # Reusable components
│   └── lib/           # Utilities & API client
├── backend/           # FastAPI server
│   ├── app/          # Application code
│   │   ├── models/   # SQLModel models
│   │   ├── routes/   # API endpoints
│   │   └── middleware/ # Auth & other middleware
│   └── tests/        # Pytest tests
├── specs/            # Specifications
│   ├── features/     # Feature specs
│   ├── api/         # API specs
│   ├── database/    # Database schemas
│   └── ui/          # UI specs
├── history/         # Historical records
│   ├── prompts/     # Prompt History Records
│   └── adr/        # Architecture Decision Records
└── .claude/        # Claude Code configuration
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.13+
- Neon Database account (free tier)
- Docker (optional)

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd full-stack-todo
   ```

2. **Set up environment variables**

   **Frontend** (create `frontend/.env.local`):
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   BETTER_AUTH_SECRET=your-secret-key-min-32-chars
   ```

   **Backend** (create `backend/.env`):
   ```env
   DATABASE_URL=postgresql://user:pass@host.neon.tech/dbname
   BETTER_AUTH_SECRET=your-secret-key-min-32-chars
   OPENAI_API_KEY=sk-your-openai-api-key
   ```

3. **Install dependencies**

   **Frontend:**
   ```bash
   cd frontend
   npm install
   ```

   **Backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

### Running Locally

**Option 1: Run services separately**

```bash
# Terminal 1 - Frontend
cd frontend
npm run dev
# → http://localhost:3000

# Terminal 2 - Backend
cd backend
uvicorn app.main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs (API docs)
```

**Option 2: Run with Docker Compose**

```bash
docker-compose up
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest                    # Run all tests
pytest --cov             # With coverage report
pytest -v                # Verbose output
```

### Frontend Tests
```bash
cd frontend
npm test                 # Run tests
npm run test:watch      # Watch mode
```

## 🌐 API Documentation

Interactive API documentation available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### API Endpoints

```
GET    /api/{user_id}/tasks              List all tasks
POST   /api/{user_id}/tasks              Create task
GET    /api/{user_id}/tasks/{id}         Get task
PUT    /api/{user_id}/tasks/{id}         Update task
DELETE /api/{user_id}/tasks/{id}         Delete task
PATCH  /api/{user_id}/tasks/{id}/complete Toggle completion
```

## 📚 Development Workflow

### Spec-Driven Development

This project follows spec-driven development principles:

1. **Write Specification**
   ```bash
   # Use spec-writer skill
   "Use spec-writer skill to create task CRUD spec"
   ```

2. **Generate Code**
   ```bash
   # Backend
   "Use fastapi-sqlmodel skill from @specs/features/task-crud.md"

   # Frontend
   "Use nextjs-betterauth skill from @specs/ui/task-management.md"
   ```

3. **Test & Iterate**
   ```bash
   pytest
   npm test
   ```

4. **Document**
   ```bash
   /sp.phr  # Create Prompt History Record
   ```

## 🚀 Deployment

### Frontend (Vercel)

1. Push code to GitHub
2. Connect repository to Vercel
3. Set environment variables
4. Deploy

```bash
cd frontend
vercel deploy
```

### Backend (Render/Railway)

1. Connect GitHub repository
2. Set environment variables:
   - `DATABASE_URL`
   - `BETTER_AUTH_SECRET`
   - `OPENAI_API_KEY`
3. Deploy from main branch

## 📝 Documentation

- **Specifications:** `/specs/features/`
- **API Docs:** `/specs/api/rest-endpoints.md`
- **Database Schema:** `/specs/database/schema.md`
- **Frontend Guide:** `frontend/CLAUDE.md`
- **Backend Guide:** `backend/CLAUDE.md`
- **Constitution:** `.specify/memory/constitution.md`

## 🤝 Contributing

This project follows spec-driven development. All changes must:

1. Have a specification in `/specs`
2. Pass all tests
3. Include a PHR in `/history/prompts`
4. Follow code conventions in CLAUDE.md files

## 📋 Hackathon Submission

### Required Deliverables
- ✅ Public GitHub repository
- ✅ Deployed frontend (Vercel)
- ✅ Deployed backend (Render/Railway)
- ✅ Demo video (< 90 seconds)
- ✅ All specifications documented

### Submission Form
Submit at: https://forms.gle/KMKEKaFUD6ZX4UtY8

## 📄 License

MIT

---

**Built with spec-driven development using Claude Code!** 🚀
