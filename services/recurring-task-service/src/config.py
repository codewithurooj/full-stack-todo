"""
Recurring Task Service Configuration
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Service configuration from environment variables"""

    # Service metadata
    SERVICE_NAME: str = "recurring-task-service"
    LOG_LEVEL: str = "INFO"

    # Kafka configuration
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092")
    KAFKA_TOPIC: str = os.getenv("KAFKA_TOPIC", "task-events")
    CONSUMER_GROUP_ID: str = os.getenv("CONSUMER_GROUP_ID", "recurring-task-service-group")

    # Kafka SASL authentication (optional)
    KAFKA_SASL_USERNAME: str = os.getenv("KAFKA_SASL_USERNAME", "")
    KAFKA_SASL_PASSWORD: str = os.getenv("KAFKA_SASL_PASSWORD", "")
    KAFKA_SECURITY_PROTOCOL: str = os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")

    # Database configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # Service configuration
    MAX_RETRIES: int = 3  # Max retries for transient failures
    RETRY_BACKOFF_BASE: float = 1.0  # Exponential backoff base (seconds)

    # Dapr Settings (Feature 012)
    DAPR_HOST: str = os.getenv("DAPR_HOST", "localhost")
    DAPR_HTTP_PORT: int = int(os.getenv("DAPR_HTTP_PORT", "3502"))
    DAPR_PUBSUB_NAME: str = os.getenv("DAPR_PUBSUB_NAME", "kafka-pubsub")
    DAPR_ENABLED: bool = os.getenv("DAPR_ENABLED", "false").lower() == "true"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
