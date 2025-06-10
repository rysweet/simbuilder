"""
Simulation endpoints for SimBuilder API.
"""

import uuid
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from pydantic import BaseModel

from src.scaffolding.config import Settings

from ..dependencies import get_settings
from ..models import Simulation
from ..models import SimulationCreate
from ..models import SimulationStatus

router = APIRouter(prefix="/simulations", tags=["simulations"])

# In-memory storage for demo purposes - TODO: Replace with database
_simulations: dict[UUID, Simulation] = {}


class SimulationListResponse(BaseModel):
    """Response model for simulation list."""

    simulations: list[Simulation]
    total: int


@router.post("", response_model=Simulation)
async def create_simulation(
    simulation_data: SimulationCreate, request: Request, settings: Settings = Depends(get_settings)
) -> Simulation:
    """Create a new simulation.

    Args:
        simulation_data: Simulation creation data
        request: HTTP request object
        settings: Application settings

    Returns:
        Created simulation
    """
    simulation_id = uuid.uuid4()
    now = datetime.utcnow()

    simulation = Simulation(
        id=simulation_id,
        name=simulation_data.name,
        status=SimulationStatus.PENDING,
        description=simulation_data.description,
        discovery_session_id=simulation_data.discovery_session_id,
        parameters=simulation_data.parameters,
        results={},
        created_at=now,
        updated_at=now,
        started_at=None,
        completed_at=None,
        error_message=None,
    )

    _simulations[simulation_id] = simulation

    # TODO: Trigger actual simulation process via service bus

    return simulation


@router.get("", response_model=SimulationListResponse)
async def list_simulations(
    request: Request, limit: int = 50, offset: int = 0, settings: Settings = Depends(get_settings)
) -> SimulationListResponse:
    """List simulations.

    Args:
        request: HTTP request object
        limit: Maximum number of simulations to return
        offset: Number of simulations to skip
        settings: Application settings

    Returns:
        List of simulations
    """
    simulations_list = list(_simulations.values())
    total = len(simulations_list)

    # Apply pagination
    paginated_simulations = simulations_list[offset : offset + limit]

    return SimulationListResponse(simulations=paginated_simulations, total=total)


@router.get("/{simulation_id}", response_model=Simulation)
async def get_simulation(
    simulation_id: UUID, request: Request, settings: Settings = Depends(get_settings)
) -> Simulation:
    """Get a specific simulation.

    Args:
        simulation_id: Simulation ID
        request: HTTP request object
        settings: Application settings

    Returns:
        Simulation details

    Raises:
        HTTPException: If simulation not found
    """
    if simulation_id not in _simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")

    return _simulations[simulation_id]


@router.delete("/{simulation_id}")
async def delete_simulation(
    simulation_id: UUID, request: Request, settings: Settings = Depends(get_settings)
) -> dict:
    """Delete a simulation.

    Args:
        simulation_id: Simulation ID
        request: HTTP request object
        settings: Application settings

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: If simulation not found
    """
    if simulation_id not in _simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")

    del _simulations[simulation_id]

    return {"message": "Simulation deleted successfully"}
