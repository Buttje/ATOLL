"""ATOLL Deployment Server - Manages local agent instances.

This module implements the deployment server that automatically starts
with ATOLL and manages agent lifecycle on the local machine.
"""

import asyncio
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..config.models import TOMLAgentConfig
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AgentInstance:
    """Represents a running agent instance."""

    name: str
    config_path: Path
    process: Optional[subprocess.Popen] = None
    pid: Optional[int] = None
    port: Optional[int] = None
    status: str = "stopped"  # stopped, starting, running, failed
    start_time: Optional[datetime] = None
    restart_count: int = 0
    last_health_check: Optional[datetime] = None
    health_status: str = "unknown"  # unknown, healthy, unhealthy
    error_message: Optional[str] = None


@dataclass
class RemoteDeploymentServer:
    """Configuration for a remote deployment server."""

    name: str
    host: str
    port: int
    enabled: bool = True
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RemoteDeploymentServer":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class DeploymentServerConfig:
    """Configuration for the deployment server."""

    enabled: bool = True  # Auto-start deployment server
    host: str = "localhost"
    base_port: int = 8100  # Starting port for agent instances
    max_agents: int = 10
    health_check_interval: int = 30  # Seconds
    restart_on_failure: bool = True
    max_restarts: int = 3
    agents_directory: Optional[Path] = None
    remote_servers: list[RemoteDeploymentServer] = field(default_factory=list)
    auto_discover_port: bool = True  # Automatically find available port

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeploymentServerConfig":
        """Create from dictionary."""
        config_dict = {
            k: v for k, v in data.items() if k in cls.__annotations__ and k != "remote_servers"
        }

        # Handle remote_servers separately
        if "remote_servers" in data:
            config_dict["remote_servers"] = [
                RemoteDeploymentServer.from_dict(s) if isinstance(s, dict) else s
                for s in data["remote_servers"]
            ]

        return cls(**config_dict)


class DeploymentServer:
    """Manages local ATOLL agent instances.

    The deployment server automatically:
    - Discovers available agents
    - Manages agent lifecycle (start/stop/restart)
    - Monitors agent health
    - Assigns ports to agent instances
    - Provides agent status information
    """

    def __init__(self, config: DeploymentServerConfig):
        """Initialize deployment server.

        Args:
            config: Deployment server configuration
        """
        self.config = config
        self.agents: dict[str, AgentInstance] = {}
        self.next_port = config.base_port
        self.health_check_task: Optional[asyncio.Task] = None
        self.running = False

    async def start(self) -> None:
        """Start the deployment server."""
        if not self.config.enabled:
            logger.info("Deployment server disabled in configuration")
            return

        logger.info(f"Starting ATOLL deployment server on {self.config.host}")
        self.running = True

        # Discover available agents
        await self.discover_agents()

        # Start health monitoring
        self.health_check_task = asyncio.create_task(self._health_check_loop())

        logger.info(f"Deployment server started. Managing {len(self.agents)} agent(s)")

    async def stop(self) -> None:
        """Stop the deployment server and all managed agents."""
        logger.info("Stopping deployment server...")
        self.running = False

        # Cancel health check task
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass

        # Stop all running agents
        for agent_name, agent in self.agents.items():
            if agent.status == "running":
                logger.info(f"Stopping agent: {agent_name}")
                await self.stop_agent(agent_name)

        logger.info("Deployment server stopped")

    async def discover_agents(self) -> None:
        """Discover available agents from the agents directory."""
        if not self.config.agents_directory:
            logger.warning("No agents directory configured")
            return

        agents_dir = self.config.agents_directory
        if not agents_dir.exists():
            logger.warning(f"Agents directory not found: {agents_dir}")
            return

        # Scan for agent configurations
        for agent_dir in agents_dir.iterdir():
            if not agent_dir.is_dir():
                continue

            # Check for agent.toml (preferred) or agent.json (legacy)
            config_path = agent_dir / "agent.toml"
            if not config_path.exists():
                config_path = agent_dir / "agent.json"
                if not config_path.exists():
                    continue

            try:
                # Load agent configuration to get name
                if config_path.suffix == ".toml":
                    config = TOMLAgentConfig.from_toml_file(str(config_path))
                    agent_name = config.agent.name
                else:
                    with open(config_path, encoding="utf-8") as f:
                        config_data = json.load(f)
                    agent_name = config_data.get("name", agent_dir.name)

                # Create agent instance entry
                self.agents[agent_name] = AgentInstance(
                    name=agent_name,
                    config_path=config_path,
                    status="discovered",
                )

                logger.info(f"Discovered agent: {agent_name} at {config_path}")

            except Exception as e:
                logger.error(f"Failed to discover agent in {agent_dir}: {e}")

    async def start_agent(self, agent_name: str) -> bool:
        """Start an agent instance.

        Args:
            agent_name: Name of the agent to start

        Returns:
            True if started successfully, False otherwise
        """
        if agent_name not in self.agents:
            logger.error(f"Agent not found: {agent_name}")
            return False

        agent = self.agents[agent_name]

        if agent.status == "running":
            logger.warning(f"Agent already running: {agent_name}")
            return True

        try:
            # Assign port
            agent.port = self._allocate_port()

            # Build command to start agent in server mode
            # This will be: atoll --server --port {port} --agent {config_path}
            cmd = [
                sys.executable,
                "-m",
                "atoll",
                "--server",
                "--port",
                str(agent.port),
                "--agent",
                str(agent.config_path),
            ]

            logger.info(f"Starting agent {agent_name} on port {agent.port}")
            logger.debug(f"Command: {' '.join(cmd)}")

            # Start agent process
            agent.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=agent.config_path.parent,
            )

            agent.pid = agent.process.pid
            agent.status = "starting"
            agent.start_time = datetime.now()

            # Wait a bit to see if it starts successfully
            await asyncio.sleep(2)

            if agent.process.poll() is None:
                # Still running
                agent.status = "running"
                logger.info(f"Agent {agent_name} started successfully (PID: {agent.pid})")
                return True
            else:
                # Process exited
                stdout, stderr = agent.process.communicate()
                agent.status = "failed"
                agent.error_message = stderr.decode() if stderr else "Unknown error"
                logger.error(f"Agent {agent_name} failed to start: {agent.error_message}")
                return False

        except Exception as e:
            agent.status = "failed"
            agent.error_message = str(e)
            logger.error(f"Failed to start agent {agent_name}: {e}")
            return False

    async def stop_agent(self, agent_name: str) -> bool:
        """Stop an agent instance.

        Args:
            agent_name: Name of the agent to stop

        Returns:
            True if stopped successfully, False otherwise
        """
        if agent_name not in self.agents:
            logger.error(f"Agent not found: {agent_name}")
            return False

        agent = self.agents[agent_name]

        if agent.status != "running":
            logger.warning(f"Agent not running: {agent_name}")
            return True

        try:
            if agent.process:
                logger.info(f"Stopping agent {agent_name} (PID: {agent.pid})")

                # Try graceful shutdown first
                agent.process.terminate()

                # Wait for graceful shutdown
                try:
                    agent.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if not terminated
                    logger.warning(f"Force killing agent {agent_name}")
                    agent.process.kill()
                    agent.process.wait()

                agent.status = "stopped"
                agent.process = None
                agent.pid = None

                # Free up the port
                if agent.port:
                    self._free_port(agent.port)
                    agent.port = None

                logger.info(f"Agent {agent_name} stopped")
                return True

        except Exception as e:
            logger.error(f"Failed to stop agent {agent_name}: {e}")
            return False

        return False

    async def restart_agent(self, agent_name: str) -> bool:
        """Restart an agent instance.

        Args:
            agent_name: Name of the agent to restart

        Returns:
            True if restarted successfully, False otherwise
        """
        if agent_name not in self.agents:
            return False

        agent = self.agents[agent_name]
        agent.restart_count += 1

        logger.info(f"Restarting agent {agent_name} (attempt {agent.restart_count})")

        await self.stop_agent(agent_name)
        await asyncio.sleep(1)
        return await self.start_agent(agent_name)

    def get_agent_status(self, agent_name: str) -> Optional[dict[str, Any]]:
        """Get status information for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Dictionary with agent status or None if not found
        """
        if agent_name not in self.agents:
            return None

        agent = self.agents[agent_name]

        return {
            "name": agent.name,
            "status": agent.status,
            "pid": agent.pid,
            "port": agent.port,
            "start_time": agent.start_time.isoformat() if agent.start_time else None,
            "restart_count": agent.restart_count,
            "health_status": agent.health_status,
            "last_health_check": (
                agent.last_health_check.isoformat() if agent.last_health_check else None
            ),
            "error_message": agent.error_message,
        }

    def list_agents(self) -> list[dict[str, Any]]:
        """List all managed agents.

        Returns:
            List of agent status dictionaries
        """
        return [self.get_agent_status(name) for name in self.agents.keys()]

    async def _health_check_loop(self) -> None:
        """Background task to monitor agent health."""
        while self.running:
            try:
                await asyncio.sleep(self.config.health_check_interval)

                for agent_name, agent in self.agents.items():
                    if agent.status == "running":
                        await self._check_agent_health(agent_name)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")

    async def _check_agent_health(self, agent_name: str) -> None:
        """Check health of a specific agent.

        Args:
            agent_name: Name of the agent to check
        """
        agent = self.agents[agent_name]

        try:
            # Check if process is still running
            if agent.process and agent.process.poll() is not None:
                # Process has exited
                agent.status = "failed"
                agent.health_status = "unhealthy"
                logger.warning(f"Agent {agent_name} process exited unexpectedly")

                # Auto-restart if configured
                if (
                    self.config.restart_on_failure
                    and agent.restart_count < self.config.max_restarts
                ):
                    logger.info(f"Auto-restarting agent {agent_name}")
                    await self.restart_agent(agent_name)
            else:
                # TODO: Add HTTP health check to agent endpoint
                # For now, just mark as healthy if process is running
                agent.health_status = "healthy"
                agent.last_health_check = datetime.now()

        except Exception as e:
            logger.error(f"Health check failed for {agent_name}: {e}")
            agent.health_status = "unhealthy"

    def _allocate_port(self) -> int:
        """Allocate a port for a new agent instance.

        Returns:
            Available port number
        """
        port = self.next_port
        self.next_port += 1
        return port

    def _free_port(self, port: int) -> None:
        """Free up a port when agent stops.

        Args:
            port: Port number to free
        """
        # Simple implementation - could be improved with port reuse
        pass

    @staticmethod
    def find_available_port(start_port: int = 8100, max_attempts: int = 100) -> Optional[int]:
        """Find an available port on localhost.

        Args:
            start_port: Starting port to try
            max_attempts: Maximum number of ports to try

        Returns:
            Available port number or None if none found
        """
        import socket

        for port in range(start_port, start_port + max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("localhost", port))
                    return port
            except OSError:
                continue

        return None

    async def validate_local_server(self) -> tuple[bool, str, Optional[int]]:
        """Validate that local deployment server can start.

        Returns:
            Tuple of (success, message, port)
        """
        # Check if enabled
        if not self.config.enabled:
            return False, "Local deployment server is disabled in configuration", None

        # Find available port if auto-discovery enabled
        if self.config.auto_discover_port:
            port = self.find_available_port(self.config.base_port)
            if port is None:
                return (
                    False,
                    f"No available ports found starting from {self.config.base_port}",
                    None,
                )

            if port != self.config.base_port:
                logger.info(
                    f"Auto-discovered available port: {port} (base port {self.config.base_port} was in use)"
                )
                self.next_port = port
                self.config.base_port = port
        else:
            port = self.config.base_port
            # Check if port is available
            test_port = self.find_available_port(port, 1)
            if test_port is None:
                return False, f"Port {port} is already in use and auto-discovery is disabled", None

        # Check agents directory
        if self.config.agents_directory:
            if not self.config.agents_directory.exists():
                logger.warning(f"Agents directory does not exist: {self.config.agents_directory}")

        return True, "Local deployment server validated successfully", port

    async def check_remote_server(self, remote: RemoteDeploymentServer) -> dict[str, Any]:
        """Check if remote deployment server is accessible and get its agents.

        Args:
            remote: Remote server configuration

        Returns:
            Dictionary with status and agent information
        """

        result = {
            "name": remote.name,
            "host": remote.host,
            "port": remote.port,
            "enabled": remote.enabled,
            "description": remote.description,
            "status": "unknown",
            "agents": [],
            "error": None,
        }

        if not remote.enabled:
            result["status"] = "disabled"
            return result

    async def generate_startup_report(self) -> str:
        """Generate a comprehensive startup report for deployment infrastructure.

        Returns:
            Formatted report string
        """
        lines = []
        lines.append("\n" + "=" * 70)
        lines.append("DEPLOYMENT SERVER STARTUP REPORT")
        lines.append("=" * 70)

        # Local server status
        success, message, port = await self.validate_local_server()
        lines.append("\n[LOCAL DEPLOYMENT SERVER]")
        if success:
            lines.append(f"  Status: ✓ Running on localhost:{port}")
            lines.append(f"  Agents Directory: {self.config.agents_directory or 'Not configured'}")
            lines.append(f"  Active Agents: {len(self.agents)}")
            if self.agents:
                for name, agent in self.agents.items():
                    is_running = agent.process and agent.process.poll() is None
                    status_icon = "●" if is_running else "○"
                    lines.append(f"    {status_icon} {name} (Port: {agent.port})")
        else:
            lines.append(f"  Status: ✗ FAILED - {message}")
            lines.append("  Action Required: Fix the issue above and restart ATOLL")

        # Remote servers status
        if self.config.remote_servers:
            lines.append(
                f"\n[REMOTE DEPLOYMENT SERVERS] ({len(self.config.remote_servers)} configured)"
            )

            for remote in self.config.remote_servers:
                status = await self.check_remote_server(remote)
                lines.append(f"\n  {status['name']} ({status['host']}:{status['port']})")

                if status["status"] == "disabled":
                    lines.append("    Status: ○ Disabled in configuration")
                elif status["status"] == "running":
                    lines.append("    Status: ✓ Running and accessible")
                    if status["agents"]:
                        lines.append(f"    Agents: {len(status['agents'])}")
                        for agent in status["agents"]:
                            lines.append(f"      • {agent}")
                    else:
                        lines.append(
                            "    Agents: No agents discovered (REST API not yet implemented)"
                        )
                elif status["status"] == "registered_not_running":
                    lines.append("    Status: ○ Registered but not running")
                    if status["error"]:
                        lines.append(f"    Error: {status['error']}")
                elif status["status"] == "error":
                    lines.append(f"    Status: ✗ Error - {status['error']}")

                if status.get("description"):
                    lines.append(f"    Description: {status['description']}")
        else:
            lines.append("\n[REMOTE DEPLOYMENT SERVERS]")
            lines.append("  No remote servers configured")

        lines.append("\n" + "=" * 70 + "\n")

        return "\n".join(lines)
