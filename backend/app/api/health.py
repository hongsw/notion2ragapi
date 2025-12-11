"""Health check endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import structlog

from app.core.config import settings

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "Notion2RAG2API",
        "version": "0.1.0"
    }


@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with service status."""
    health_status = {
        "status": "healthy",
        "service": "Notion2RAG2API",
        "version": "0.1.0",
        "checks": {
            "config": True,
            "vector_db": False,
            "notion_api": False,
            "openai_api": False
        }
    }

    # Check configuration
    try:
        health_status["checks"]["config"] = bool(
            settings.notion_token and settings.openai_api_key
        )
    except Exception as e:
        logger.error("Config check failed", error=str(e))
        health_status["checks"]["config"] = False

    # Check vector database (will be implemented)
    # TODO: Add actual vector DB health check

    # Check Notion API (will be implemented)
    # TODO: Add actual Notion API health check

    # Check OpenAI API (will be implemented)
    # TODO: Add actual OpenAI API health check

    # Determine overall status
    if not all(health_status["checks"].values()):
        health_status["status"] = "degraded"

    return health_status