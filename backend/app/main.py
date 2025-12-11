"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.core.config import settings
from app.api import health, query, refresh, auth
from app.services.vector_db import VectorDBService


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.log_format == "json" else structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Notion2RAG2API server",
                port=settings.port,
                vector_db=settings.vector_db_type)

    # Initialize vector database (non-blocking for Railway deployment)
    app.state.vector_service = None
    try:
        # Check if essential config is available before initializing
        if settings.notion_token and settings.openai_api_key:
            vector_service = VectorDBService()
            await vector_service.initialize()
            app.state.vector_service = vector_service
            logger.info("Vector database initialized successfully")
        else:
            logger.warning("Vector database initialization skipped - missing configuration")
            logger.info("App started in degraded mode - configure NOTION_TOKEN and OPENAI_API_KEY to enable full functionality")
    except Exception as e:
        logger.error("Failed to initialize vector database", error=str(e))
        logger.info("App started in degraded mode - vector database unavailable")

    yield

    # Shutdown
    logger.info("Shutting down Notion2RAG2API server")
    if hasattr(app.state, "vector_service") and app.state.vector_service:
        await app.state.vector_service.close()


# Create FastAPI app
app = FastAPI(
    title="Notion2RAG2API",
    description="Convert Notion documents to RAG-powered API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(query.router, prefix="/api/v1", tags=["query"])
app.include_router(refresh.router, prefix="/api/v1", tags=["refresh"])


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error("Unhandled exception",
                 error=str(exc),
                 path=request.url.path,
                 method=request.method)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Notion2RAG2API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=settings.workers if not settings.reload else 1,
    )