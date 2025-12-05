"""Unit tests for MCP server manager."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from ollama_mcp_agent.mcp.server_manager import MCPServerManager
from ollama_mcp_agent.config.models import MCPConfig, MCPServerConfig


class TestMCPServerManager:
    """Test the MCPServerManager class."""
    
    def test_initialization(self):
        """Test server manager initialization."""
        config = MCPConfig(servers={})
        manager = MCPServerManager(config)
        
        assert manager.config == config
        assert len(manager.clients) == 0
        assert manager.tool_registry is not None
    
    @pytest.mark.asyncio
    async def test_connect_all(self):
        """Test connecting to all servers."""
        config = MCPConfig(servers={
            "server1": MCPServerConfig(
                transport="stdio",
                command="echo",
                args=[],
                timeoutSeconds=10
            )
        })
        
        manager = MCPServerManager(config)
        
        with patch('ollama_mcp_agent.mcp.server_manager.MCPClient') as mock_client_class:
            mock_client = Mock()
            mock_client.connect = AsyncMock(return_value=True)
            mock_client.list_tools = AsyncMock(return_value=[{"name": "tool1"}])
            mock_client.name = "server1"
            mock_client_class.return_value = mock_client
            
            await manager.connect_all()
            
            assert "server1" in manager.clients
            mock_client.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnect_all(self):
        """Test disconnecting from all servers."""
        config = MCPConfig(servers={})
        manager = MCPServerManager(config)
        
        # Add a mock client
        mock_client = Mock()
        mock_client.disconnect = AsyncMock()
        manager.clients["server1"] = mock_client
        
        await manager.disconnect_all()
        
        mock_client.disconnect.assert_called_once()
        assert len(manager.clients) == 0
        @pytest.mark.asyncio
        async def test_execute_tool(self):
            """Test executing a tool."""
            config = MCPConfig(servers={})
            manager = MCPServerManager(config)
        
            # Set up mock client
            mock_client = Mock()
            mock_client.call_tool = AsyncMock(return_value={"result": "success"})
            manager.clients["server1"] = mock_client
        
            # Register tool using correct method name
            manager.tool_registry.register_tools("server1", [{"name": "tool1"}])
        
            # Execute tool
            result = await manager.execute_tool("server1", "tool1", {"arg": "value"})
        
            assert result == {"result": "success"}
            mock_client.call_tool.assert_called_once_with("tool1", {"arg": "value"})
    
    def test_get_client(self):
        """Test getting a specific client."""
        config = MCPConfig(servers={})
        manager = MCPServerManager(config)
        
        mock_client = Mock()
        manager.clients["server1"] = mock_client
        
        assert manager.get_client("server1") == mock_client
        assert manager.get_client("nonexistent") is None
    
    def test_list_servers(self):
        """Test listing server names."""
        config = MCPConfig(servers={})
        manager = MCPServerManager(config)
        
        manager.clients["server1"] = Mock()
        manager.clients["server2"] = Mock()
        
        servers = manager.list_servers()
        assert len(servers) == 2
        assert "server1" in servers
        assert "server2" in servers