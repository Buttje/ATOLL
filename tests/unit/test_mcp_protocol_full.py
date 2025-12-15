"""Comprehensive tests for full MCP protocol compliance."""

from unittest.mock import AsyncMock, patch

import pytest

from atoll.config.models import MCPServerConfig
from atoll.mcp.client import MCPClient


class TestMCPResources:
    """Test MCP Resources protocol implementation."""

    @pytest.mark.asyncio
    async def test_list_resources_success(self):
        """Test successfully listing resources."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )

        client = MCPClient("test", config)
        client.connected = True

        mock_response = {
            "result": {
                "resources": [
                    {
                        "uri": "file:///example.txt",
                        "name": "example.txt",
                        "description": "Example file",
                        "mimeType": "text/plain",
                    }
                ]
            }
        }

        with patch.object(client, "_send_message", new_callable=AsyncMock):
            with patch.object(client, "_receive_message", return_value=mock_response):
                result = await client.list_resources()

                assert len(result["resources"]) == 1
                assert result["resources"][0]["uri"] == "file:///example.txt"

    @pytest.mark.asyncio
    async def test_list_resources_with_pagination(self):
        """Test listing resources with pagination cursor."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )

        client = MCPClient("test", config)
        client.connected = True

        mock_response = {
            "result": {"resources": [{"uri": "file:///test.txt"}], "nextCursor": "page2"}
        }

        with patch.object(client, "_send_message", new_callable=AsyncMock) as mock_send:
            with patch.object(client, "_receive_message", return_value=mock_response):
                result = await client.list_resources(cursor="page1")

                # Verify cursor was passed in request
                request = mock_send.call_args[0][0]
                assert request["params"]["cursor"] == "page1"
                assert result["nextCursor"] == "page2"

    @pytest.mark.asyncio
    async def test_list_resources_not_connected(self):
        """Test listing resources when not connected."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )

        client = MCPClient("test", config)
        result = await client.list_resources()

        assert result == {"resources": []}

    @pytest.mark.asyncio
    async def test_read_resource_success(self):
        """Test successfully reading a resource."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )

        client = MCPClient("test", config)
        client.connected = True

        mock_response = {
            "result": {
                "contents": [
                    {
                        "uri": "file:///example.txt",
                        "mimeType": "text/plain",
                        "text": "Hello, world!",
                    }
                ]
            }
        }

        with patch.object(client, "_send_message", new_callable=AsyncMock) as mock_send:
            with patch.object(client, "_receive_message", return_value=mock_response):
                result = await client.read_resource("file:///example.txt")

                # Verify request format
                request = mock_send.call_args[0][0]
                assert request["method"] == "resources/read"
                assert request["params"]["uri"] == "file:///example.txt"

                # Verify response
                assert len(result["contents"]) == 1
                assert result["contents"][0]["text"] == "Hello, world!"

    @pytest.mark.asyncio
    async def test_read_resource_not_connected(self):
        """Test reading resource when not connected raises error."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )

        client = MCPClient("test", config)

        with pytest.raises(RuntimeError, match="Not connected"):
            await client.read_resource("file:///test.txt")

    @pytest.mark.asyncio
    async def test_read_resource_error(self):
        """Test reading resource with error response."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )

        client = MCPClient("test", config)
        client.connected = True

        mock_response = {"error": {"code": -32002, "message": "Resource not found"}}

        with patch.object(client, "_send_message", new_callable=AsyncMock):
            with patch.object(client, "_receive_message", return_value=mock_response):
                with pytest.raises(RuntimeError, match="Resource read error"):
                    await client.read_resource("file:///nonexistent.txt")

    @pytest.mark.asyncio
    async def test_subscribe_resource_success(self):
        """Test successfully subscribing to a resource."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )

        client = MCPClient("test", config)
        client.connected = True
        client.capabilities = {"resources": {"subscribe": True}}

        mock_response = {"result": {}}

        with patch.object(client, "_send_message", new_callable=AsyncMock):
            with patch.object(client, "_receive_message", return_value=mock_response):
                result = await client.subscribe_resource("file:///example.txt")

                assert result is True

    @pytest.mark.asyncio
    async def test_subscribe_resource_not_supported(self):
        """Test subscribing when server doesn't support it."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )

        client = MCPClient("test", config)
        client.connected = True
        client.capabilities = {"resources": {}}  # No subscribe capability

        result = await client.subscribe_resource("file:///example.txt")
        assert result is False

    @pytest.mark.asyncio
    async def test_unsubscribe_resource_success(self):
        """Test successfully unsubscribing from a resource."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )

        client = MCPClient("test", config)
        client.connected = True

        mock_response = {"result": {}}

        with patch.object(client, "_send_message", new_callable=AsyncMock):
            with patch.object(client, "_receive_message", return_value=mock_response):
                result = await client.unsubscribe_resource("file:///example.txt")

                assert result is True

    @pytest.mark.asyncio
    async def test_list_resource_templates(self):
        """Test listing resource templates."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )

        client = MCPClient("test", config)
        client.connected = True

        mock_response = {
            "result": {
                "resourceTemplates": [
                    {
                        "uriTemplate": "file:///{path}",
                        "name": "Project Files",
                        "mimeType": "application/octet-stream",
                    }
                ]
            }
        }

        with patch.object(client, "_send_message", new_callable=AsyncMock):
            with patch.object(client, "_receive_message", return_value=mock_response):
                result = await client.list_resource_templates()

                assert len(result) == 1
                assert result[0]["uriTemplate"] == "file:///{path}"


class TestMCPPrompts:
    """Test MCP Prompts protocol implementation."""

    @pytest.mark.asyncio
    async def test_list_prompts_success(self):
        """Test successfully listing prompts."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )

        client = MCPClient("test", config)
        client.connected = True

        mock_response = {
            "result": {
                "prompts": [
                    {
                        "name": "code_review",
                        "description": "Review code quality",
                        "arguments": [
                            {"name": "code", "description": "Code to review", "required": True}
                        ],
                    }
                ]
            }
        }

        with patch.object(client, "_send_message", new_callable=AsyncMock):
            with patch.object(client, "_receive_message", return_value=mock_response):
                result = await client.list_prompts()

                assert len(result["prompts"]) == 1
                assert result["prompts"][0]["name"] == "code_review"

    @pytest.mark.asyncio
    async def test_list_prompts_with_pagination(self):
        """Test listing prompts with pagination."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )

        client = MCPClient("test", config)
        client.connected = True

        mock_response = {"result": {"prompts": [{"name": "test"}], "nextCursor": "page2"}}

        with patch.object(client, "_send_message", new_callable=AsyncMock) as mock_send:
            with patch.object(client, "_receive_message", return_value=mock_response):
                result = await client.list_prompts(cursor="page1")

                request = mock_send.call_args[0][0]
                assert request["params"]["cursor"] == "page1"
                assert result["nextCursor"] == "page2"

    @pytest.mark.asyncio
    async def test_get_prompt_success(self):
        """Test successfully getting a prompt."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )

        client = MCPClient("test", config)
        client.connected = True

        mock_response = {
            "result": {
                "description": "Code review prompt",
                "messages": [
                    {"role": "user", "content": {"type": "text", "text": "Please review this code"}}
                ],
            }
        }

        with patch.object(client, "_send_message", new_callable=AsyncMock) as mock_send:
            with patch.object(client, "_receive_message", return_value=mock_response):
                result = await client.get_prompt("code_review", {"code": "def test(): pass"})

                # Verify request
                request = mock_send.call_args[0][0]
                assert request["method"] == "prompts/get"
                assert request["params"]["name"] == "code_review"
                assert request["params"]["arguments"]["code"] == "def test(): pass"

                # Verify response
                assert len(result["messages"]) == 1
                assert result["messages"][0]["role"] == "user"

    @pytest.mark.asyncio
    async def test_get_prompt_without_arguments(self):
        """Test getting a prompt without arguments."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )

        client = MCPClient("test", config)
        client.connected = True

        mock_response = {
            "result": {"messages": [{"role": "user", "content": {"type": "text", "text": "test"}}]}
        }

        with patch.object(client, "_send_message", new_callable=AsyncMock) as mock_send:
            with patch.object(client, "_receive_message", return_value=mock_response):
                await client.get_prompt("simple_prompt")

                request = mock_send.call_args[0][0]
                assert "arguments" not in request["params"]

    @pytest.mark.asyncio
    async def test_get_prompt_not_connected(self):
        """Test getting prompt when not connected raises error."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )

        client = MCPClient("test", config)

        with pytest.raises(RuntimeError, match="Not connected"):
            await client.get_prompt("test")

    @pytest.mark.asyncio
    async def test_get_prompt_error(self):
        """Test getting prompt with error response."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )

        client = MCPClient("test", config)
        client.connected = True

        mock_response = {"error": {"code": -32602, "message": "Invalid prompt name"}}

        with patch.object(client, "_send_message", new_callable=AsyncMock):
            with patch.object(client, "_receive_message", return_value=mock_response):
                with pytest.raises(RuntimeError, match="Prompt get error"):
                    await client.get_prompt("nonexistent")


class TestMCPLogging:
    """Test MCP Logging protocol implementation."""

    @pytest.mark.asyncio
    async def test_set_logging_level_success(self):
        """Test successfully setting logging level."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )

        client = MCPClient("test", config)
        client.connected = True

        mock_response = {"result": {}}

        with patch.object(client, "_send_message", new_callable=AsyncMock) as mock_send:
            with patch.object(client, "_receive_message", return_value=mock_response):
                result = await client.set_logging_level("debug")

                # Verify request
                request = mock_send.call_args[0][0]
                assert request["method"] == "logging/setLevel"
                assert request["params"]["level"] == "debug"

                assert result is True

    @pytest.mark.asyncio
    async def test_set_logging_level_all_levels(self):
        """Test setting all valid logging levels."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )

        client = MCPClient("test", config)
        client.connected = True

        levels = ["debug", "info", "notice", "warning", "error", "critical", "alert", "emergency"]

        for level in levels:
            mock_response = {"result": {}}

            with patch.object(client, "_send_message", new_callable=AsyncMock):
                with patch.object(client, "_receive_message", return_value=mock_response):
                    result = await client.set_logging_level(level)
                    assert result is True

    @pytest.mark.asyncio
    async def test_set_logging_level_not_connected(self):
        """Test setting logging level when not connected."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )

        client = MCPClient("test", config)

        result = await client.set_logging_level("info")
        assert result is False

    @pytest.mark.asyncio
    async def test_set_logging_level_error(self):
        """Test setting logging level with error response."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )

        client = MCPClient("test", config)
        client.connected = True

        mock_response = {"error": {"code": -32603, "message": "Internal error"}}

        with patch.object(client, "_send_message", new_callable=AsyncMock):
            with patch.object(client, "_receive_message", return_value=mock_response):
                result = await client.set_logging_level("info")
                assert result is False


class TestMCPProtocolCompliance:
    """Test overall MCP protocol compliance."""

    @pytest.mark.asyncio
    async def test_initialize_declares_client_info(self):
        """Verify initialize request includes clientInfo per spec."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )

        client = MCPClient("test", config)

        mock_process = AsyncMock()
        mock_process.stdin.write = lambda x: None
        mock_process.stdin.drain = AsyncMock()
        client.process = mock_process

        init_response = {
            "result": {
                "protocolVersion": "0.1.0",
                "capabilities": {
                    "resources": {"subscribe": True},
                    "prompts": {},
                    "tools": {"listChanged": True},
                },
                "serverInfo": {"name": "test-server", "version": "1.0.0"},
            }
        }

        with patch.object(client, "_receive_message", return_value=init_response):
            with patch.object(client, "_send_message", new_callable=AsyncMock) as mock_send:
                await client._initialize()

                # Verify initialize request format
                request = mock_send.call_args[0][0]
                assert request["method"] == "initialize"
                assert "clientInfo" in request["params"]
                assert request["params"]["clientInfo"]["name"] == "ATOLL"
                assert request["params"]["clientInfo"]["version"] == "1.0.0"

                # Verify capabilities were stored
                assert "resources" in client.capabilities
                assert "prompts" in client.capabilities
                assert "tools" in client.capabilities

    @pytest.mark.asyncio
    async def test_jsonrpc_message_format(self):
        """Verify all requests follow JSON-RPC 2.0 format."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )

        client = MCPClient("test", config)
        client.connected = True

        mock_response = {"result": {}}

        methods_to_test = [
            ("list_tools", []),
            ("list_resources", []),
            ("list_prompts", []),
            ("list_resource_templates", []),
            ("set_logging_level", ["info"]),
        ]

        for method_name, args in methods_to_test:
            with patch.object(client, "_send_message", new_callable=AsyncMock) as mock_send:
                with patch.object(client, "_receive_message", return_value=mock_response):
                    method = getattr(client, method_name)
                    await method(*args)

                    request = mock_send.call_args[0][0]

                    # Verify JSON-RPC 2.0 format
                    assert request["jsonrpc"] == "2.0"
                    assert "id" in request
                    assert isinstance(request["id"], int)
                    assert "method" in request
                    assert "params" in request
