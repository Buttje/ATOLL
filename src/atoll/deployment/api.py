"""REST API for ATOLL Deployment Server.

This module provides HTTP endpoints for remote agent management.
"""

import hashlib
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
import venv
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, File, HTTPException, Security, UploadFile, status
from fastapi.security import APIKeyHeader
from fastapi.responses import Response
from pydantic import BaseModel

from ..utils.venv_utils import get_venv_pip_path
from .metrics import get_metrics, get_metrics_content, is_prometheus_available
from .server import AgentInstance, DeploymentServer

logger = logging.getLogger(__name__)

# Security: API Key authentication
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


# API Models
class DeployAgentRequest(BaseModel):
    """Request to deploy an agent package."""

    name: Optional[str] = None  # Optional, can be inferred from package
    force: bool = False  # Force reinstall even if checksum matches


class AgentActionRequest(BaseModel):
    """Request to start/stop/restart an agent."""

    agent_name: str


class AgentStatusResponse(BaseModel):
    """Response with agent status."""

    name: str
    status: str  # discovered, starting, running, stopped, failed
    port: Optional[int] = None
    pid: Optional[int] = None
    checksum: Optional[str] = None
    error_message: Optional[str] = None


class DeploymentServerAPI:
    """FastAPI application for deployment server."""

    def __init__(
        self,
        deployment_server: DeploymentServer,
        storage_path: Path,
        require_auth: bool = True,
        api_key: Optional[str] = None,
    ):
        """Initialize API.

        Args:
            deployment_server: The deployment server instance
            storage_path: Path to store agent packages and metadata
            require_auth: Whether to require API key authentication
            api_key: The API key to use (or from ATOLL_API_KEY env var)
        """
        self.server = deployment_server
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Authentication configuration
        self.require_auth = require_auth
        self.api_key = api_key or os.getenv("ATOLL_API_KEY")

        if self.require_auth and not self.api_key:
            logger.warning(
                "Authentication enabled but no API key configured. "
                "Set ATOLL_API_KEY environment variable or disable auth."
            )

        # Metrics
        self.metrics = get_metrics()

        # Persistent storage - use deployment server's metadata store
        # Checksum database is now part of metadata store

        # Create FastAPI app
        self.checksum_db_path = storage_path / "checksums.json"
        self.checksums: dict[str, str] = self._load_checksums()

        # Create FastAPI app
        self.app = FastAPI(
            title="ATOLL Deployment Server API",
            description="REST API for managing ATOLL agent deployments",
            version="2.0.0",
        )

        # Register routes
        self._register_routes()

    def _verify_api_key(self, api_key: Optional[str] = Security(api_key_header)) -> bool:
        """Verify API key for authentication.

        Args:
            api_key: API key from request header

        Returns:
            True if authentication is disabled or key is valid

        Raises:
            HTTPException: If authentication fails
        """
        # Authentication disabled
        if not self.require_auth:
            return True

        # No API key in request
        if not api_key:
            self.metrics.record_auth_attempt("failure")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required. Provide X-API-Key header.",
            )

        # Invalid API key
        if api_key != self.api_key:
            logger.warning(f"Invalid API key attempt: {api_key[:10]}...")
            self.metrics.record_auth_attempt("failure")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )

        self.metrics.record_auth_attempt("success")
        return True

    def _load_checksums(self) -> dict[str, str]:
        """Load checksum database from disk."""
        if self.checksum_db_path.exists():
            try:
                with open(self.checksum_db_path) as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load checksums: {e}")
        return {}

    def _save_checksums(self) -> None:
        """Save checksum database to disk."""
        try:
            with open(self.checksum_db_path, "w") as f:
                json.dump(self.checksums, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save checksums: {e}")

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of a file."""
        md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5.update(chunk)
        return md5.hexdigest()

    async def _create_venv(self, agent_path: Path) -> bool:
        """Create virtual environment for agent.

        Args:
            agent_path: Path to agent directory

        Returns:
            True if successful
        """
        venv_path = agent_path / ".venv"

        try:
            # Create venv
            logger.info(f"Creating virtual environment at {venv_path}")
            print("  → Creating venv with pip...")
            venv.create(venv_path, with_pip=True)
            print("  ✓ Virtual environment created")

            # Install dependencies if requirements.txt exists
            requirements_file = agent_path / "requirements.txt"
            if requirements_file.exists():
                print("\n📦 Installing dependencies...")
                print(f"  → Requirements file: {requirements_file}")
                logger.info("Installing dependencies from requirements.txt")

                # Get pip executable using cross-platform utility
                pip_exe = get_venv_pip_path(venv_path)

                print(f"  → Using pip: {pip_exe}")
                print("  → Installing packages (this may take a while)...")

                # Install requirements
                result = subprocess.run(
                    [str(pip_exe), "install", "-r", str(requirements_file)],
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    print("  ✗ Failed to install dependencies!")
                    print(f"  Error: {result.stderr}")
                    logger.error(f"Failed to install dependencies: {result.stderr}")
                    return False

                # Count installed packages
                installed_packages = [
                    line for line in result.stdout.split("\n") if "Successfully installed" in line
                ]
                if installed_packages:
                    print("  ✓ Dependencies installed successfully")
                else:
                    print("  ✓ All dependencies already satisfied")

            return True

        except Exception as e:
            print(f"  ✗ Failed to create virtual environment: {e}")
            logger.error(f"Failed to create venv: {e}")
            return False

    def _register_routes(self) -> None:
        """Register API routes."""

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint (no authentication required)."""
            self.metrics.health_checks_total.labels(status="success").inc()
            return {
                "status": "healthy",
                "version": "2.0.0",
                "auth_enabled": self.require_auth,
                "metrics_enabled": is_prometheus_available(),
            }

        @self.app.get("/metrics")
        async def metrics_endpoint():
            """Prometheus metrics endpoint (no authentication required).

            Returns metrics in Prometheus exposition format for scraping.
            Install prometheus-client to enable: pip install atoll[monitoring]
            """
            # Update agent count metrics before serving
            status_counts = {}
            for agent in self.server.agents.values():
                status = agent.status
                status_counts[status] = status_counts.get(status, 0) + 1

            self.metrics.update_agent_counts(status_counts)
            self.metrics.set_allocated_ports(len(self.server.port_manager.allocated_ports))

            # Count active processes
            active_count = sum(
                1
                for agent in self.server.agents.values()
                if agent.process and agent.process.poll() is None
            )
            self.metrics.set_active_processes(active_count)

            # Return metrics in Prometheus format
            content, content_type = get_metrics_content()
            return Response(content=content, media_type=content_type)

        @self.app.get("/agents", dependencies=[Depends(self._verify_api_key)])
        async def list_agents():
            """List all agents."""
            agents = []
            for name, agent in self.server.agents.items():
                agents.append(
                    {
                        "name": name,
                        "status": agent.status,
                        "port": agent.port,
                        "pid": agent.pid,
                        "checksum": self.checksums.get(name),
                        "config_path": str(agent.config_path),
                    }
                )
            return {"agents": agents, "count": len(agents)}

        @self.app.post("/check", dependencies=[Depends(self._verify_api_key)])
        async def check_agent(checksum: str):
            """Check if agent with checksum exists.

            Args:
                checksum: MD5 checksum of agent package

            Returns:
                Information about whether agent exists and its status
            """
            # Find agent by checksum
            agent_name = None
            for name, stored_checksum in self.checksums.items():
                if stored_checksum == checksum:
                    agent_name = name
                    break

            if agent_name and agent_name in self.server.agents:
                agent = self.server.agents[agent_name]
                return {
                    "exists": True,
                    "name": agent_name,
                    "status": agent.status,
                    "port": agent.port,
                    "running": agent.process and agent.process.poll() is None,
                }
            else:
                return {
                    "exists": False,
                    "message": "Agent not found. Upload required.",
                }

        @self.app.post("/deploy", dependencies=[Depends(self._verify_api_key)])
        async def deploy_agent(file: UploadFile = File(...), force: bool = False):
            """Deploy agent from ZIP package.

            Args:
                file: ZIP file containing agent package
                force: Force reinstall even if agent exists

            Returns:
                Deployment result with agent information
            """
            if not file.filename or not file.filename.endswith(".zip"):
                raise HTTPException(status_code=400, detail="File must be a ZIP archive")

            print(f"\n{'='*70}")
            print("DEPLOYING AGENT FROM ZIP PACKAGE")
            print(f"{'='*70}")
            print(f"  → Filename: {file.filename}")

            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
                content = await file.read()
                tmp.write(content)
                tmp_path = Path(tmp.name)

            print(f"  → Temporary file: {tmp_path}")

            try:
                # Calculate checksum
                print("\n📊 Calculating MD5 checksum...")
                checksum = self._calculate_checksum(tmp_path)
                print(f"  → MD5: {checksum}")

                # Check if agent already exists
                if not force:
                    print("\n🔍 Checking if agent already installed...")
                    for name, stored_checksum in self.checksums.items():
                        if stored_checksum == checksum:
                            print(f"  ✓ Agent '{name}' already installed with this checksum")
                            print("    Use force=true to reinstall")
                            logger.info(f"Agent {name} already installed with this checksum")
                            self.metrics.record_deployment("cached")
                            self.metrics.checksum_cache_hits.inc()
                            return {
                                "status": "already_installed",
                                "name": name,
                                "checksum": checksum,
                                "message": "Agent already installed. Use force=true to reinstall.",
                            }
                    print("  → Agent not found, proceeding with installation")

                # Extract ZIP
                extract_path = self.storage_path / f"agent_{checksum[:8]}"
                extract_path.mkdir(parents=True, exist_ok=True)

                print("\n📦 Unpacking ZIP archive...")
                print(f"  → Extraction directory: {extract_path}")

                with zipfile.ZipFile(tmp_path) as zf:
                    zf.extractall(extract_path)
                    print(f"  ✓ Extracted {len(zf.namelist())} file(s)")

                # Find agent.toml or agent.json
                print("\n🔎 Looking for agent configuration...")
                config_path = extract_path / "agent.toml"
                if not config_path.exists():
                    config_path = extract_path / "agent.json"
                    if not config_path.exists():
                        print("  ✗ Configuration file not found!")
                        raise HTTPException(
                            status_code=400,
                            detail="Package must contain agent.toml or agent.json",
                        )
                print(f"  ✓ Found: {config_path.name}")

                # Read agent name from config
                print("\n📖 Reading agent configuration...")
                if config_path.suffix == ".toml":
                    try:
                        import tomllib  # Python 3.11+
                    except ImportError:
                        import tomli as tomllib  # Python <3.11

                    with open(config_path, "rb") as f:
                        config_data = tomllib.load(f)
                    agent_name = config_data.get("agent", {}).get("name")
                else:
                    with open(config_path) as f:
                        config_data = json.load(f)
                    agent_name = config_data.get("agent", {}).get("name")

                if not agent_name:
                    print("  ✗ Agent name not found in configuration!")
                    raise HTTPException(
                        status_code=400, detail="Agent configuration missing 'name' field"
                    )
                print(f"  → Agent name: {agent_name}")
                print(
                    f"  → Agent version: {config_data.get('agent', {}).get('version', 'unknown')}"
                )

                # Create virtual environment
                print("\n🐍 Creating virtual environment...")
                venv_path = extract_path / ".venv"
                print(f"  → Virtual environment path: {venv_path}")
                venv_success = await self._create_venv(extract_path)
                if not venv_success:
                    print("  ✗ Failed to create virtual environment!")
                    raise HTTPException(
                        status_code=500, detail="Failed to create virtual environment"
                    )
                print("  ✓ Virtual environment created successfully")

                # Register agent
                print("\n📝 Registering agent with deployment server...")
                agent_instance = AgentInstance(
                    name=agent_name,
                    config_path=config_path,
                    status="discovered",
                )
                self.server.agents[agent_name] = agent_instance
                print(f"  ✓ Agent '{agent_name}' registered")

                # Store checksum
                self.checksums[agent_name] = checksum
                self._save_checksums()
                print("  ✓ Checksum stored")

                print(f"\n✅ Successfully deployed agent '{agent_name}'")
                print(f"{'='*70}\n")
                logger.info(f"Successfully deployed agent {agent_name}")

                # Record metrics
                duration = time.time() - start_time
                self.metrics.record_deployment("success", duration)
                self.metrics.checksum_cache_misses.inc()

                return {
                    "status": "deployed",
                    "name": agent_name,
                    "checksum": checksum,
                    "config_path": str(config_path),
                    "message": f"Agent {agent_name} deployed successfully",
                }

            except HTTPException:
                self.metrics.record_deployment("failure")
                raise
            except Exception as e:
                logger.error(f"Deployment failed: {e}")
                self.metrics.record_deployment("failure")
                raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")
            finally:
                # Clean up temp file
                tmp_path.unlink(missing_ok=True)

        @self.app.post("/start", dependencies=[Depends(self._verify_api_key)])
        async def start_agent(request: AgentActionRequest):
            """Start an agent."""
            success = await self.server.start_agent(request.agent_name)
            if success:
                agent = self.server.agents[request.agent_name]
                self.metrics.record_agent_start("success")
                return {
                    "status": "started",
                    "name": request.agent_name,
                    "port": agent.port,
                    "pid": agent.pid,
                }
            else:
                agent = self.server.agents.get(request.agent_name)
                error_msg = agent.error_message if agent else "Agent not found"
                self.metrics.record_agent_start("failure")
                if agent:
                    self.metrics.record_agent_failure(request.agent_name, error_msg or "unknown")
                raise HTTPException(status_code=500, detail=f"Failed to start agent: {error_msg}")

        @self.app.post("/stop", dependencies=[Depends(self._verify_api_key)])
        async def stop_agent(request: AgentActionRequest):
            """Stop an agent."""
            success = await self.server.stop_agent(request.agent_name)
            if success:
                self.metrics.agent_stops_total.inc()
                return {
                    "status": "stopped",
                    "name": request.agent_name,
                }
            else:
                raise HTTPException(status_code=404, detail="Agent not found or not running")

        @self.app.post("/restart", dependencies=[Depends(self._verify_api_key)])
        async def restart_agent(request: AgentActionRequest):
            """Restart an agent."""
            success = await self.server.restart_agent(request.agent_name)
            if success:
                agent = self.server.agents[request.agent_name]
                self.metrics.agent_restarts_total.inc()
                return {
                    "status": "restarted",
                    "name": request.agent_name,
                    "port": agent.port,
                    "pid": agent.pid,
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to restart agent")

        @self.app.get("/status/{agent_name}", dependencies=[Depends(self._verify_api_key)])
        async def get_agent_status(agent_name: str):
            """Get status of a specific agent."""
            if agent_name not in self.server.agents:
                raise HTTPException(status_code=404, detail="Agent not found")

            agent = self.server.agents[agent_name]
            return {
                "name": agent_name,
                "status": agent.status,
                "port": agent.port,
                "pid": agent.pid,
                "checksum": self.checksums.get(agent_name),
                "start_time": agent.start_time.isoformat() if agent.start_time else None,
                "restart_count": agent.restart_count,
                "health_status": agent.health_status,
                "error_message": agent.error_message,
            }

        @self.app.get("/agents/{agent_name}/diagnostics", dependencies=[Depends(self._verify_api_key)])
        async def get_agent_diagnostics(agent_name: str):
            """Get diagnostic information for an agent.

            Returns detailed diagnostics including:
            - Configuration validation
            - Python version compatibility
            - Port conflict detection
            - Dependency issues
            - Captured stdout/stderr logs

            Args:
                agent_name: Name of the agent

            Returns:
                Diagnostic report with analysis and recommendations
            """
            if agent_name not in self.server.agents:
                raise HTTPException(status_code=404, detail="Agent not found")

            agent = self.server.agents[agent_name]

            # Generate diagnostics
            diagnostics_text = self.server._generate_diagnostics(agent)

            return {
                "agent_name": agent_name,
                "status": agent.status,
                "diagnostics": diagnostics_text,
                "error_message": agent.error_message,
                "exit_code": agent.exit_code,
                "stdout": agent.stdout_log,
                "stderr": agent.stderr_log,
                "config_path": str(agent.config_path),
                "timestamp": datetime.now().isoformat(),
            }

            agent = self.server.agents[agent_name]
            is_running = agent.process and agent.process.poll() is None

            return AgentStatusResponse(
                name=agent_name,
                status=agent.status if is_running else "stopped",
                port=agent.port,
                pid=agent.pid,
                checksum=self.checksums.get(agent_name),
                error_message=agent.error_message,
            )


async def run_api_server(
    deployment_server: DeploymentServer,
    host: str = "localhost",
    port: int = 8080,
    storage_path: Optional[Path] = None,
):
    """Run the deployment server API.

    Args:
        deployment_server: Deployment server instance
        host: Host to bind to
        port: Port to bind to
        storage_path: Path for storing agent packages
    """
    import uvicorn

    if storage_path is None:
        storage_path = Path.home() / ".atoll_deployment" / "agents"

    api = DeploymentServerAPI(deployment_server, storage_path)

    config = uvicorn.Config(
        api.app,
        host=host,
        port=port,
        log_level="info",
    )

    server = uvicorn.Server(config)
    await server.serve()
