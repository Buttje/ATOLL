"""Unit tests for the agent module."""

from unittest.mock import AsyncMock, Mock

import pytest

from atoll.agent.root_agent import RootAgent
from atoll.mcp.server_manager import MCPServerManager
from atoll.mcp.tool_registry import ToolRegistry


class TestRootAgent:
    """Test the RootAgent class (replaces OllamaMCPAgent tests)."""

    @pytest.mark.asyncio
    async def test_agent_initialization(self, ollama_config, mock_ui):
        """Test agent initialization."""
        mock_manager = Mock(spec=MCPServerManager)
        mock_registry = Mock(spec=ToolRegistry)
        mock_registry.tools = {}
        mock_manager.tool_registry = mock_registry
        mock_manager.clients = {}

        agent = RootAgent(
            name="TestAgent",
            version="1.0.0",
            llm_config=ollama_config,
            mcp_manager=mock_manager,
            ui=mock_ui,
        )

        assert agent.llm_config == ollama_config
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

        agent = RootAgent(
            name="TestAgent",
            version="1.0.0",
            llm_config=ollama_config,
            mcp_manager=mock_manager,
            ui=mock_ui,
        )

        # Mock the entire LLM object
        mock_llm = Mock()
        mock_llm.invoke = Mock(return_value="Test response")
        agent.llm = mock_llm

        # Mock reasoning engine if it exists
        if agent.reasoning_engine:
            agent.reasoning_engine.analyze = AsyncMock(return_value=[])

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

        agent = RootAgent(
            name="TestAgent",
            version="1.0.0",
            llm_config=ollama_config,
            mcp_manager=mock_manager,
            ui=mock_ui,
        )

        result = agent.change_model("new-model")

        assert result is True
        assert agent.llm_config.model == "new-model"
