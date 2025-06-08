"""Graph database service for Tenant Discovery.

This module provides Neo4j-backed data layer for managing tenants and subscriptions.
"""

from .service import GraphService


def get_graph_service() -> GraphService:
    """Get a configured GraphService instance.

    Returns:
        GraphService: Configured graph service instance
    """
    return GraphService()

__all__ = ["GraphService", "get_graph_service"]
