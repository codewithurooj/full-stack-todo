"""Pytest configuration and fixtures"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

from app.main import app
from app.database import get_session


@pytest.fixture(name="session")
def session_fixture():
    """Create in-memory SQLite database for testing"""
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
def auth_headers(mock_jwt_token):
    """Create authorization headers with mock JWT token"""
    return {"Authorization": f"Bearer {mock_jwt_token}"}
