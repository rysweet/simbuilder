"""Pydantic models for graph database nodes."""

from pydantic import BaseModel
from pydantic import Field


class TenantNode(BaseModel):
    """Represents a tenant node in the graph database."""

    id: str = Field(..., description="Unique tenant identifier")
    name: str = Field(..., description="Tenant display name")

    class Config:
        """Pydantic configuration."""
        frozen = True
        extra = "forbid"


class SubscriptionNode(BaseModel):
    """Represents a subscription node in the graph database."""

    id: str = Field(..., description="Unique subscription identifier")
    tenant_id: str = Field(..., description="Associated tenant identifier")
    name: str = Field(..., description="Subscription display name")

    class Config:
        """Pydantic configuration."""
        frozen = True
        extra = "forbid"
