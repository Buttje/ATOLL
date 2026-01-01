"""Tests for deployment server error diagnostics."""

import sys

import pytest

from atoll.deployment.server import AgentInstance, DeploymentServer, DeploymentServerConfig


@pytest.fixture
def mock_config(tmp_path):
    """Create test deployment server config."""
    return DeploymentServerConfig(
        enabled=True,
        agents_directory=tmp_path,
        base_port=8100,
        health_check_interval=30,
        restart_on_failure=False,
    )


@pytest.fixture
def deployment_server(mock_config):
    """Create deployment server instance."""
    return DeploymentServer(mock_config)


class TestErrorDiagnostics:
    """Test error diagnostics generation."""

    @pytest.mark.asyncio
    async def test_diagnostics_for_python_version_issue(self, deployment_server, tmp_path):
        """Test diagnostics detects Python 3.14 Pydantic issue."""
        # Create test agent
        config_path = tmp_path / "test_agent" / "agent.toml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(
            """
[agent]
name = "TestAgent"
version = "1.0.0"
description = "Test agent"
entry_point = "main.py"

[llm]
provider = "ollama"
model = "llama3.2"
        """
        )

        agent = AgentInstance(
            name="TestAgent",
            config_path=config_path,
            status="failed",
            port=8100,
            error_message="Startup failed",
            stderr_log=(
                "C:\\Users\\test\\AppData\\Local\\Python\\pythoncore-3.14-64\\Lib\\site-packages\\"
                "langchain_core\\_api\\deprecation.py:26: UserWarning: "
                "Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.\n"
                "  from pydantic.v1.fields import FieldInfo as FieldInfoV1\n"
                "Traceback (most recent call last):\n"
                '  File "main.py", line 1, in <module>\n'
                "    from langchain import LLMChain\n"
                "ImportError: cannot import name 'LLMChain' from 'langchain'\n"
            ),
            stdout_log="Starting agent...\n",
            exit_code=1,
        )

        # Generate diagnostics
        diagnostics = deployment_server._generate_diagnostics(agent)

        # Verify diagnostics content
        assert "Python version:" in diagnostics
        if sys.version_info >= (3, 14):
            assert "Python 3.14+ detected" in diagnostics
            assert "Use Python 3.11 or 3.13" in diagnostics
        assert "Pydantic V1 compatibility" in diagnostics
        assert "Config file:" in diagnostics
        assert "exists" in diagnostics

    @pytest.mark.asyncio
    async def test_diagnostics_for_missing_dependencies(self, deployment_server, tmp_path):
        """Test diagnostics detects missing dependencies."""
        config_path = tmp_path / "test_agent" / "agent.toml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(
            """
[agent]
name = "TestAgent"
version = "1.0.0"
description = "Test agent"
entry_point = "main.py"

[dependencies]
python = ">=3.11"
packages = ["langchain", "aiohttp", "pydantic>=2.0"]
        """
        )

        agent = AgentInstance(
            name="TestAgent",
            config_path=config_path,
            status="failed",
            port=8100,
            error_message="Startup failed",
            stderr_log=(
                "Traceback (most recent call last):\n"
                '  File "main.py", line 1, in <module>\n'
                "    import langchain\n"
                "ModuleNotFoundError: No module named 'langchain'\n"
            ),
            exit_code=1,
        )

        # Generate diagnostics
        diagnostics = deployment_server._generate_diagnostics(agent)

        # Verify diagnostics content
        assert "Missing Python dependencies" in diagnostics
        assert "install -r requirements.txt" in diagnostics  # Match without full path
        assert "Dependencies: 3 packages required" in diagnostics
        assert "langchain" in diagnostics

    @pytest.mark.asyncio
    async def test_diagnostics_for_port_conflict(self, deployment_server, tmp_path):
        """Test diagnostics detects port conflicts."""
        config_path = tmp_path / "test_agent" / "agent.toml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(
            """
[agent]
name = "TestAgent"
version = "1.0.0"
description = "Test agent"
entry_point = "main.py"
        """
        )

        agent = AgentInstance(
            name="TestAgent",
            config_path=config_path,
            status="failed",
            port=8100,
            error_message="Startup failed",
            stderr_log=(
                "Traceback (most recent call last):\n"
                '  File "main.py", line 15, in <module>\n'
                "    server.bind(('localhost', 8100))\n"
                "OSError: [Errno 98] Address already in use: Port 8100\n"
            ),
            stdout_log="Starting server...\n",
            exit_code=1,
        )

        # Generate diagnostics
        diagnostics = deployment_server._generate_diagnostics(agent)

        # Verify diagnostics content
        assert "Port 8100 already in use" in diagnostics
        assert "Stop other services" in diagnostics
        assert "base_port" in diagnostics

    @pytest.mark.asyncio
    async def test_diagnostics_includes_troubleshooting_steps(self, deployment_server, tmp_path):
        """Test diagnostics includes general troubleshooting steps."""
        config_path = tmp_path / "test_agent" / "agent.toml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(
            """
[agent]
name = "TestAgent"
version = "1.0.0"
description = "Test agent"
entry_point = "main.py"
        """
        )

        agent = AgentInstance(
            name="TestAgent",
            config_path=config_path,
            status="failed",
            port=8100,
            error_message="Startup failed",
            stderr_log="Some error\n",
            exit_code=1,
        )

        # Generate diagnostics
        diagnostics = deployment_server._generate_diagnostics(agent)

        # Verify diagnostics content
        assert "TROUBLESHOOTING STEPS:" in diagnostics
        assert "Check the STDERR and STDOUT logs" in diagnostics
        assert "Verify all dependencies are installed" in diagnostics
        assert "Test the agent configuration" in diagnostics
