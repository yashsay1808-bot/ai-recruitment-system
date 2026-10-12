"""
Main FastAPI Application Entrypoint
Exposes the modern RESTful API for the AI Recruitment Platform.
Integrates:
- Job vacancy management
- Resume upload & SHA-256 deduplicated ingestion
- Multi-dimensional candidate screening & ranking
- System compliance & audit logging
"""

import time
from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import get_settings
from api.routers import jobs_router, resumes_router, screenings_router, audits_router
from db.session import engine
from db.base import Base

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager to initialize DB tables and graceful teardown."""
    # Ensure database tables exist (compatible with SQLite fallback or Postgres)
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"[Startup Warning] Could not initialize database tables: {e}")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="High-performance REST API for AI Candidate Screening, Skill Ontology & Explainable ATS Ranking.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Middleware to track request execution duration."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time-Sec"] = f"{process_time:.4f}"
    return response


# Include API v1 Routers
app.include_router(jobs_router, prefix=settings.API_V1_STR)
app.include_router(resumes_router, prefix=settings.API_V1_STR)
app.include_router(screenings_router, prefix=settings.API_V1_STR)
app.include_router(audits_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["System"])
def root() -> Dict[str, Any]:
    """Root endpoint returning API metadata and documentation links."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "api_v1": settings.API_V1_STR,
        "status": "operational"
    }


@app.get("/health", tags=["System"], status_code=status.HTTP_200_OK)
def health_check() -> Dict[str, Any]:
    """Health check endpoint verifying system connectivity."""
    db_status = "connected"
    try:
        with engine.connect() as conn:
            conn.execute(Base.metadata.tables.get("jobs", None).select().limit(1) if "jobs" in Base.metadata.tables else "SELECT 1")
    except Exception:
        # Fallback ping
        db_status = "degraded_or_initializing"

    return {
        "status": "healthy",
        "database": db_status,
        "timestamp": time.time(),
        "version": settings.VERSION
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global catch-all exception handler returning standard JSON error response."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": str(exc),
            "path": str(request.url.path)
        }
    )
