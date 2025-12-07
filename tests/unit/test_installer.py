"""Unit tests for MCP installer."""

import asyncio
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from atoll.mcp.installer import MCPInstaller
from atoll.config.models import MCPConfig, MCPServerConfig
from atoll.ui.terminal import TerminalUI


class TestMCPInstaller:
    """Test the MCPInstaller class."""

    @pytest.fixture
    def mock_ui(self):
        """Create mock UI."""
        ui = Mock(spec=TerminalUI)
        ui.display_info = Mock()
        ui.display_error = Mock()
        ui.display_verbose = Mock()
        return ui

    @pytest.fixture
    def mock_config_manager(self):
        """Create mock config manager."""
        manager = Mock()
        manager.mcp_config = MCPConfig()
        return manager

    @pytest.fixture
    def mock_agent(self):
        """Create mock agent."""
        agent = Mock()
        agent.process_prompt = AsyncMock()
        return agent

    @pytest.fixture
    def installer(self, mock_ui, mock_config_manager, mock_agent):
        """Create installer instance."""
        return MCPInstaller(mock_ui, mock_config_manager, mock_agent)

    def test_initialization(self, installer):
        """Test installer initialization."""
        assert installer.ui is not None
        assert installer.config_manager is not None
        assert installer.agent is not None
        assert installer.log_dir.exists()
        assert installer.log_file.exists() or installer.log_file.parent.exists()
        assert installer.servers_dir.exists()

    def test_detect_source_type_directory(self, installer, tmp_path):
        """Test detecting directory source type."""
        test_dir = tmp_path / "test_server"
        test_dir.mkdir()
        result = installer._detect_source_type(str(test_dir))
        assert result == "dir"

    def test_detect_source_type_github_url(self, installer):
        """Test detecting GitHub repository source type."""
        result = installer._detect_source_type("https://github.com/user/repo")
        assert result == "repo"

    def test_detect_source_type_http_url(self, installer):
        """Test detecting HTTP URL source type."""
        result = installer._detect_source_type("http://localhost:8080")
        assert result == "url"

    def test_detect_source_type_command(self, installer):
        """Test detecting command source type."""
        result = installer._detect_source_type("python server.py")
        assert result == "cmd"

    def test_generate_server_name_from_directory(self, installer, tmp_path):
        """Test generating server name from directory."""
        test_dir = tmp_path / "test-server"
        test_dir.mkdir()
        name = installer._generate_server_name(str(test_dir), "dir")
        assert name == "test-server"

    def test_generate_server_name_from_github(self, installer):
        """Test generating server name from GitHub URL."""
        name = installer._generate_server_name("https://github.com/user/my-server", "repo")
        assert name == "my-server"

    def test_generate_server_name_from_url(self, installer):
        """Test generating server name from URL."""
        name = installer._generate_server_name("http://example.com:8080", "url")
        assert name == "example-com"

    def test_generate_unique_name_collision(self, installer, mock_config_manager):
        """Test generating unique name when collision occurs."""
        # Add existing server
        mock_config_manager.mcp_config.servers["test-server"] = MCPServerConfig(transport="stdio")
        installer.config_manager = mock_config_manager

        name = installer._generate_server_name("test-server", "dir")
        assert name == "test-server-1"

    def test_validate_unique_name_success(self, installer):
        """Test validating unique name success."""
        assert installer._validate_unique_name("new-server") is True

    def test_validate_unique_name_collision(self, installer, mock_config_manager):
        """Test validating unique name collision."""
        mock_config_manager.mcp_config.servers["existing"] = MCPServerConfig(transport="stdio")
        installer.config_manager = mock_config_manager
        assert installer._validate_unique_name("existing") is False

    def test_find_readme_success(self, installer, tmp_path):
        """Test finding README file."""
        test_dir = tmp_path / "server"
        test_dir.mkdir()
        readme = test_dir / "README.md"
        readme.write_text("# Test Server")

        found = installer._find_readme(test_dir)
        assert found == readme

    def test_find_readme_not_found(self, installer, tmp_path):
        """Test finding README when it doesn't exist."""
        test_dir = tmp_path / "server"
        test_dir.mkdir()

        found = installer._find_readme(test_dir)
        assert found is None

    @pytest.mark.asyncio
    async def test_extract_install_command(self, installer, tmp_path, mock_agent):
        """Test extracting install command from README."""
        readme = tmp_path / "README.md"
        readme.write_text("# Server\n\nInstall: npm install\n")

        mock_agent.process_prompt.return_value = "npm install"
        installer.agent = mock_agent

        command = await installer._extract_install_command(readme, tmp_path)
        assert command == "npm install"
        mock_agent.process_prompt.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_install_command_none(self, installer, tmp_path, mock_agent):
        """Test extracting install command when none needed."""
        readme = tmp_path / "README.md"
        readme.write_text("# Server\n\nNo installation required.")

        mock_agent.process_prompt.return_value = "NONE"
        installer.agent = mock_agent

        command = await installer._extract_install_command(readme, tmp_path)
        assert command is None

    @pytest.mark.asyncio
    async def test_find_server_command(self, installer, tmp_path, mock_agent):
        """Test finding server start command."""
        readme = tmp_path / "README.md"
        readme.write_text("# Server\n\nRun: python server.py\n")

        mock_agent.process_prompt.return_value = "python server.py"
        installer.agent = mock_agent

        command = await installer._find_server_command(readme, tmp_path)
        assert command == "python server.py"

    @pytest.mark.asyncio
    async def test_execute_install_command_success(self, installer, tmp_path):
        """Test executing install command successfully."""
        # Use a simple echo command that works on all platforms
        result = await installer._execute_install_command("echo test", tmp_path)
        assert result is True

    @pytest.mark.asyncio
    async def test_execute_install_command_failure(self, installer, tmp_path):
        """Test executing install command failure."""
        result = await installer._execute_install_command("nonexistent_command_xyz", tmp_path)
        assert result is False

    @pytest.mark.asyncio
    async def test_create_server_config_stdio(self, installer):
        """Test creating server config for stdio."""
        config = await installer._create_server_config(
            "test", "stdio", "python server.py", "/path/to/server"
        )
        assert config.transport == "stdio"
        assert config.command == "python"
        assert config.args == ["server.py"]
        assert config.cwd == "/path/to/server"

    @pytest.mark.asyncio
    async def test_create_server_config_http(self, installer):
        """Test creating server config for HTTP."""
        config = await installer._create_server_config(
            "test", "http", "", "http://localhost:8080"
        )
        assert config.transport == "http"
        assert config.url == "http://localhost:8080"

    @pytest.mark.asyncio
    async def test_validate_server_success(self, installer):
        """Test server validation success."""
        config = MCPServerConfig(transport="stdio", command="test")

        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        mock_client.list_tools = AsyncMock(
            return_value=[{"name": "tool1", "description": "Test tool", "inputSchema": {}}]
        )
        mock_client.disconnect = AsyncMock()

        with patch("atoll.mcp.installer.MCPClient", return_value=mock_client):
            result = await installer._validate_server(config)

        assert result is True
        mock_client.connect.assert_called_once()
        mock_client.list_tools.assert_called_once()
        mock_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_server_no_tools(self, installer):
        """Test server validation failure with no tools."""
        config = MCPServerConfig(transport="stdio", command="test")

        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        mock_client.list_tools = AsyncMock(return_value=[])
        mock_client.disconnect = AsyncMock()

        with patch("atoll.mcp.installer.MCPClient", return_value=mock_client):
            result = await installer._validate_server(config)

        assert result is False

    @pytest.mark.asyncio
    async def test_validate_server_invalid_tool_structure(self, installer):
        """Test server validation failure with invalid tool structure."""
        config = MCPServerConfig(transport="stdio", command="test")

        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        mock_client.list_tools = AsyncMock(return_value=[{"name": "tool1"}])  # Missing description
        mock_client.disconnect = AsyncMock()

        with patch("atoll.mcp.installer.MCPClient", return_value=mock_client):
            result = await installer._validate_server(config)

        assert result is False

    def test_save_server_config(self, installer, tmp_path, monkeypatch):
        """Test saving server configuration."""
        # Use a temporary config file
        config_dir = tmp_path / ".atoll"
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        config = MCPServerConfig(transport="stdio", command="python", args=["server.py"])
        result = installer._save_server_config("test-server", config)

        assert result is True
        config_file = config_dir / "mcp_config.json"
        assert config_file.exists()

        # Verify content
        with open(config_file) as f:
            saved = json.load(f)
        assert "servers" in saved
        assert "test-server" in saved["servers"]
        assert saved["servers"]["test-server"]["transport"] == "stdio"

    @pytest.mark.asyncio
    async def test_install_from_directory_no_directory(self, installer):
        """Test installing from non-existent directory."""
        result = await installer._install_from_directory("/nonexistent", "test")
        assert result is False

    @pytest.mark.asyncio
    async def test_install_from_directory_no_readme(self, installer, tmp_path):
        """Test installing from directory without README."""
        test_dir = tmp_path / "server"
        test_dir.mkdir()

        result = await installer._install_from_directory(str(test_dir), "test")
        assert result is False

    @pytest.mark.asyncio
    async def test_install_from_url_unsupported_scheme(self, installer):
        """Test installing from URL with unsupported scheme."""
        result = await installer._install_from_url("ftp://example.com", "test")
        assert result is False

    @pytest.mark.asyncio
    async def test_install_server_invalid_type(self, installer):
        """Test installing server with invalid type."""
        result = await installer.install_server("source", "invalid_type", "test")
        assert result is False

    @pytest.mark.asyncio
    async def test_install_server_duplicate_name(self, installer, mock_config_manager):
        """Test installing server with duplicate name."""
        mock_config_manager.mcp_config.servers["test"] = MCPServerConfig(transport="stdio")
        installer.config_manager = mock_config_manager

        result = await installer.install_server("source", "dir", "test")
        assert result is False
        installer.ui.display_error.assert_called()

    @pytest.mark.asyncio
    async def test_install_server_with_exception(self, installer):
        """Test install server handles exceptions."""
        with patch.object(installer, "_detect_source_type", side_effect=Exception("Test error")):
            result = await installer.install_server("source", None, "test")
            assert result is False
            installer.ui.display_error.assert_called()

    @pytest.mark.asyncio
    async def test_install_from_url_websocket(self, installer):
        """Test installing from WebSocket URL."""
        result = await installer._install_from_url("ws://localhost:8080", "test")
        assert result is False
        installer.ui.display_error.assert_called_with("WebSocket transport not yet implemented")

    @pytest.mark.asyncio
    async def test_install_from_repository_git_not_found(self, installer):
        """Test repository installation when git is not available."""
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            result = await installer._install_from_repository("https://github.com/user/repo", "test")
            assert result is False
            installer.ui.display_error.assert_called()

    @pytest.mark.asyncio
    async def test_install_from_repository_clone_failure(self, installer):
        """Test repository installation when clone fails."""
        import subprocess

        with patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "git", stderr="clone failed"),
        ):
            result = await installer._install_from_repository("https://github.com/user/repo", "test")
            assert result is False
            installer.ui.display_error.assert_called()

    @pytest.mark.asyncio
    async def test_install_from_repository_existing_directory(self, installer, tmp_path):
        """Test repository installation when target directory exists."""
        installer.servers_dir = tmp_path
        target_dir = tmp_path / "test"
        target_dir.mkdir()

        result = await installer._install_from_repository("https://github.com/user/repo", "test")
        assert result is False
        installer.ui.display_error.assert_called()

    @pytest.mark.asyncio
    async def test_extract_install_command_exception(self, installer, tmp_path):
        """Test extract install command with exception."""
        readme = tmp_path / "README.md"
        readme.write_text("# Test")

        installer.agent.process_prompt.side_effect = Exception("LLM error")
        result = await installer._extract_install_command(readme, tmp_path)
        assert result is None

    @pytest.mark.asyncio
    async def test_find_server_command_exception(self, installer, tmp_path):
        """Test find server command with exception."""
        readme = tmp_path / "README.md"
        readme.write_text("# Test")

        installer.agent.process_prompt.side_effect = Exception("LLM error")
        result = await installer._find_server_command(readme, tmp_path)
        assert result is None

    @pytest.mark.asyncio
    async def test_find_server_command_empty_response(self, installer, tmp_path):
        """Test find server command with empty response."""
        readme = tmp_path / "README.md"
        readme.write_text("# Test")

        installer.agent.process_prompt.return_value = ""
        result = await installer._find_server_command(readme, tmp_path)
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_server_connection_failure(self, installer):
        """Test server validation with connection failure."""
        config = MCPServerConfig(transport="stdio", command="test")

        mock_client = AsyncMock()
        mock_client.connect = AsyncMock(side_effect=Exception("Connection failed"))

        with patch("atoll.mcp.installer.MCPClient", return_value=mock_client):
            result = await installer._validate_server(config)

        assert result is False

    @pytest.mark.asyncio
    async def test_save_server_config_exception(self, installer, tmp_path, monkeypatch):
        """Test saving server config with exception."""
        # Make the config directory read-only would be complex, so simulate write error
        with patch("builtins.open", side_effect=PermissionError("Write failed")):
            config = MCPServerConfig(transport="stdio", command="test")
            result = installer._save_server_config("test", config)
            assert result is False
            installer.ui.display_error.assert_called()

    def test_detect_source_type_file(self, installer, tmp_path):
        """Test detecting file source type."""
        test_file = tmp_path / "server.py"
        test_file.write_text("# server")
        result = installer._detect_source_type(str(test_file))
        assert result == "cmd"

    def test_find_readme_case_insensitive(self, installer, tmp_path):
        """Test finding README with different cases."""
        test_dir = tmp_path / "server"
        test_dir.mkdir()

        # Test lowercase
        readme = test_dir / "readme.md"
        readme.write_text("# Test")
        found = installer._find_readme(test_dir)
        assert found == readme

    @pytest.mark.asyncio
    async def test_install_server_auto_name_generation(self, installer, tmp_path):
        """Test install server auto-generates name."""
        test_dir = tmp_path / "my-server"
        test_dir.mkdir()

        with patch.object(installer, "_install_from_directory", return_value=True):
            result = await installer.install_server(str(test_dir), "dir", None)
            # Verify name was generated
            assert result is True

    @pytest.mark.asyncio
    async def test_create_server_config_sse(self, installer):
        """Test creating server config for SSE."""
        config = await installer._create_server_config("test", "sse", "", "http://localhost:8080")
        assert config.transport == "sse"
        assert config.url == "http://localhost:8080"

