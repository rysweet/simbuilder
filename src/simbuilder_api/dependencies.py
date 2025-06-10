"""
Dependency injection for SimBuilder API.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from fastapi import Header
from fastapi import HTTPException
from jose import JWTError

from simbuilder_graph.service import GraphService  # type: ignore[import-not-found]
from simbuilder_servicebus.client import ServiceBusClient  # type: ignore[import-not-found]
from src.scaffolding.config import Settings
from src.scaffolding.config import get_settings as _get_settings

from .auth.jwt_handler import JWTHandler


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return _get_settings()


@lru_cache
def get_jwt_handler() -> JWTHandler:
    """Get cached JWT handler instance."""
    settings = get_settings()
    return JWTHandler(secret=settings.jwt_secret)


def get_graph_service(settings: Settings = Depends(get_settings)) -> GraphService:
    """Get graph database service instance.

    Args:
        settings: Application settings

    Returns:
        Graph service instance
    """
    return GraphService(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
        database=settings.neo4j_database
    )


def get_service_bus(settings: Settings = Depends(get_settings)) -> ServiceBusClient:
    """Get service bus client instance.

    Args:
        settings: Application settings

    Returns:
        Service bus client instance
    """
    return ServiceBusClient(
        server_url=settings.service_bus_url,
        cluster_id=settings.service_bus_cluster_id
    )


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    jwt_handler: JWTHandler = Depends(get_jwt_handler)
) -> str:
    """Get current authenticated user from JWT token.

    Args:
        authorization: Authorization header with Bearer token
        jwt_handler: JWT handler instance

    Returns:
        User ID from token subject

    Raises:
        HTTPException: If token is missing or invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        # Extract Bearer token
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid authorization scheme")

        # Verify and decode token
        token_data = jwt_handler.decode_token(token)
        return token_data.sub

    except (ValueError, JWTError) as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        ) from e


def get_optional_user(
    authorization: Annotated[str | None, Header()] = None,
    jwt_handler: JWTHandler = Depends(get_jwt_handler)
) -> str | None:
    """Get current user if authenticated, None otherwise.

    Args:
        authorization: Authorization header with Bearer token
        jwt_handler: JWT handler instance

    Returns:
        User ID from token subject or None if not authenticated
    """
    try:
        return get_current_user(authorization, jwt_handler)
    except HTTPException:
        return None
