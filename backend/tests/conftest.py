"""Pytest configuration and fixtures"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool
from freezegun import freeze_time
from sqlalchemy import event, JSON, Text
from sqlalchemy.engine import Engine

from app.main import app
from app.database import get_session


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key constraints in SQLite"""
    if 'sqlite' in str(dbapi_conn):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


@pytest.fixture(name="session")
def session_fixture():
    """Create in-memory SQLite database for testing"""
    from app.models.task import Task
    from sqlalchemy import ARRAY, String, Column

    # Monkey-patch ARRAY columns to use JSON for SQLite testing
    for col_name, col in Task.__table__.columns.items():
        if hasattr(col.type, '__class__') and col.type.__class__.__name__ == 'ARRAY':
            # Replace ARRAY with JSON for SQLite
            col.type = JSON()

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create test client with database session override"""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()


@pytest.fixture
def mock_jwt_token():
    """Create a mock JWT token for testing"""
    import jwt
    from app.config import settings

    payload = {
        "sub": "test-user-123",
        "exp": 9999999999  # Far future expiration
    }

    token = jwt.encode(payload, settings.BETTER_AUTH_SECRET, algorithm="HS256")
    return token


@pytest.fixture
def mock_jwt():
    """Create a mock JWT token for user123"""
    import jwt
    from app.config import settings

    payload = {
        "sub": "user123",
        "exp": 9999999999  # Far future expiration
    }

    token = jwt.encode(payload, settings.BETTER_AUTH_SECRET, algorithm="HS256")
    return token


@pytest.fixture
def auth_headers(mock_jwt_token):
    """Create authorization headers with mock JWT token"""
    return {"Authorization": f"Bearer {mock_jwt_token}"}


@pytest.fixture
def freezer():
    """Fixture for freezing time in tests"""
    with freeze_time("2026-01-09 10:00:00") as frozen_time:
        yield frozen_time
