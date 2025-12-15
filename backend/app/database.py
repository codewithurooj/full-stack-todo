"""Database engine and session management"""
from sqlmodel import create_engine, Session
from app.config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=True,  # SQL logging in development
    pool_pre_ping=True,  # Verify connections before using
    pool_size=5,
    max_overflow=10
)


def get_session():
    """Database session dependency for FastAPI routes"""
    with Session(engine) as session:
        yield session
