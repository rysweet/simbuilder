"""
Error handling middleware for SimBuilder API.
"""

import traceback
from collections.abc import Awaitable
from collections.abc import Callable
from typing import Any

import structlog
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware."""

    def __init__(self, app: Any, debug: bool = False) -> None:
        """Initialize error handler middleware.

        Args:
            app: FastAPI application instance
            debug: Whether to include debug information in error responses
        """
        super().__init__(app)
        self.debug = debug

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process request with global error handling.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            HTTP response with error handling
        """
        try:
            response = await call_next(request)
            return response
        except HTTPException:
            # Re-raise HTTP exceptions to be handled by FastAPI
            raise
        except Exception as exc:
            # Log the exception
            session_id = getattr(request.state, "session_id", "unknown")
            logger.error(
                "Unhandled exception in API request",
                exception=str(exc),
                session_id=session_id,
                path=request.url.path,
                method=request.method,
                exc_info=True
            )

            # Prepare error response
            error_detail = {
                "error": "Internal server error",
                "session_id": session_id,
                "path": request.url.path,
                "method": request.method
            }

            # Include debug information if enabled
            if self.debug:
                error_detail.update({
                    "exception": str(exc),
                    "traceback": traceback.format_exc()
                })

            return JSONResponse(
                status_code=500,
                content=error_detail
            )
