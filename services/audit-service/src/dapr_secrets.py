"""
Dapr Secrets Module for Audit Service
Feature: 012-dapr-integration
Purpose: Retrieve secrets from Kubernetes via Dapr secrets component
"""
import logging
import os
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

# Dapr configuration
DAPR_HOST = os.getenv("DAPR_HOST", "localhost")
DAPR_HTTP_PORT = int(os.getenv("DAPR_HTTP_PORT", "3503"))
DAPR_BASE_URL = f"http://{DAPR_HOST}:{DAPR_HTTP_PORT}"
DEFAULT_SECRETS_STORE = "kubernetes-secrets"


class DaprSecretsClient:
    """Simple Dapr secrets client for microservices"""

    def __init__(self, store_name: str = DEFAULT_SECRETS_STORE):
        self.store_name = store_name
        self.base_url = DAPR_BASE_URL
        self._cache: dict[str, str] = {}

    async def get_secret(
        self,
        secret_name: str,
        key: Optional[str] = None,
        env_var_fallback: Optional[str] = None,
        default: Optional[str] = None
    ) -> Optional[str]:
        """
        Get a secret from Dapr with env var fallback.

        Args:
            secret_name: Kubernetes secret name
            key: Key within the secret
            env_var_fallback: Env var to use if Dapr unavailable
            default: Default value if not found

        Returns:
            Secret value or default
        """
        cache_key = f"{secret_name}:{key or ''}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        # Try Dapr
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_url}/v1.0/secrets/{self.store_name}/{secret_name}"
                )
                if response.status_code == 200:
                    secrets = response.json()
                    value = secrets.get(key) if key else list(secrets.values())[0]
                    if value:
                        self._cache[cache_key] = value
                        return value
        except Exception as e:
            logger.warning(f"Dapr secrets unavailable: {e}")

        # Fallback to env var
        fallback_var = env_var_fallback or key
        if fallback_var:
            env_value = os.getenv(fallback_var)
            if env_value:
                logger.warning(f"Using env var {fallback_var} as fallback")
                return env_value

        return default

    async def get_database_url(self) -> Optional[str]:
        """Get database connection URL"""
        return await self.get_secret(
            "postgres-credentials", "connectionString", "DATABASE_URL"
        )


# Global instance
_secrets_client: Optional[DaprSecretsClient] = None


def get_secrets_client() -> DaprSecretsClient:
    """Get the global secrets client"""
    global _secrets_client
    if _secrets_client is None:
        _secrets_client = DaprSecretsClient()
    return _secrets_client
