"""
Dapr Service Invocation Client for Notification Service
Feature: 012-dapr-integration
Purpose: Invoke backend-service methods via Dapr service invocation API
"""
import logging
import os
from typing import Any, Dict, Optional
import httpx

logger = logging.getLogger(__name__)

# Dapr configuration
DAPR_HOST = os.getenv("DAPR_HOST", "localhost")
DAPR_HTTP_PORT = int(os.getenv("DAPR_HTTP_PORT", "3501"))
DAPR_BASE_URL = f"http://{DAPR_HOST}:{DAPR_HTTP_PORT}"

# Service invocation configuration
DEFAULT_TIMEOUT = 30.0  # T064: Default 30s timeout
MAX_RETRIES = 3  # T065: Retry count
RETRY_BACKOFF = 1.0  # T065: Initial backoff in seconds


class DaprServiceClient:
    """
    Dapr service invocation client for calling backend-service.

    Implements:
    - Service invocation via Dapr HTTP API
    - Timeout configuration (T064)
    - Retry with exponential backoff (T065)
    """

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES
    ):
        self.base_url = DAPR_BASE_URL
        self.timeout = timeout
        self.max_retries = max_retries

    async def invoke_service(
        self,
        app_id: str,
        method: str,
        http_method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Optional[httpx.Response]:
        """
        Invoke a method on another service via Dapr.

        Args:
            app_id: Target service's Dapr app ID (e.g., "backend-service")
            method: Method/path to invoke (e.g., "api/user123/tasks/1")
            http_method: HTTP method (GET, POST, PUT, DELETE)
            data: Optional request body for POST/PUT
            headers: Optional additional headers

        Returns:
            httpx.Response or None on error
        """
        url = f"{self.base_url}/v1.0/invoke/{app_id}/method/{method}"
        request_headers = headers or {}
        request_headers["Content-Type"] = "application/json"

        last_error = None

        # Retry with exponential backoff (T065)
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
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

                    # Check for success
                    if response.status_code < 500:
                        return response

                    # Server error - retry
                    last_error = f"HTTP {response.status_code}"
                    logger.warning(
                        f"Service invocation failed (attempt {attempt + 1}/{self.max_retries}): "
                        f"{app_id}/{method} - {last_error}"
                    )

            except httpx.TimeoutException as e:
                last_error = f"Timeout: {e}"
                logger.warning(
                    f"Service invocation timeout (attempt {attempt + 1}/{self.max_retries}): "
                    f"{app_id}/{method}"
                )
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Service invocation error (attempt {attempt + 1}/{self.max_retries}): "
                    f"{app_id}/{method} - {e}"
                )

            # Exponential backoff before retry
            if attempt < self.max_retries - 1:
                import asyncio
                backoff = RETRY_BACKOFF * (2 ** attempt)
                await asyncio.sleep(backoff)

        logger.error(f"Service invocation failed after {self.max_retries} attempts: {last_error}")
        return None

    async def get_task_details(
        self,
        user_id: str,
        task_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get task details from backend-service via Dapr service invocation (T058).

        Args:
            user_id: User who owns the task
            task_id: Task ID to retrieve

        Returns:
            Task details dict or None if not found/error
        """
        response = await self.invoke_service(
            app_id="backend-service",
            method=f"api/{user_id}/tasks/{task_id}",
            http_method="GET"
        )

        if response and response.status_code == 200:
            return response.json()

        logger.warning(f"Failed to get task details: user={user_id}, task_id={task_id}")
        return None

    async def get_user_tasks(
        self,
        user_id: str
    ) -> Optional[list[Dict[str, Any]]]:
        """
        Get all tasks for a user from backend-service.

        Args:
            user_id: User ID

        Returns:
            List of task dicts or None on error
        """
        response = await self.invoke_service(
            app_id="backend-service",
            method=f"api/{user_id}/tasks",
            http_method="GET"
        )

        if response and response.status_code == 200:
            data = response.json()
            return data.get("tasks", [])

        return None


# Global instance
_service_client: Optional[DaprServiceClient] = None


def get_service_client() -> DaprServiceClient:
    """Get the global Dapr service client"""
    global _service_client
    if _service_client is None:
        _service_client = DaprServiceClient()
    return _service_client
