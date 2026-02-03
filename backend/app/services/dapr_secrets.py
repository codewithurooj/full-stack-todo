"""
Dapr Secrets Management Service
Feature: 012-dapr-integration
Purpose: Retrieve secrets from Kubernetes via Dapr secrets component with env var fallback
"""
import logging
import os
from typing import Optional

from app.services.dapr_client import get_dapr_client

logger = logging.getLogger(__name__)

# Default secrets store name
DEFAULT_SECRETS_STORE = "kubernetes-secrets"


class DaprSecretsService:
    """
    Service for retrieving secrets via Dapr secrets API.

    Falls back to environment variables when Dapr is unavailable,
    with warning logging to indicate the fallback.
    """

    def __init__(self, store_name: str = DEFAULT_SECRETS_STORE):
        self.store_name = store_name
        self._client = None
        self._cache: dict[str, str] = {}  # Simple in-memory cache

    @property
    def client(self):
        """Lazy load Dapr client"""
        if self._client is None:
            self._client = get_dapr_client()
        return self._client

    async def get_secret(
        self,
        secret_name: str,
        key: Optional[str] = None,
        env_var_fallback: Optional[str] = None,
        default: Optional[str] = None
    ) -> Optional[str]:
        """
        Get a secret from Dapr secrets store with environment variable fallback.

        Args:
            secret_name: Name of the Kubernetes secret (e.g., "app-secrets")
            key: Key within the secret (e.g., "OPENAI_API_KEY")
            env_var_fallback: Environment variable to use as fallback
            default: Default value if secret not found anywhere

        Returns:
            Secret value or default if not found
        """
        cache_key = f"{secret_name}:{key or ''}"

        # Check cache first
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Try Dapr first
        try:
            value = await self.client.get_secret(
                store_name=self.store_name,
                secret_name=secret_name,
                key=key
            )
            if value:
                self._cache[cache_key] = value
                logger.debug(f"Retrieved secret {secret_name}/{key} from Dapr")
                return value
        except Exception as e:
            logger.warning(
                f"Failed to get secret {secret_name}/{key} from Dapr: {e}. "
                f"Falling back to environment variables."
            )

        # Fallback to environment variable (T045, T046)
        fallback_var = env_var_fallback or key
        if fallback_var:
            env_value = os.getenv(fallback_var)
            if env_value:
                logger.warning(
                    f"Using environment variable {fallback_var} instead of "
                    f"Dapr secret {secret_name}/{key}"
                )
                self._cache[cache_key] = env_value
                return env_value

        # Return default
        if default is not None:
            logger.debug(
                f"Secret {secret_name}/{key} not found, using default value"
            )
            return default

        logger.warning(f"Secret {secret_name}/{key} not found and no default provided")
        return None

    async def get_database_url(self) -> Optional[str]:
        """Get database connection URL (T048)"""
        return await self.get_secret(
            secret_name="postgres-credentials",
            key="connectionString",
            env_var_fallback="DATABASE_URL"
        )

    async def get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key (T047)"""
        return await self.get_secret(
            secret_name="app-secrets",
            key="OPENAI_API_KEY",
            env_var_fallback="OPENAI_API_KEY"
        )

    async def get_auth_secret(self) -> Optional[str]:
        """Get Better Auth secret (T049)"""
        return await self.get_secret(
            secret_name="app-secrets",
            key="BETTER_AUTH_SECRET",
            env_var_fallback="BETTER_AUTH_SECRET"
        )

    async def get_vapid_keys(self) -> tuple[Optional[str], Optional[str]]:
        """Get VAPID keys for web push notifications"""
        private_key = await self.get_secret(
            secret_name="app-secrets",
            key="VAPID_PRIVATE_KEY",
            env_var_fallback="VAPID_PRIVATE_KEY"
        )
        public_key = await self.get_secret(
            secret_name="app-secrets",
            key="VAPID_PUBLIC_KEY",
            env_var_fallback="VAPID_PUBLIC_KEY"
        )
        return private_key, public_key

    async def get_kafka_credentials(self) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Get Kafka connection credentials"""
        brokers = await self.get_secret(
            secret_name="kafka-credentials",
            key="brokers",
            env_var_fallback="KAFKA_BOOTSTRAP_SERVERS"
        )
        username = await self.get_secret(
            secret_name="kafka-credentials",
            key="username",
            env_var_fallback="KAFKA_SASL_USERNAME"
        )
        password = await self.get_secret(
            secret_name="kafka-credentials",
            key="password",
            env_var_fallback="KAFKA_SASL_PASSWORD"
        )
        return brokers, username, password

    def clear_cache(self):
        """Clear the secrets cache (for testing or secret rotation)"""
        self._cache.clear()
        logger.info("Secrets cache cleared")


# Global secrets service instance
_secrets_service: Optional[DaprSecretsService] = None


def get_secrets_service() -> DaprSecretsService:
    """Get the global Dapr secrets service instance"""
    global _secrets_service
    if _secrets_service is None:
        _secrets_service = DaprSecretsService()
    return _secrets_service
