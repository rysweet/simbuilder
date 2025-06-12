"""Tests for tenant discovery CLI commands."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
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
    return mock_settings


class TestDiscoveryCommands:
    """Test discovery CLI commands."""

    @patch("src.tenant_discovery.cli.get_td_settings")
    def test_discovery_start_success(
        self, mock_get_settings: MagicMock, runner: CliRunner, mock_settings: MagicMock
    ) -> None:
        """Test discovery start command succeeds."""
        mock_get_settings.return_value = mock_settings

        result = runner.invoke(app, ["discovery", "start"])

        assert result.exit_code == 0
        assert "Discovery started for 12345678-1234-1234-1234-123456789012" in result.stdout

    @patch("src.tenant_discovery.cli.get_td_settings")
    def test_discovery_start_with_tenant_id_override(
        self, mock_get_settings: MagicMock, runner: CliRunner, mock_settings: MagicMock
    ) -> None:
        """Test discovery start command with tenant ID override."""
        mock_get_settings.return_value = mock_settings
        custom_tenant_id = "99999999-8888-7777-6666-555555555555"

        result = runner.invoke(app, ["discovery", "start", "--tenant-id", custom_tenant_id])

        assert result.exit_code == 0
        assert f"Discovery started for {custom_tenant_id}" in result.stdout

    @patch("src.tenant_discovery.cli.get_td_settings")
    def test_discovery_run_alias(
        self, mock_get_settings: MagicMock, runner: CliRunner, mock_settings: MagicMock
    ) -> None:
        """Test discovery run command (alias for start)."""
        mock_get_settings.return_value = mock_settings

        result = runner.invoke(app, ["discovery", "run"])

        assert result.exit_code == 0
        assert "Discovery started for 12345678-1234-1234-1234-123456789012" in result.stdout

    def test_discovery_list_success(self, runner: CliRunner) -> None:
        """Test discovery list command succeeds."""
        result = runner.invoke(app, ["discovery", "list"])

        assert result.exit_code == 0
        assert "Discovery Sessions" in result.stdout
        assert "session-001" in result.stdout
        assert "session-002" in result.stdout

    def test_discovery_status_with_session_id(self, runner: CliRunner) -> None:
        """Test discovery status command with session ID."""
        result = runner.invoke(app, ["discovery", "status", "session-001"])

        assert result.exit_code == 0
        assert "Status for session session-001" in result.stdout
        assert "Status: Running" in result.stdout
        assert "Progress: 45%" in result.stdout

    def test_discovery_status_without_session_id(self, runner: CliRunner) -> None:
        """Test discovery status command without session ID."""
        result = runner.invoke(app, ["discovery", "status"])

        assert result.exit_code == 0
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


@pytest.mark.usefixtures("runner")
def test_start_subcommand_success(runner):
    """
    Test 'tenant-discovery start --name smoke' sends correct POST and prints response.
    """
    import httpx
    import respx

    api_base_url = "http://localhost:8000"
    session_response = {
        "id": "s123",
        "name": "smoke",
        "description": "test session",
        "created": "2025-06-12T12:00:00Z",
    }

    with respx.mock(assert_all_called=True) as respx_mock:
        route = respx_mock.post(f"{api_base_url}/tenant-discovery/sessions").mock(
            return_value=httpx.Response(201, json=session_response)
        )
        result = runner.invoke(app, ["start", "--name", "smoke", "--description", "test session"])
        assert result.exit_code == 0, f"CLI exited {result.exit_code}, output: {result.stdout}"
        assert "✓ Discovery session started!" in result.stdout
        assert "s123" in result.stdout
        assert route.called, "API endpoint was not called"


def test_start_subcommand_arg_required(runner):
    """Test start subcommand fails if --name argument is missing (Typer parsing)."""
    result = runner.invoke(app, ["start"])
    # Typer/Click usually reports exit_code 2 for usage error
    assert result.exit_code == 2
    assert "--name" in result.output or "Missing option" in result.output
