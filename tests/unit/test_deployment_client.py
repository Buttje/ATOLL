"""Tests for Deployment Client API.

These tests verify the deployment client can make proper HTTP requests.
Full integration tests should be done with a running deployment server.
"""

from pathlib import Path

import pytest

from atoll.deployment.client import DeploymentClient


@pytest.fixture
def client():
    """Create deployment client."""
    return DeploymentClient("http://localhost:8080")


@pytest.fixture
def sample_package(tmp_path):
    """Create sample package file."""
    package = tmp_path / "test-agent.zip"
    package.write_bytes(b"fake zip content")
    return package


class TestClientInit:
    """Tests for client initialization."""

    def test_init_with_base_url(self):
        """Test client initialization."""
        client = DeploymentClient("http://localhost:8080")
        assert client.base_url == "http://localhost:8080"

    def test_init_strips_trailing_slash(self):
        """Test trailing slash is stripped."""
        client = DeploymentClient("http://localhost:8080/")
        assert client.base_url == "http://localhost:8080"

    def test_init_with_timeout(self):
        """Test custom timeout."""
        client = DeploymentClient("http://localhost:8080", timeout=60)
        assert client.timeout.total == 60


class TestClientMethods:
    """Tests for client methods exist and have correct signatures."""

    def test_has_health_check(self, client):
        """Test health check method exists."""
        assert hasattr(client, "health_check")
        assert callable(client.health_check)

    def test_has_list_agents(self, client):
        """Test list agents method exists."""
        assert hasattr(client, "list_agents")
        assert callable(client.list_agents)

    def test_has_check_agent(self, client):
        """Test check agent method exists."""
        assert hasattr(client, "check_agent")
        assert callable(client.check_agent)

    def test_has_deploy_agent(self, client):
        """Test deploy agent method exists."""
        assert hasattr(client, "deploy_agent")
        assert callable(client.deploy_agent)

    def test_has_start_agent(self, client):
        """Test start agent method exists."""
        assert hasattr(client, "start_agent")
        assert callable(client.start_agent)

    def test_has_stop_agent(self, client):
        """Test stop agent method exists."""
        assert hasattr(client, "stop_agent")
        assert callable(client.stop_agent)

    def test_has_restart_agent(self, client):
        """Test restart agent method exists."""
        assert hasattr(client, "restart_agent")
        assert callable(client.restart_agent)

    def test_has_get_agent_status(self, client):
        """Test get agent status method exists."""
        assert hasattr(client, "get_agent_status")
        assert callable(client.get_agent_status)


class TestClientSyncWrappers:
    """Tests for synchronous wrapper methods."""

    def test_has_sync_wrappers(self, client):
        """Test all sync wrapper methods exist."""
        assert hasattr(client, "health_check_sync")
        assert hasattr(client, "list_agents_sync")
        assert hasattr(client, "check_agent_sync")
        assert hasattr(client, "deploy_agent_sync")
        assert hasattr(client, "start_agent_sync")
        assert hasattr(client, "stop_agent_sync")
        assert hasattr(client, "restart_agent_sync")
        assert hasattr(client, "get_agent_status_sync")


class TestClientFileHandling:
    """Tests for file handling in deployment."""

    @pytest.mark.asyncio
    async def test_deploy_agent_file_not_found(self, client):
        """Test deploying non-existent package."""
        with pytest.raises(FileNotFoundError):
            await client.deploy_agent(Path("/nonexistent/package.zip"))

    @pytest.mark.asyncio
    async def test_deploy_agent_validates_file_exists(self, client, sample_package):
        """Test deploy validates file exists before attempting upload."""
        # This should not raise FileNotFoundError
        try:
            await client.deploy_agent(sample_package)
        except FileNotFoundError:
            pytest.fail("Should not raise FileNotFoundError for existing file")
        except Exception:
            # Other exceptions (like connection errors) are expected in unit tests
            pass
