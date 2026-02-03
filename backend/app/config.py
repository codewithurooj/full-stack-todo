"""Application configuration management"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment variables"""

    DATABASE_URL: str
    BETTER_AUTH_SECRET: str
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    CHAT_SYSTEM_PROMPT: str = "You are a helpful AI assistant for task management. You can create, list, update, complete, and delete tasks for users. Be concise and friendly."
    CHAT_HISTORY_LIMIT: int = 50

    # CORS settings
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "https://full-stack-todo-application-five.vercel.app",
        "https://135.235.185.11.nip.io",
        "http://135.235.185.11.nip.io"
    ]

    # API Settings
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "Todo API"
    PROJECT_VERSION: str = "1.0.0"

    # Kafka Settings (Feature 011)
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:19092"
    KAFKA_SASL_USERNAME: str = ""
    KAFKA_SASL_PASSWORD: str = ""
    KAFKA_SECURITY_PROTOCOL: str = "PLAINTEXT"

    # Web Push Settings (Feature 011)
    VAPID_PRIVATE_KEY: str = ""
    VAPID_PUBLIC_KEY: str = ""
    VAPID_SUBJECT: str = "mailto:admin@example.com"

    # Dapr Settings (Feature 012)
    DAPR_HOST: str = "localhost"
    DAPR_HTTP_PORT: int = 3500
    DAPR_GRPC_PORT: int = 50001
    DAPR_PUBSUB_NAME: str = "kafka-pubsub"
    DAPR_STATESTORE_NAME: str = "statestore"
    DAPR_SECRETS_STORE_NAME: str = "kubernetes-secrets"
    DAPR_ENABLED: bool = False  # Set to True when running with Dapr sidecar

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
