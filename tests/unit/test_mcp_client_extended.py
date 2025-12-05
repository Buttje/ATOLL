"""Extended tests for MCP client."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from ollama_mcp_agent.mcp.client import MCPClient
from ollama_mcp_agent.config.models import MCPServerConfig


class TestMCPClientExtended:
    """Extended tests for MCPClient."""
    
    @pytest.mark.asyncio
    async def test_connect_unsupported_transport(self):
        """Test connecting with unsupported transport."""
        config = MCPServerConfig(
            transport="websocket",
            command="test",
        )
        
        client = MCPClient("test", config)
        result = await client.connect()
        
        assert result is False
        assert client.connected is False
    
    @pytest.mark.asyncio
    async def test_connect_sse_not_implemented(self):
        """Test SSE transport (not implemented)."""
        config = MCPServerConfig(
            transport="sse",
            url="http://localhost:8000",
        )
        
        client = MCPClient("test", config)
        result = await client.connect()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_message(self):
        """Test sending a message."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
            args=["test.py"],
        )
        
        client = MCPClient("test", config)
        
        # Mock process with proper async mocks
        mock_process = Mock()
        mock_stdin = Mock()
        mock_stdin.write = Mock()
        mock_stdin.drain = AsyncMock()
        mock_process.stdin = mock_stdin
        client.process = mock_process
        
        message = {"test": "data"}
        await client._send_message(message)
        
        mock_stdin.write.assert_called_once()
        mock_stdin.drain.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_receive_message_timeout(self):
        """Test receiving message with timeout."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
            timeoutSeconds=1,
        )
        
        client = MCPClient("test", config)
        
        # Mock process with timeout
        mock_process = Mock()
        mock_stdout = Mock()
        mock_stdout.readline = AsyncMock(side_effect=TimeoutError)
        mock_process.stdout = mock_stdout
        client.process = mock_process
        
        with patch('asyncio.wait_for', side_effect=TimeoutError):
            result = await client._receive_message()
            assert result is None
    
    @pytest.mark.asyncio
    async def test_receive_message_json_error(self):
        """Test receiving message with JSON decode error."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
            timeoutSeconds=1,
        )
        
        client = MCPClient("test", config)
        
        # Mock process with invalid JSON
        mock_process = Mock()
        mock_stdout = Mock()
        mock_stdout.readline = AsyncMock(return_value=b"invalid json\n")
        mock_process.stdout = mock_stdout
        client.process = mock_process
        
        result = await client._receive_message()
        assert result is None
    
    @pytest.mark.asyncio
    async def test_list_tools_with_cached_tools(self):
        """Test listing tools with cached tools."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )
        
        client = MCPClient("test", config)
        client.connected = True
        
        # Test with dict format
        client.tools = {
            "tool1": {"description": "Tool 1"},
            "tool2": {"description": "Tool 2"}
        }
        
        tools = await client.list_tools()
        assert len(tools) == 2
        assert tools[0]["name"] in ["tool1", "tool2"]
        
        # Test with list format
        client.tools = [
            {"name": "tool1", "description": "Tool 1"},
            {"name": "tool2", "description": "Tool 2"}
        ]
        
        tools = await client.list_tools()
        assert len(tools) == 2
    
    @pytest.mark.asyncio
    async def test_list_tools_not_connected(self):
        """Test listing tools when not connected."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )
        
        client = MCPClient("test", config)
        client.connected = False
        
        tools = await client.list_tools()
        assert tools == []
    
    @pytest.mark.asyncio
    async def test_call_tool_not_connected(self):
        """Test calling tool when not connected."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )
        
        client = MCPClient("test", config)
        client.connected = False
        
        with pytest.raises(RuntimeError, match="Not connected"):
            await client.call_tool("test_tool", {})
    
    @pytest.mark.asyncio
    async def test_call_tool_error_response(self):
        """Test calling tool with error response."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )
        
        client = MCPClient("test", config)
        client.connected = True
        
        # Mock process with proper async mocks
        mock_process = Mock()
        mock_stdin = Mock()
        mock_stdin.write = Mock()
        mock_stdin.drain = AsyncMock()
        mock_process.stdin = mock_stdin
        client.process = mock_process
        
        # Mock error response
        with patch.object(client, '_receive_message', return_value={"error": "Test error"}):
            with pytest.raises(RuntimeError, match="Tool call error"):
                await client.call_tool("test_tool", {})
    
    @pytest.mark.asyncio
    async def test_call_tool_no_response(self):
        """Test calling tool with no response."""
        config = MCPServerConfig(
            transport="stdio",
            command="python",
        )
        
        client = MCPClient("test", config)
        client.connected = True
        
        # Mock process with proper async mocks
        mock_process = Mock()
        mock_stdin = Mock()
        mock_stdin.write = Mock()
        mock_stdin.drain = AsyncMock()
        mock_process.stdin = mock_stdin
        client.process = mock_process
        
        # Mock no response
        with patch.object(client, '_receive_message', return_value=None):
            with pytest.raises(RuntimeError, match="No response"):
                await client.call_tool("test_tool", {})