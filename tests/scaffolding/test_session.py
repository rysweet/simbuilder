"""
Tests for the SessionManager module.
"""

import json
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.scaffolding.session import SessionManager
from src.scaffolding.port_manager import PortManager


class TestSessionManager:
    """Test cases for SessionManager."""

    def test_init(self):
        """Test SessionManager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                
                assert session_manager.project_root == Path(temp_dir)
                assert session_manager.sessions_dir == Path(temp_dir) / ".sessions"
                assert session_manager.sessions_dir.exists()

    @patch('uuid.uuid4')
    @patch.object(PortManager, 'get_port')
    @patch.object(PortManager, 'save_to_file')
    def test_create_session_default_services(self, mock_save_to_file, mock_get_port, mock_uuid):
        """Test create_session with default services."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock UUID generation
            test_uuid = uuid.UUID('12345678-1234-5678-9012-123456789012')
            mock_uuid.return_value = test_uuid
            
            # Mock port allocation
            port_map = {
                "neo4j": 30000,
                "neo4j_http": 30001,
                "nats": 30002,
                "nats_http": 30003,
                "nats_cluster": 30004,
                "azurite_blob": 30005,
                "azurite_queue": 30006,
                "azurite_table": 30007,
                "core_api": 30008,
                "api_gateway": 30009,
                "graph_db_admin": 30010,
                "spec_library_api": 30011,
                "tenant_discovery_api": 30012
            }
            mock_get_port.side_effect = lambda service: port_map[service]
            
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                session_info = session_manager.create_session()
                
                # Verify session info
                assert session_info["session_id"] == str(test_uuid)
                assert session_info["session_short"] == "12345678"
                assert session_info["compose_project_name"] == "simbuilder-12345678"
                assert "created_at" in session_info
                assert session_info["env_file_path"] == str(Path(temp_dir) / ".env.session")
                
                # Verify allocated ports
                expected_ports = port_map
                assert session_info["allocated_ports"] == expected_ports
                
                # Verify services
                assert set(session_info["services"]) == set(SessionManager.DEFAULT_SERVICES)
                
                # Verify .env.session file was created
                env_file = Path(temp_dir) / ".env.session"
                assert env_file.exists()
                
                # Check env file content
                with open(env_file, 'r', encoding='utf-8') as f:
                    env_content = f.read()
                
                assert f"SIMBUILDER_SESSION_ID={test_uuid}" in env_content
                assert "SIMBUILDER_SESSION_SHORT=12345678" in env_content
                assert "COMPOSE_PROJECT_NAME=simbuilder-12345678" in env_content
                assert "NEO4J_PORT=30000" in env_content
                assert "NEO4J_HTTP_PORT=30001" in env_content
                assert "NATS_PORT=30002" in env_content
                assert "NATS_HTTP_PORT=30003" in env_content
                assert "CORE_API_PORT=30008" in env_content
                
                # Verify session metadata file was created
                session_dir = session_manager.sessions_dir / str(test_uuid)
                metadata_file = session_dir / "metadata.json"
                assert metadata_file.exists()
                
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                assert metadata["session_id"] == str(test_uuid)
                assert metadata["compose_project_name"] == "simbuilder-12345678"

    @patch('uuid.uuid4')
    @patch.object(PortManager, 'get_port')
    @patch.object(PortManager, 'save_to_file')
    def test_create_session_custom_services(self, mock_save_to_file, mock_get_port, mock_uuid):
        """Test create_session with custom services list."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_uuid = uuid.UUID('12345678-1234-5678-9012-123456789012')
            mock_uuid.return_value = test_uuid
            
            custom_services = ["service1", "service2"]
            port_map = {"service1": 30000, "service2": 30001}
            mock_get_port.side_effect = lambda service: port_map[service]
            
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                session_info = session_manager.create_session(custom_services)
                
                assert session_info["services"] == custom_services
                assert session_info["allocated_ports"] == port_map

    def test_list_sessions_empty(self):
        """Test list_sessions returns empty list when no sessions exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                sessions = session_manager.list_sessions()
                
                assert sessions == []

    def test_list_sessions_with_sessions(self):
        """Test list_sessions returns list of sessions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                
                # Create a test session directory and metadata
                session_id = "test-session-1"
                session_dir = session_manager.sessions_dir / session_id
                session_dir.mkdir(parents=True)
                
                metadata = {
                    "session_id": session_id,
                    "session_short": "test1234",
                    "compose_project_name": "simbuilder-test1234",
                    "created_at": "2024-01-01T00:00:00",
                    "services": ["service1", "service2"]
                }
                
                metadata_file = session_dir / "metadata.json"
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f)
                
                sessions = session_manager.list_sessions()
                
                assert len(sessions) == 1
                assert sessions[0]["session_id"] == session_id
                assert sessions[0]["compose_project_name"] == "simbuilder-test1234"

    def test_get_session_status_nonexistent(self):
        """Test get_session_status returns None for nonexistent session."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                status = session_manager.get_session_status("nonexistent-session")
                
                assert status is None

    @patch.object(SessionManager, '_check_containers_running')
    def test_get_session_status_existing(self, mock_check_containers):
        """Test get_session_status returns status for existing session."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                mock_check_containers.return_value = False
                
                # Create test session
                session_id = "test-session-1"
                session_dir = session_manager.sessions_dir / session_id
                session_dir.mkdir(parents=True)
                
                env_file_path = Path(temp_dir) / ".env.session"
                env_file_path.write_text("SIMBUILDER_SESSION_ID=test-session-1")
                
                metadata = {
                    "session_id": session_id,
                    "session_short": "test1234",
                    "compose_project_name": "simbuilder-test1234",
                    "created_at": "2024-01-01T00:00:00",
                    "env_file_path": str(env_file_path),
                    "allocated_ports": {"service1": 30000}
                }
                
                metadata_file = session_dir / "metadata.json"
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f)
                
                status = session_manager.get_session_status(session_id)
                
                assert status is not None
                assert status["session_id"] == session_id
                assert status["env_file_exists"] is True
                assert status["containers_running"] is False

    @patch.object(SessionManager, '_stop_containers')
    def test_cleanup_session_nonexistent(self, mock_stop_containers):
        """Test cleanup_session returns False for nonexistent session."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                result = session_manager.cleanup_session("nonexistent-session")
                
                assert result is False
                mock_stop_containers.assert_not_called()

    @patch.object(SessionManager, '_stop_containers')
    def test_cleanup_session_existing(self, mock_stop_containers):
        """Test cleanup_session removes session files and stops containers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                
                # Create test session
                session_id = "test-session-1"
                session_dir = session_manager.sessions_dir / session_id
                session_dir.mkdir(parents=True)
                
                env_file_path = Path(temp_dir) / ".env.session"
                env_file_path.write_text(f"SIMBUILDER_SESSION_ID={session_id}")
                
                metadata = {
                    "session_id": session_id,
                    "compose_project_name": "simbuilder-test1234",
                    "env_file_path": str(env_file_path)
                }
                
                metadata_file = session_dir / "metadata.json"
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f)
                
                result = session_manager.cleanup_session(session_id)
                
                assert result is True
                assert not session_dir.exists()
                assert not env_file_path.exists()
                mock_stop_containers.assert_called_once_with("simbuilder-test1234")

    def test_write_env_file(self):
        """Test _write_env_file creates environment file with variables."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                
                env_vars = {
                    "SIMBUILDER_SESSION_ID": "test-session",
                    "NEO4J_PORT": "30000",
                    "CORE_API_PORT": "30001"
                }
                
                env_file_path = Path(temp_dir) / "test.env"
                session_manager._write_env_file(env_file_path, env_vars)
                
                assert env_file_path.exists()
                
                with open(env_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                assert "SIMBUILDER_SESSION_ID=test-session" in content
                assert "NEO4J_PORT=30000" in content
                assert "CORE_API_PORT=30001" in content

    def test_write_session_metadata(self):
        """Test _write_session_metadata creates JSON metadata file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                
                session_info = {
                    "session_id": "test-session",
                    "compose_project_name": "simbuilder-test",
                    "allocated_ports": {"service1": 30000}
                }
                
                metadata_file = Path(temp_dir) / "metadata.json"
                session_manager._write_session_metadata(metadata_file, session_info)
                
                assert metadata_file.exists()
                
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                
                assert loaded_data == session_info

    def test_read_session_metadata(self):
        """Test _read_session_metadata loads JSON metadata file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                
                session_info = {
                    "session_id": "test-session",
                    "compose_project_name": "simbuilder-test"
                }
                
                metadata_file = Path(temp_dir) / "metadata.json"
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(session_info, f)
                
                loaded_data = session_manager._read_session_metadata(metadata_file)
                
                assert loaded_data == session_info

    @patch('subprocess.run')
    def test_check_containers_running_true(self, mock_run):
        """Test _check_containers_running returns True when containers are running."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                
                mock_run.return_value = MagicMock(stdout="container1\ncontainer2\n")
                
                result = session_manager._check_containers_running("test-project")
                
                assert result is True
                mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_check_containers_running_false(self, mock_run):
        """Test _check_containers_running returns False when no containers running."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                
                mock_run.return_value = MagicMock(stdout="")
                
                result = session_manager._check_containers_running("test-project")
                
                assert result is False

    @patch('subprocess.run')
    def test_check_containers_running_exception(self, mock_run):
        """Test _check_containers_running returns False on exception."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                
                mock_run.side_effect = Exception("Docker not available")
                
                result = session_manager._check_containers_running("test-project")
                
                assert result is False

    @patch('subprocess.run')
    def test_stop_containers_success(self, mock_run):
        """Test _stop_containers calls docker-compose down successfully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                
                mock_run.return_value = MagicMock(returncode=0)
                
                session_manager._stop_containers("test-project")
                
                mock_run.assert_called_once_with(
                    ["docker", "compose", "-p", "test-project", "down"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=Path(temp_dir)
                )

    @patch('subprocess.run')
    def test_stop_containers_failure(self, mock_run):
        """Test _stop_containers handles failure gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                
                mock_run.return_value = MagicMock(returncode=1, stderr="Error message")
                
                # Should not raise exception
                session_manager._stop_containers("test-project")

    @patch('subprocess.run')
    def test_stop_containers_exception(self, mock_run):
        """Test _stop_containers handles exception gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                
                mock_run.side_effect = Exception("Command failed")
                
                # Should not raise exception
                session_manager._stop_containers("test-project")

    @patch('subprocess.run')
    def test_compose_up_success(self, mock_run):
        """Test compose_up calls docker compose up successfully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                
                # Create .env.session file
                env_file_path = Path(temp_dir) / ".env.session"
                env_file_path.write_text("COMPOSE_PROJECT_NAME=simbuilder-test1234\n")
                
                mock_run.return_value = MagicMock(returncode=0)
                
                result = session_manager.compose_up()
                
                assert result is True
                mock_run.assert_called_once_with(
                    ["docker", "compose", "-p", "simbuilder-test1234", "--env-file", str(env_file_path), "up", "-d"],
                    cwd=Path(temp_dir),
                    capture_output=True,
                    text=True,
                    timeout=300
                )

    @patch('subprocess.run')
    def test_compose_up_with_profile(self, mock_run):
        """Test compose_up with profile option."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                
                # Create .env.session file
                env_file_path = Path(temp_dir) / ".env.session"
                env_file_path.write_text("COMPOSE_PROJECT_NAME=simbuilder-test1234\n")
                
                mock_run.return_value = MagicMock(returncode=0)
                
                result = session_manager.compose_up(profile="full")
                
                assert result is True
                mock_run.assert_called_once_with(
                    ["docker", "compose", "-p", "simbuilder-test1234", "--env-file", str(env_file_path), "up", "-d", "--profile", "full"],
                    cwd=Path(temp_dir),
                    capture_output=True,
                    text=True,
                    timeout=300
                )

    @patch('subprocess.run')
    def test_compose_up_no_detached(self, mock_run):
        """Test compose_up without detached mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                
                # Create .env.session file
                env_file_path = Path(temp_dir) / ".env.session"
                env_file_path.write_text("COMPOSE_PROJECT_NAME=simbuilder-test1234\n")
                
                mock_run.return_value = MagicMock(returncode=0)
                
                result = session_manager.compose_up(detached=False)
                
                assert result is True
                mock_run.assert_called_once_with(
                    ["docker", "compose", "-p", "simbuilder-test1234", "--env-file", str(env_file_path), "up"],
                    cwd=Path(temp_dir),
                    capture_output=True,
                    text=True,
                    timeout=300
                )

    def test_compose_up_no_env_file(self):
        """Test compose_up returns False when .env.session doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                
                result = session_manager.compose_up()
                
                assert result is False

    @patch('subprocess.run')
    def test_compose_up_no_project_name(self, mock_run):
        """Test compose_up returns False when COMPOSE_PROJECT_NAME not found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                
                # Create .env.session file without COMPOSE_PROJECT_NAME
                env_file_path = Path(temp_dir) / ".env.session"
                env_file_path.write_text("OTHER_VAR=value\n")
                
                result = session_manager.compose_up()
                
                assert result is False
                mock_run.assert_not_called()

    @patch('subprocess.run')
    def test_compose_up_failure(self, mock_run):
        """Test compose_up returns False on command failure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                
                # Create .env.session file
                env_file_path = Path(temp_dir) / ".env.session"
                env_file_path.write_text("COMPOSE_PROJECT_NAME=simbuilder-test1234\n")
                
                mock_run.return_value = MagicMock(returncode=1, stderr="Docker error")
                
                result = session_manager.compose_up()
                
                assert result is False

    @patch('subprocess.run')
    def test_compose_down_success(self, mock_run):
        """Test compose_down calls docker compose down successfully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                
                # Create .env.session file
                env_file_path = Path(temp_dir) / ".env.session"
                env_file_path.write_text("COMPOSE_PROJECT_NAME=simbuilder-test1234\n")
                
                mock_run.return_value = MagicMock(returncode=0)
                
                result = session_manager.compose_down()
                
                assert result is True
                mock_run.assert_called_once_with(
                    ["docker", "compose", "-p", "simbuilder-test1234", "--env-file", str(env_file_path), "down"],
                    cwd=Path(temp_dir),
                    capture_output=True,
                    text=True,
                    timeout=120
                )

    @patch('subprocess.run')
    def test_compose_down_with_volumes(self, mock_run):
        """Test compose_down with remove_volumes option."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                
                # Create .env.session file
                env_file_path = Path(temp_dir) / ".env.session"
                env_file_path.write_text("COMPOSE_PROJECT_NAME=simbuilder-test1234\n")
                
                mock_run.return_value = MagicMock(returncode=0)
                
                result = session_manager.compose_down(remove_volumes=True)
                
                assert result is True
                mock_run.assert_called_once_with(
                    ["docker", "compose", "-p", "simbuilder-test1234", "--env-file", str(env_file_path), "down", "-v"],
                    cwd=Path(temp_dir),
                    capture_output=True,
                    text=True,
                    timeout=120
                )

    def test_compose_down_no_env_file(self):
        """Test compose_down returns False when .env.session doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                
                result = session_manager.compose_down()
                
                assert result is False

    @patch('subprocess.run')
    def test_compose_down_failure(self, mock_run):
        """Test compose_down returns False on command failure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.scaffolding.session.get_project_root', return_value=Path(temp_dir)):
                session_manager = SessionManager()
                
                # Create .env.session file
                env_file_path = Path(temp_dir) / ".env.session"
                env_file_path.write_text("COMPOSE_PROJECT_NAME=simbuilder-test1234\n")
                
                mock_run.return_value = MagicMock(returncode=1, stderr="Docker error")
                
                result = session_manager.compose_down()
                
                assert result is False