"""Unit tests for MCP tools module."""

import pytest
from ollama_mcp_agent.mcp.tools import MCPTool, MCPToolRegistry


class TestMCPTool:
    """Test MCPTool class."""
    
    def test_tool_initialization(self):
        """Test tool initialization."""
        metadata = {
            "description": "Test tool description",
            "inputSchema": {"type": "object", "properties": {}}
        }
        
        tool = MCPTool(
            name="test_tool",
            server="test_server",
            metadata=metadata
        )
        
        assert tool.name == "test_tool"
        assert tool.server == "test_server"
        assert tool.description == "Test tool description"
        assert tool.parameters == {"type": "object", "properties": {}}
    
    def test_tool_default_description(self):
        """Test tool with default description."""
        tool = MCPTool(
            name="test_tool",
            server="test_server",
            metadata={}
        )
        
        assert tool.description == "Tool: test_tool"
        assert tool.parameters == {}


class TestMCPToolRegistry:
    """Test MCPToolRegistry class."""
    
    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = MCPToolRegistry()
        assert registry.tools == {}
    
    def test_register_tool(self):
        """Test registering a tool."""
        registry = MCPToolRegistry()
        
        tool_data = {
            "name": "test_tool",
            "description": "A test tool",
            "inputSchema": {"type": "object"}
        }
        
        registry.register_tool("test_server", tool_data)
        
        assert "test_server_test_tool" in registry.tools
        assert registry.tools["test_server_test_tool"]["name"] == "test_tool"
        assert registry.tools["test_server_test_tool"]["server"] == "test_server"
    
    def test_register_tool_without_name(self):
        """Test registering a tool without name."""
        registry = MCPToolRegistry()
        
        tool_data = {
            "description": "A test tool"
        }
        
        registry.register_tool("test_server", tool_data)
        
        assert len(registry.tools) == 0
    
    def test_get_tool(self):
        """Test getting a tool."""
        registry = MCPToolRegistry()
        
        tool_data = {
            "name": "test_tool",
            "description": "A test tool"
        }
        
        registry.register_tool("test_server", tool_data)
        
        tool = registry.get_tool("test_server_test_tool")
        assert tool["name"] == "test_tool"
        
        # Test non-existent tool
        assert registry.get_tool("non_existent") == {}
    
    def test_list_tools(self):
        """Test listing all tools."""
        registry = MCPToolRegistry()
        
        registry.register_tool("server1", {"name": "tool1"})
        registry.register_tool("server2", {"name": "tool2"})
        
        tools = registry.list_tools()
        assert len(tools) == 2
        assert "server1_tool1" in tools
        assert "server2_tool2" in tools