"""Unit tests for tool registry."""

import pytest
from ollama_mcp_agent.mcp.tool_registry import ToolRegistry


class TestToolRegistry:
    """Test the ToolRegistry class."""
    
    def test_initialization(self):
        """Test registry initialization."""
        registry = ToolRegistry()
        assert registry.tools == {}
        assert registry._tool_to_server == {}
    
    def test_register_tools(self):
        """Test registering tools."""
        registry = ToolRegistry()
        
        tools = [
            {"name": "tool1", "description": "Tool 1"},
            {"name": "tool2", "description": "Tool 2"}
        ]
        
        registry.register_tools("server1", tools)
        
        assert len(registry.tools) == 2
        assert "tool1" in registry.tools
        assert registry.tools["tool1"]["server"] == "server1"
        assert registry._tool_to_server["tool1"] == "server1"
    
    def test_register_duplicate_tool(self):
        """Test registering duplicate tools."""
        registry = ToolRegistry()
        
        registry.register_tools("server1", [{"name": "tool1"}])
        registry.register_tools("server2", [{"name": "tool1"}])
        
        # Should overwrite with the latest
        assert registry._tool_to_server["tool1"] == "server2"
    
    def test_unregister_server_tools(self):
        """Test unregistering all tools from a server."""
        registry = ToolRegistry()
        
        registry.register_tools("server1", [{"name": "tool1"}, {"name": "tool2"}])
        registry.register_tools("server2", [{"name": "tool3"}])
        
        registry.unregister_server_tools("server1")
        
        assert "tool1" not in registry.tools
        assert "tool2" not in registry.tools
        assert "tool3" in registry.tools
    
    def test_get_tool(self):
        """Test getting a tool by name."""
        registry = ToolRegistry()
        
        registry.register_tools("server1", [{"name": "tool1", "data": "value"}])
        
        tool = registry.get_tool("tool1")
        assert tool is not None
        assert tool["data"] == "value"
        
        assert registry.get_tool("nonexistent") is None
    
    def test_get_server_for_tool(self):
        """Test getting server name for a tool."""
        registry = ToolRegistry()
        
        registry.register_tools("server1", [{"name": "tool1"}])
        
        assert registry.get_server_for_tool("tool1") == "server1"
        assert registry.get_server_for_tool("nonexistent") is None
    
    def test_list_tools(self):
        """Test listing all tools."""
        registry = ToolRegistry()
        
        registry.register_tools("server1", [{"name": "tool1"}, {"name": "tool2"}])
        
        tools = registry.list_tools()
        assert len(tools) == 2
        assert "tool1" in tools
        assert "tool2" in tools
    
    def test_list_server_tools(self):
        """Test listing tools from a specific server."""
        registry = ToolRegistry()
        
        registry.register_tools("server1", [{"name": "tool1"}, {"name": "tool2"}])
        registry.register_tools("server2", [{"name": "tool3"}])
        
        server1_tools = registry.list_server_tools("server1")
        assert len(server1_tools) == 2
        assert "tool1" in server1_tools
        assert "tool2" in server1_tools
        assert "tool3" not in server1_tools
    
    def test_clear(self):
        """Test clearing all tools."""
        registry = ToolRegistry()
        
        registry.register_tools("server1", [{"name": "tool1"}])
        registry.clear()
        
        assert len(registry.tools) == 0
        assert len(registry._tool_to_server) == 0
    
    def test_skip_tool_without_name(self):
        """Test skipping tools without names."""
        registry = ToolRegistry()
        
        tools = [
            {"description": "No name tool"},
            {"name": "valid_tool"}
        ]
        
        registry.register_tools("server1", tools)
        
        assert len(registry.tools) == 1
        assert "valid_tool" in registry.tools