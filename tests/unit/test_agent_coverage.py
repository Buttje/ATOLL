"""Tests to improve agent coverage."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from atoll.agent.root_agent import RootAgent
from atoll.mcp.server_manager import MCPServerManager
from atoll.mcp.tool_registry import ToolRegistry


class TestAgentCoverage:
    """Tests to improve agent coverage."""

    @pytest.mark.asyncio
    async def test_list_models_success(self, ollama_config, mock_ui):
        """Test successful model listing."""
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

        # Mock aiohttp response
        mock_response_data = {
            "models": [{"name": "model1"}, {"name": "model2"}, {"name": "model3"}]
        }

        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_get = Mock(return_value=mock_response)
            mock_session_instance = AsyncMock()
            mock_session_instance.get = mock_get
            mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session_instance.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_session_instance

            models = await agent.list_models()

            assert len(models) == 3
            assert "model1" in models
            assert "model2" in models
            assert "model3" in models

    def test_change_model_failure(self, ollama_config, mock_ui):
        """Test model change failure."""
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

        # Mock LLM creation to fail
        with patch.object(agent, "_initialize_llm", side_effect=Exception("LLM creation failed")):
            result = agent.change_model("new-model")

            assert result is False
            mock_ui.display_error.assert_called()

    @pytest.mark.asyncio
    async def test_process_prompt_with_reasoning(self, ollama_config, mock_ui):
        """Test process_prompt with reasoning output."""
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

        # Mock reasoning engine to return reasoning steps if it exists
        if agent.reasoning_engine:
            with patch.object(agent.reasoning_engine, "analyze", return_value=["Step 1", "Step 2"]):
                mock_llm = Mock()
                mock_llm.invoke = Mock(return_value="response")
                agent.llm = mock_llm

                result = await agent.process_prompt("test")
                assert result == "response"
        else:
            mock_llm = Mock()
            mock_llm.invoke = Mock(return_value="response")
            agent.llm = mock_llm

            result = await agent.process_prompt("test")
            assert result == "response"
