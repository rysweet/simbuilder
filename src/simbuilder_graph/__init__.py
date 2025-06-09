"""
SimBuilder shared graph database package.

This package provides a Neo4j-backed data layer and CLI utilities for
working with tenant and subscription information in a single place that
can be reused by multiple services.
"""

from __future__ import annotations

from . import models as models  # noqa: F401  (re-export for convenience)
from .service import GraphService


def get_graph_service() -> GraphService:
    """Return a configured GraphService instance."""
    return GraphService()


__all__: list[str] = ["GraphService", "get_graph_service", "models"]
