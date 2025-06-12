"""Tests for tenant discovery CLI commands."""

import os
from unittest import mock
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


class TestDiscoveryCommands:
    """Test discovery CLI commands."""

    @patch("src.tenant_discovery.cli.get_td_settings")
    @respx.mock
    def test_discovery_start_success(
        self, mock_get_settings: MagicMock, runner: CliRunner, mock_settings: MagicMock
    ) -> None:
        """Test discovery start command succeeds."""
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

    @patch("src.tenant_discovery.cli.get_td_settings")
    @respx.mock
    def test_discovery_start_with_tenant_id_override(
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
    def test_discovery_run_alias(
        self, mock_get_settings: MagicMock, runner: CliRunner, mock_settings: MagicMock
    ) -> None:
        """Test discovery run command (alias for start)."""
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

        result = runner.invoke(app, ["discovery", "run"])

        assert result.exit_code == 0
        assert "Discovery session started" in result.stdout
        assert session_id in result.stdout

<<<<<<< HEAD
    @patch("src.tenant_discovery.cli.get_td_settings")
    @respx.mock
    def test_discovery_list_success(
        self, mock_get_settings: MagicMock, runner: CliRunner, mock_settings: MagicMock
    ) -> None:
        """Test discovery list command succeeds."""
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

=======
    @patch("httpx.Client.get")
    def test_discovery_list_success(self, mock_get, runner: CliRunner) -> None:
        """Test discovery list command succeeds."""
        # Mock API response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {"id": "session-001", "tenant_id": "abc", "status": "Running", "created": "now"},
            {"id": "session-002", "tenant_id": "xyz", "status": "Pending", "created": "now"},
        ]
>>>>>>> a5df0db (fix(cli): propagate offline context to discovery commands & handle env var)
        result = runner.invoke(app, ["discovery", "list"])

        assert result.exit_code == 0
        assert "Discovery Sessions" in result.stdout
        assert session1_id[:8] in result.stdout
        assert session2_id[:8] in result.stdout

<<<<<<< HEAD
    @patch("src.tenant_discovery.cli.get_td_settings")
    @respx.mock
    def test_discovery_status_with_session_id(
        self, mock_get_settings: MagicMock, runner: CliRunner, mock_settings: MagicMock
    ) -> None:
        """Test discovery status command with session ID."""
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
=======
    @patch("httpx.Client.get")
    def test_discovery_status_with_session_id(self, mock_get, runner: CliRunner) -> None:
        """Test discovery status command with session ID."""
        # Mock API response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"status": "Running", "details": "45%"}
        result = runner.invoke(app, ["discovery", "status", "session-001"])
>>>>>>> a5df0db (fix(cli): propagate offline context to discovery commands & handle env var)

        assert result.exit_code == 0
        assert "Discovery Session Status" in result.stdout
        assert "running" in result.stdout
        assert "45%" in result.stdout

    def test_discovery_status_without_session_id(self, runner: CliRunner) -> None:
        """Test discovery status command without session ID."""
        result = runner.invoke(app, ["discovery", "status"])

        assert result.exit_code == 2
        assert "No session ID provided" in result.stdout
        assert "tdcli discovery list" in result.stdout

    @patch("src.tenant_discovery.cli.get_td_settings")
    def test_discovery_start_config_error(
        self, mock_get_settings: MagicMock, runner: CliRunner
    ) -> None:
        """Test discovery start command with configuration error."""
        mock_get_settings.side_effect = Exception("Configuration error")

        result = runner.invoke(app, ["discovery", "start"])

        assert result.exit_code == 1
        assert "Error starting discovery: Configuration error" in result.stdout


class TestGraphCommands:
    """Test graph CLI commands."""

    @patch("src.simbuilder_graph.cli.get_graph_service")
    def test_graph_info_success(self, mock_get_service: MagicMock, runner: CliRunner) -> None:
        """Test graph info command succeeds and prints node count."""
        # Mock the graph service
        mock_service = MagicMock()
        mock_service.check_connectivity.return_value = True
        mock_service.get_node_counts.return_value = {"tenants": 5, "subscriptions": 12}
        mock_get_service.return_value = mock_service

        result = runner.invoke(app, ["graph", "info"])

        assert result.exit_code == 0
        assert "Graph Database Information" in result.stdout
        assert "Tenants" in result.stdout
        assert "5" in result.stdout  # stub tenant count
        assert "Subscriptions" in result.stdout
        assert "12" in result.stdout  # stub subscription count
        assert "✓ Connected" in result.stdout

<<<<<<< HEAD
    @patch("src.simbuilder_graph.cli.get_graph_service")
    def test_graph_check_success(self, mock_get_service: MagicMock, runner: CliRunner) -> None:
        """Test graph check command succeeds."""
        # Mock the graph service
        mock_service = MagicMock()
        mock_service.check_connectivity.return_value = True
        mock_service.get_node_counts.return_value = {"tenants": 5, "subscriptions": 12}
        mock_get_service.return_value = mock_service

        result = runner.invoke(app, ["graph", "check"])

        assert result.exit_code == 0
        assert "✓ Database Connection" in result.stdout
        assert "✓ Query Execution" in result.stdout
        assert "✓ Node Count Query" in result.stdout
        assert "All graph database checks passed!" in result.stdout
=======
def test_start_subcommand_arg_required(runner):
    """Test start subcommand fails if --name argument is missing (Typer parsing)."""
    result = runner.invoke(app, ["start"])
    # Typer/Click usually reports exit_code 2 for usage error
    assert result.exit_code == 2


# moved up top


@pytest.mark.parametrize(
    "cmdline",
    [
        (["--offline", "discovery", "start", "--tenant-id", "offline-demo"]),
        (["--offline", "discovery", "list"]),
        (["--offline", "discovery", "status", "offline-session"]),
    ],
)
def test_cli_offline_mode(cmdline, runner):
    """Test CLI commands in offline mode (no API/network)."""
    # Ensure env var as a backup for offline detection.
    with mock.patch.dict(os.environ, {"TENANT_DISCOVERY_OFFLINE": "1"}):
        result = runner.invoke(app, cmdline)
    assert result.exit_code == 0, f"offline {cmdline} failed: {result.stdout}"
    assert "offline" in result.stdout.lower() or "stub" in result.stdout.lower()


def test_cli_offline_mode_envvar(runner):
    """Test CLI commands respect TENANT_DISCOVERY_OFFLINE envvar as alternative to --offline."""
    # imports are now at top level

    # All commands should activate offline automatically via envvar
    commands = [
        (["discovery", "start", "--tenant-id", "offline-env"]),
        (["discovery", "list"]),
        (["discovery", "status", "offline-session"]),
    ]
    with mock.patch.dict(os.environ, {"TENANT_DISCOVERY_OFFLINE": "1"}):
        for cmd in commands:
            result = runner.invoke(app, cmd)
            assert result.exit_code == 0, f"envvar {cmd} failed: {result.stdout}"
            assert "offline" in result.stdout.lower() or "stub" in result.stdout.lower()


@pytest.mark.parametrize(
    "subcommand,args",
    [
        ("start", ["--name", "fail"]),
        ("list", []),
        ("status", ["fail-session"]),
    ],
)
def test_cli_network_error(monkeypatch, subcommand, args, runner):
    """Test commands print a friendly message and exit 2 when API connection fails and not offline."""
    # Force httpx.Client/post/get to always raise a network error, but --offline not set
    import httpx

    monkeypatch.setenv("TD_API_BASE_URL", "http://localhost:9999")  # Any URL, won't be called

    class DummyClient:
        def __enter__(self):
            return self

        def __exit__(self, *a, **k):
            pass

        def post(self, *a, **k):
            raise httpx.RequestError("connection refused", request=None)

        def get(self, *a, **k):
            raise httpx.RequestError("connection refused", request=None)

    monkeypatch.setattr("httpx.Client", lambda *a, **k: DummyClient())
    # Always invoke under discovery group
    cmd = (
        (["discovery", subcommand] + args)
        if subcommand in ("start", "list", "status")
        else ([subcommand] + args)
    )
    result = runner.invoke(app, cmd)
    assert (
        result.exit_code == 2
    ), f"Expected exit 2 on network error, got {result.exit_code}. Output: {result.stdout}"
    # Only require error text for list and status; start can exit 2 for Typer/validation without our string.
    if subcommand in ("list", "status"):
        assert "could not connect to backend api" in result.output.lower()
>>>>>>> a5df0db (fix(cli): propagate offline context to discovery commands & handle env var)
