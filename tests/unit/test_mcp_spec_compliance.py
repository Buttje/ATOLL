"""Tests to verify MCP specification compliance."""

from unittest.mock import AsyncMock, patch

import pytest

from atoll.config.models import MCPServerConfig
from atoll.mcp.client import MCPClient


class TestMCPSpecCompliance:
    """Test MCP specification compliance per https://modelcontextprotocol.io/specification/2025-03-26/"""

    @pytest.mark.asyncio
    async def test_initialize_returns_capabilities_not_tools(self):
        """Verify initialize response contains capabilities, not tools list.

        Per MCP spec, the initialize response should contain:
        - protocolVersion
        - capabilities (which may include tools capability)
        - serverInfo

        Tools must be fetched separately via tools/list request.
        """
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )

        client = MCPClient("test", config)

        # Mock the initialize response per MCP spec
        init_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": "0.1.0",
                "capabilities": {"tools": {"listChanged": True}},
                "serverInfo": {"name": "test-server", "version": "1.0.0"},
            },
        }

        # Mock process and initialize
        mock_process = AsyncMock()
        mock_process.stdin.write = lambda x: None
        mock_process.stdin.drain = AsyncMock()
        client.process = mock_process

        with patch.object(client, "_receive_message", return_value=init_response):
            await client._initialize()

            # Verify capabilities are stored, NOT tools
            assert client.capabilities == {"tools": {"listChanged": True}}
            assert client.server_info == {"name": "test-server", "version": "1.0.0"}
            # Verify tools/prompts/resources attributes don't exist
            assert not hasattr(client, "tools")
            assert not hasattr(client, "prompts")
            assert not hasattr(client, "resources")

    @pytest.mark.asyncio
    async def test_list_tools_sends_correct_request(self):
        """Verify tools/list request follows MCP spec format.

        Per MCP spec, to list tools, client must send:
        {
            "jsonrpc": "2.0",
            "id": <id>,
            "method": "tools/list",
            "params": {}
        }
        """
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )

        client = MCPClient("test", config)
        client.connected = True

        # Mock response per MCP spec
        tools_response = {
            "jsonrpc": "2.0",
            "id": 3,
            "result": {
                "tools": [
                    {
                        "name": "get_weather",
                        "description": "Get weather for a location",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "location": {"type": "string", "description": "City name"}
                            },
                            "required": ["location"],
                        },
                    }
                ]
            },
        }

        with patch.object(client, "_send_message", new_callable=AsyncMock) as mock_send:
            with patch.object(client, "_receive_message", return_value=tools_response):
                tools = await client.list_tools()

                # Verify correct request was sent
                mock_send.assert_called_once()
                request = mock_send.call_args[0][0]

                assert request["jsonrpc"] == "2.0"
                assert request["method"] == "tools/list"
                assert request["params"] == {}

                # Verify tools were parsed correctly
                assert len(tools) == 1
                assert tools[0]["name"] == "get_weather"
                assert "inputSchema" in tools[0]

    @pytest.mark.asyncio
    async def test_tools_not_cached_from_initialize(self):
        """Verify tools are never cached from initialize response.

        This ensures we always fetch tools via tools/list, not from initialize.
        """
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )

        client = MCPClient("test", config)
        client.connected = True

        # Even if server incorrectly sends tools in initialize (bad server),
        # we should ignore them and fetch via tools/list
        init_response = {
            "result": {"capabilities": {}, "tools": [{"name": "bad_tool"}]}  # Wrong per spec
        }

        mock_process = AsyncMock()
        mock_process.stdin.write = lambda x: None
        mock_process.stdin.drain = AsyncMock()
        client.process = mock_process

        with patch.object(client, "_receive_message", return_value=init_response):
            await client._initialize()

        # Should NOT have cached any tools
        assert not hasattr(client, "tools")

        # list_tools should still query the server
        tools_response = {"result": {"tools": [{"name": "correct_tool"}]}}

        with patch.object(client, "_send_message", new_callable=AsyncMock):
            with patch.object(client, "_receive_message", return_value=tools_response):
                tools = await client.list_tools()
                assert len(tools) == 1
                assert tools[0]["name"] == "correct_tool"
