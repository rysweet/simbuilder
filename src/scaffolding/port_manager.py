"""
Port management for SimBuilder sessions with dynamic port allocation.
"""

import socket
from typing import Dict, Set
from pathlib import Path
import json
from filelock import FileLock
from .config import get_project_root

from .logging import get_logger, LoggingMixin
from .exceptions import ConfigurationError


class PortManager(LoggingMixin):
    """Manages dynamic port allocation for SimBuilder services."""

    def __init__(self, port_range_start: int = 30000, port_range_end: int = 40000):
        """
        Initialize the PortManager.
        
        Args:
            port_range_start: Start of port range to scan
            port_range_end: End of port range to scan
        """
        super().__init__()
        self.port_range_start = port_range_start
        self.port_range_end = port_range_end
        self.allocated_ports: Dict[str, int] = {}
        self.used_ports: Set[int] = set()

        # Global tracking files
        self.global_file: Path = get_project_root() / ".port_allocations.json"
        self.lock_file: Path = self.global_file.with_suffix(".lock")

        # Load any previously allocated global ports
        self._load_global_state()
        
        self.logger.info(
            "PortManager initialized",
            port_range_start=port_range_start,
            port_range_end=port_range_end
        )

    def _is_port_available(self, port: int) -> bool:
        """
        Check if a port is available for binding.
        
        Args:
            port: Port number to check
            
        Returns:
            True if port is available, False otherwise
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('localhost', port))
                return True
        except OSError:
            return False

    def _find_free_port(self) -> int:
        """
        Find the next available port in the configured range.
        
        Returns:
            Available port number
            
        Raises:
            ConfigurationError: If no free ports available in range
        """
        for port in range(self.port_range_start, self.port_range_end + 1):
            if port not in self.used_ports and self._is_port_available(port):
                self.used_ports.add(port)
                self._save_global_state()
                self.logger.debug("Found free port", port=port)
                return port
        
        raise ConfigurationError(
            f"No free ports available in range {self.port_range_start}-{self.port_range_end}"
        )

    def get_port(self, service_name: str) -> int:
        """
        Get a port for the specified service, allocating one if needed.
        
        Args:
            service_name: Name of the service requesting a port
            
        Returns:
            Port number allocated to the service
        """
        if service_name in self.allocated_ports:
            port = self.allocated_ports[service_name]
            self.logger.debug("Returning existing port", service=service_name, port=port)
            return port
        
        port = self._find_free_port()
        self.allocated_ports[service_name] = port
        
        self.logger.info(
            "Allocated new port",
            service=service_name,
            port=port
        )
        
        return port

    def release_port(self, service_name: str) -> None:
        """
        Release a port allocated to a service.
        
        Args:
            service_name: Name of the service to release port for
        """
        if service_name in self.allocated_ports:
            port = self.allocated_ports.pop(service_name)
            self.used_ports.discard(port)
            self._save_global_state()
            
            self.logger.info(
                "Released port",
                service=service_name,
                port=port
            )

    def get_allocated_ports(self) -> Dict[str, int]:
        """
        Get all currently allocated ports.
        
        Returns:
            Dictionary mapping service names to allocated ports
        """
        return self.allocated_ports.copy()

    def save_to_file(self, file_path: Path) -> None:
        """
        Save allocated ports to a JSON file.
        
        Args:
            file_path: Path to save the port allocation data
        """
        port_data = {
            "port_range_start": self.port_range_start,
            "port_range_end": self.port_range_end,
            "allocated_ports": self.allocated_ports,
            "used_ports": list(self.used_ports)
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(port_data, f, indent=2)
            
            self.logger.info("Saved port data to file", file_path=str(file_path))
        except Exception as e:
            self.log_error(e, {"operation": "save_to_file", "file_path": str(file_path)})
            raise

    def load_from_file(self, file_path: Path) -> None:
        """
        Load allocated ports from a JSON file.
        
        Args:
            file_path: Path to load the port allocation data from
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                port_data = json.load(f)
            
            self.port_range_start = port_data.get("port_range_start", self.port_range_start)
            self.port_range_end = port_data.get("port_range_end", self.port_range_end)
            self.allocated_ports = port_data.get("allocated_ports", {})
            self.used_ports = set(port_data.get("used_ports", []))
            
            self.logger.info(
                "Loaded port data from file",
                file_path=str(file_path),
                allocated_count=len(self.allocated_ports)
            )
        except FileNotFoundError:
            self.logger.info("Port data file not found, starting fresh", file_path=str(file_path))
        except Exception as e:
            self.log_error(e, {"operation": "load_from_file", "file_path": str(file_path)})
            raise

    # ------------------------------------------------------------------ #
    # Global state helpers
    # ------------------------------------------------------------------ #

    def _load_global_state(self) -> None:
        """Load global port usage from disk under a file lock."""
        # In unit tests, don't load global state to keep tests isolated
        import sys
        if "pytest" in sys.modules:
            return
            
        try:
            with FileLock(str(self.lock_file), timeout=10):
                if self.global_file.exists():
                    with open(self.global_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.used_ports.update(data.get("used_ports", []))
        except Exception as e:
            # Non-critical; log and continue with fresh state
            self.log_error(e, {"operation": "load_global_state", "file": str(self.global_file)})

    def _save_global_state(self) -> None:
        """Persist global port usage to disk under a file lock."""
        try:
            with FileLock(str(self.lock_file), timeout=10):
                with open(self.global_file, "w", encoding="utf-8") as f:
                    json.dump({"used_ports": list(self.used_ports)}, f, indent=2)
        except Exception as e:
            self.log_error(e, {"operation": "save_global_state", "file": str(self.global_file)})

    def clear_all_ports(self) -> None:
        """Clear all allocated ports."""
        cleared_count = len(self.allocated_ports)
        self.allocated_ports.clear()
        self.used_ports.clear()
        self._save_global_state()
        
        self.logger.info("Cleared all allocated ports", cleared_count=cleared_count)