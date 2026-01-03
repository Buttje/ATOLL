"""Tests for port allocation and management."""

import socket
from unittest.mock import patch

import pytest

from atoll.utils.port_manager import PortManager


class TestPortManagerBasics:
    """Test basic port manager functionality."""

    def test_initialization(self):
        """Test port manager initialization."""
        manager = PortManager(base_port=8100, max_ports=50)
        assert manager.base_port == 8100
        assert manager.max_ports == 50
        assert len(manager.allocated_ports) == 0
        assert len(manager.port_assignments) == 0

    def test_allocate_first_port(self):
        """Test allocating first available port."""
        manager = PortManager(base_port=9000, max_ports=10)
        port = manager.allocate_port("test_agent")

        assert port >= 9000
        assert port < 9010
        assert port in manager.allocated_ports
        assert manager.port_assignments["test_agent"] == port

    def test_allocate_multiple_ports(self):
        """Test allocating multiple ports for different agents."""
        manager = PortManager(base_port=9100, max_ports=10)

        port1 = manager.allocate_port("agent1")
        port2 = manager.allocate_port("agent2")
        port3 = manager.allocate_port("agent3")

        # All ports should be different
        assert port1 != port2 != port3
        assert len(manager.allocated_ports) == 3
        assert len(manager.port_assignments) == 3

    def test_allocate_same_agent_twice_returns_same_port(self):
        """Test that allocating for same agent returns the same port."""
        manager = PortManager(base_port=9200, max_ports=10)

        port1 = manager.allocate_port("test_agent")
        port2 = manager.allocate_port("test_agent")

        assert port1 == port2
        assert len(manager.allocated_ports) == 1

    def test_release_port(self):
        """Test releasing an allocated port."""
        manager = PortManager(base_port=9300, max_ports=10)

        port = manager.allocate_port("test_agent")
        assert "test_agent" in manager.port_assignments
        assert port in manager.allocated_ports

        manager.release_port("test_agent")
        assert "test_agent" not in manager.port_assignments
        assert port not in manager.allocated_ports

    def test_release_nonexistent_port(self):
        """Test releasing port for agent that doesn't have one."""
        manager = PortManager()
        # Should not raise exception
        manager.release_port("nonexistent_agent")

    def test_get_port(self):
        """Test getting port for an agent."""
        manager = PortManager(base_port=9400, max_ports=10)

        port = manager.allocate_port("test_agent")
        retrieved_port = manager.get_port("test_agent")

        assert retrieved_port == port

    def test_get_port_nonexistent(self):
        """Test getting port for agent that doesn't exist."""
        manager = PortManager()
        port = manager.get_port("nonexistent_agent")
        assert port is None


class TestPreferredPorts:
    """Test preferred port allocation."""

    def test_allocate_with_preferred_port_available(self):
        """Test allocating a specific preferred port when available."""
        manager = PortManager(base_port=9500, max_ports=100)

        # Mock port availability check to return True for our preferred port
        with patch.object(manager, "_is_port_available", return_value=True):
            port = manager.allocate_port("test_agent", preferred_port=9550)
            assert port == 9550

    def test_allocate_with_preferred_port_unavailable(self):
        """Test that fallback works when preferred port is unavailable."""
        manager = PortManager(base_port=9600, max_ports=100)

        # First allocate the preferred port
        manager.allocate_port("agent1", preferred_port=9650)

        # Try to allocate same port for different agent - should get different port
        port = manager.allocate_port("agent2", preferred_port=9650)
        assert port != 9650
        assert port >= 9600


class TestPortAvailability:
    """Test port availability checking."""

    def test_is_port_allocated(self):
        """Test checking if port is allocated."""
        manager = PortManager(base_port=9700, max_ports=10)

        port = manager.allocate_port("test_agent")
        assert manager.is_port_allocated(port)
        assert not manager.is_port_allocated(port + 1)

    def test_get_allocated_ports(self):
        """Test getting set of allocated ports."""
        manager = PortManager(base_port=9800, max_ports=10)

        port1 = manager.allocate_port("agent1")
        port2 = manager.allocate_port("agent2")

        allocated = manager.get_allocated_ports()
        assert port1 in allocated
        assert port2 in allocated
        assert len(allocated) == 2

    def test_get_available_port_count(self):
        """Test getting count of available ports."""
        manager = PortManager(base_port=9900, max_ports=10)

        assert manager.get_available_port_count() == 10

        manager.allocate_port("agent1")
        assert manager.get_available_port_count() == 9

        manager.allocate_port("agent2")
        assert manager.get_available_port_count() == 8

        manager.release_port("agent1")
        assert manager.get_available_port_count() == 9


class TestPortExhaustion:
    """Test behavior when ports are exhausted."""

    def test_allocate_all_ports(self):
        """Test allocating all available ports."""
        manager = PortManager(base_port=10000, max_ports=5)

        # Allocate all 5 ports
        agents = []
        for i in range(5):
            agent_name = f"agent{i}"
            agents.append(agent_name)
            port = manager.allocate_port(agent_name)
            assert port is not None

        assert len(manager.allocated_ports) == 5
        assert manager.get_available_port_count() == 0

    def test_allocate_beyond_capacity_raises_error(self):
        """Test that allocating beyond capacity raises RuntimeError."""
        manager = PortManager(base_port=10100, max_ports=2)

        # Allocate both ports
        manager.allocate_port("agent1")
        manager.allocate_port("agent2")

        # Mock all ports as unavailable
        with patch.object(manager, "_is_port_available", return_value=False):
            with pytest.raises(RuntimeError, match="No available ports"):
                manager.allocate_port("agent3")

    def test_released_port_can_be_reallocated(self):
        """Test that released ports can be allocated again."""
        manager = PortManager(base_port=10200, max_ports=3)

        # Allocate and release
        manager.allocate_port("agent1")
        manager.release_port("agent1")

        # Allocate again - might get same or different port
        port2 = manager.allocate_port("agent2")
        assert port2 is not None


class TestPersistence:
    """Test port registry persistence."""

    def test_set_registry_path(self, tmp_path):
        """Test setting registry path."""
        manager = PortManager()
        registry_path = tmp_path / "port_registry.json"
        manager.set_registry_path(registry_path)
        assert manager.registry_path == registry_path

    def test_save_and_load_registry(self, tmp_path):
        """Test saving and loading port registry."""
        registry_path = tmp_path / "port_registry.json"

        # Create manager and allocate ports
        manager1 = PortManager(base_port=10300, max_ports=10)
        manager1.set_registry_path(registry_path)

        port1 = manager1.allocate_port("agent1")
        port2 = manager1.allocate_port("agent2")

        # Verify registry file was created
        assert registry_path.exists()

        # Create new manager and load registry
        manager2 = PortManager(base_port=10300, max_ports=10)
        manager2.set_registry_path(registry_path)

        # Check that assignments were restored
        assert manager2.get_port("agent1") == port1
        assert manager2.get_port("agent2") == port2
        assert len(manager2.allocated_ports) == 2

    def test_load_nonexistent_registry(self, tmp_path):
        """Test loading registry when file doesn't exist."""
        manager = PortManager()
        registry_path = tmp_path / "nonexistent.json"
        # Should not raise exception
        manager.set_registry_path(registry_path)
        assert len(manager.port_assignments) == 0

    def test_corrupted_registry_handled_gracefully(self, tmp_path):
        """Test that corrupted registry files are handled gracefully."""
        registry_path = tmp_path / "corrupted.json"
        registry_path.write_text("{ invalid json")

        manager = PortManager()
        # Should not crash, just log error
        manager.set_registry_path(registry_path)
        assert len(manager.port_assignments) == 0


class TestCleanup:
    """Test cleanup functionality."""

    def test_cleanup_clears_all_ports(self):
        """Test that cleanup releases all ports."""
        manager = PortManager(base_port=10400, max_ports=10)

        manager.allocate_port("agent1")
        manager.allocate_port("agent2")
        manager.allocate_port("agent3")

        assert len(manager.allocated_ports) == 3

        manager.cleanup()

        assert len(manager.allocated_ports) == 0
        assert len(manager.port_assignments) == 0

    def test_cleanup_with_persistence(self, tmp_path):
        """Test cleanup saves empty registry."""
        registry_path = tmp_path / "port_registry.json"

        manager = PortManager(base_port=10500, max_ports=10)
        manager.set_registry_path(registry_path)

        manager.allocate_port("agent1")
        manager.cleanup()

        # Load in new manager to verify empty state was saved
        manager2 = PortManager(base_port=10500, max_ports=10)
        manager2.set_registry_path(registry_path)

        assert len(manager2.allocated_ports) == 0


class TestOSLevelBinding:
    """Test OS-level port binding."""

    def test_is_port_available_with_free_port(self):
        """Test checking availability of a free port."""
        manager = PortManager()

        # Find a definitely free port by binding ourselves
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("localhost", 0))
            free_port = s.getsockname()[1]

        # The port should be available again after we close the socket
        assert manager._is_port_available(free_port)

    def test_is_port_available_with_used_port(self):
        """Test checking availability of a port in use."""
        manager = PortManager()

        # Bind a socket to occupy a port
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("localhost", 0))
        used_port = server_socket.getsockname()[1]
        server_socket.listen(1)

        try:
            # Port should not be available
            assert not manager._is_port_available(used_port)
        finally:
            server_socket.close()
