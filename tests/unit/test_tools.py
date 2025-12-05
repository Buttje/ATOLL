"""Unit tests for MCP tools integration."""

import json
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from ollama_mcp_agent.agent.tools import MCPToolWrapper
from ollama_mcp_agent.mcp.server_manager import MCPServerManager


class TestMCPToolWrapper:
    """Test the MCPToolWrapper class."""
    
    @pytest.mark.asyncio
    async def test_tool_wrapper_initialization(self):
        """Test tool wrapper initialization."""
        mock_manager = MagicMock(spec=MCPServerManager)
        
        # Don't patch BaseTool.__init__, let it initialize properly
        tool = MCPToolWrapper(
            name="test_tool",
            description="Test tool description",
            mcp_manager=mock_manager,
            server_name="test_server"
        )
        
        assert tool.name == "test_tool"
        assert tool.description == "Test tool description"
        assert tool.server_name == "test_server"
    
    @pytest.mark.asyncio
    async def test_arun_with_json_input(self):
        """Test async execution with JSON input."""
        mock_manager = MagicMock(spec=MCPServerManager)
        mock_manager.execute_tool = AsyncMock(return_value={"result": "success"})
        
        tool = MCPToolWrapper(
            name="test_tool",
            description="Test tool",
            mcp_manager=mock_manager,
            server_name="test_server"
        )
        
        input_json = json.dumps({"key": "value"})
        result = await tool._arun(input_json)
        
        assert "success" in result
        assert isinstance(result, str)
        mock_manager.execute_tool.assert_called_once_with(
            server_name="test_server",
            tool_name="test_tool",
            arguments={"key": "value"}
        )
    
    @pytest.mark.asyncio
    async def test_arun_with_string_input(self):
        """Test async execution with plain string input."""
        mock_manager = MagicMock(spec=MCPServerManager)
        mock_manager.execute_tool = AsyncMock(return_value="plain result")
        
        tool = MCPToolWrapper(
            name="test_tool",
            description="Test tool",
            mcp_manager=mock_manager,
            server_name="test_server"
        )
        
        result = await tool._arun("plain input")
        
        assert result == "plain result"
        mock_manager.execute_tool.assert_called_once_with(
            server_name="test_server",
            tool_name="test_tool",
            arguments={"input": "plain input"}
        )
    
    @pytest.mark.asyncio
    async def test_arun_error_handling(self):
        """Test error handling in async execution."""
        mock_manager = MagicMock(spec=MCPServerManager)
        mock_manager.execute_tool = AsyncMock(side_effect=Exception("Test error"))
        
        tool = MCPToolWrapper(
            name="test_tool",
            description="Test tool",
            mcp_manager=mock_manager,
            server_name="test_server"
        )
        
        result = await tool._arun("test input")
        
        assert "Error executing tool" in result
        assert "Test error" in result
    
    def test_run_sync_wrapper(self):
        """Test synchronous execution wrapper."""
        mock_manager = MagicMock(spec=MCPServerManager)
        mock_manager.execute_tool = AsyncMock(return_value="sync result")
        
        tool = MCPToolWrapper(
            name="test_tool",
            description="Test tool",
            mcp_manager=mock_manager,
            server_name="test_server"
        )
        
        # Mock asyncio.run
        with patch('asyncio.run', return_value="sync result"):
            result = tool._run("test")
            assert result == "sync result"


class TestMCPToolIntegration:
    """Test MCP tool integration scenarios."""
    
    def test_tool_creation_from_mcp_definition(self):
        """Test creating tool from MCP tool definition."""
        tool_def = {
            "name": "analyze_binary",
            "description": "Analyzes a binary file",
            "server": "ghidra_server",
            "parameters": {
                "file_path": {"type": "string"},
                "options": {"type": "object"}
            }
        }
        
        mock_manager = MagicMock(spec=MCPServerManager)
        
        tool = MCPToolWrapper(
            name=tool_def["name"],
            description=tool_def["description"],
            mcp_manager=mock_manager,
            server_name=tool_def["server"]
        )
        
        assert tool.name == "analyze_binary"
        assert tool.description == "Analyzes a binary file"
        assert tool.server_name == "ghidra_server"