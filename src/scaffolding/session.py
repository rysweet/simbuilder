"""
Session management for SimBuilder with UUID generation and environment setup.
"""

import os
import uuid
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from .config import get_project_root, get_settings
from .port_manager import PortManager
from .logging import get_logger, LoggingMixin
from .exceptions import ConfigurationError


class SessionManager(LoggingMixin):
    """Manages SimBuilder sessions with dynamic port allocation and environment setup."""

    # Default services that need ports allocated
    DEFAULT_SERVICES = [
        "neo4j",
        "neo4j_http",
        "nats",
        "nats_http",
        "nats_cluster",
        "azurite_blob",
        "azurite_queue",
        "azurite_table",
        "core_api",
        "api_gateway",
        "graph_db_admin",
        "spec_library_api",
        "tenant_discovery_api"
    ]

    def __init__(self):
        """Initialize the SessionManager."""
        super().__init__()
        self.project_root = get_project_root()
        self.sessions_dir = self.project_root / ".sessions"
        self.sessions_dir.mkdir(exist_ok=True)
        
        self.logger.info("SessionManager initialized", sessions_dir=str(self.sessions_dir))

    def create_session(self, services: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Create a new session with unique ID and allocated ports.
        
        Args:
            services: List of services to allocate ports for, defaults to DEFAULT_SERVICES
            
        Returns:
            Dictionary containing session information
        """
        # Generate session identifiers
        session_id = str(uuid.uuid4())
        session_short = session_id[:8]
        compose_project_name = f"simbuilder-{session_short}"
        
        # Create session directory
        session_dir = self.sessions_dir / session_id
        session_dir.mkdir(exist_ok=True)
        
        # Initialize port manager
        port_manager = PortManager()
        
        # Allocate ports for services
        if services is None:
            services = self.DEFAULT_SERVICES.copy()
        
        allocated_ports = {}
        for service in services:
            allocated_ports[service] = port_manager.get_port(service)
        
        # Save port allocation data
        port_file = session_dir / "ports.json"
        port_manager.save_to_file(port_file)
        
        # Create environment variables dictionary
        env_vars = {
            "SIMBUILDER_SESSION_ID": session_id,
            "SIMBUILDER_SESSION_SHORT": session_short,
            "COMPOSE_PROJECT_NAME": compose_project_name,
        }
        
        # Add port mappings for allocated services
        for service, port in allocated_ports.items():
            env_vars[f"{service.upper()}_PORT"] = str(port)
        
        # Add derived URLs for known services
        if "neo4j" in allocated_ports:
            env_vars["NEO4J_URI"] = f"neo4j://localhost:{allocated_ports['neo4j']}"
        if "nats" in allocated_ports:
            env_vars["SERVICE_BUS_URL"] = f"nats://localhost:{allocated_ports['nats']}"
        if "core_api" in allocated_ports:
            env_vars["CORE_API_URL"] = f"http://localhost:{allocated_ports['core_api']}"
        if "api_gateway" in allocated_ports:
            env_vars["API_GATEWAY_URL"] = f"http://localhost:{allocated_ports['api_gateway']}"
        
        # Write .env.session file
        env_session_path = self.project_root / ".env.session"
        self._write_env_file(env_session_path, env_vars)
        
        # Create session metadata
        session_info = {
            "session_id": session_id,
            "session_short": session_short,
            "compose_project_name": compose_project_name,
            "created_at": datetime.now().isoformat(),
            "env_file_path": str(env_session_path),
            "session_dir": str(session_dir),
            "allocated_ports": allocated_ports,
            "services": services
        }
        
        # Save session metadata
        session_metadata_path = session_dir / "metadata.json"
        self._write_session_metadata(session_metadata_path, session_info)
        
        self.logger.info(
            "Created new session",
            session_id=session_id,
            session_short=session_short,
            compose_project_name=compose_project_name,
            allocated_ports=allocated_ports
        )
        
        return session_info

    def list_sessions(self) -> List[Dict[str, str]]:
        """
        List all existing sessions.
        
        Returns:
            List of session information dictionaries
        """
        sessions = []
        
        if not self.sessions_dir.exists():
            return sessions
        
        for session_dir in self.sessions_dir.iterdir():
            if session_dir.is_dir():
                metadata_path = session_dir / "metadata.json"
                if metadata_path.exists():
                    try:
                        session_info = self._read_session_metadata(metadata_path)
                        sessions.append(session_info)
                    except Exception as e:
                        self.log_error(
                            e, 
                            {"operation": "list_sessions", "session_dir": str(session_dir)}
                        )
        
        # Sort by creation time, newest first
        sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        self.logger.debug("Listed sessions", session_count=len(sessions))
        return sessions

    def get_session_status(self, session_id: str) -> Optional[Dict[str, str]]:
        """
        Get status information for a specific session.
        
        Args:
            session_id: Session ID to get status for
            
        Returns:
            Session information if found, None otherwise
        """
        session_dir = self.sessions_dir / session_id
        metadata_path = session_dir / "metadata.json"
        
        if not metadata_path.exists():
            self.logger.warning("Session not found", session_id=session_id)
            return None
        
        try:
            session_info = self._read_session_metadata(metadata_path)
            
            # Add runtime status information
            env_session_path = Path(session_info["env_file_path"])
            session_info["env_file_exists"] = env_session_path.exists()
            
            # Check if Docker containers are running
            session_info["containers_running"] = self._check_containers_running(
                session_info["compose_project_name"]
            )
            
            self.logger.debug("Retrieved session status", session_id=session_id)
            return session_info
            
        except Exception as e:
            self.log_error(
                e, 
                {"operation": "get_session_status", "session_id": session_id}
            )
            return None

    def cleanup_session(self, session_id: str) -> bool:
        """
        Clean up a session by stopping containers and removing files.
        
        Args:
            session_id: Session ID to clean up
            
        Returns:
            True if cleanup successful, False otherwise
        """
        session_dir = self.sessions_dir / session_id
        
        if not session_dir.exists():
            self.logger.warning("Session directory not found", session_id=session_id)
            return False
        
        try:
            # Load session metadata
            metadata_path = session_dir / "metadata.json"
            if metadata_path.exists():
                session_info = self._read_session_metadata(metadata_path)
                compose_project_name = session_info["compose_project_name"]
                
                # Stop Docker containers
                self._stop_containers(compose_project_name)
                
                # Remove .env.session file if it matches this session
                env_session_path = Path(session_info["env_file_path"])
                if env_session_path.exists():
                    try:
                        # Check if the env file contains our session ID
                        with open(env_session_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        if session_id in content:
                            env_session_path.unlink()
                            self.logger.info("Removed .env.session file", path=str(env_session_path))
                    except Exception as e:
                        self.log_error(e, {"operation": "remove_env_file"})
            
            # Remove session directory
            import shutil
            shutil.rmtree(session_dir)
            
            self.logger.info("Session cleanup completed", session_id=session_id)
            return True
            
        except Exception as e:
            self.log_error(
                e, 
                {"operation": "cleanup_session", "session_id": session_id}
            )
            return False

    def _write_env_file(self, file_path: Path, env_vars: Dict[str, str]) -> None:
        """Write environment variables to a .env file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# SimBuilder Session Environment Variables\n")
                f.write(f"# Generated on {datetime.now().isoformat()}\n\n")
                
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
            
            self.logger.info("Wrote environment file", path=str(file_path))
            
        except Exception as e:
            self.log_error(e, {"operation": "write_env_file", "path": str(file_path)})
            raise

    def _write_session_metadata(self, file_path: Path, session_info: Dict[str, str]) -> None:
        """Write session metadata to JSON file."""
        import json
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(session_info, f, indent=2)
            
            self.logger.debug("Wrote session metadata", path=str(file_path))
            
        except Exception as e:
            self.log_error(e, {"operation": "write_session_metadata", "path": str(file_path)})
            raise

    def _read_session_metadata(self, file_path: Path) -> Dict[str, str]:
        """Read session metadata from JSON file."""
        import json
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _check_containers_running(self, compose_project_name: str) -> bool:
        """Check if Docker containers for the project are running."""
        try:
            import subprocess
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={compose_project_name}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return len(result.stdout.strip()) > 0
        except Exception:
            return False

    def _stop_containers(self, compose_project_name: str) -> None:
        """Stop Docker containers for the project."""
        try:
            import subprocess
            
            # Stop containers using docker compose down
            result = subprocess.run(
                ["docker", "compose", "-p", compose_project_name, "down"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                self.logger.info("Stopped containers", project=compose_project_name)
            else:
                self.logger.warning(
                    "Failed to stop containers",
                    project=compose_project_name,
                    stderr=result.stderr
                )
                
        except Exception as e:
            self.log_error(
                e,
                {"operation": "stop_containers", "project": compose_project_name}
            )

    def compose_up(self, detached: bool = True, profile: Optional[str] = None) -> bool:
        """
        Start Docker Compose services using the current session environment.
        
        Args:
            detached: Whether to run in detached mode
            profile: Optional profile to activate (e.g., 'full')
            
        Returns:
            True if successful, False otherwise
        """
        env_session_path = self.project_root / ".env.session"
        
        if not env_session_path.exists():
            self.logger.error("No .env.session file found", path=str(env_session_path))
            return False
        
        try:
            # Read compose project name from env file
            compose_project_name = None
            with open(env_session_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('COMPOSE_PROJECT_NAME='):
                        compose_project_name = line.split('=', 1)[1].strip()
                        break
            
            if not compose_project_name:
                self.logger.error("COMPOSE_PROJECT_NAME not found in .env.session")
                return False
            
            # Build docker compose command
            cmd = [
                "docker", "compose",
                "-p", compose_project_name,
                "--env-file", str(env_session_path),
                "up"
            ]
            
            if detached:
                cmd.append("-d")
            
            if profile:
                cmd.extend(["--profile", profile])
            
            self.logger.info(
                "Starting Docker Compose services",
                project=compose_project_name,
                command=" ".join(cmd)
            )
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                self.logger.info(
                    "Docker Compose services started successfully",
                    project=compose_project_name
                )
                return True
            else:
                self.logger.error(
                    "Failed to start Docker Compose services",
                    project=compose_project_name,
                    stdout=result.stdout,
                    stderr=result.stderr
                )
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Docker Compose startup timed out")
            return False
        except Exception as e:
            self.log_error(e, {"operation": "compose_up"})
            return False

    def compose_down(self, remove_volumes: bool = False) -> bool:
        """
        Stop Docker Compose services using the current session environment.
        
        Args:
            remove_volumes: Whether to remove volumes when stopping
            
        Returns:
            True if successful, False otherwise
        """
        env_session_path = self.project_root / ".env.session"
        
        if not env_session_path.exists():
            self.logger.error("No .env.session file found", path=str(env_session_path))
            return False
        
        try:
            # Read compose project name from env file
            compose_project_name = None
            with open(env_session_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('COMPOSE_PROJECT_NAME='):
                        compose_project_name = line.split('=', 1)[1].strip()
                        break
            
            if not compose_project_name:
                self.logger.error("COMPOSE_PROJECT_NAME not found in .env.session")
                return False
            
            # Build docker compose command
            cmd = [
                "docker", "compose",
                "-p", compose_project_name,
                "--env-file", str(env_session_path),
                "down"
            ]
            
            if remove_volumes:
                cmd.append("-v")
            
            self.logger.info(
                "Stopping Docker Compose services",
                project=compose_project_name,
                command=" ".join(cmd)
            )
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            if result.returncode == 0:
                self.logger.info(
                    "Docker Compose services stopped successfully",
                    project=compose_project_name
                )
                return True
            else:
                self.logger.error(
                    "Failed to stop Docker Compose services",
                    project=compose_project_name,
                    stdout=result.stdout,
                    stderr=result.stderr
                )
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Docker Compose shutdown timed out")
            return False
        except Exception as e:
            self.log_error(e, {"operation": "compose_down"})
            return False