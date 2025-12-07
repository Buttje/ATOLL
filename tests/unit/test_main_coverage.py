"""Additional tests for main module to improve coverage."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from atoll.config.models import OllamaConfig
from atoll.main import Application
from atoll.ui.terminal import UIMode


class TestApplicationCoverage:
    """Additional coverage tests for Application."""

    @pytest.mark.asyncio
    async def test_run_with_exception(self):
        """Test run method with exception handling."""
        app = Application()

        with patch.object(app, "startup", new_callable=AsyncMock):
            with patch.object(app.ui, "display_header"):
                # Create a counter to limit iterations
                call_count = [0]

                def get_input_side_effect(*args, **kwargs):
                    call_count[0] += 1
                    if call_count[0] == 1:
                        raise Exception("Test error")
                    else:
                        app.ui.running = False
                        return "quit"

                with patch.object(app.ui, "get_input", side_effect=get_input_side_effect):
                    with patch.object(app.ui, "display_error") as mock_error:
                        app.ui.running = True

                        await app.run()

                        mock_error.assert_called()

    @pytest.mark.asyncio
    async def test_handle_command_with_spaces(self):
        """Test handle_command with extra spaces."""
        app = Application()
        app.agent = Mock()
        app.agent.list_models = AsyncMock(return_value=["model1", "model2"])
        app.agent.change_model = Mock(return_value=True)

        # Mock the config manager
        app.config_manager.ollama_config = OllamaConfig(
            base_url="http://localhost", port=11434, model="test-model"
        )

        with patch.object(app.ui, "display_models"):
            # Test with extra spaces
            await app.handle_command("  models  ")
            app.agent.list_models.assert_called_once()

        # Test changemodel with spaces
        with patch.object(app.ui, "display_info"):
            await app.handle_command("  changemodel   test-model  ")
            app.agent.change_model.assert_called_with("test-model")

    @pytest.mark.asyncio
    async def test_handle_prompt_empty_string(self):
        """Test handle_prompt with empty string."""
        app = Application()
        app.agent = Mock()
        app.agent.process_prompt = AsyncMock()

        # Empty prompt should not call process_prompt
        await app.handle_prompt("")
        app.agent.process_prompt.assert_not_called()

        # Whitespace-only prompt should not call process_prompt
        await app.handle_prompt("   ")
        app.agent.process_prompt.assert_not_called()

    @pytest.mark.asyncio
    async def test_startup_connection_messages(self):
        """Test startup displays connection messages."""
        app = Application()

        # Properly mock the ollama_config
        from atoll.config.models import OllamaConfig

        app.config_manager.ollama_config = OllamaConfig()
        app.config_manager.mcp_config = Mock(servers={})

        with patch.object(app.config_manager, "load_configs"):
            with patch("atoll.mcp.server_manager.MCPServerManager") as mock_manager_class:
                mock_manager = Mock()
                mock_manager.connect_all = AsyncMock()
                mock_manager_class.return_value = mock_manager

                with patch("atoll.agent.agent.OllamaMCPAgent") as mock_agent_class:
                    # Mock the agent's async methods
                    mock_agent_instance = Mock()
                    mock_agent_instance.check_server_connection = AsyncMock(return_value=True)
                    mock_agent_instance.check_model_available = AsyncMock(return_value=True)
                    mock_agent_class.return_value = mock_agent_instance

                    with patch("builtins.print") as mock_print:
                        await app.startup()

                        # Check that startup messages were printed
                        assert mock_print.call_count > 0

    @pytest.mark.asyncio
    async def test_run_esc_key_handling(self):
        """Test ESC key toggles mode."""
        app = Application()

        with patch.object(app, "startup", new_callable=AsyncMock):
            with patch.object(app.ui, "display_header"):
                # Create a controlled input sequence
                call_count = [0]

                def get_input_side_effect(*args, **kwargs):
                    call_count[0] += 1
                    if call_count[0] == 1:
                        return "ESC"
                    else:
                        # Stop the loop after ESC is handled
                        app.ui.running = False
                        return "quit"

                with patch.object(app.ui, "get_input", side_effect=get_input_side_effect):
                    with patch.object(app.ui, "toggle_mode") as mock_toggle:
                        app.ui.mode = UIMode.COMMAND
                        app.ui.running = True

                        await app.run()

                        # Verify toggle_mode was called
                        mock_toggle.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_command_case_insensitive(self):
        """Test commands are case-insensitive."""
        app = Application()
        app.agent = Mock()
        app.agent.list_models = AsyncMock(return_value=[])

        # Mock the config manager
        app.config_manager.ollama_config = OllamaConfig(
            base_url="http://localhost", port=11434, model="test-model"
        )

        with patch.object(app.ui, "display_models"):
            # Test uppercase
            await app.handle_command("MODELS")
            app.agent.list_models.assert_called()

            # Test mixed case
            app.agent.list_models.reset_mock()
            await app.handle_command("MoDeLs")
            app.agent.list_models.assert_called()
            app.agent.list_models.assert_called()
