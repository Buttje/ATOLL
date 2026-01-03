"""Client for connecting to ATOLL Deployment Server API.

This module provides a client for interacting with remote deployment servers.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class DeploymentClient:
    """Client for ATOLL Deployment Server API."""

    def __init__(self, base_url: str, timeout: int = 30):
        """Initialize client.

        Args:
            base_url: Base URL of deployment server (e.g., http://localhost:8080)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    async def health_check(self) -> dict[str, Any]:
        """Check if server is healthy.

        Returns:
            Health check response

        Raises:
            aiohttp.ClientError: If request fails
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(f"{self.base_url}/health") as response:
                response.raise_for_status()
                return await response.json()

    async def list_agents(self) -> list[dict[str, Any]]:
        """List all agents on server.

        Returns:
            List of agent information

        Raises:
            aiohttp.ClientError: If request fails
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(f"{self.base_url}/agents") as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("agents", [])

    async def check_agent(self, checksum: str) -> dict[str, Any]:
        """Check if agent with checksum exists.

        Args:
            checksum: MD5 checksum of agent package

        Returns:
            Information about agent existence

        Raises:
            aiohttp.ClientError: If request fails
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session, session.post(
            f"{self.base_url}/check",
            params={"checksum": checksum},
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def deploy_agent(
        self,
        package_path: Path,
        force: bool = False,
    ) -> dict[str, Any]:
        """Deploy agent from ZIP package.

        Args:
            package_path: Path to ZIP package
            force: Force reinstall even if agent exists

        Returns:
            Deployment result

        Raises:
            aiohttp.ClientError: If request fails
            FileNotFoundError: If package doesn't exist
        """
        if not package_path.exists():
            raise FileNotFoundError(f"Package not found: {package_path}")

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            with open(package_path, "rb") as f:
                data = aiohttp.FormData()
                data.add_field(
                    "file",
                    f,
                    filename=package_path.name,
                    content_type="application/zip",
                )

                async with session.post(
                    f"{self.base_url}/deploy",
                    data=data,
                    params={"force": force},
                ) as response:
                    response.raise_for_status()
                    return await response.json()

    async def start_agent(self, agent_name: str) -> dict[str, Any]:
        """Start an agent.

        Args:
            agent_name: Name of agent to start

        Returns:
            Start result

        Raises:
            aiohttp.ClientError: If request fails
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session, session.post(
            f"{self.base_url}/start",
            json={"agent_name": agent_name},
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def stop_agent(self, agent_name: str) -> dict[str, Any]:
        """Stop an agent.

        Args:
            agent_name: Name of agent to stop

        Returns:
            Stop result

        Raises:
            aiohttp.ClientError: If request fails
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session, session.post(
            f"{self.base_url}/stop",
            json={"agent_name": agent_name},
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def restart_agent(self, agent_name: str) -> dict[str, Any]:
        """Restart an agent.

        Args:
            agent_name: Name of agent to restart

        Returns:
            Restart result

        Raises:
            aiohttp.ClientError: If request fails
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session, session.post(
            f"{self.base_url}/restart",
            json={"agent_name": agent_name},
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def get_agent_status(self, agent_name: str) -> dict[str, Any]:
        """Get status of specific agent.

        Args:
            agent_name: Name of agent

        Returns:
            Agent status information

        Raises:
            aiohttp.ClientError: If request fails
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(f"{self.base_url}/status/{agent_name}") as response:
                response.raise_for_status()
                return await response.json()

    # Synchronous wrappers for convenience
    def health_check_sync(self) -> dict[str, Any]:
        """Synchronous wrapper for health_check."""
        return asyncio.run(self.health_check())

    def list_agents_sync(self) -> list[dict[str, Any]]:
        """Synchronous wrapper for list_agents."""
        return asyncio.run(self.list_agents())

    def check_agent_sync(self, checksum: str) -> dict[str, Any]:
        """Synchronous wrapper for check_agent."""
        return asyncio.run(self.check_agent(checksum))

    def deploy_agent_sync(
        self,
        package_path: Path,
        force: bool = False,
    ) -> dict[str, Any]:
        """Synchronous wrapper for deploy_agent."""
        return asyncio.run(self.deploy_agent(package_path, force))

    def start_agent_sync(self, agent_name: str) -> dict[str, Any]:
        """Synchronous wrapper for start_agent."""
        return asyncio.run(self.start_agent(agent_name))

    def stop_agent_sync(self, agent_name: str) -> dict[str, Any]:
        """Synchronous wrapper for stop_agent."""
        return asyncio.run(self.stop_agent(agent_name))

    def restart_agent_sync(self, agent_name: str) -> dict[str, Any]:
        """Synchronous wrapper for restart_agent."""
        return asyncio.run(self.restart_agent(agent_name))

    def get_agent_status_sync(self, agent_name: str) -> dict[str, Any]:
        """Synchronous wrapper for get_agent_status."""
        return asyncio.run(self.get_agent_status(agent_name))
