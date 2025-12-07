"""Additional tests for main.py coverage."""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from atoll.main import Application


class TestHandleInstallCommand:
    """Test the install command handling."""

    @pytest.mark.asyncio
    async def test_handle_install_command_no_args(self):
        """Test install command with no arguments."""
        app = Application()
        app.ui = Mock()

        await app.handle_install_command(["install"])

        app.ui.display_error.assert_called_once()
        assert "Usage:" in str(app.ui.display_error.call_args)

    @pytest.mark.asyncio
    async def test_handle_install_command_with_source(self):
        """Test install command with source."""
        app = Application()
        app.ui = Mock()
        app.installer = Mock()
        app.installer.install_server = AsyncMock(return_value=True)
        
        # Create mock manager
        mock_manager = Mock()
        mock_manager.disconnect_all = AsyncMock()
        mock_manager.connect_all = AsyncMock()
        app.mcp_manager = mock_manager
        
        app.config_manager = Mock()
        app.config_manager.load_configs = Mock()
        app.config_manager.mcp_config = Mock()
        app.agent = Mock()

        with patch("atoll.main.MCPServerManager") as MockMCPServerManager:
            MockMCPServerManager.return_value = mock_manager
            await app.handle_install_command(["install", "/path/to/server"])

        app.installer.install_server.assert_called_once_with("/path/to/server", None, None)

    @pytest.mark.asyncio
    async def test_handle_install_command_with_all_args(self):
        """Test install command with all arguments."""
        app = Application()
        app.ui = Mock()
        app.installer = Mock()
        app.installer.install_server = AsyncMock(return_value=True)
        
        # Create mock manager
        mock_manager = Mock()
        mock_manager.disconnect_all = AsyncMock()
        mock_manager.connect_all = AsyncMock()
        app.mcp_manager = mock_manager
        
        app.config_manager = Mock()
        app.config_manager.load_configs = Mock()
        app.config_manager.mcp_config = Mock()
        app.agent = Mock()

        with patch("atoll.main.MCPServerManager") as MockMCPServerManager:
            MockMCPServerManager.return_value = mock_manager
            await app.handle_install_command(
                ["install", "/path/to/server", "--name", "myserver", "--type", "dir"]
            )

        app.installer.install_server.assert_called_once_with("/path/to/server", "dir", "myserver")

    @pytest.mark.asyncio
    async def test_handle_install_command_failure(self):
        """Test install command when installation fails."""
        app = Application()
        app.ui = Mock()
        app.installer = Mock()
        app.installer.install_server = AsyncMock(return_value=False)

        await app.handle_install_command(["install", "/path/to/server"])

        app.installer.install_server.assert_called_once()
        # Should not reconnect on failure
        assert app.ui.display_info.call_count <= 1  # Only the usage message


class TestHelpSystem:
    """Test help command functionality."""

    def test_display_help_server(self):
        """Test help server command."""
        app = Application()
        app.ui = Mock()
        app.config_manager = Mock()
        app.config_manager.mcp_config = Mock()
        
        # Create proper mock for server config
        mock_server_config = Mock()
        mock_server_config.transport = "stdio"
        mock_server_config.command = "python"
        mock_server_config.args = ["server.py"]
        mock_server_config.url = None
        mock_server_config.timeoutSeconds = 30
        mock_server_config.env = {"KEY": "value"}
        
        app.config_manager.mcp_config.servers = {
            "test-server": mock_server_config
        }
        
        app.mcp_manager = Mock()
        app.mcp_manager.get_client = Mock(return_value=Mock(connected=True))
        app.mcp_manager.tool_registry = Mock()
        app.mcp_manager.tool_registry.list_server_tools = Mock(
            return_value=["tool1"]
        )
        app.mcp_manager.tool_registry.get_tool = Mock(
            return_value={
                "name": "tool1",
                "description": "Test tool",
                "inputSchema": {"properties": {"param1": {"type": "string"}}},
            }
        )
        app.mcp_manager.clients = {
            "test-server": Mock(
                config=Mock(transport="stdio", command="python", args=["server.py"])
            )
        }
        app.mcp_manager.tool_registry = Mock()
        app.mcp_manager.tool_registry.list_server_tools = Mock(
            return_value=[
                {
                    "name": "tool1",
                    "description": "Test tool",
                    "inputSchema": {"properties": {"param1": {"type": "string"}}},
                }
            ]
        )
        app.colors = Mock()
        app.colors.header = Mock(return_value="HEADER")
        app.colors.info = Mock(return_value="INFO")
        app.colors.user_input = Mock(return_value="INPUT")
        app.colors.reasoning = Mock(return_value="REASONING")

        with patch("builtins.print"):
            app.display_server_help("test-server")

    def test_display_help_server_not_found(self):
        """Test help server command for non-existent server."""
        app = Application()
        app.ui = Mock()
        app.config_manager = Mock()
        app.config_manager.mcp_config = Mock()
        app.config_manager.mcp_config.servers = {}
        app.mcp_manager = Mock()
        app.mcp_manager.get_client = Mock(return_value=None)
        app.colors = Mock()
        app.colors.warning = Mock(return_value="WARNING")

        with patch("builtins.print"):
            app.display_server_help("nonexistent")

    def test_display_help_tool(self):
        """Test help tool command."""
        app = Application()
        app.ui = Mock()
        app.mcp_manager = Mock()
        app.mcp_manager.tool_registry = Mock()
        app.mcp_manager.tool_registry.get_tool = Mock(
            return_value={
                "name": "test_tool",
                "description": "Test tool description",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "param1": {
                            "type": "string",
                            "description": "Parameter 1",
                            "enum": ["a", "b"],
                            "default": "a",
                        }
                    },
                    "required": ["param1"],
                },
            }
        )
        app.mcp_manager.tool_registry.get_server_for_tool = Mock(return_value="test-server")
        app.colors = Mock()
        app.colors.header = Mock(return_value="HEADER")
        app.colors.info = Mock(return_value="INFO")
        app.colors.user_input = Mock(return_value="INPUT")
        app.colors.reasoning = Mock(return_value="REASONING")
        app.colors.warning = Mock(return_value="WARNING")
        app.colors.answer_text = Mock(return_value="ANSWER")

        with patch("builtins.print"):
            app.display_tool_help("test_tool")

    def test_display_help_tool_not_found(self):
        """Test help tool command for non-existent tool."""
        app = Application()
        app.ui = Mock()
        app.mcp_manager = Mock()
        app.mcp_manager.tool_registry = Mock()
        app.mcp_manager.tool_registry.get_tool = Mock(return_value=None)
        app.colors = Mock()
        app.colors.warning = Mock(return_value="WARNING")

        with patch("builtins.print"):
            app.display_tool_help("nonexistent")

    def test_display_help_tool_no_schema(self):
        """Test help tool command for tool without input schema."""
        app = Application()
        app.ui = Mock()
        app.mcp_manager = Mock()
        app.mcp_manager.tool_registry = Mock()
        app.mcp_manager.tool_registry.get_tool = Mock(
            return_value={
                "name": "test_tool",
                "description": "Test tool",
            }
        )
        app.mcp_manager.tool_registry.get_server_for_tool = Mock(return_value="test-server")
        app.colors = Mock()
        app.colors.header = Mock(return_value="HEADER")
        app.colors.info = Mock(return_value="INFO")
        app.colors.warning = Mock(return_value="WARNING")
        app.colors.answer_text = Mock(return_value="ANSWER")

        with patch("builtins.print"):
            app.display_tool_help("test_tool")


class TestSetOllamaServer:
    """Test setOllamaServer command."""

    @pytest.mark.asyncio
    async def test_set_ollama_server_model_unavailable(self):
        """Test setserver when model is not available on new server."""
        app = Application()
        app.ui = Mock()
        app.config_manager = Mock()
        app.config_manager.ollama_config = Mock(base_url="http://old", port=11434)
        app.config_manager.save_ollama_config = Mock()
        app.agent = Mock()
        app.agent.ollama_config = Mock(base_url="http://old", port=11434)
        app.agent._create_llm = Mock()
        app.agent.check_server_connection = AsyncMock(return_value=True)
        app.agent.check_model_available = AsyncMock(return_value=False)
        app.colors = Mock()
        app.colors.info = Mock(return_value="INFO")
        app.colors.warning = Mock(return_value="WARNING")

        with patch("builtins.print"):
            await app.set_ollama_server("http://new", 8080)

        assert app.agent.ollama_config.base_url == "http://new"
        assert app.agent.ollama_config.port == 8080

    @pytest.mark.asyncio
    async def test_set_ollama_server_connection_failure(self):
        """Test setserver when connection fails."""
        app = Application()
        app.ui = Mock()
        app.config_manager = Mock()
        app.config_manager.ollama_config = Mock(base_url="http://old", port=11434)
        app.agent = Mock()
        app.agent.ollama_config = Mock(base_url="http://old", port=11434)
        app.agent._create_llm = Mock()
        app.agent.check_server_connection = AsyncMock(return_value=False)
        app.colors = Mock()
        app.colors.info = Mock(return_value="INFO")
        app.colors.error = Mock(return_value="ERROR")

        with patch("builtins.print"):
            await app.set_ollama_server("http://invalid", None)

        # Should revert changes
        assert app.agent.ollama_config.base_url == "http://old"
