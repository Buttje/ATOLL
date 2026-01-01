"""Tests for Deployment Server API (v2.0 features)."""

import hashlib
import json
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from atoll.deployment.api import DeploymentServerAPI
from atoll.deployment.server import AgentInstance, DeploymentServer


@pytest.fixture
def temp_storage(tmp_path):
    """Create temporary storage directory."""
    storage = tmp_path / "storage"
    storage.mkdir()
    return storage


@pytest.fixture
def mock_deployment_server():
    """Create mock deployment server."""
    server = MagicMock(spec=DeploymentServer)
    server.agents = {}
    server.start_agent = AsyncMock(return_value=True)
    server.stop_agent = AsyncMock(return_value=True)
    server.restart_agent = AsyncMock(return_value=True)
    return server


@pytest.fixture
def api_server(mock_deployment_server, temp_storage):
    """Create API server instance."""
    return DeploymentServerAPI(mock_deployment_server, temp_storage)


@pytest.fixture
def test_client(api_server):
    """Create FastAPI test client."""
    return TestClient(api_server.app)


@pytest.fixture
def sample_agent_package(tmp_path):
    """Create a sample agent ZIP package."""
    agent_dir = tmp_path / "sample_agent"
    agent_dir.mkdir()

    # Create agent.json
    agent_config = {
        "agent": {
            "name": "test-agent",
            "description": "Test agent for deployment",
        }
    }
    with open(agent_dir / "agent.json", "w") as f:
        json.dump(agent_config, f)

    # Create requirements.txt
    with open(agent_dir / "requirements.txt", "w") as f:
        f.write("requests>=2.31.0\n")

    # Create main script
    with open(agent_dir / "main.py", "w") as f:
        f.write("print('Hello from agent')\n")

    # Create ZIP package
    zip_path = tmp_path / "test-agent.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for file in agent_dir.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(agent_dir))

    return zip_path


class TestAPIHealthCheck:
    """Tests for health check endpoint."""

    def test_health_check(self, test_client):
        """Test health check returns 200."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0"


class TestAPIListAgents:
    """Tests for list agents endpoint."""

    def test_list_agents_empty(self, test_client):
        """Test listing agents when none exist."""
        response = test_client.get("/agents")
        assert response.status_code == 200
        data = response.json()
        assert data["agents"] == []
        assert data["count"] == 0

    def test_list_agents_with_agents(self, test_client, mock_deployment_server, api_server):
        """Test listing agents when some exist."""
        # Add mock agents
        agent1 = AgentInstance(
            name="agent1", config_path=Path("/tmp/agent1.json"), status="running", port=8001
        )
        agent2 = AgentInstance(
            name="agent2", config_path=Path("/tmp/agent2.json"), status="stopped"
        )
        mock_deployment_server.agents = {"agent1": agent1, "agent2": agent2}

        # Store checksums
        api_server.checksums = {"agent1": "abc123", "agent2": "def456"}

        response = test_client.get("/agents")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["agents"]) == 2

        # Check agent1
        agent1_data = next(a for a in data["agents"] if a["name"] == "agent1")
        assert agent1_data["status"] == "running"
        assert agent1_data["port"] == 8001
        assert agent1_data["checksum"] == "abc123"


class TestAPICheckAgent:
    """Tests for check agent endpoint."""

    def test_check_agent_exists(self, test_client, mock_deployment_server, api_server):
        """Test checking for agent that exists."""
        # Add mock agent
        agent = AgentInstance(
            name="test-agent", config_path=Path("/tmp/agent.json"), status="running", port=8001
        )
        agent.process = MagicMock()
        agent.process.poll = MagicMock(return_value=None)  # Running
        mock_deployment_server.agents = {"test-agent": agent}
        api_server.checksums = {"test-agent": "abc123"}

        response = test_client.post("/check?checksum=abc123")
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is True
        assert data["name"] == "test-agent"
        assert data["status"] == "running"
        assert data["port"] == 8001

    def test_check_agent_not_exists(self, test_client):
        """Test checking for agent that doesn't exist."""
        response = test_client.post("/check?checksum=nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is False


class TestAPIDeployAgent:
    """Tests for deploy agent endpoint."""

    @patch("atoll.deployment.api.DeploymentServerAPI._create_venv")
    def test_deploy_agent_success(
        self, mock_create_venv, test_client, sample_agent_package, api_server
    ):
        """Test successful agent deployment."""
        mock_create_venv.return_value = AsyncMock(return_value=True)()

        # Deploy agent
        with open(sample_agent_package, "rb") as f:
            response = test_client.post(
                "/deploy", files={"file": ("test-agent.zip", f, "application/zip")}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deployed"
        assert data["name"] == "test-agent"
        assert "checksum" in data
        assert len(data["checksum"]) == 32  # MD5 hash length

        # Verify checksum stored
        assert "test-agent" in api_server.checksums

    def test_deploy_agent_invalid_file(self, test_client):
        """Test deploying with invalid file type."""
        response = test_client.post(
            "/deploy", files={"file": ("test.txt", b"not a zip", "text/plain")}
        )
        assert response.status_code == 400
        assert "ZIP archive" in response.json()["detail"]

    @patch("atoll.deployment.api.DeploymentServerAPI._create_venv")
    def test_deploy_agent_already_installed(
        self, mock_create_venv, test_client, sample_agent_package, api_server
    ):
        """Test deploying agent that's already installed."""
        mock_create_venv.return_value = AsyncMock(return_value=True)()

        # Calculate checksum
        md5 = hashlib.md5()
        with open(sample_agent_package, "rb") as f:
            md5.update(f.read())
        checksum = md5.hexdigest()

        # Pre-register checksum
        api_server.checksums = {"existing-agent": checksum}

        # Try to deploy
        with open(sample_agent_package, "rb") as f:
            response = test_client.post(
                "/deploy", files={"file": ("test-agent.zip", f, "application/zip")}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "already_installed"
        assert data["name"] == "existing-agent"

    @patch("atoll.deployment.api.DeploymentServerAPI._create_venv")
    def test_deploy_agent_force_reinstall(
        self, mock_create_venv, test_client, sample_agent_package, api_server
    ):
        """Test force reinstalling existing agent."""
        mock_create_venv.return_value = AsyncMock(return_value=True)()

        # Calculate checksum
        md5 = hashlib.md5()
        with open(sample_agent_package, "rb") as f:
            md5.update(f.read())
        checksum = md5.hexdigest()

        # Pre-register checksum
        api_server.checksums = {"existing-agent": checksum}

        # Deploy with force=true
        with open(sample_agent_package, "rb") as f:
            response = test_client.post(
                "/deploy?force=true",
                files={"file": ("test-agent.zip", f, "application/zip")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deployed"
        assert data["name"] == "test-agent"


class TestAPIStartStopAgent:
    """Tests for start/stop/restart agent endpoints."""

    def test_start_agent_success(self, test_client, mock_deployment_server):
        """Test starting an agent."""
        agent = AgentInstance(
            name="test-agent", config_path=Path("/tmp/agent.json"), status="stopped", port=8001
        )
        agent.pid = 1234
        mock_deployment_server.agents = {"test-agent": agent}

        response = test_client.post("/start", json={"agent_name": "test-agent"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert data["name"] == "test-agent"
        assert data["port"] == 8001
        assert data["pid"] == 1234

    def test_start_agent_failure(self, test_client, mock_deployment_server):
        """Test starting agent that fails."""
        # Configure mock to return False
        mock_deployment_server.start_agent = AsyncMock(return_value=False)

        agent = AgentInstance(
            name="test-agent",
            config_path=Path("/tmp/agent.json"),
            status="failed",
            error_message="Port in use",
        )
        mock_deployment_server.agents = {"test-agent": agent}

        response = test_client.post("/start", json={"agent_name": "test-agent"})

        assert response.status_code == 500
        assert "Port in use" in response.json()["detail"]

    def test_stop_agent_success(self, test_client, mock_deployment_server):
        """Test stopping an agent."""
        response = test_client.post("/stop", json={"agent_name": "test-agent"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "stopped"
        assert data["name"] == "test-agent"

    def test_restart_agent_success(self, test_client, mock_deployment_server):
        """Test restarting an agent."""
        agent = AgentInstance(
            name="test-agent", config_path=Path("/tmp/agent.json"), status="running", port=8001
        )
        agent.pid = 5678
        mock_deployment_server.agents = {"test-agent": agent}

        response = test_client.post("/restart", json={"agent_name": "test-agent"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "restarted"
        assert data["name"] == "test-agent"


class TestAPIAgentStatus:
    """Tests for agent status endpoint."""

    def test_get_agent_status_running(self, test_client, mock_deployment_server, api_server):
        """Test getting status of running agent."""
        agent = AgentInstance(
            name="test-agent", config_path=Path("/tmp/agent.json"), status="running", port=8001
        )
        agent.pid = 1234
        agent.process = MagicMock()
        agent.process.poll = MagicMock(return_value=None)  # Running
        mock_deployment_server.agents = {"test-agent": agent}
        api_server.checksums = {"test-agent": "abc123"}

        response = test_client.get("/status/test-agent")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test-agent"
        assert data["status"] == "running"
        assert data["port"] == 8001
        assert data["pid"] == 1234
        assert data["checksum"] == "abc123"

    def test_get_agent_status_not_found(self, test_client):
        """Test getting status of non-existent agent."""
        response = test_client.get("/status/nonexistent")
        assert response.status_code == 404


class TestChecksumManagement:
    """Tests for checksum tracking."""

    def test_load_checksums(self, temp_storage):
        """Test loading checksums from disk."""
        # Create checksum file
        checksums_data = {"agent1": "abc123", "agent2": "def456"}
        with open(temp_storage / "checksums.json", "w") as f:
            json.dump(checksums_data, f)

        # Create API (should load checksums)
        server = MagicMock(spec=DeploymentServer)
        server.agents = {}
        api = DeploymentServerAPI(server, temp_storage)

        assert api.checksums == checksums_data

    def test_save_checksums(self, api_server, temp_storage):
        """Test saving checksums to disk."""
        api_server.checksums = {"agent1": "abc123", "agent2": "def456"}
        api_server._save_checksums()

        # Verify file created
        checksum_file = temp_storage / "checksums.json"
        assert checksum_file.exists()

        # Verify content
        with open(checksum_file) as f:
            data = json.load(f)
        assert data == api_server.checksums

    def test_calculate_checksum(self, api_server, tmp_path):
        """Test MD5 checksum calculation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        checksum = api_server._calculate_checksum(test_file)

        # Verify it's an MD5 hash
        assert len(checksum) == 32
        assert all(c in "0123456789abcdef" for c in checksum)
