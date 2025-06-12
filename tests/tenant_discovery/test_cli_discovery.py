"""Tests for tenant discovery CLI discovery commands."""

from unittest.mock import MagicMock
from unittest.mock import patch
from uuid import uuid4

import httpx
import pytest
import respx
from typer.testing import CliRunner

from src.tenant_discovery.cli import app
from src.tenant_discovery.config import TenantDiscoverySettings


@pytest.fixture
def runner() -> CliRunner:
    """CLI test runner fixture."""
    return CliRunner()


@pytest.fixture
def mock_settings() -> MagicMock:
    """Mock TenantDiscoverySettings fixture."""
    mock_settings = MagicMock(spec=TenantDiscoverySettings)
    mock_settings.azure_tenant_id = "12345678-1234-1234-1234-123456789012"
    mock_settings.azure_client_id = "87654321-4321-4321-4321-210987654321"
    mock_settings.azure_client_secret = "test-secret-key"  # noqa: S105
    mock_settings.subscription_id = "11111111-2222-3333-4444-555555555555"
    mock_settings.graph_db_url = "bolt://localhost:30000"
    mock_settings.service_bus_url = "nats://localhost:30002"
    mock_settings.api_base_url = "http://localhost:8001"
    return mock_settings


class TestDiscoveryAPICommands:
    """Test discovery CLI commands with API integration."""

    @patch("src.tenant_discovery.cli.get_td_settings")
    @respx.mock
    def test_discovery_start_success(
        self, mock_get_settings: MagicMock, runner: CliRunner, mock_settings: MagicMock
    ) -> None:
        """Test discovery start command succeeds with API call."""
        mock_get_settings.return_value = mock_settings
        session_id = str(uuid4())

        # Mock API response
        respx.post("http://localhost:8001/tenant-discovery/sessions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": session_id,
                    "tenant_id": "12345678-1234-1234-1234-123456789012",
                    "status": "pending",
                    "description": "CLI discovery session for tenant 12345678-1234-1234-1234-123456789012",
                    "config": {},
                    "results": {},
                    "created_at": "2025-06-12T14:30:00Z",
                    "updated_at": "2025-06-12T14:30:00Z",
                    "completed_at": None,
                    "error_message": None,
                },
            )
        )

        result = runner.invoke(app, ["discovery", "start"])

        assert result.exit_code == 0
        assert "Discovery session started" in result.stdout
        assert session_id in result.stdout
        assert "12345678-1234-1234-1234-123456789012" in result.stdout
        assert "pending" in result.stdout

    @patch("src.tenant_discovery.cli.get_td_settings")
    @respx.mock
    def test_discovery_start_with_tenant_override(
        self, mock_get_settings: MagicMock, runner: CliRunner, mock_settings: MagicMock
    ) -> None:
        """Test discovery start command with tenant ID override."""
        mock_get_settings.return_value = mock_settings
        custom_tenant_id = "99999999-8888-7777-6666-555555555555"
        session_id = str(uuid4())

        # Mock API response
        respx.post("http://localhost:8001/tenant-discovery/sessions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": session_id,
                    "tenant_id": custom_tenant_id,
                    "status": "pending",
                    "description": f"CLI discovery session for tenant {custom_tenant_id}",
                    "config": {},
                    "results": {},
                    "created_at": "2025-06-12T14:30:00Z",
                    "updated_at": "2025-06-12T14:30:00Z",
                    "completed_at": None,
                    "error_message": None,
                },
            )
        )

        result = runner.invoke(app, ["discovery", "start", "--tenant-id", custom_tenant_id])

        assert result.exit_code == 0
        assert "Discovery session started" in result.stdout
        assert custom_tenant_id in result.stdout

    @patch("src.tenant_discovery.cli.get_td_settings")
    @respx.mock
    def test_discovery_list_success(
        self, mock_get_settings: MagicMock, runner: CliRunner, mock_settings: MagicMock
    ) -> None:
        """Test discovery list command succeeds with API call."""
        mock_get_settings.return_value = mock_settings
        session1_id = str(uuid4())
        session2_id = str(uuid4())

        # Mock API response
        respx.get("http://localhost:8001/tenant-discovery/sessions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "sessions": [
                        {
                            "id": session1_id,
                            "tenant_id": "12345678-1234-1234-1234-123456789012",
                            "status": "running",
                            "description": "Test session 1",
                            "config": {},
                            "results": {},
                            "created_at": "2025-06-12T14:30:00Z",
                            "updated_at": "2025-06-12T14:30:00Z",
                            "completed_at": None,
                            "error_message": None,
                        },
                        {
                            "id": session2_id,
                            "tenant_id": "87654321-4321-4321-4321-210987654321",
                            "status": "completed",
                            "description": "Test session 2",
                            "config": {},
                            "results": {},
                            "created_at": "2025-06-12T14:25:00Z",
                            "updated_at": "2025-06-12T14:35:00Z",
                            "completed_at": "2025-06-12T14:35:00Z",
                            "error_message": None,
                        },
                    ],
                    "total": 2,
                },
            )
        )

        result = runner.invoke(app, ["discovery", "list"])

        assert result.exit_code == 0
        assert "Discovery Sessions (2 total)" in result.stdout
        assert session1_id[:8] in result.stdout
        assert session2_id[:8] in result.stdout
        assert "running" in result.stdout
        assert "completed" in result.stdout

    @patch("src.tenant_discovery.cli.get_td_settings")
    @respx.mock
    def test_discovery_list_empty(
        self, mock_get_settings: MagicMock, runner: CliRunner, mock_settings: MagicMock
    ) -> None:
        """Test discovery list command with no sessions."""
        mock_get_settings.return_value = mock_settings
        # Mock API response
        respx.get("http://localhost:8001/tenant-discovery/sessions").mock(
            return_value=httpx.Response(200, json={"sessions": [], "total": 0})
        )

        result = runner.invoke(app, ["discovery", "list"])

        assert result.exit_code == 0
        assert "No discovery sessions found" in result.stdout

    @patch("src.tenant_discovery.cli.get_td_settings")
    @respx.mock
    def test_discovery_status_success(
        self, mock_get_settings: MagicMock, runner: CliRunner, mock_settings: MagicMock
    ) -> None:
        """Test discovery status command succeeds with API call."""
        mock_get_settings.return_value = mock_settings
        session_id = str(uuid4())

        # Mock API responses
        respx.get(f"http://localhost:8001/tenant-discovery/sessions/{session_id}/status").mock(
            return_value=httpx.Response(
                200,
                json={
                    "session_id": session_id,
                    "status": "running",
                    "updated_at": "2025-06-12T14:30:00Z",
                    "progress": 45,
                },
            )
        )

        respx.get(f"http://localhost:8001/tenant-discovery/sessions/{session_id}").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": session_id,
                    "tenant_id": "12345678-1234-1234-1234-123456789012",
                    "status": "running",
                    "description": "Test session",
                    "config": {},
                    "results": {},
                    "created_at": "2025-06-12T14:30:00Z",
                    "updated_at": "2025-06-12T14:30:00Z",
                    "completed_at": None,
                    "error_message": None,
                },
            )
        )

        result = runner.invoke(app, ["discovery", "status", session_id])

        assert result.exit_code == 0
        assert "Discovery Session Status" in result.stdout
        assert session_id in result.stdout
        assert "running" in result.stdout
        assert "45%" in result.stdout

    def test_discovery_status_no_session_id(self, runner: CliRunner) -> None:
        """Test discovery status command without session ID."""
        result = runner.invoke(app, ["discovery", "status"])

        assert result.exit_code == 0
        assert "No session ID provided" in result.stdout
        assert "tdcli discovery list" in result.stdout

    @patch("src.tenant_discovery.cli.get_td_settings")
    @respx.mock
    def test_discovery_status_short_id(
        self, mock_get_settings: MagicMock, runner: CliRunner, mock_settings: MagicMock
    ) -> None:
        """Test discovery status command with short session ID."""
        mock_get_settings.return_value = mock_settings
        session_id = str(uuid4())
        short_id = session_id[:8]

        # Mock list response for short ID lookup
        respx.get("http://localhost:8001/tenant-discovery/sessions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "sessions": [
                        {
                            "id": session_id,
                            "tenant_id": "12345678-1234-1234-1234-123456789012",
                            "status": "running",
                            "description": "Test session",
                            "config": {},
                            "results": {},
                            "created_at": "2025-06-12T14:30:00Z",
                            "updated_at": "2025-06-12T14:30:00Z",
                            "completed_at": None,
                            "error_message": None,
                        }
                    ],
                    "total": 1,
                },
            )
        )

        # Mock status and detail responses
        respx.get(f"http://localhost:8001/tenant-discovery/sessions/{session_id}/status").mock(
            return_value=httpx.Response(
                200,
                json={
                    "session_id": session_id,
                    "status": "running",
                    "updated_at": "2025-06-12T14:30:00Z",
                    "progress": 45,
                },
            )
        )

        respx.get(f"http://localhost:8001/tenant-discovery/sessions/{session_id}").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": session_id,
                    "tenant_id": "12345678-1234-1234-1234-123456789012",
                    "status": "running",
                    "description": "Test session",
                    "config": {},
                    "results": {},
                    "created_at": "2025-06-12T14:30:00Z",
                    "updated_at": "2025-06-12T14:30:00Z",
                    "completed_at": None,
                    "error_message": None,
                },
            )
        )

        result = runner.invoke(app, ["discovery", "status", short_id])

        assert result.exit_code == 0
        assert "Discovery Session Status" in result.stdout
        assert session_id in result.stdout

    @patch("src.tenant_discovery.cli.get_td_settings")
    @respx.mock
    def test_discovery_start_api_error(
        self, mock_get_settings: MagicMock, runner: CliRunner, mock_settings: MagicMock
    ) -> None:
        """Test discovery start command with API error."""
        mock_get_settings.return_value = mock_settings

        # Mock API error response
        respx.post("http://localhost:8001/tenant-discovery/sessions").mock(
            return_value=httpx.Response(400, json={"detail": "Invalid tenant ID"})
        )

        result = runner.invoke(app, ["discovery", "start"])

        assert result.exit_code == 1
        assert "API error: Invalid tenant ID" in result.stdout

    @patch("src.tenant_discovery.cli.get_td_settings")
    @respx.mock
    def test_discovery_list_api_error(
        self, mock_get_settings: MagicMock, runner: CliRunner, mock_settings: MagicMock
    ) -> None:
        """Test discovery list command with API error."""
        mock_get_settings.return_value = mock_settings
        # Mock API error response
        respx.get("http://localhost:8001/tenant-discovery/sessions").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )

        result = runner.invoke(app, ["discovery", "list"])

        assert result.exit_code == 1
        assert "Server error: 500" in result.stdout
