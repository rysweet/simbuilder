"""
Discovery session models for SimBuilder API.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field


class DiscoverySessionStatus(str, Enum):
    """Discovery session status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DiscoverySessionCreate(BaseModel):
    """Request model for creating a discovery session."""

    tenant_id: str = Field(..., description="Azure tenant ID")
    description: str | None = Field(None, description="Session description")
    config: dict[str, Any] = Field(default_factory=dict, description="Discovery configuration")


class DiscoverySession(BaseModel):
    """Discovery session model."""

    id: UUID = Field(..., description="Session unique identifier")
    tenant_id: str = Field(..., description="Azure tenant ID")
    status: DiscoverySessionStatus = Field(..., description="Current session status")
    description: str | None = Field(None, description="Session description")
    config: dict[str, Any] = Field(default_factory=dict, description="Discovery configuration")
    results: dict[str, Any] = Field(default_factory=dict, description="Discovery results")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Session last update timestamp")
    completed_at: datetime | None = Field(None, description="Session completion timestamp")
    error_message: str | None = Field(None, description="Error message if failed")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }
