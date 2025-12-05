"""Unit tests for the agent module."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from ollama_mcp_agent.agent.agent import OllamaMCPAgent
from ollama_mcp_agent.mcp.server_manager import MCPServerManager
from ollama_mcp_agent.mcp.tool_registry import ToolRegistry


class TestOllamaMCPAgent:
    """Test the OllamaMCPAgent class."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, ollama_config, mock_ui):
        """Test agent initialization."""
        mock_manager = Mock(spec=MCPServerManager)
        mock_registry = Mock(spec=ToolRegistry)
        mock_registry.tools = {}
        mock_manager.tool_registry = mock_registry
        mock_manager.clients = {}
        
        agent = OllamaMCPAgent(
            ollama_config=ollama_config,
            mcp_manager=mock_manager,
            ui=mock_ui,
        )
        
        assert agent.ollama_config == ollama_config
        assert agent.mcp_manager == mock_manager
        assert agent.ui == mock_ui
        assert agent.llm is not None
    
    @pytest.mark.asyncio
    async def test_process_prompt(self, ollama_config, mock_ui):
        """Test processing a user prompt."""
        mock_manager = Mock(spec=MCPServerManager)
        mock_registry = Mock(spec=ToolRegistry)
        mock_registry.tools = {}
        mock_manager.tool_registry = mock_registry
        mock_manager.clients = {}
        
        agent = OllamaMCPAgent(
            ollama_config=ollama_config,
            mcp_manager=mock_manager,
            ui=mock_ui,
        )
        
        # Mock the entire LLM object
        mock_llm = Mock()
        mock_llm.invoke = Mock(return_value="Test response")
        agent.llm = mock_llm
        
        result = await agent.process_prompt("Test prompt")
        
        assert result == "Test response"
        mock_ui.display_user_input.assert_called_with("Test prompt")
        mock_ui.display_response.assert_called_with("Test response")
        mock_llm.invoke.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_change_model(self, ollama_config, mock_ui):
        """Test changing the LLM model."""
        mock_manager = Mock(spec=MCPServerManager)
        mock_registry = Mock(spec=ToolRegistry)
        mock_registry.tools = {}
        mock_manager.tool_registry = mock_registry
        mock_manager.clients = {}
        
        agent = OllamaMCPAgent(
            ollama_config=ollama_config,
            mcp_manager=mock_manager,
            ui=mock_ui,
        )
        
        result = agent.change_model("new-model")
        
        assert result is True
        assert agent.ollama_config.model == "new-model"