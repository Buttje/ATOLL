"""Unit tests for main application."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from atoll.config.models import MCPConfig, OllamaConfig
from atoll.main import Application


class TestApplication:
    """Test the Application class."""

    @pytest.mark.skip(
        reason="Integration-level test - mocking startup flow requires module reload. Covered by integration tests."
    )
    @pytest.mark.asyncio
    async def test_startup(self):
        """Test application startup."""
        with (
            patch("atoll.config.manager.ConfigManager") as mock_config_manager,
            patch("atoll.ui.terminal.TerminalUI"),
            patch("atoll.mcp.server_manager.MCPServerManager") as mock_server_manager,
            patch("atoll.agent.agent.OllamaMCPAgent") as mock_agent,
            patch("builtins.print"),  # Mock print to avoid Unicode errors
        ):
            # Set up mocks
            mock_config_instance = mock_config_manager.return_value
            mock_config_instance.ollama_config = OllamaConfig()
            mock_config_instance.mcp_config = MCPConfig()
            mock_config_instance.load_configs = Mock()

            mock_server_instance = mock_server_manager.return_value
            mock_server_instance.connect_all = AsyncMock()

            # Mock the agent's async methods
            mock_agent_instance = mock_agent.return_value
            mock_agent_instance.check_server_connection = AsyncMock(return_value=True)
            mock_agent_instance.check_model_available = AsyncMock(return_value=True)

            app = Application()
            await app.startup()

            # Verify startup completed successfully
            assert app.agent is not None
            assert app.mcp_manager is not None
            # Verify connect_all was called
            assert mock_server_instance.connect_all.called

    @pytest.mark.asyncio
    async def test_handle_prompt(self):
        """Test handling prompts."""
        with patch("atoll.config.manager.ConfigManager"):
            app = Application()

            # Set up mock agent
            app.agent = Mock()
            app.agent.process_prompt = AsyncMock(return_value="Test response")

            await app.handle_prompt("Test prompt")

            app.agent.process_prompt.assert_called_once_with("Test prompt")

    @pytest.mark.asyncio
    async def test_handle_command_models(self):
        """Test handling models command."""
        with patch("atoll.config.manager.ConfigManager"):
            app = Application()

            app.agent = Mock()
            app.agent.list_models = AsyncMock(return_value=["model1", "model2"])
            app.config_manager = Mock()
            app.config_manager.ollama_config = Mock()
            app.config_manager.ollama_config.model = "model1"
            app.ui = Mock()

            await app.handle_command("models")

            app.agent.list_models.assert_called_once()
            app.ui.display_models.assert_called_once_with(["model1", "model2"], "model1")

    @pytest.mark.asyncio
    async def test_handle_command_changemodel(self):
        """Test handling changemodel command."""
        with patch("atoll.config.manager.ConfigManager"):
            app = Application()

            app.agent = Mock()
            app.agent.change_model = Mock(return_value=True)
            app.ui = Mock()
            app.config_manager.ollama_config = Mock()
            app.config_manager.save_ollama_config = Mock()

            await app.handle_command("changemodel test-model")

            app.agent.change_model.assert_called_once_with("test-model")
            assert app.config_manager.ollama_config.model == "test-model"
            app.config_manager.save_ollama_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_command_quit(self):
        """Test handling quit command."""
        with patch("atoll.config.manager.ConfigManager"):
            app = Application()

            app.ui = Mock()
            app.ui.running = True

            await app.handle_command("quit")

            assert app.ui.running is False

    @pytest.mark.asyncio
    async def test_handle_command_unknown(self):
        """Test handling unknown command."""
        with patch("atoll.config.manager.ConfigManager"):
            app = Application()

            app.ui = Mock()

            await app.handle_command("unknown_command")

            # Should display error for unknown command
            app.ui.display_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_loop_keyboard_interrupt(self):
        """Test the main run loop with keyboard interrupt."""
        with (
            patch("atoll.config.manager.ConfigManager"),
            patch("atoll.ui.terminal.TerminalUI"),
            patch("atoll.mcp.server_manager.MCPServerManager"),
            patch("atoll.agent.agent.OllamaMCPAgent"),
        ):
            app = Application()

            # Mock startup and shutdown
            app.startup = AsyncMock()
            app.shutdown = AsyncMock()
            app.ui = Mock()
            app.ui.display_header = Mock()
            app.colors = Mock()
            app.colors.info = Mock(return_value="Exiting...")

            # Set running to False immediately to exit the loop
            app.ui.running = False

            # Run should handle the loop exit gracefully
            await app.run()

            # Verify startup and shutdown were called
            app.startup.assert_called_once()
            app.shutdown.assert_called_once()


def test_main_function():
    """Test the main entry point."""
    import importlib

    main_module = importlib.import_module("atoll.main")

    with (
        patch("atoll.config.manager.ConfigManager"),
        patch("atoll.ui.terminal.TerminalUI"),
        patch("asyncio.run") as mock_run,
        patch("sys.argv", ["atoll"]),
    ):
        main_module.main()

        # Verify asyncio.run was called with a coroutine
        mock_run.assert_called_once()
        assert asyncio.iscoroutine(mock_run.call_args[0][0]) or hasattr(
            mock_run.call_args[0][0], "__await__"
        )
