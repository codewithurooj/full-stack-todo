"""Application configuration management"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment variables"""

    DATABASE_URL: str
    BETTER_AUTH_SECRET: str
    OPENAI_API_KEY: str = ""

    # CORS settings
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "https://full-stack-todo-application-five.vercel.app"
    ]

    # API Settings
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "Todo API"
    PROJECT_VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
