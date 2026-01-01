"""Extended unit tests for agent module to improve coverage."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from atoll.agent.agent import OllamaMCPAgent
from atoll.mcp.server_manager import MCPServerManager
from atoll.mcp.tool_registry import ToolRegistry


class TestOllamaMCPAgentExtended:
    """Extended tests for OllamaMCPAgent."""

    @pytest.mark.asyncio
    async def test_process_prompt_with_tools(self, ollama_config, mock_ui):
        """Test process_prompt with tools available."""
        mock_manager = Mock(spec=MCPServerManager)
        mock_registry = Mock(spec=ToolRegistry)
        mock_registry.tools = {
            "test_tool": {
                "name": "test_tool",
                "description": "A test tool",
                "server": "test_server",
            }
        }
        mock_manager.tool_registry = mock_registry
        mock_manager.clients = {}

        agent = OllamaMCPAgent(
            ollama_config=ollama_config,
            mcp_manager=mock_manager,
            ui=mock_ui,
        )

        # Mock the LLM
        mock_llm = Mock()
        mock_llm.invoke = Mock(return_value="response with tools")
        agent.llm = mock_llm

        # Mock reasoning engine
        agent.reasoning_engine.analyze = AsyncMock(return_value=[])

        result = await agent.process_prompt("test")
        assert result == "response with tools"

    @pytest.mark.asyncio
    async def test_process_prompt_error_handling(self, ollama_config, mock_ui):
        """Test error handling in process_prompt."""
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

        # Mock LLM to raise an exception
        mock_llm = Mock()
        mock_llm.invoke = Mock(side_effect=Exception("Test error"))
        agent.llm = mock_llm

        result = await agent.process_prompt("test")
        assert "Error processing prompt" in result
        mock_ui.display_error.assert_called()

    @pytest.mark.asyncio
    async def test_process_prompt_empty_response(self, ollama_config, mock_ui):
        """Test when LLM returns empty response."""
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

        # Mock LLM
        mock_llm = Mock()
        mock_llm.invoke = Mock(return_value="")
        agent.llm = mock_llm

        # Mock reasoning engine
        agent.reasoning_engine.analyze = AsyncMock(return_value=[])

        result = await agent.process_prompt("test")
        assert result == ""

    @pytest.mark.asyncio
    async def test_list_models_error(self, ollama_config, mock_ui):
        """Test list_models when request fails."""
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

        # Mock aiohttp to raise exception
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session_class.side_effect = Exception("Network error")

            models = await agent.list_models()

            assert models == []
            mock_ui.display_error.assert_called()

    def test_clear_memory(self, ollama_config, mock_ui):
        """Test clearing memory."""
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

        agent.clear_memory()
        mock_ui.display_info.assert_called_with("Conversation memory cleared")

    def test_create_agent_no_tools(self, ollama_config, mock_ui):
        """Test creating agent without tools."""
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

        assert agent.tools == []
        assert agent.llm is not None
        assert agent.llm is not None
