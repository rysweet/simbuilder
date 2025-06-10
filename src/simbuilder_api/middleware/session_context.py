"""
Session context middleware for SimBuilder API.
"""

import uuid
from collections.abc import Awaitable
from collections.abc import Callable
from typing import Any

from fastapi import Request
from fastapi import Response
from starlette.middleware.base import BaseHTTPMiddleware


class SessionContextMiddleware(BaseHTTPMiddleware):
    """Middleware to inject session ID into request state."""

    def __init__(self, app: Any, session_header: str = "X-Session-Id") -> None:
        """Initialize session context middleware.

        Args:
            app: FastAPI application instance
            session_header: Header name for session ID
        """
        super().__init__(app)
        self.session_header = session_header

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request and inject session context.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            HTTP response with session context
        """
        # Get session ID from header or generate new one
        session_id = request.headers.get(self.session_header)
        if not session_id:
            session_id = str(uuid.uuid4())

        # Store session ID in request state
        request.state.session_id = session_id

        # Process request
        response = await call_next(request)

        # Add session ID to response headers
        response.headers[self.session_header] = session_id

        return response
