"""
Tests for session context middleware.
"""

import uuid
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi import Request
from fastapi.testclient import TestClient

from simbuilder_api.middleware.session_context import SessionContextMiddleware


@pytest.fixture
def app_with_middleware():
    """Create FastAPI app with session middleware for testing."""
    app = FastAPI()
    app.add_middleware(SessionContextMiddleware)

    @app.get("/test")
    async def test_endpoint(request: Request):
        return {
            "session_id": getattr(request.state, "session_id", None),
            "path": request.url.path
        }

    return app


@pytest.fixture
def client(app_with_middleware):
    """Create test client with session middleware."""
    return TestClient(app_with_middleware)


class TestSessionContextMiddleware:
    """Test session context middleware functionality."""

    def test_middleware_initialization(self):
        """Test middleware initialization with default header."""
        app = FastAPI()
        middleware = SessionContextMiddleware(app)

        assert middleware.session_header == "X-Session-Id"

    def test_middleware_initialization_custom_header(self):
        """Test middleware initialization with custom header."""
        app = FastAPI()
        middleware = SessionContextMiddleware(app, session_header="X-Custom-Session")

        assert middleware.session_header == "X-Custom-Session"

    def test_session_id_from_header(self, client):
        """Test session ID extraction from request header."""
        session_id = "test-session-123"

        response = client.get("/test", headers={"X-Session-Id": session_id})

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert response.headers["X-Session-Id"] == session_id

    def test_session_id_generation_when_missing(self, client):
        """Test session ID generation when header is missing."""
        response = client.get("/test")

        assert response.status_code == 200
        data = response.json()

        # Should have generated a session ID
        session_id = data["session_id"]
        assert session_id is not None
        assert len(session_id) > 0

        # Should be a valid UUID format
        try:
            uuid.UUID(session_id)
        except ValueError:
            pytest.fail("Generated session ID is not a valid UUID")

        # Response should include the generated session ID in headers
        assert response.headers["X-Session-Id"] == session_id

    def test_session_id_consistency_across_requests(self, client):
        """Test that different requests get different session IDs when none provided."""
        response1 = client.get("/test")
        response2 = client.get("/test")

        assert response1.status_code == 200
        assert response2.status_code == 200

        session_id1 = response1.json()["session_id"]
        session_id2 = response2.json()["session_id"]

        # Different requests should get different session IDs
        assert session_id1 != session_id2

    def test_session_id_persistence_with_header(self, client):
        """Test that same session ID is maintained when provided in header."""
        session_id = "persistent-session-456"

        response1 = client.get("/test", headers={"X-Session-Id": session_id})
        response2 = client.get("/test", headers={"X-Session-Id": session_id})

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Both responses should have the same session ID
        assert response1.json()["session_id"] == session_id
        assert response2.json()["session_id"] == session_id
        assert response1.headers["X-Session-Id"] == session_id
        assert response2.headers["X-Session-Id"] == session_id

    def test_custom_session_header(self):
        """Test middleware with custom session header name."""
        app = FastAPI()
        app.add_middleware(SessionContextMiddleware, session_header="X-Custom-Session")

        @app.get("/test")
        async def test_endpoint(request: Request):
            return {"session_id": getattr(request.state, "session_id", None)}

        client = TestClient(app)
        session_id = "custom-header-session"

        response = client.get("/test", headers={"X-Custom-Session": session_id})

        assert response.status_code == 200
        assert response.json()["session_id"] == session_id
        assert response.headers["X-Custom-Session"] == session_id

    def test_empty_session_header_generates_new_id(self, client):
        """Test that empty session header generates new ID."""
        response = client.get("/test", headers={"X-Session-Id": ""})

        assert response.status_code == 200
        data = response.json()

        # Should generate new ID when header is empty
        session_id = data["session_id"]
        assert session_id is not None
        assert len(session_id) > 0
        assert response.headers["X-Session-Id"] == session_id

    def test_whitespace_session_header_generates_new_id(self, client):
        """Test that whitespace-only session header generates new ID."""
        response = client.get("/test", headers={"X-Session-Id": "   "})

        assert response.status_code == 200
        data = response.json()

        # Should use the whitespace value as-is
        session_id = data["session_id"]
        assert session_id == "   "
        assert response.headers["X-Session-Id"] == "   "

    def test_session_id_with_uuid_format(self, client):
        """Test session ID with proper UUID format."""
        session_id = str(uuid.uuid4())

        response = client.get("/test", headers={"X-Session-Id": session_id})

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert response.headers["X-Session-Id"] == session_id

    def test_session_id_with_non_uuid_format(self, client):
        """Test session ID with non-UUID format."""
        session_id = "not-a-uuid-format"

        response = client.get("/test", headers={"X-Session-Id": session_id})

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert response.headers["X-Session-Id"] == session_id

    @pytest.mark.asyncio
    async def test_middleware_async_dispatch(self):
        """Test middleware async dispatch functionality."""
        app = FastAPI()
        middleware = SessionContextMiddleware(app)

        # Mock request and call_next
        request = MagicMock(spec=Request)
        request.headers = {}
        request.state = MagicMock()

        # Mock response
        mock_response = MagicMock()
        mock_response.headers = {}

        call_next = AsyncMock(return_value=mock_response)

        # Call middleware dispatch
        result = await middleware.dispatch(request, call_next)

        # Verify call_next was called
        call_next.assert_called_once_with(request)

        # Verify session_id was set on request state
        assert hasattr(request.state, "session_id")

        # Verify response headers were set
        assert "X-Session-Id" in mock_response.headers

        assert result == mock_response
