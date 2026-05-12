from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.config import settings
from app.core.database import get_db, init_db
from app.schemas import HealthCheckResponse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="AI-powered government workforce integrity platform",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # MVP: Allow all. Production: Restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize app on startup."""
    logger.info("GhostShield AI backend starting...")
    
    # Initialize database tables
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
    
    # Load AI models
    logger.info("AI models loading...")
    # DeepFace loads on first use, so no explicit initialization needed
    logger.info("Startup complete")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    logger.info("GhostShield AI backend shutting down...")


# Health check endpoint
@app.get("/health", response_model=HealthCheckResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for monitoring.
    
    MVP: Simple health check
    Production: Add readiness probes, dependency checks
    """
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_connected = True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_connected = False
    
    return HealthCheckResponse(
        status="healthy" if db_connected else "degraded",
        environment=settings.ENVIRONMENT,
        timestamp=datetime.utcnow(),
        database_connected=db_connected,
        ai_models_loaded=True
    )


# Import routes (will be defined in separate files)
# These imports are commented for now since route files will be created separately

logger.info(f"GhostShield API initialized (env={settings.ENVIRONMENT})")
