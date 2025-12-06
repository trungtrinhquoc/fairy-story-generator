"""
FastAPI application entry point.
Main application with routes and middleware setup.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from story_generator.config import settings
from story_generator.database import db
from story_generator.api.routes import health, stories

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =================================
# LIFESPAN CONTEXT
# =================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("🚀 Starting Story Generator API...")
    logger.info(f"📍 Environment: {settings.environment}")
    logger.info(f"🗄️  Supabase URL: {settings.supabase_url}")
    
    # Test database connection
    db_health = await db.health_check()
    if db_health:
        logger.info("✅ Database connection successful")
    else:
        logger.error("❌ Database connection failed!")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down Story Generator API...")


# =================================
# FASTAPI APP
# =================================
app = FastAPI(
    title="Fairy Story Generator API",
    description="AI-powered personalized fairy tale generator for children",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)


# =================================
# MIDDLEWARE
# =================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing."""
    start_time = time.time()
    
    # Log request
    logger.info(f"➡️  {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Log response
    logger.info(
        f"⬅️  {request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {duration:.2f}s"
    )
    
    return response


# =================================
# EXCEPTION HANDLERS
# =================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions."""
    logger.error(f"❌ Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.is_development else "An error occurred",
            "path": str(request.url.path)
        }
    )


# =================================
# INCLUDE ROUTERS
# =================================

# Health check routes
app.include_router(
    health.router,
    tags=["Health"]
)

# Story generation routes
app.include_router(
    stories.router,
    prefix="/api/v1/stories",
    tags=["Stories"]
)


# =================================
# ROOT ENDPOINT
# =================================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Fairy Story Generator API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.environment,
        "endpoints": {
            "docs": "/docs" if settings.is_development else "disabled",
            "health": "/health",
            "stories": "/api/v1/stories"
        }
    }


# =================================
# RUN WITH UVICORN
# =================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.log_level.lower()
    )