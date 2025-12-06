"""
Health check endpoints.
"""

from fastapi import APIRouter
from story_generator.database import db
from story_generator.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "service": "Fairy Story Generator API",
        "version": "1.0.0",
        "environment": settings.environment
    }


@router.get("/health/db")
async def database_health():
    """Check database connection."""
    db_healthy = await db.health_check()
    
    return {
        "database": "connected" if db_healthy else "disconnected",
        "status": "healthy" if db_healthy else "unhealthy"
    }