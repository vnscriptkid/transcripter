import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import get_settings
from app.database import init_db, close_db

# Initialize settings (creates directories)
get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup: Initialize database
    await init_db()
    yield
    # Shutdown: Close database connections
    await close_db()


app = FastAPI(
    title="Video Transcription API",
    description="API for transcribing video files using OpenAI Whisper",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for frontend
# Get allowed origins from environment variable (comma-separated)
# Default to localhost for development
allowed_origins_str = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000"
)
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/health/db")
async def health_check_db():
    """Database health check endpoint."""
    try:
        from sqlalchemy import text
        from app.database import engine
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
