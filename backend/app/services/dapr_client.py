"""
Dapr HTTP Client Wrapper
Feature: 012-dapr-integration
Purpose: Provides HTTP-based access to Dapr sidecar APIs for pub/sub, state, jobs, secrets, and service invocation
"""
import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)

# Dapr configuration from environment
DAPR_HOST = os.getenv("DAPR_HOST", "localhost")
DAPR_HTTP_PORT = int(os.getenv("DAPR_HTTP_PORT", "3500"))
DAPR_BASE_URL = f"http://{DAPR_HOST}:{DAPR_HTTP_PORT}"

# Default timeouts
DEFAULT_TIMEOUT = 10.0
HEALTH_CHECK_TIMEOUT = 2.0


class DaprClient:
    """
    HTTP client wrapper for Dapr sidecar APIs.
    Uses httpx for async HTTP calls to Dapr sidecar.
    """

    def __init__(
        self,
        host: str = DAPR_HOST,
        http_port: int = DAPR_HTTP_PORT,
        timeout: float = DEFAULT_TIMEOUT
    ):
        self.host = host
        self.http_port = http_port
        self.base_url = f"http://{host}:{http_port}"
        self.timeout = timeout
        self._is_healthy: Optional[bool] = None
        self._last_health_check: Optional[datetime] = None

    async def check_health(self) -> bool:
        """
        Check if Dapr sidecar is healthy and available.

        Returns:
            True if Dapr sidecar is healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=HEALTH_CHECK_TIMEOUT) as client:
                response = await client.get(f"{self.base_url}/v1.0/healthz")
                self._is_healthy = response.status_code == 204
                self._last_health_check = datetime.utcnow()
                return self._is_healthy
        except Exception as e:
            logger.warning(f"Dapr health check failed: {e}")
            self._is_healthy = False
            self._last_health_check = datetime.utcnow()
            return False

    @property
    def is_healthy(self) -> bool:
        """Return cached health status (call check_health() for fresh check)"""
        return self._is_healthy if self._is_healthy is not None else False

    async def get_metadata(self) -> Optional[Dict[str, Any]]:
        """
        Get Dapr sidecar metadata including registered components.

        Returns:
            Metadata dict or None if unavailable
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/v1.0/metadata")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Failed to get Dapr metadata: {e}")
        return None

    # ==================== Pub/Sub APIs ====================

    async def publish_event(
        self,
        pubsub_name: str,
        topic: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Publish an event to a Dapr pub/sub topic.

        Args:
            pubsub_name: Name of the pub/sub component (e.g., "kafka-pubsub")
            topic: Topic to publish to (e.g., "task-events")
            data: Event payload as dict
            metadata: Optional CloudEvent metadata

        Returns:
            True if publish succeeded, False otherwise
        """
        try:
            headers = {"Content-Type": "application/json"}
            if metadata:
                for key, value in metadata.items():
                    headers[f"ce-{key}"] = value

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/v1.0/publish/{pubsub_name}/{topic}",
                    json=data,
                    headers=headers
                )
                if response.status_code in (200, 204):
                    logger.debug(f"Published event to {pubsub_name}/{topic}")
                    return True
                else:
                    logger.error(
                        f"Failed to publish event to {pubsub_name}/{topic}: "
                        f"{response.status_code} - {response.text}"
                    )
                    return False
        except Exception as e:
            logger.error(f"Error publishing event to {pubsub_name}/{topic}: {e}")
            return False

    # ==================== State Store APIs ====================

    async def save_state(
        self,
        store_name: str,
        key: str,
        value: Any,
        etag: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Save state to a Dapr state store.

        Args:
            store_name: Name of the state store component (e.g., "statestore")
            key: State key
            value: State value (will be JSON serialized)
            etag: Optional etag for optimistic concurrency
            metadata: Optional state metadata

        Returns:
            True if save succeeded, False otherwise
        """
        try:
            state_item = {"key": key, "value": value}
            if etag:
                state_item["etag"] = etag
                state_item["options"] = {"concurrency": "first-write-wins"}
            if metadata:
                state_item["metadata"] = metadata

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/v1.0/state/{store_name}",
                    json=[state_item]
                )
                if response.status_code in (200, 201, 204):
                    logger.debug(f"Saved state to {store_name}/{key}")
                    return True
                else:
                    logger.error(
                        f"Failed to save state to {store_name}/{key}: "
                        f"{response.status_code} - {response.text}"
                    )
                    return False
        except Exception as e:
            logger.error(f"Error saving state to {store_name}/{key}: {e}")
            return False

    async def get_state(
        self,
        store_name: str,
        key: str
    ) -> tuple[Optional[Any], Optional[str]]:
        """
        Get state from a Dapr state store.

        Args:
            store_name: Name of the state store component
            key: State key

        Returns:
            Tuple of (value, etag) or (None, None) if not found
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/v1.0/state/{store_name}/{key}"
                )
                if response.status_code == 200:
                    etag = response.headers.get("ETag")
                    return response.json(), etag
                elif response.status_code == 204:
                    return None, None
                else:
                    logger.warning(
                        f"Failed to get state from {store_name}/{key}: "
                        f"{response.status_code}"
                    )
                    return None, None
        except Exception as e:
            logger.error(f"Error getting state from {store_name}/{key}: {e}")
            return None, None

    async def delete_state(
        self,
        store_name: str,
        key: str,
        etag: Optional[str] = None
    ) -> bool:
        """
        Delete state from a Dapr state store.

        Args:
            store_name: Name of the state store component
            key: State key
            etag: Optional etag for concurrency

        Returns:
            True if delete succeeded, False otherwise
        """
        try:
            headers = {}
            if etag:
                headers["If-Match"] = etag

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(
                    f"{self.base_url}/v1.0/state/{store_name}/{key}",
                    headers=headers
                )
                if response.status_code in (200, 204):
                    logger.debug(f"Deleted state from {store_name}/{key}")
                    return True
                else:
                    logger.error(
                        f"Failed to delete state from {store_name}/{key}: "
                        f"{response.status_code}"
                    )
                    return False
        except Exception as e:
            logger.error(f"Error deleting state from {store_name}/{key}: {e}")
            return False

    # ==================== Jobs API (v1.0-alpha1) ====================

    async def schedule_job(
        self,
        job_name: str,
        due_time: datetime,
        data: Dict[str, Any],
        ttl: Optional[str] = None
    ) -> bool:
        """
        Schedule a job using Dapr Jobs API.

        Args:
            job_name: Unique job identifier
            due_time: When the job should execute
            data: Job payload
            ttl: Optional time-to-live (e.g., "24h")

        Returns:
            True if job scheduled successfully, False otherwise
        """
        try:
            import json
            job_request = {
                "dueTime": due_time.isoformat() + "Z",
                "data": {
                    "@type": "type.googleapis.com/google.protobuf.StringValue",
                    "value": json.dumps(data)
                }
            }
            if ttl:
                job_request["ttl"] = ttl

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/v1.0-alpha1/jobs/{job_name}",
                    json=job_request
                )
                if response.status_code in (200, 201, 204):
                    logger.debug(f"Scheduled job: {job_name} for {due_time}")
                    return True
                else:
                    logger.error(
                        f"Failed to schedule job {job_name}: "
                        f"{response.status_code} - {response.text}"
                    )
                    return False
        except Exception as e:
            logger.error(f"Error scheduling job {job_name}: {e}")
            return False

    async def cancel_job(self, job_name: str) -> bool:
        """
        Cancel a scheduled job.

        Args:
            job_name: Job identifier to cancel

        Returns:
            True if job cancelled successfully, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(
                    f"{self.base_url}/v1.0-alpha1/jobs/{job_name}"
                )
                if response.status_code in (200, 204, 404):
                    logger.debug(f"Cancelled job: {job_name}")
                    return True
                else:
                    logger.error(
                        f"Failed to cancel job {job_name}: "
                        f"{response.status_code}"
                    )
                    return False
        except Exception as e:
            logger.error(f"Error cancelling job {job_name}: {e}")
            return False

    # ==================== Secrets API ====================

    async def get_secret(
        self,
        store_name: str,
        secret_name: str,
        key: Optional[str] = None
    ) -> Optional[str]:
        """
        Get a secret from a Dapr secrets store.

        Args:
            store_name: Name of the secrets store component (e.g., "kubernetes-secrets")
            secret_name: Name of the secret
            key: Optional specific key within the secret

        Returns:
            Secret value as string, or None if not found
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/v1.0/secrets/{store_name}/{secret_name}"
                )
                if response.status_code == 200:
                    secrets = response.json()
                    if key:
                        return secrets.get(key)
                    # Return first value if no key specified
                    return list(secrets.values())[0] if secrets else None
                else:
                    logger.warning(
                        f"Failed to get secret {store_name}/{secret_name}: "
                        f"{response.status_code}"
                    )
                    return None
        except Exception as e:
            logger.error(f"Error getting secret {store_name}/{secret_name}: {e}")
            return None

    # ==================== Service Invocation API ====================

    async def invoke_service(
        self,
        app_id: str,
        method: str,
        http_method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Optional[httpx.Response]:
        """
        Invoke a method on another service via Dapr service invocation.

        Args:
            app_id: Target service's Dapr app ID
            method: Method/path to invoke (e.g., "api/user123/tasks")
            http_method: HTTP method (GET, POST, PUT, DELETE)
            data: Optional request body for POST/PUT
            headers: Optional additional headers

        Returns:
            httpx.Response object or None on error
        """
        try:
            request_headers = headers or {}
            request_headers["Content-Type"] = "application/json"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.base_url}/v1.0/invoke/{app_id}/method/{method}"

                if http_method.upper() == "GET":
                    response = await client.get(url, headers=request_headers)
                elif http_method.upper() == "POST":
                    response = await client.post(url, json=data, headers=request_headers)
                elif http_method.upper() == "PUT":
                    response = await client.put(url, json=data, headers=request_headers)
                elif http_method.upper() == "DELETE":
                    response = await client.delete(url, headers=request_headers)
                else:
                    logger.error(f"Unsupported HTTP method: {http_method}")
                    return None

                return response
        except Exception as e:
            logger.error(f"Error invoking {app_id}/{method}: {e}")
            return None


# Global Dapr client instance
_dapr_client: Optional[DaprClient] = None


def get_dapr_client() -> DaprClient:
    """Get or create the global Dapr client instance."""
    global _dapr_client
    if _dapr_client is None:
        _dapr_client = DaprClient()
    return _dapr_client


async def check_dapr_health() -> bool:
    """Check Dapr sidecar health using the global client."""
    client = get_dapr_client()
    return await client.check_health()
