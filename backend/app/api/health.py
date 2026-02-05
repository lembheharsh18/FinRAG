"""
Health check endpoints for the FinRAG application.

Provides endpoints to verify the application and its
dependencies are running correctly.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.config import get_settings


router = APIRouter()
settings = get_settings()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    app_name: str
    version: str


class DetailedHealthResponse(BaseModel):
    """Detailed health check response with dependency status."""
    status: str
    timestamp: datetime
    app_name: str
    version: str
    dependencies: dict


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Basic Health Check",
    description="Returns the health status of the application."
)
async def health_check():
    """
    Basic health check endpoint.
    
    Returns a simple status indicating the API is running.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        app_name=settings.app_name,
        version=settings.app_version
    )


@router.get(
    "/health/detailed",
    response_model=DetailedHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Detailed Health Check",
    description="Returns detailed health status including dependency checks."
)
async def detailed_health_check():
    """
    Detailed health check endpoint.
    
    Checks the status of all dependencies:
    - OpenAI API connectivity
    - ChromaDB connection
    - File system access
    
    Note: Full implementation will be added when services are set up.
    """
    dependencies = {
        "openai": {
            "status": "configured" if settings.openai_api_key else "not_configured",
            "model": settings.openai_model
        },
        "chromadb": {
            "status": "pending",  # Will be updated when ChromaDB is initialized
            "persist_directory": settings.chroma_persist_directory,
            "collection": settings.chroma_collection_name
        },
        "embedding_model": {
            "status": "pending",  # Will be updated when model is loaded
            "model": settings.embedding_model
        },
        "auth": {
            "provider": settings.auth_provider,
            "status": "configured" if (
                settings.firebase_project_id or settings.supabase_url
            ) else "not_configured"
        }
    }
    
    # Determine overall status
    overall_status = "healthy"
    if not settings.openai_api_key:
        overall_status = "degraded"
    
    return DetailedHealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        app_name=settings.app_name,
        version=settings.app_version,
        dependencies=dependencies
    )
