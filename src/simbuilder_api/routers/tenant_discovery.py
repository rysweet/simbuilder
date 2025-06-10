"""
Tenant discovery endpoints for SimBuilder API.
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
from ..models import DiscoverySession
from ..models import DiscoverySessionCreate
from ..models import DiscoverySessionStatus

router = APIRouter(prefix="/tenant-discovery", tags=["tenant-discovery"])

# In-memory storage for demo purposes - TODO: Replace with database
_sessions: dict[UUID, DiscoverySession] = {}


class SessionListResponse(BaseModel):
    """Response model for session list."""

    sessions: list[DiscoverySession]
    total: int


@router.post("/sessions", response_model=DiscoverySession)
async def create_discovery_session(
    session_data: DiscoverySessionCreate,
    request: Request,
    settings: Settings = Depends(get_settings)
) -> DiscoverySession:
    """Create a new tenant discovery session.

    Args:
        session_data: Discovery session creation data
        request: HTTP request object
        settings: Application settings

    Returns:
        Created discovery session
    """
    session_id = uuid.uuid4()
    now = datetime.utcnow()

    session = DiscoverySession(
        id=session_id,
        tenant_id=session_data.tenant_id,
        status=DiscoverySessionStatus.PENDING,
        description=session_data.description,
        config=session_data.config,
        results={},
        created_at=now,
        updated_at=now,
        completed_at=None,
        error_message=None
    )

    _sessions[session_id] = session

    # TODO: Trigger actual discovery process via service bus

    return session


@router.get("/sessions", response_model=SessionListResponse)
async def list_discovery_sessions(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    settings: Settings = Depends(get_settings)
) -> SessionListResponse:
    """List discovery sessions.

    Args:
        request: HTTP request object
        limit: Maximum number of sessions to return
        offset: Number of sessions to skip
        settings: Application settings

    Returns:
        List of discovery sessions
    """
    sessions_list = list(_sessions.values())
    total = len(sessions_list)

    # Apply pagination
    paginated_sessions = sessions_list[offset:offset + limit]

    return SessionListResponse(
        sessions=paginated_sessions,
        total=total
    )


@router.get("/sessions/{session_id}", response_model=DiscoverySession)
async def get_discovery_session(
    session_id: UUID,
    request: Request,
    settings: Settings = Depends(get_settings)
) -> DiscoverySession:
    """Get a specific discovery session.

    Args:
        session_id: Discovery session ID
        request: HTTP request object
        settings: Application settings

    Returns:
        Discovery session details

    Raises:
        HTTPException: If session not found
    """
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Discovery session not found")

    return _sessions[session_id]


@router.get("/sessions/{session_id}/status")
async def get_session_status(
    session_id: UUID,
    request: Request,
    settings: Settings = Depends(get_settings)
) -> dict:
    """Get discovery session status.

    Args:
        session_id: Discovery session ID
        request: HTTP request object
        settings: Application settings

    Returns:
        Session status information

    Raises:
        HTTPException: If session not found
    """
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Discovery session not found")

    session = _sessions[session_id]

    return {
        "session_id": session_id,
        "status": session.status,
        "updated_at": session.updated_at,
        "progress": 0  # TODO: Calculate actual progress
    }
