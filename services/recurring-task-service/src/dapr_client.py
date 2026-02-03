"""
Dapr Service Invocation Client for Recurring Task Service
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
DAPR_HTTP_PORT = int(os.getenv("DAPR_HTTP_PORT", "3502"))
DAPR_BASE_URL = f"http://{DAPR_HOST}:{DAPR_HTTP_PORT}"

# Service invocation configuration
DEFAULT_TIMEOUT = 30.0  # T064: Default 30s timeout
MAX_RETRIES = 3  # T065: Retry count
RETRY_BACKOFF = 1.0  # T065: Initial backoff


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
            app_id: Target service's Dapr app ID
            method: Method/path to invoke
            http_method: HTTP method
            data: Optional request body
            headers: Optional headers

        Returns:
            httpx.Response or None on error
        """
        url = f"{self.base_url}/v1.0/invoke/{app_id}/method/{method}"
        request_headers = headers or {}
        request_headers["Content-Type"] = "application/json"

        last_error = None

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
                        return None

                    if response.status_code < 500:
                        return response

                    last_error = f"HTTP {response.status_code}"

            except httpx.TimeoutException:
                last_error = "Timeout"
            except Exception as e:
                last_error = str(e)

            if attempt < self.max_retries - 1:
                import asyncio
                await asyncio.sleep(RETRY_BACKOFF * (2 ** attempt))

        logger.error(f"Service invocation failed: {app_id}/{method} - {last_error}")
        return None

    async def invoke_backend_service(
        self,
        method: str,
        http_method: str = "GET",
        data: Optional[Dict[str, Any]] = None
    ) -> Optional[httpx.Response]:
        """
        Invoke backend-service via Dapr (T062).

        Args:
            method: API method path
            http_method: HTTP method
            data: Optional request body

        Returns:
            Response or None on error
        """
        return await self.invoke_service(
            app_id="backend-service",
            method=method,
            http_method=http_method,
            data=data
        )

    async def create_recurring_task_instance(
        self,
        user_id: str,
        task_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new task instance via backend-service.

        Used when a recurring task is completed to create the next instance.

        Args:
            user_id: User who owns the task
            task_data: New task data

        Returns:
            Created task or None on error
        """
        response = await self.invoke_backend_service(
            method=f"api/{user_id}/tasks",
            http_method="POST",
            data=task_data
        )

        if response and response.status_code == 201:
            return response.json()

        logger.warning(f"Failed to create recurring task instance for user {user_id}")
        return None

    async def get_task_details(
        self,
        user_id: str,
        task_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get task details from backend-service"""
        response = await self.invoke_backend_service(
            method=f"api/{user_id}/tasks/{task_id}"
        )

        if response and response.status_code == 200:
            return response.json()

        return None


# Global instance
_service_client: Optional[DaprServiceClient] = None


def get_service_client() -> DaprServiceClient:
    """Get the global Dapr service client"""
    global _service_client
    if _service_client is None:
        _service_client = DaprServiceClient()
    return _service_client
