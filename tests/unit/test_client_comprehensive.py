"""Comprehensive tests for MCP client to improve coverage."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from atoll.config.models import MCPServerConfig
from atoll.mcp.client import MCPClient


class TestMCPClientComprehensive:
    """Comprehensive tests for MCP client."""

    @pytest.mark.asyncio
    async def test_connect_stdio_with_env_vars(self):
        """Test stdio connection with environment variables."""
        config = MCPServerConfig(
            transport="stdio", command="$HOME/test", args=["$VAR1"], env={"TEST": "$VAR2"}
        )

        client = MCPClient("test", config)

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = Mock()
            mock_process.stdin = Mock()
            mock_process.stdout = Mock()
            mock_process.stderr = Mock()
            mock_exec.return_value = mock_process

            with patch.object(client, "_initialize", new_callable=AsyncMock):
                result = await client._connect_stdio()

                assert result is True
                mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_stdio_exception(self):
        """Test stdio connection with exception."""
        config = MCPServerConfig(
            transport="stdio",
            command="test",
        )

        client = MCPClient("test", config)

        with patch("asyncio.create_subprocess_exec", side_effect=Exception("Test error")):
            result = await client._connect_stdio()

            assert result is False
            assert client.connected is False

    @pytest.mark.asyncio
    async def test_initialize_with_response(self):
        """Test initialization with server response."""
        config = MCPServerConfig(
            transport="stdio",
            command="test",
        )

        client = MCPClient("test", config)

        mock_process = Mock()
        mock_stdin = Mock()
        mock_stdin.write = Mock()
        mock_stdin.drain = AsyncMock()
        mock_process.stdin = mock_stdin
        client.process = mock_process

        response = {
            "result": {
                "capabilities": {"tools": {"listChanged": True}},
                "serverInfo": {"name": "test-server", "version": "1.0.0"},
            }
        }

        with patch.object(client, "_receive_message", return_value=response):
            await client._initialize()

            assert client.capabilities == {"tools": {"listChanged": True}}
            assert client.server_info == {"name": "test-server", "version": "1.0.0"}

    @pytest.mark.asyncio
    async def test_list_tools_query_server(self):
        """Test listing tools by querying server."""
        config = MCPServerConfig(
            transport="stdio",
            command="test",
        )

        client = MCPClient("test", config)
        client.connected = True
        client.tools = {}  # Empty cache

        mock_process = Mock()
        mock_stdin = Mock()
        mock_stdin.write = Mock()
        mock_stdin.drain = AsyncMock()
        mock_process.stdin = mock_stdin
        client.process = mock_process

        response = {
            "result": {
                "tools": [
                    {"name": "tool1", "description": "Tool 1"},
                    {"name": "tool2", "description": "Tool 2"},
                ]
            }
        }

        with patch.object(client, "_receive_message", return_value=response):
            tools = await client.list_tools()

            assert len(tools) == 2
            assert tools[0]["name"] == "tool1"
