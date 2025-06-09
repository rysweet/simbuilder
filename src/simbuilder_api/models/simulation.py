"""
Simulation models for SimBuilder API.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field


class SimulationStatus(str, Enum):
    """Simulation status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SimulationCreate(BaseModel):
    """Request model for creating a simulation."""

    name: str = Field(..., description="Simulation name")
    description: str | None = Field(None, description="Simulation description")
    discovery_session_id: UUID | None = Field(None, description="Associated discovery session ID")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Simulation parameters")


class Simulation(BaseModel):
    """Simulation model."""

    id: UUID = Field(..., description="Simulation unique identifier")
    name: str = Field(..., description="Simulation name")
    status: SimulationStatus = Field(..., description="Current simulation status")
    description: str | None = Field(None, description="Simulation description")
    discovery_session_id: UUID | None = Field(None, description="Associated discovery session ID")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Simulation parameters")
    results: dict[str, Any] = Field(default_factory=dict, description="Simulation results")
    created_at: datetime = Field(..., description="Simulation creation timestamp")
    updated_at: datetime = Field(..., description="Simulation last update timestamp")
    started_at: datetime | None = Field(None, description="Simulation start timestamp")
    completed_at: datetime | None = Field(None, description="Simulation completion timestamp")
    error_message: str | None = Field(None, description="Error message if failed")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }
