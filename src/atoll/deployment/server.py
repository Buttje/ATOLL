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
from ..utils.venv_utils import get_venv_pip_path

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
    stdout_log: Optional[str] = None  # Captured stdout
    stderr_log: Optional[str] = None  # Captured stderr
    exit_code: Optional[int] = None  # Process exit code if failed


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
    api_port: int = 8080  # Port for REST API server
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

        # Convert agents_directory string to Path if present
        if "agents_directory" in config_dict and config_dict["agents_directory"] is not None:
            config_dict["agents_directory"] = Path(config_dict["agents_directory"])

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
        self.api_task: Optional[asyncio.Task] = None
        self.running = False

    async def start(self) -> None:
        """Start the deployment server."""
        if not self.config.enabled:
            logger.info("Deployment server disabled in configuration")
            return

        print("\n" + "=" * 70)
        print("STARTING LOCAL DEPLOYMENT SERVER")
        print("=" * 70)
        logger.info("Starting ATOLL deployment server")
        print(f"  → REST API Port: {self.config.api_port}")
        print(f"  → Agents Directory: {self.config.agents_directory}")
        print(
            f"  → Agent Port Range: {self.config.base_port}-{self.config.base_port + self.config.max_agents - 1}"
        )
        print(f"    (First agent will use port {self.config.base_port})")

        self.running = True

        # Start REST API server
        from .api import run_api_server

        storage_path = Path.home() / ".atoll_deployment" / "agents"
        storage_path.mkdir(parents=True, exist_ok=True)

        print("\n🌐 Starting REST API...")
        self.api_task = asyncio.create_task(
            run_api_server(
                deployment_server=self,
                host=self.config.host,
                port=self.config.api_port,
                storage_path=storage_path,
            )
        )
        # Give API a moment to start
        await asyncio.sleep(0.5)
        print(f"   ✓ REST API running on http://{self.config.host}:{self.config.api_port}")
        logger.info(f"REST API started on {self.config.host}:{self.config.api_port}")
        self.running = True

        # Discover available agents
        print("\n📂 Discovering agent configurations...")
        await self.discover_agents()
        print(f"   ✓ Found {len(self.agents)} agent configuration(s)")

        # Auto-start all discovered agents
        if self.agents:
            print(f"\n{'='*70}")
            print("STARTING AGENT SERVERS")
            print(f"{'='*70}")
            for agent_name in list(self.agents.keys()):
                logger.info(f"Auto-starting discovered agent: {agent_name}")
                await self.start_agent(agent_name)

        # Start health monitoring
        self.health_check_task = asyncio.create_task(self._health_check_loop())

        print(f"\n{'='*70}")
        print("✓ DEPLOYMENT SERVER STARTED")
        print(f"{'='*70}")
        print(f"  → Managing {len(self.agents)} agent(s)")
        print(
            f"  → Running agents: {len([a for a in self.agents.values() if a.status == 'running'])}"
        )
        print(f"{'='*70}\n")
        logger.info(f"Deployment server started. Managing {len(self.agents)} agent(s)")

    async def stop(self) -> None:
        """Stop the deployment server and all managed agents."""
        logger.info("Stopping deployment server...")
        self.running = False

        # Cancel API task
        if self.api_task:
            self.api_task.cancel()
            try:
                await self.api_task
            except asyncio.CancelledError:
                pass

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

            print(f"\n  🚀 Starting Agent Server: {agent_name}")
            print(f"     → Agent will listen on port: {agent.port}")
            print(f"     → Working directory: {agent.config_path.parent}")

            # Build command to start agent in server mode
            # This will be: atoll --server --port {port} --agent {config_path}
            # Use config filename only since cwd is set to agent directory
            cmd = [
                sys.executable,
                "-m",
                "atoll",
                "--server",
                "--port",
                str(agent.port),
                "--agent",
                agent.config_path.name,  # Just the filename, not full path
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
            print(f"     → Process ID: {agent.pid}")

            # Wait a bit to see if it starts successfully
            await asyncio.sleep(2)

            if agent.process.poll() is None:
                # Still running
                agent.status = "running"
                print(f"\n  ✓ Agent Server running: {agent_name}")
                print(f"     → API endpoint: http://{self.config.host}:{agent.port}")
                print(f"     → Process ID: {agent.pid}")
                print(f"     → Status: {agent.status}")
                logger.info(f"Agent {agent_name} started successfully (PID: {agent.pid})")
                return True
            else:
                # Process exited - capture full error details
                stdout, stderr = agent.process.communicate()
                agent.exit_code = agent.process.returncode
                agent.stdout_log = stdout.decode(errors="replace") if stdout else ""
                agent.stderr_log = stderr.decode(errors="replace") if stderr else ""
                agent.status = "failed"

                # Build comprehensive error message
                error_parts = [
                    f"Agent failed to start (exit code: {agent.exit_code})",
                    "\n--- STDERR ---",
                    agent.stderr_log if agent.stderr_log else "(no stderr output)",
                    "\n--- STDOUT ---",
                    agent.stdout_log if agent.stdout_log else "(no stdout output)",
                    "\n--- DIAGNOSTICS ---",
                    self._generate_diagnostics(agent),
                ]
                agent.error_message = "\n".join(error_parts)

                print(f"  ✗ {agent_name} failed to start")
                print(f"    Exit code: {agent.exit_code}")
                print(f"\n{agent.error_message}")
                logger.error(f"Agent {agent_name} failed to start:")
                logger.error(agent.error_message)
                return False

        except Exception as e:
            agent.status = "failed"
            import traceback

            error_details = [
                f"Exception during agent startup: {type(e).__name__}: {e}",
                "\n--- TRACEBACK ---",
                traceback.format_exc(),
                "\n--- DIAGNOSTICS ---",
                self._generate_diagnostics(agent),
            ]
            agent.error_message = "\n".join(error_details)
            logger.error(f"Failed to start agent {agent_name}:")
            logger.error(agent.error_message)
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
        # Find next available port
        port = self.find_available_port(self.next_port)
        if port is None:
            # Fallback to incrementing if search fails
            port = self.next_port
            self.next_port += 1
        else:
            self.next_port = port + 1
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

        Note: The deployment server itself doesn't listen on a port - it manages
        agent subprocesses. This validation ensures we can allocate ports for agents.

        Returns:
            Tuple of (success, message, base_port_for_agents)
        """
        # Check if enabled
        if not self.config.enabled:
            return False, "Local deployment server is disabled in configuration", None

        # Auto-discover API port if enabled
        if self.config.auto_discover_port:
            # Find available port for REST API
            api_port = self.find_available_port(self.config.api_port)
            if api_port is None:
                return (
                    False,
                    f"No available ports found for REST API starting from {self.config.api_port}",
                    None,
                )

            if api_port != self.config.api_port:
                logger.info(
                    f"REST API port changed to {api_port} (port {self.config.api_port} was in use)"
                )
                self.config.api_port = api_port

        # Set up port range for agents
        if self.config.auto_discover_port:
            # Find first available port in range for agent allocation
            port = self.find_available_port(self.config.base_port)
            if port is None:
                return (
                    False,
                    f"No available ports found starting from {self.config.base_port}",
                    None,
                )

            if port != self.config.base_port:
                logger.info(
                    f"Agent port range starts at {port} (base port {self.config.base_port} was in use)"
                )
                self.next_port = port
                self.config.base_port = port
            else:
                self.next_port = port
        else:
            # Use configured base port
            self.next_port = self.config.base_port

        # Check agents directory
        if self.config.agents_directory:
            if not self.config.agents_directory.exists():
                logger.warning(f"Agents directory does not exist: {self.config.agents_directory}")

        return True, "Local deployment server validated successfully", self.next_port

    def _generate_diagnostics(self, agent: AgentInstance) -> str:
        """Generate diagnostic information for failed agent startup.

        Args:
            agent: The agent instance that failed

        Returns:
            Formatted diagnostic string with actionable suggestions
        """
        diagnostics = []

        # Check Python version
        python_version = (
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        )
        diagnostics.append(f"Python version: {python_version}")

        # Python 3.14 known issue
        if sys.version_info >= (3, 14):
            diagnostics.append("⚠️  WARNING: Python 3.14+ detected")
            diagnostics.append("   LangChain's Pydantic V1 compatibility may cause issues")
            diagnostics.append("   RECOMMENDED: Use Python 3.11 or 3.13")

        # Check configuration file
        if agent.config_path and agent.config_path.exists():
            diagnostics.append(f"Config file: {agent.config_path} (exists)")

            # Check for common config issues
            try:
                if agent.config_path.suffix == ".toml":
                    config = TOMLAgentConfig.from_toml_file(str(agent.config_path))

                    # Check Python version requirement
                    if config.dependencies and config.dependencies.python:
                        diagnostics.append(f"Required Python: {config.dependencies.python}")

                    # Check if packages are listed
                    if config.dependencies and config.dependencies.packages:
                        diagnostics.append(
                            f"Dependencies: {len(config.dependencies.packages)} packages required"
                        )
                        diagnostics.append(
                            f"  Packages: {', '.join(config.dependencies.packages[:5])}"
                        )
                        if len(config.dependencies.packages) > 5:
                            diagnostics.append(
                                f"  ... and {len(config.dependencies.packages) - 5} more"
                            )

            except Exception as e:
                diagnostics.append(f"⚠️  Config parsing error: {e}")

        else:
            diagnostics.append(f"⚠️  Config file not found: {agent.config_path}")

        # Check working directory
        if agent.config_path:
            work_dir = agent.config_path.parent
            diagnostics.append(f"Working directory: {work_dir}")

            # Check for common files
            has_main = (work_dir / "main.py").exists()
            has_requirements = (work_dir / "requirements.txt").exists()
            has_venv = (work_dir / ".venv").exists()

            diagnostics.append(f"  main.py: {'✓ found' if has_main else '✗ missing'}")
            diagnostics.append(
                f"  requirements.txt: {'✓ found' if has_requirements else '✗ missing'}"
            )
            diagnostics.append(
                f"  .venv: {'✓ found' if has_venv else '✗ missing (no virtual environment)'}"
            )

        # Common error patterns
        if agent.stderr_log:
            stderr_lower = agent.stderr_log.lower()

            if "modulenotfounderror" in stderr_lower or "importerror" in stderr_lower:
                diagnostics.append("\\n💡 LIKELY CAUSE: Missing Python dependencies")
                diagnostics.append(
                    "   FIX: Install dependencies in the agent's virtual environment:"
                )
                if agent.config_path:
                    venv_path = agent.config_path.parent / ".venv"
                    pip_exe = get_venv_pip_path(venv_path)
                    diagnostics.append(f"   {pip_exe} install -r requirements.txt")

            elif "pydantic" in stderr_lower and "v1" in stderr_lower:
                diagnostics.append("\\n💡 LIKELY CAUSE: Pydantic V1 compatibility with Python 3.14+")
                diagnostics.append("   FIX: Use Python 3.11 or 3.13 instead of 3.14")
                diagnostics.append("   OR: Wait for LangChain to fully support Python 3.14")

            elif "port" in stderr_lower and ("in use" in stderr_lower or "bind" in stderr_lower):
                diagnostics.append(f"\\n💡 LIKELY CAUSE: Port {agent.port} already in use")
                diagnostics.append("   FIX: Stop other services using that port, or")
                diagnostics.append("   change 'base_port' in deployment server config")

            elif "permission" in stderr_lower or "access denied" in stderr_lower:
                diagnostics.append("\\n💡 LIKELY CAUSE: Permission/access error")
                diagnostics.append(
                    "   FIX: Check file permissions and try running with appropriate privileges"
                )

            elif "connection" in stderr_lower and "refused" in stderr_lower:
                diagnostics.append("\\n💡 LIKELY CAUSE: Cannot connect to required service")
                diagnostics.append(
                    "   FIX: Ensure Ollama, Ghidra, or other required services are running"
                )

        # General suggestions
        diagnostics.append("\\n📋 TROUBLESHOOTING STEPS:")
        diagnostics.append("   1. Check the STDERR and STDOUT logs above for specific errors")
        diagnostics.append("   2. Verify all dependencies are installed in the virtual environment")
        diagnostics.append(
            "   3. Test the agent configuration with: atoll --agent <config_path> --test"
        )
        diagnostics.append("   4. Check system logs for more details")

        if agent.config_path:
            diagnostics.append(
                f"   5. Review agent documentation: {agent.config_path.parent / 'README.md'}"
            )

        return "\\n".join(diagnostics)

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
        lines.append("DEPLOYMENT INFRASTRUCTURE STATUS")
        lines.append("=" * 70)

        # Local server status
        success, message, base_port = await self.validate_local_server()
        lines.append("\n[DEPLOYMENT SERVER]")
        lines.append("  Type: Local Process Manager + REST API")
        lines.append("  Function: Manages agent lifecycle and provides remote deployment API")
        if success:
            lines.append("  Status: ✓ Running")
            lines.append(f"  Host: {self.config.host}")
            lines.append(f"  REST API: http://{self.config.host}:{self.config.api_port}")
            lines.append("  API Endpoints:")
            lines.append("    → POST /agents/deploy - Deploy agent package")
            lines.append("    → GET /agents - List all agents")
            lines.append("    → POST /agents/{name}/start - Start agent")
            lines.append("    → POST /agents/{name}/stop - Stop agent")
            lines.append(f"  Agents Directory: {self.config.agents_directory or 'Not configured'}")
            lines.append(
                f"  Agent Port Range: {base_port}-{base_port + self.config.max_agents - 1}"
            )
            lines.append(f"  Managed Agents: {len(self.agents)}")
            lines.append(
                f"  Running Agents: {len([a for a in self.agents.values() if a.status == 'running'])}"
            )
        else:
            lines.append(f"  Status: ✗ FAILED - {message}")
            lines.append("  Action Required: Fix the issue above and restart ATOLL")

        # Agent servers status
        if self.agents:
            lines.append("\n[AGENT SERVERS] (Individual API Endpoints)")
            for name, agent in self.agents.items():
                is_running = agent.process and agent.process.poll() is None
                if is_running:
                    status_icon = "✓"
                    status_text = "Running"
                elif agent.status == "failed":
                    status_icon = "✗"
                    status_text = "Failed to start"
                else:
                    status_icon = "○"
                    status_text = "Stopped"

                lines.append(f"\n  {status_icon} {name}")
                if agent.port:
                    lines.append(f"     → API Endpoint: http://{self.config.host}:{agent.port}")
                    lines.append(f"     → Port: {agent.port}")
                if agent.pid:
                    lines.append(f"     → Process ID: {agent.pid}")
                lines.append(f"     → Status: {status_text}")
                if agent.error_message:
                    lines.append(f"     → Error: {agent.error_message}")
                    if agent.error_details:
                        lines.append(f"\n{agent.error_details}")

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
