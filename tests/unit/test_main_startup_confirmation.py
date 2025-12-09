"""Tests for startup confirmation functionality."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from atoll.config.models import OllamaConfig
from atoll.main import Application


class TestStartupConfirmation:
    """Test startup confirmation feature."""

    @pytest.mark.asyncio
    async def test_wait_for_startup_confirmation_enter(self):
        """Test that pressing Enter returns True."""
        app = Application()

        with patch("atoll.ui.input_handler.InputHandler") as MockInputHandler:
            mock_handler = Mock()
            mock_handler.is_windows = True
            mock_handler._get_char_windows = Mock(return_value="\r")
            MockInputHandler.return_value = mock_handler

            with patch("builtins.print"):
                result = await app._wait_for_startup_confirmation()

            assert result is True

    @pytest.mark.asyncio
    async def test_wait_for_startup_confirmation_escape(self):
        """Test that pressing Escape returns False."""
        app = Application()

        with patch("atoll.ui.input_handler.InputHandler") as MockInputHandler:
            mock_handler = Mock()
            mock_handler.is_windows = True
            mock_handler._get_char_windows = Mock(return_value="\x1b")
            MockInputHandler.return_value = mock_handler

            with patch("builtins.print"):
                result = await app._wait_for_startup_confirmation()

            assert result is False

    @pytest.mark.asyncio
    async def test_startup_returns_confirmation_result(self):
        """Test that startup() returns the confirmation result."""
        app = Application()
        app.config_manager.ollama_config = OllamaConfig()
        app.config_manager.mcp_config = Mock(servers={})

        with patch.object(app.config_manager, "load_configs"):
            with patch("atoll.mcp.server_manager.MCPServerManager") as mock_manager_class:
                mock_manager = Mock()
                mock_manager.connect_all = AsyncMock()
                mock_manager_class.return_value = mock_manager

                with patch("atoll.agent.agent.OllamaMCPAgent") as mock_agent_class:
                    mock_agent_instance = Mock()
                    mock_agent_instance.check_server_connection = AsyncMock(return_value=True)
                    mock_agent_instance.check_model_available = AsyncMock(return_value=True)
                    mock_agent_class.return_value = mock_agent_instance

                    # Mock the confirmation to return True
                    with patch.object(
                        app,
                        "_wait_for_startup_confirmation",
                        new_callable=AsyncMock,
                        return_value=True,
                    ):
                        with patch("builtins.print"):
                            result = await app.startup()
                            assert result is True

                    # Mock the confirmation to return False
                    with patch.object(
                        app,
                        "_wait_for_startup_confirmation",
                        new_callable=AsyncMock,
                        return_value=False,
                    ):
                        with patch("builtins.print"):
                            result = await app.startup()
                            assert result is False

    @pytest.mark.asyncio
    async def test_run_exits_when_startup_returns_false(self):
        """Test that run() exits early if startup confirmation is False."""
        app = Application()

        with patch.object(app, "startup", new_callable=AsyncMock, return_value=False):
            with patch.object(app, "shutdown", new_callable=AsyncMock) as mock_shutdown:
                with patch.object(app.ui, "display_header") as mock_display_header:
                    with patch("builtins.print"):
                        await app.run()

                    # display_header should NOT be called
                    mock_display_header.assert_not_called()
                    # shutdown should still be called
                    mock_shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_continues_when_startup_returns_true(self):
        """Test that run() continues normally if startup confirmation is True."""
        app = Application()

        with patch.object(app, "startup", new_callable=AsyncMock, return_value=True):
            with patch.object(app, "shutdown", new_callable=AsyncMock):
                with patch.object(app.ui, "display_header") as mock_display_header:
                    # Make get_input stop the loop immediately
                    def side_effect_get_input(*args, **kwargs):
                        app.ui.running = False
                        return "quit"

                    with patch.object(app.ui, "get_input", side_effect=side_effect_get_input):
                        with patch.object(app, "handle_command", new_callable=AsyncMock):
                            app.ui.running = True

                            await app.run()

                            # display_header SHOULD be called
                            mock_display_header.assert_called_once()
