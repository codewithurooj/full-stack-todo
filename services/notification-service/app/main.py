"""
Notification Service
Feature 011: Consumes reminder events from Kafka and sends Web Push notifications to users
Feature 012: Supports Dapr pub/sub via HTTP endpoints (FastAPI mode)
"""
import asyncio
import signal
import sys
import logging
import os
from app.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global shutdown flag
shutdown_event = asyncio.Event()


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_event.set()


async def run_kafka_consumer():
    """Run the Kafka consumer (legacy mode)"""
    from app.consumer import NotificationConsumer

    logger.info(f"Starting {settings.SERVICE_NAME} in Kafka consumer mode")
    logger.info(f"Kafka bootstrap servers: {settings.KAFKA_BOOTSTRAP_SERVERS}")
    logger.info(f"Consumer group: {settings.CONSUMER_GROUP_ID}")
    logger.info(f"Topic: {settings.KAFKA_TOPIC}")
    logger.info(f"Batch window: {settings.BATCH_WINDOW_SECONDS}s")
    logger.info(f"Rate limit: {settings.RATE_LIMIT_PER_USER} per {settings.RATE_LIMIT_WINDOW_SECONDS}s")

    # Validate configuration
    if not settings.VAPID_PRIVATE_KEY:
        logger.error("VAPID_PRIVATE_KEY not set, notifications will not work!")

    # Initialize consumer
    consumer = NotificationConsumer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.CONSUMER_GROUP_ID,
        topic=settings.KAFKA_TOPIC
    )

    try:
        await consumer.start()
        await shutdown_event.wait()
    finally:
        logger.info("Shutting down consumer...")
        await consumer.stop()
        logger.info("Shutdown complete")


def create_fastapi_app():
    """Create FastAPI app for Dapr mode"""
    from fastapi import FastAPI
    from app.routes import router

    app = FastAPI(
        title="Notification Service",
        description="Notification service with Dapr pub/sub support",
        version="2.0.0"
    )
    app.include_router(router)

    @app.on_event("startup")
    async def startup_event():
        logger.info(f"Starting {settings.SERVICE_NAME} in Dapr/FastAPI mode")
        logger.info(f"Dapr HTTP port: {settings.DAPR_HTTP_PORT}")
        logger.info(f"Dapr pub/sub name: {settings.DAPR_PUBSUB_NAME}")

    return app


# Create FastAPI app instance for uvicorn
app = create_fastapi_app()


async def main():
    """Main entry point - choose mode based on DAPR_ENABLED"""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if settings.DAPR_ENABLED:
        # Dapr mode: Run as FastAPI app (started via uvicorn)
        logger.info("Dapr mode enabled - use uvicorn to start the service")
        logger.info("Example: uvicorn app.main:app --host 0.0.0.0 --port 8001")
    else:
        # Legacy mode: Run Kafka consumer directly
        try:
            await run_kafka_consumer()
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
