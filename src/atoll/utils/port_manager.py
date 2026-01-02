"""Port allocation and management utilities.

This module provides robust port allocation and tracking for agent instances,
ensuring ports are properly allocated and released across the deployment lifecycle.
"""

import socket
from pathlib import Path
from typing import Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class PortManager:
    """Manages port allocation and release for agent instances.

    The PortManager uses OS-level socket binding to discover free ports
    and maintains a registry of allocated ports to prevent conflicts.
    """

    def __init__(self, base_port: int = 8100, max_ports: int = 100):
        """Initialize port manager.

        Args:
            base_port: Starting port number for allocation range
            max_ports: Maximum number of ports to manage
        """
        self.base_port = base_port
        self.max_ports = max_ports
        self.allocated_ports: set[int] = set()
        self.port_assignments: dict[str, int] = {}  # agent_name -> port
        self.registry_path: Optional[Path] = None

    def set_registry_path(self, path: Path) -> None:
        """Set path for persistent port registry.

        Args:
            path: Path to store port registry file
        """
        self.registry_path = path
        self._load_registry()

    def allocate_port(self, agent_name: str, preferred_port: Optional[int] = None) -> int:
        """Allocate a port for an agent.

        Uses OS-level socket binding to find available ports. If a preferred
        port is specified and available, it will be used.

        Args:
            agent_name: Name of the agent requesting the port
            preferred_port: Optional preferred port number

        Returns:
            Allocated port number

        Raises:
            RuntimeError: If no ports are available

        Examples:
            >>> manager = PortManager(base_port=8100)
            >>> port = manager.allocate_port("test_agent")
            >>> assert 8100 <= port < 8200
            >>> manager.release_port("test_agent")
        """
        # Check if agent already has a port allocated
        if agent_name in self.port_assignments:
            existing_port = self.port_assignments[agent_name]
            logger.debug(f"Agent {agent_name} already has port {existing_port}")
            return existing_port

        # Try preferred port first if specified
        if preferred_port is not None:
            if self._is_port_available(preferred_port) and preferred_port not in self.allocated_ports:
                self._register_port(agent_name, preferred_port)
                return preferred_port
            else:
                logger.warning(
                    f"Preferred port {preferred_port} for {agent_name} is not available"
                )

        # Find next available port using OS binding
        for offset in range(self.max_ports):
            candidate_port = self.base_port + offset

            # Skip if already allocated
            if candidate_port in self.allocated_ports:
                continue

            # Test if port is available at OS level
            if self._is_port_available(candidate_port):
                self._register_port(agent_name, candidate_port)
                return candidate_port

        raise RuntimeError(
            f"No available ports in range {self.base_port}-{self.base_port + self.max_ports - 1}"
        )

    def release_port(self, agent_name: str) -> None:
        """Release a port allocated to an agent.

        Args:
            agent_name: Name of the agent releasing the port

        Examples:
            >>> manager = PortManager()
            >>> port = manager.allocate_port("test_agent")
            >>> manager.release_port("test_agent")
            >>> assert "test_agent" not in manager.port_assignments
        """
        if agent_name in self.port_assignments:
            port = self.port_assignments[agent_name]
            del self.port_assignments[agent_name]
            self.allocated_ports.discard(port)
            logger.info(f"Released port {port} from agent {agent_name}")
            self._save_registry()
        else:
            logger.warning(f"Agent {agent_name} has no allocated port to release")

    def get_port(self, agent_name: str) -> Optional[int]:
        """Get the port allocated to an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Port number if allocated, None otherwise
        """
        return self.port_assignments.get(agent_name)

    def is_port_allocated(self, port: int) -> bool:
        """Check if a port is currently allocated.

        Args:
            port: Port number to check

        Returns:
            True if port is allocated
        """
        return port in self.allocated_ports

    def get_allocated_ports(self) -> set[int]:
        """Get set of all currently allocated ports.

        Returns:
            Set of allocated port numbers
        """
        return self.allocated_ports.copy()

    def get_available_port_count(self) -> int:
        """Get count of available ports in the managed range.

        Returns:
            Number of available ports
        """
        return self.max_ports - len(self.allocated_ports)

    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available at OS level.

        Args:
            port: Port number to check

        Returns:
            True if port can be bound
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("localhost", port))
                return True
        except OSError:
            return False

    def _register_port(self, agent_name: str, port: int) -> None:
        """Register a port allocation.

        Args:
            agent_name: Name of the agent
            port: Port number allocated
        """
        self.port_assignments[agent_name] = port
        self.allocated_ports.add(port)
        logger.info(f"Allocated port {port} to agent {agent_name}")
        self._save_registry()

    def _save_registry(self) -> None:
        """Save port registry to persistent storage."""
        if self.registry_path is None:
            return

        import json

        try:
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "base_port": self.base_port,
                "assignments": self.port_assignments,
            }
            with open(self.registry_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved port registry to {self.registry_path}")
        except Exception as e:
            logger.error(f"Failed to save port registry: {e}")

    def _load_registry(self) -> None:
        """Load port registry from persistent storage."""
        if self.registry_path is None or not self.registry_path.exists():
            return

        import json

        try:
            with open(self.registry_path) as f:
                data = json.load(f)

            # Validate and restore assignments
            for agent_name, port in data.get("assignments", {}).items():
                if isinstance(port, int) and self.base_port <= port < self.base_port + self.max_ports:
                    self.port_assignments[agent_name] = port
                    self.allocated_ports.add(port)

            logger.info(f"Loaded {len(self.port_assignments)} port assignments from registry")
        except Exception as e:
            logger.error(f"Failed to load port registry: {e}")

    def cleanup(self) -> None:
        """Clean up all port allocations.

        Should be called on server shutdown to release all ports.
        """
        logger.info(f"Cleaning up {len(self.allocated_ports)} allocated ports")
        self.allocated_ports.clear()
        self.port_assignments.clear()
        self._save_registry()
