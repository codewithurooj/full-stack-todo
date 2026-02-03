"""
Dapr Subscription Endpoints
Feature: 012-dapr-integration
Purpose: Dapr subscription configuration endpoint (backend is publisher-only, returns empty list)
"""
import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dapr"])


@router.get("/dapr/subscribe")
async def dapr_subscribe():
    """
    Dapr subscription configuration endpoint.

    The backend service is a publisher only - it does not consume events from Kafka.
    Returns an empty list to indicate no subscriptions.

    Consumers (notification-service, recurring-task-service, audit-service)
    will have their own subscription endpoints.

    Returns:
        Empty list indicating no subscriptions for this service
    """
    logger.debug("Dapr subscription endpoint called - returning empty list (publisher only)")
    return []
