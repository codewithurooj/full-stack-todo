"""FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
import logging

from app.config import settings
from app.database import engine
from app.routes import tasks, auth, mcp, chat, due_dates, reminders, recurring, dapr_subscriptions
from app.mcp_server.server import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Scheduler imports
from app.jobs.scheduler import start_scheduler, shutdown_scheduler, add_job
from app.jobs.reminder_processor import process_due_reminders, retry_failed_reminders
from app.jobs.recurring_generator import generate_due_instances

# Kafka imports (Feature 011)
from app.services.kafka_producer import KafkaProducerService
from app.services import event_publisher

# Dapr imports (Feature 012)
from app.services.dapr_client import get_dapr_client, check_dapr_health

logger = logging.getLogger(__name__)

# Create database tables
SQLModel.metadata.create_all(engine)

# Initialize Kafka producer (Feature 011)
kafka_producer = KafkaProducerService()
event_publisher.set_producer(kafka_producer)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Full-Stack Todo Application API - Phase V",
    version=settings.PROJECT_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(due_dates.router)
app.include_router(reminders.router)
app.include_router(recurring.router)
app.include_router(mcp.router)
app.include_router(chat.router)
app.include_router(dapr_subscriptions.router)


# Startup event - Initialize scheduler and Kafka producer
@app.on_event("startup")
async def startup_event():
    """Initialize scheduler, Kafka producer, Dapr sidecar, and background jobs on application startup"""
    logger.info("Application startup: initializing scheduler, Kafka producer, and Dapr sidecar")

    # Check Dapr sidecar health (Feature 012)
    if settings.DAPR_ENABLED:
        try:
            dapr_healthy = await check_dapr_health()
            if dapr_healthy:
                logger.info("Dapr sidecar is healthy and available")
            else:
                logger.warning("Dapr sidecar is not available - will use fallback mechanisms")
        except Exception as e:
            logger.warning(f"Could not check Dapr sidecar health: {e}")

    # Start Kafka producer (Feature 011)
    try:
        await kafka_producer.start()
        logger.info("Kafka producer started successfully")
    except Exception as e:
        logger.error(f"Failed to start Kafka producer: {e}")
        logger.warning("Application will continue without event publishing")

    # Start scheduler
    start_scheduler()

    # Add reminder processor job (runs every 30 seconds)
    add_job(
        func=process_due_reminders,
        trigger='interval',
        seconds=30,
        id='process_due_reminders',
        replace_existing=True
    )
    logger.info("Added job: process_due_reminders (every 30 seconds)")

    # Add retry job (runs every 5 minutes)
    add_job(
        func=retry_failed_reminders,
        trigger='interval',
        minutes=5,
        id='retry_failed_reminders',
        replace_existing=True
    )
    logger.info("Added job: retry_failed_reminders (every 5 minutes)")

    # Add recurring task generator job (runs every 1 minute)
    add_job(
        func=generate_due_instances,
        trigger='interval',
        minutes=1,
        id='recurring_generator',
        replace_existing=True
    )
    logger.info("Added job: recurring_generator (every 1 minute)")

    logger.info("Application startup complete")


# Shutdown event - Cleanup scheduler and Kafka producer
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown scheduler and Kafka producer gracefully on application shutdown"""
    logger.info("Application shutdown: cleaning up scheduler and Kafka producer")

    # Stop Kafka producer (Feature 011)
    try:
        await kafka_producer.stop()
        logger.info("Kafka producer stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping Kafka producer: {e}")

    # Stop scheduler
    shutdown_scheduler()
    logger.info("Application shutdown complete")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Todo API - Phase V: Event-Driven Architecture",
        "version": settings.PROJECT_VERSION,
        "docs": "/docs",
        "features": {
            "kafka_events": kafka_producer.is_started,
            "scheduler_jobs": True
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint with Kafka producer and Dapr status"""
    # Calculate average latency
    avg_latency_ms = 0
    if kafka_producer.publish_count > 0:
        avg_latency_ms = (kafka_producer.total_latency / kafka_producer.publish_count) * 1000

    # Check Dapr sidecar health (Feature 012)
    dapr_status = "disabled"
    if settings.DAPR_ENABLED:
        dapr_healthy = await check_dapr_health()
        dapr_status = "healthy" if dapr_healthy else "unavailable"

    return {
        "status": "healthy",
        "kafka_producer": {
            "status": "healthy" if kafka_producer.is_started else "unavailable",
            "metrics": {
                "publish_count": kafka_producer.publish_count,
                "error_count": kafka_producer.error_count,
                "avg_latency_ms": round(avg_latency_ms, 2)
            }
        },
        "dapr": {
            "enabled": settings.DAPR_ENABLED,
            "status": dapr_status,
            "http_port": settings.DAPR_HTTP_PORT
        }
    }
