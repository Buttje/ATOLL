"""Unit tests for MCP client."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from atoll.config.models import MCPServerConfig
from atoll.mcp.client import MCPClient


class TestMCPClient:
    """Test the MCPClient class."""

    def test_client_initialization(self):
        """Test client initialization."""
        config = MCPServerConfig(
            transport="stdio",
            command="test",
            args=["arg1"],
            timeoutSeconds=10,
        )

        client = MCPClient("test-server", config)

        assert client.name == "test-server"
        assert client.config == config
        assert not client.connected
        assert client.process is None
        assert client.capabilities == {}
        assert client.server_info == {}

    @pytest.mark.asyncio
    async def test_connect_stdio(self):
        """Test connecting via stdio transport."""
        config = MCPServerConfig(
            transport="stdio",
            command="echo",
            args=["test"],
            timeoutSeconds=10,
        )

        client = MCPClient("test-server", config)

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_subprocess:
            mock_process = Mock()
            mock_process.stdin = Mock()
            mock_process.stdin.write = Mock()
            mock_process.stdin.drain = AsyncMock()
            mock_process.stdout = Mock()
            mock_process.stdout.readline = AsyncMock(return_value=b'{"result": {}}\n')
            mock_process.stderr = Mock()
            mock_subprocess.return_value = mock_process

            result = await client.connect()

            assert result is True
            assert client.connected
            assert client.process is not None

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting MCP client."""
        config = MCPServerConfig(
            transport="stdio",
            command="echo",
            args=["test"],
            timeoutSeconds=10,
        )

        client = MCPClient("test-server", config)

        # Mock the process
        client.process = Mock()
        client.process.terminate = Mock()
        client.process.wait = AsyncMock()
        client.connected = True

        await client.disconnect()

        assert not client.connected
        assert client.process is None

    @pytest.mark.asyncio
    async def test_call_tool(self):
        """Test calling a tool."""
        config = MCPServerConfig(
            transport="stdio",
            command="test",
            args=["arg1"],
            timeoutSeconds=10,
        )

        client = MCPClient("test-server", config)
        client.connected = True
        client.process = Mock()
        client.process.stdin = Mock()
        client.process.stdin.write = Mock()
        client.process.stdin.drain = AsyncMock()
        client.process.stdout = Mock()
        client.process.stdout.readline = AsyncMock(
            return_value=b'{"result": {"output": "test result"}}\n'
        )

        result = await client.call_tool("test_tool", {"arg": "value"})

        assert result == {"output": "test result"}
