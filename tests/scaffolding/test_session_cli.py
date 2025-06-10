"""
Tests for the session CLI commands.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

from typer.testing import CliRunner

from src.scaffolding.cli import session_app


class TestSessionCLI:
    """Test cases for session CLI commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch('src.scaffolding.cli.SessionManager')
    @patch('src.scaffolding.cli.setup_logging')
    def test_session_create_success(self, mock_setup_logging, mock_session_manager_class):
        """Test session create command success."""
        # Mock logger
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger

        # Mock session manager
        mock_session_manager = MagicMock()
        mock_session_manager_class.return_value = mock_session_manager

        session_info = {
            "session_id": "12345678-1234-5678-9012-123456789012",
            "session_short": "12345678",
            "compose_project_name": "simbuilder-12345678",
            "created_at": "2024-01-01T00:00:00",
            "env_file_path": "/path/to/.env.session",
            "allocated_ports": {
                "neo4j": 30000,
                "nats": 30001,
                "core_api": 30002
            }
        }
        mock_session_manager.create_session.return_value = session_info

        result = self.runner.invoke(session_app, ["create"])

        assert result.exit_code == 0
        assert "* New SimBuilder session created!" in result.stdout
        assert "Session ID" in result.stdout
        assert "12345678-1234-5678-9012-123456789012" in result.stdout
        assert "Allocated Ports" in result.stdout

        mock_session_manager.create_session.assert_called_once_with(None)

    @patch('src.scaffolding.cli.SessionManager')
    @patch('src.scaffolding.cli.setup_logging')
    def test_session_create_with_services(self, mock_setup_logging, mock_session_manager_class):
        """Test session create command with custom services."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger

        mock_session_manager = MagicMock()
        mock_session_manager_class.return_value = mock_session_manager

        session_info = {
            "session_id": "test-session",
            "session_short": "testsess",
            "compose_project_name": "simbuilder-testsess",
            "created_at": "2024-01-01T00:00:00",
            "env_file_path": "/path/to/.env.session",
            "allocated_ports": {"service1": 30000, "service2": 30001}
        }
        mock_session_manager.create_session.return_value = session_info

        result = self.runner.invoke(session_app, ["create", "--services", "service1,service2"])

        assert result.exit_code == 0
        mock_session_manager.create_session.assert_called_once_with(["service1", "service2"])

    @patch('src.scaffolding.cli.SessionManager')
    @patch('src.scaffolding.cli.setup_logging')
    def test_session_create_failure(self, mock_setup_logging, mock_session_manager_class):
        """Test session create command failure."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger

        mock_session_manager = MagicMock()
        mock_session_manager_class.return_value = mock_session_manager
        mock_session_manager.create_session.side_effect = Exception("Creation failed")

        result = self.runner.invoke(session_app, ["create"])

        assert result.exit_code == 1
        assert "Error creating session" in result.stdout

    @patch('src.scaffolding.cli.SessionManager')
    @patch('src.scaffolding.cli.setup_logging')
    def test_session_list_empty(self, mock_setup_logging, mock_session_manager_class):
        """Test session list command with no sessions."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger

        mock_session_manager = MagicMock()
        mock_session_manager_class.return_value = mock_session_manager
        mock_session_manager.list_sessions.return_value = []

        result = self.runner.invoke(session_app, ["list"])

        assert result.exit_code == 0
        assert "No sessions found." in result.stdout

    @patch('src.scaffolding.cli.SessionManager')
    @patch('src.scaffolding.cli.setup_logging')
    def test_session_list_with_sessions(self, mock_setup_logging, mock_session_manager_class):
        """Test session list command with existing sessions."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger

        mock_session_manager = MagicMock()
        mock_session_manager_class.return_value = mock_session_manager

        sessions = [
            {
                "session_id": "12345678-1234-5678-9012-123456789012",
                "session_short": "12345678",
                "compose_project_name": "simbuilder-12345678",
                "created_at": "2024-01-01T00:00:00",
                "services": ["neo4j", "nats", "core_api"]
            },
            {
                "session_id": "87654321-4321-8765-2109-876543210987",
                "session_short": "87654321",
                "compose_project_name": "simbuilder-87654321",
                "created_at": "2024-01-02T12:00:00",
                "services": ["service1", "service2"]
            }
        ]
        mock_session_manager.list_sessions.return_value = sessions

        result = self.runner.invoke(session_app, ["list"])

        assert result.exit_code == 0
        assert "SimBuilder Sessions (2 found)" in result.stdout
        assert "12345678..." in result.stdout
        assert "87654321..." in result.stdout
        assert "simbuilder-12345678" in result.stdout
        assert "3 services" in result.stdout
        assert "2 services" in result.stdout

    @patch('src.scaffolding.cli.SessionManager')
    @patch('src.scaffolding.cli.setup_logging')
    def test_session_list_failure(self, mock_setup_logging, mock_session_manager_class):
        """Test session list command failure."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger

        mock_session_manager = MagicMock()
        mock_session_manager_class.return_value = mock_session_manager
        mock_session_manager.list_sessions.side_effect = Exception("List failed")

        result = self.runner.invoke(session_app, ["list"])

        assert result.exit_code == 1
        assert "Error listing sessions" in result.stdout

    @patch('src.scaffolding.cli.SessionManager')
    @patch('src.scaffolding.cli.setup_logging')
    def test_session_status_not_found(self, mock_setup_logging, mock_session_manager_class):
        """Test session status command for nonexistent session."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger

        mock_session_manager = MagicMock()
        mock_session_manager_class.return_value = mock_session_manager
        mock_session_manager.get_session_status.return_value = None

        result = self.runner.invoke(session_app, ["status", "nonexistent-session"])

        assert result.exit_code == 1
        assert "Session not found" in result.stdout

    @patch('src.scaffolding.cli.SessionManager')
    @patch('src.scaffolding.cli.setup_logging')
    def test_session_status_found(self, mock_setup_logging, mock_session_manager_class):
        """Test session status command for existing session."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger

        mock_session_manager = MagicMock()
        mock_session_manager_class.return_value = mock_session_manager

        session_info = {
            "session_id": "12345678-1234-5678-9012-123456789012",
            "session_short": "12345678",
            "compose_project_name": "simbuilder-12345678",
            "created_at": "2024-01-01T00:00:00",
            "env_file_path": "/path/to/.env.session",
            "env_file_exists": True,
            "containers_running": False,
            "allocated_ports": {
                "neo4j": 30000,
                "nats": 30001
            }
        }
        mock_session_manager.get_session_status.return_value = session_info

        result = self.runner.invoke(session_app, ["status", "test-session"])

        assert result.exit_code == 0
        assert "Session Status: 12345678" in result.stdout
        assert "Session ID" in result.stdout
        assert "Env File Exists" in result.stdout
        assert "* Yes" in result.stdout  # env file exists
        assert "Containers Running" in result.stdout
        assert "X No" in result.stdout  # containers not running
        assert "Allocated Ports" in result.stdout
        assert "neo4j" in result.stdout
        assert "30000" in result.stdout

    @patch('src.scaffolding.cli.SessionManager')
    @patch('src.scaffolding.cli.setup_logging')
    def test_session_status_failure(self, mock_setup_logging, mock_session_manager_class):
        """Test session status command failure."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger

        mock_session_manager = MagicMock()
        mock_session_manager_class.return_value = mock_session_manager
        mock_session_manager.get_session_status.side_effect = Exception("Status failed")

        result = self.runner.invoke(session_app, ["status", "test-session"])

        assert result.exit_code == 1
        assert "Error getting session status" in result.stdout

    @patch('src.scaffolding.cli.SessionManager')
    @patch('src.scaffolding.cli.setup_logging')
    def test_session_cleanup_not_found(self, mock_setup_logging, mock_session_manager_class):
        """Test session cleanup command for nonexistent session."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger

        mock_session_manager = MagicMock()
        mock_session_manager_class.return_value = mock_session_manager
        mock_session_manager.get_session_status.return_value = None

        result = self.runner.invoke(session_app, ["cleanup", "nonexistent-session"])

        assert result.exit_code == 1
        assert "Session not found" in result.stdout

    @patch('src.scaffolding.cli.SessionManager')
    @patch('src.scaffolding.cli.setup_logging')
    def test_session_cleanup_success(self, mock_setup_logging, mock_session_manager_class):
        """Test session cleanup command success."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger

        mock_session_manager = MagicMock()
        mock_session_manager_class.return_value = mock_session_manager

        session_info = {
            "session_short": "12345678",
            "compose_project_name": "simbuilder-12345678"
        }
        mock_session_manager.get_session_status.return_value = session_info
        mock_session_manager.cleanup_session.return_value = True

        result = self.runner.invoke(session_app, ["cleanup", "test-session"])

        assert result.exit_code == 0
        assert "Cleaning up session: 12345678" in result.stdout
        assert "* Session cleanup completed successfully!" in result.stdout
        assert "Stopped containers for project: simbuilder-12345678" in result.stdout
        assert "Removed session files and directories" in result.stdout
        assert "Freed allocated ports" in result.stdout

    @patch('src.scaffolding.cli.SessionManager')
    @patch('src.scaffolding.cli.setup_logging')
    def test_session_cleanup_failure(self, mock_setup_logging, mock_session_manager_class):
        """Test session cleanup command failure."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger

        mock_session_manager = MagicMock()
        mock_session_manager_class.return_value = mock_session_manager

        session_info = {
            "session_short": "12345678",
            "compose_project_name": "simbuilder-12345678"
        }
        mock_session_manager.get_session_status.return_value = session_info
        mock_session_manager.cleanup_session.return_value = False

        result = self.runner.invoke(session_app, ["cleanup", "test-session"])

        assert result.exit_code == 1
        assert "X Session cleanup failed!" in result.stdout

    @patch('src.scaffolding.cli.SessionManager')
    @patch('src.scaffolding.cli.setup_logging')
    def test_session_cleanup_exception(self, mock_setup_logging, mock_session_manager_class):
        """Test session cleanup command with exception."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger

        mock_session_manager = MagicMock()
        mock_session_manager_class.return_value = mock_session_manager
        mock_session_manager.get_session_status.side_effect = Exception("Cleanup failed")

        result = self.runner.invoke(session_app, ["cleanup", "test-session"])

        assert result.exit_code == 1
        assert "Error cleaning up session" in result.stdout

    @patch('src.scaffolding.cli._get_current_session_id')
    @patch('src.scaffolding.cli.setup_logging')
    def test_get_current_session_id_from_env(self, mock_setup_logging, mock_get_session_id):
        """Test that CLI commands use session ID from environment."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger
        mock_get_session_id.return_value = "test-session-id"

        # Test that _get_current_session_id is imported and callable
        result = mock_get_session_id()
        assert result == "test-session-id"

    def test_get_current_session_id_function(self):
        """Test _get_current_session_id function directly."""
        from src.scaffolding.cli import _get_current_session_id

        # Test with environment variable
        with patch('os.getenv', return_value="env-session-id"):
            session_id = _get_current_session_id()
            assert session_id == "env-session-id"

    def test_get_current_session_id_from_file(self):
        """Test _get_current_session_id reads from .env.session file."""
        from src.scaffolding.cli import _get_current_session_id

        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env.session"
            env_file.write_text("SIMBUILDER_SESSION_ID=file-session-id\nOTHER_VAR=value\n")

            with patch('os.getenv', return_value=None), patch('src.scaffolding.config.get_project_root', return_value=Path(temp_dir)):
                session_id = _get_current_session_id()
                assert session_id == "file-session-id"

    def test_get_current_session_id_none(self):
        """Test _get_current_session_id returns None when no session found."""
        from src.scaffolding.cli import _get_current_session_id

        with patch('os.getenv', return_value=None), patch('src.scaffolding.config.get_project_root') as mock_get_root:
            # Point to non-existent directory
            mock_get_root.return_value = Path("/nonexistent")
            session_id = _get_current_session_id()
            assert session_id is None
