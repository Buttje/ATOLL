# Save this to tests\unit\test_server_manager_extended.py
"""Extended tests for MCP server manager."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from atoll.mcp.server_manager import MCPServerManager
from atoll.config.models import MCPConfig, MCPServerConfig


class TestMCPServerManagerExtended:
    """Extended tests for MCPServerManager."""
    
    @pytest.mark.asyncio
    async def test_connect_and_discover_with_tools(self):
        """Test connecting and discovering tools."""
        config = MCPConfig(
            servers={
                "test": MCPServerConfig(
                    transport="stdio",
                    command="python",
                    args=["test.py"]
                )
            }
        )
        
        manager = MCPServerManager(config)
        
        # Create a mock client
        mock_client = Mock()
        mock_client.name = "test"
        mock_client.connect = AsyncMock(return_value=True)
        mock_client.list_tools = AsyncMock(return_value=[
            {"name": "tool1", "description": "Tool 1"},
            {"name": "tool2", "description": "Tool 2"}
        ])
        
        await manager._connect_and_discover(mock_client)
        
        mock_client.connect.assert_called_once()
        mock_client.list_tools.assert_called_once()
        
        # Check tools were registered
        assert len(manager.tool_registry.tools) == 2
    
    @pytest.mark.asyncio
    async def test_connect_and_discover_connection_failure(self):
        """Test handling connection failure during discovery."""
        config = MCPConfig(
            servers={
                "test": MCPServerConfig(
                    transport="stdio",
                    command="python"
                )
            }
        )
        
        manager = MCPServerManager(config)
        
        # Create a mock client that fails to connect
        mock_client = Mock()
        mock_client.name = "test"
        mock_client.connect = AsyncMock(return_value=False)
        
        await manager._connect_and_discover(mock_client)
        
        mock_client.connect.assert_called_once()
        # No tools should be registered
        assert len(manager.tool_registry.tools) == 0
    
    @pytest.mark.asyncio
    async def test_connect_and_discover_exception(self):
        """Test handling exception during discovery."""
        config = MCPConfig(
            servers={
                "test": MCPServerConfig(
                    transport="stdio",
                    command="python"
                )
            }
        )
        
        manager = MCPServerManager(config)
        
        # Create a mock client that raises exception
        mock_client = Mock()
        mock_client.name = "test"
        mock_client.connect = AsyncMock(side_effect=Exception("Connection error"))
        
        # Should not raise exception
        await manager._connect_and_discover(mock_client)
        
        # No tools should be registered
        assert len(manager.tool_registry.tools) == 0
    
    @pytest.mark.asyncio
    async def test_execute_tool(self):
        """Test executing a tool through the manager."""
        config = MCPConfig(servers={})
        manager = MCPServerManager(config)
        
        # Register tools using the correct method name
        manager.tool_registry.register_tools("test_server", [
            {
                "name": "test_tool",
                "description": "Test tool"
            }
        ])
        
        # Create a mock client
        mock_client = Mock()
        mock_client.call_tool = AsyncMock(return_value={"result": "success"})
        manager.clients["test_server"] = mock_client
        
        # Execute the tool
        result = await manager.execute_tool(
            server_name="test_server",
            tool_name="test_tool",
            arguments={"arg": "value"}
        )
        
        assert result == {"result": "success"}
        mock_client.call_tool.assert_called_once_with("test_tool", {"arg": "value"})
    
    @pytest.mark.asyncio
    async def test_execute_tool_server_not_found(self):
        """Test executing tool when server not found."""
        config = MCPConfig(servers={})
        manager = MCPServerManager(config)
        
        with pytest.raises(ValueError, match="Server 'nonexistent' not found"):
            await manager.execute_tool(
                server_name="nonexistent",
                tool_name="test_tool",
                arguments={}
            )