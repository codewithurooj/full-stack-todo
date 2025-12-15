# Todo API - Backend

FastAPI backend for the Full-Stack Todo Application (Hackathon II Phase 2).

## Quick Start

### Prerequisites
- Python 3.13+
- Neon PostgreSQL database

### Installation

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Unix/MacOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create `.env` file:
```env
DATABASE_URL=postgresql://user:password@host.neon.tech/dbname
BETTER_AUTH_SECRET=your-secret-key-min-32-chars
OPENAI_API_KEY=sk-your-openai-api-key
```

### Running

```bash
# Development server with auto-reload
uvicorn app.main:app --reload

# Custom host and port
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Production with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### API Documentation

Once running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## API Endpoints

### Tasks

```
GET    /api/{user_id}/tasks              List all tasks
POST   /api/{user_id}/tasks              Create new task
GET    /api/{user_id}/tasks/{id}         Get task details
PUT    /api/{user_id}/tasks/{id}         Update task
DELETE /api/{user_id}/tasks/{id}         Delete task
PATCH  /api/{user_id}/tasks/{id}/complete Toggle completion
```

### Authentication

All endpoints require JWT token in header:
```
Authorization: Bearer <jwt-token>
```

The `user_id` in the path must match the user ID in the JWT token.

## Testing

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=app

# Verbose output
pytest -v

# Specific test file
pytest tests/test_tasks.py
```

## Code Quality

```bash
# Linting
ruff check app/

# Type checking
mypy app/

# Format code
ruff format app/
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app
│   ├── config.py         # Settings
│   ├── database.py       # DB session
│   ├── models/           # SQLModel models
│   ├── routes/           # API endpoints
│   ├── services/         # Business logic
│   ├── middleware/       # Auth middleware
│   └── utils/            # Utilities
├── tests/                # Pytest tests
├── requirements.txt      # Dependencies
├── pyproject.toml        # Project config
└── .env                  # Environment vars
```

## Development Guidelines

See `CLAUDE.md` for detailed development patterns and best practices.

## Deployment

### Render/Railway

1. Connect GitHub repository
2. Set environment variables (DATABASE_URL, BETTER_AUTH_SECRET)
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Security

- JWT verification on all endpoints
- User ID validation (path matches JWT)
- Environment-based secrets
- SQL injection prevention (SQLModel)
- CORS configuration

---

For detailed API documentation and examples, see `CLAUDE.md`.
