"""
Tests for the PortManager module.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.scaffolding.exceptions import ConfigurationError
from src.scaffolding.port_manager import PortManager


class TestPortManager:
    """Test cases for PortManager."""

    def test_init(self):
        """Test PortManager initialization."""
        port_manager = PortManager()

        assert port_manager.port_range_start == 30000
        assert port_manager.port_range_end == 40000
        assert port_manager.allocated_ports == {}
        assert port_manager.used_ports == set()

    def test_init_custom_range(self):
        """Test PortManager initialization with custom range."""
        port_manager = PortManager(port_range_start=35000, port_range_end=36000)

        assert port_manager.port_range_start == 35000
        assert port_manager.port_range_end == 36000

    @patch("socket.socket")
    def test_is_port_available_true(self, mock_socket):
        """Test _is_port_available returns True for available port."""
        mock_sock = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        mock_sock.bind.return_value = None

        port_manager = PortManager()
        result = port_manager._is_port_available(30000)

        assert result is True
        mock_sock.bind.assert_called_once_with(("localhost", 30000))

    @patch("socket.socket")
    def test_is_port_available_false(self, mock_socket):
        """Test _is_port_available returns False for unavailable port."""
        mock_sock = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        mock_sock.bind.side_effect = OSError("Port in use")

        port_manager = PortManager()
        result = port_manager._is_port_available(30000)

        assert result is False

    @patch.object(PortManager, "_is_port_available")
    def test_find_free_port_success(self, mock_is_available):
        """Test _find_free_port finds an available port."""
        mock_is_available.return_value = True

        port_manager = PortManager(port_range_start=30000, port_range_end=30002)
        port = port_manager._find_free_port()

        assert port == 30000
        assert 30000 in port_manager.used_ports
        mock_is_available.assert_called_once_with(30000)

    @patch.object(PortManager, "_is_port_available")
    def test_find_free_port_no_available_ports(self, mock_is_available):
        """Test _find_free_port raises error when no ports available."""
        mock_is_available.return_value = False

        port_manager = PortManager(port_range_start=30000, port_range_end=30001)

        with pytest.raises(ConfigurationError, match="No free ports available"):
            port_manager._find_free_port()

    @patch.object(PortManager, "_find_free_port")
    def test_get_port_new_service(self, mock_find_free_port):
        """Test get_port allocates new port for new service."""
        mock_find_free_port.return_value = 30000

        port_manager = PortManager()
        port = port_manager.get_port("test_service")

        assert port == 30000
        assert port_manager.allocated_ports["test_service"] == 30000
        mock_find_free_port.assert_called_once()

    @patch.object(PortManager, "_find_free_port")
    def test_get_port_existing_service(self, mock_find_free_port):
        """Test get_port returns existing port for existing service."""
        port_manager = PortManager()
        port_manager.allocated_ports["test_service"] = 30000

        port = port_manager.get_port("test_service")

        assert port == 30000
        mock_find_free_port.assert_not_called()

    def test_release_port_existing_service(self):
        """Test release_port removes allocation for existing service."""
        port_manager = PortManager()
        port_manager.allocated_ports["test_service"] = 30000
        port_manager.used_ports.add(30000)

        port_manager.release_port("test_service")

        assert "test_service" not in port_manager.allocated_ports
        assert 30000 not in port_manager.used_ports

    def test_release_port_nonexistent_service(self):
        """Test release_port handles nonexistent service gracefully."""
        port_manager = PortManager()

        # Should not raise an exception
        port_manager.release_port("nonexistent_service")

    def test_get_allocated_ports(self):
        """Test get_allocated_ports returns copy of allocated ports."""
        port_manager = PortManager()
        port_manager.allocated_ports = {"service1": 30000, "service2": 30001}

        result = port_manager.get_allocated_ports()

        assert result == {"service1": 30000, "service2": 30001}
        # Verify it's a copy
        result["service3"] = 30002
        assert "service3" not in port_manager.allocated_ports

    def test_save_to_file(self):
        """Test save_to_file writes port data to JSON file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "ports.json"

            port_manager = PortManager(port_range_start=35000, port_range_end=36000)
            port_manager.allocated_ports = {"service1": 35000}
            port_manager.used_ports = {35000}

            port_manager.save_to_file(file_path)

            assert file_path.exists()

            with file_path.open(encoding="utf-8") as f:
                data = json.load(f)

            expected_data = {
                "port_range_start": 35000,
                "port_range_end": 36000,
                "allocated_ports": {"service1": 35000},
                "used_ports": [35000],
            }

            assert data == expected_data

    def test_load_from_file_existing_file(self):
        """Test load_from_file loads port data from existing JSON file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "ports.json"

            data = {
                "port_range_start": 35000,
                "port_range_end": 36000,
                "allocated_ports": {"service1": 35000},
                "used_ports": [35000],
            }

            with file_path.open("w", encoding="utf-8") as f:
                json.dump(data, f)

            port_manager = PortManager()
            port_manager.load_from_file(file_path)

            assert port_manager.port_range_start == 35000
            assert port_manager.port_range_end == 36000
            assert port_manager.allocated_ports == {"service1": 35000}
            assert port_manager.used_ports == {35000}

    def test_load_from_file_nonexistent_file(self):
        """Test load_from_file handles nonexistent file gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "nonexistent.json"

            port_manager = PortManager(port_range_start=35000, port_range_end=36000)
            original_start = port_manager.port_range_start
            original_end = port_manager.port_range_end

            # Should not raise exception
            port_manager.load_from_file(file_path)

            # Should maintain original settings
            assert port_manager.port_range_start == original_start
            assert port_manager.port_range_end == original_end
            assert port_manager.allocated_ports == {}
            assert port_manager.used_ports == set()

    def test_clear_all_ports(self):
        """Test clear_all_ports removes all allocations."""
        port_manager = PortManager()
        port_manager.allocated_ports = {"service1": 30000, "service2": 30001}
        port_manager.used_ports = {30000, 30001}

        port_manager.clear_all_ports()

        assert port_manager.allocated_ports == {}
        assert port_manager.used_ports == set()

    @patch.object(PortManager, "_is_port_available")
    def test_port_reuse_after_clear(self, mock_is_available):
        """Test that ports can be reused after clearing all allocations."""
        mock_is_available.return_value = True

        port_manager = PortManager(port_range_start=30000, port_range_end=30002)

        # Allocate port
        port1 = port_manager.get_port("service1")
        assert port1 == 30000

        # Clear and reallocate
        port_manager.clear_all_ports()
        port2 = port_manager.get_port("service2")
        assert port2 == 30000  # Same port should be available again

    @patch.object(PortManager, "_is_port_available")
    def test_sequential_port_allocation(self, mock_is_available):
        """Test that multiple services get different sequential ports."""
        mock_is_available.return_value = True

        port_manager = PortManager(port_range_start=30000, port_range_end=30005)

        port1 = port_manager.get_port("service1")
        port2 = port_manager.get_port("service2")
        port3 = port_manager.get_port("service3")

        assert port1 == 30000
        assert port2 == 30001
        assert port3 == 30002

        assert len(port_manager.allocated_ports) == 3
        assert len(port_manager.used_ports) == 3
