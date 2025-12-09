"""Tests for graceful shutdown handling."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from atoll.main import Application
from atoll.ui.terminal import UIMode


class TestGracefulShutdown:
    """Tests for graceful shutdown."""

    @pytest.mark.asyncio
    async def test_shutdown_disconnects_mcp_servers(self):
        """Test shutdown disconnects MCP servers."""
        app = Application()
        app.mcp_manager = Mock()
        app.mcp_manager.disconnect_all = AsyncMock()

        await app.shutdown()

        app.mcp_manager.disconnect_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_handles_errors_gracefully(self):
        """Test shutdown handles errors without raising."""
        app = Application()
        app.mcp_manager = Mock()
        app.mcp_manager.disconnect_all = AsyncMock(side_effect=Exception("Test error"))

        # Should not raise
        await app.shutdown()

    @pytest.mark.asyncio
    async def test_shutdown_with_no_mcp_manager(self):
        """Test shutdown when mcp_manager is None."""
        app = Application()
        app.mcp_manager = None

        # Should not raise
        await app.shutdown()

    @pytest.mark.asyncio
    async def test_run_calls_shutdown_on_exit(self):
        """Test run calls shutdown when exiting."""
        app = Application()

        with patch.object(app, "startup", new_callable=AsyncMock, return_value=True):
            with patch.object(app, "shutdown", new_callable=AsyncMock) as mock_shutdown:
                with patch.object(app.ui, "display_header"):
                    # Make get_input return 'quit' once, then stop the loop
                    def side_effect_get_input(*args, **kwargs):
                        app.ui.running = False
                        return "quit"

                    with patch.object(app.ui, "get_input", side_effect=side_effect_get_input):
                        with patch.object(app, "handle_command", new_callable=AsyncMock):
                            app.ui.mode = UIMode.COMMAND
                            app.ui.running = True

                            await app.run()

                            mock_shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_calls_shutdown_on_keyboard_interrupt(self):
        """Test run calls shutdown on KeyboardInterrupt."""
        app = Application()

        with patch.object(app, "startup", new_callable=AsyncMock, return_value=True):
            with patch.object(app, "shutdown", new_callable=AsyncMock) as mock_shutdown:
                with patch.object(app.ui, "display_header"):
                    with patch.object(app.ui, "get_input", side_effect=KeyboardInterrupt):
                        with patch("builtins.print"):
                            app.ui.running = True

                            await app.run()

                            mock_shutdown.assert_called_once()

    def test_main_handles_keyboard_interrupt(self):
        """Test main function handles KeyboardInterrupt gracefully."""
        import importlib

        main_module = importlib.import_module("atoll.main")

        with patch("atoll.config.manager.ConfigManager"):
            with patch("atoll.ui.terminal.TerminalUI"):
                with patch("asyncio.run", side_effect=KeyboardInterrupt):
                    with patch("builtins.print") as mock_print:
                        with patch("sys.exit") as mock_exit:
                            main_module.main()

                            # Should print goodbye message
                            assert any("Goodbye" in str(call) for call in mock_print.call_args_list)
                            # Should exit with code 0
                            mock_exit.assert_called_with(0)

    def test_main_handles_general_exception(self):
        """Test main function handles general exceptions."""
        import importlib

        main_module = importlib.import_module("atoll.main")

        with patch("atoll.config.manager.ConfigManager"):
            with patch("atoll.ui.terminal.TerminalUI"):
                with patch("asyncio.run", side_effect=Exception("Test error")):
                    with patch("builtins.print") as mock_print:
                        with patch("sys.exit") as mock_exit:
                            main_module.main()

                            # Should print error message
                            assert mock_print.called
                            # Should exit with code 1
                            mock_exit.assert_called_with(1)
