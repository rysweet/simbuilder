"""
Main FastAPI application for SimBuilder API.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI

from src.scaffolding.config import get_settings

from .middleware import ErrorHandlerMiddleware
from .middleware import SessionContextMiddleware
from .routers import health_router
from .routers import simulations_router
from .routers import tenant_discovery_router

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI lifespan context manager for startup/shutdown events.

    Args:
        app: FastAPI application instance

    Yields:
        None during application lifetime
    """
    settings = get_settings()

    # Startup
    logger.info(
        "SimBuilder API starting up",
        environment=settings.environment,
        port=settings.core_api_port,
        debug=settings.debug_mode,
    )

    # TODO: Initialize database connections
    # TODO: Initialize service bus connections
    # TODO: Validate external dependencies

    yield

    # Shutdown
    logger.info("SimBuilder API shutting down")

    # TODO: Close database connections
    # TODO: Close service bus connections
    # TODO: Cleanup resources


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    settings = get_settings()

    app = FastAPI(
        title="SimBuilder Core API",
        description="Core API service for SimBuilder tenant discovery and simulation platform",
        version="1.0.0",
        lifespan=lifespan,
        debug=settings.debug_mode,
    )

    # Add middleware
    app.add_middleware(ErrorHandlerMiddleware, debug=settings.debug_mode)
    app.add_middleware(SessionContextMiddleware)

    # Include routers
    app.include_router(health_router)
    app.include_router(tenant_discovery_router)
    app.include_router(simulations_router)

    return app


# Create application instance
app = create_app()


@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint providing API information."""
    return {
        "name": "SimBuilder Core API",
        "version": "1.0.0",
        "description": "Core API service for SimBuilder tenant discovery and simulation platform",
        "endpoints": {
            "health": "/health/healthz",
            "readiness": "/health/readyz",
            "tenant_discovery": "/tenant-discovery",
            "simulations": "/simulations",
            "docs": "/docs",
            "openapi": "/openapi.json",
        },
    }
