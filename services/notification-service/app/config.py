"""
Service configuration
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Service configuration from environment variables"""

    # Service metadata
    SERVICE_NAME: str = "notification-service"
    LOG_LEVEL: str = "INFO"

    # Kafka configuration
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_TOPIC: str = os.getenv("KAFKA_TOPIC", "reminders")
    CONSUMER_GROUP_ID: str = os.getenv("CONSUMER_GROUP_ID", "notification-service")

    # Database configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # Web Push configuration
    VAPID_PUBLIC_KEY: str = os.getenv("VAPID_PUBLIC_KEY", "")
    VAPID_PRIVATE_KEY: str = os.getenv("VAPID_PRIVATE_KEY", "")
    VAPID_CLAIMS_EMAIL: str = os.getenv("VAPID_CLAIMS_EMAIL", "mailto:admin@example.com")

    # Notification settings
    BATCH_WINDOW_SECONDS: int = int(os.getenv("BATCH_WINDOW_SECONDS", "120"))  # 2 minutes
    RATE_LIMIT_PER_USER: int = int(os.getenv("RATE_LIMIT_PER_USER", "10"))  # 10 per minute
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))  # 1 minute

    # Dapr Settings (Feature 012)
    DAPR_HOST: str = os.getenv("DAPR_HOST", "localhost")
    DAPR_HTTP_PORT: int = int(os.getenv("DAPR_HTTP_PORT", "3501"))
    DAPR_PUBSUB_NAME: str = os.getenv("DAPR_PUBSUB_NAME", "kafka-pubsub")
    DAPR_ENABLED: bool = os.getenv("DAPR_ENABLED", "false").lower() == "true"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
