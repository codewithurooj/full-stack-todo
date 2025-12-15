"""FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from app.config import settings
from app.database import engine
from app.routes import tasks, auth

# Create database tables
SQLModel.metadata.create_all(engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Full-Stack Todo Application API - Phase 2",
    version=settings.PROJECT_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

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


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Todo API - Phase 2",
        "version": settings.PROJECT_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
