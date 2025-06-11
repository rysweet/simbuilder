"""
Health check endpoints for SimBuilder API.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from pydantic import BaseModel

from src.scaffolding.config import Settings

from ..dependencies import get_settings

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: datetime
    version: str = "1.0.0"
    environment: str


class ReadinessResponse(BaseModel):
    """Readiness check response model."""

    status: str
    timestamp: datetime
    checks: dict[str, Any]


@router.get("/healthz", response_model=HealthResponse)
async def health_check(
    request: Request, settings: Settings = Depends(get_settings)
) -> HealthResponse:
    """Basic health check endpoint.

    Returns:
        Health status information
    """
    return HealthResponse(
        status="healthy", timestamp=datetime.utcnow(), environment=settings.environment
    )


@router.get("/readyz", response_model=ReadinessResponse)
async def readiness_check(
    request: Request, settings: Settings = Depends(get_settings)
) -> ReadinessResponse:
    """Readiness check endpoint with dependency validation.

    Returns:
        Readiness status with dependency checks
    """
    checks = {
        "database": "healthy",  # TODO: Add actual Neo4j health check
        "service_bus": "healthy",  # TODO: Add actual NATS health check
        "configuration": "healthy",
    }

    # Determine overall status
    all_healthy = all(status == "healthy" for status in checks.values())
    status = "ready" if all_healthy else "not_ready"

    return ReadinessResponse(status=status, timestamp=datetime.utcnow(), checks=checks)
