"""Tests for help and additional commands."""

from unittest.mock import Mock, patch

import pytest

from atoll.main import Application


class TestHelpCommand:
    """Tests for help command."""

    @pytest.mark.asyncio
    async def test_help_command(self):
        """Test help command displays help text."""
        app = Application()

        with patch.object(app, "display_help") as mock_help:
            await app.handle_command("help")
            mock_help.assert_called_once()

    def test_display_help(self):
        """Test display_help shows all commands."""
        app = Application()

        with patch("builtins.print") as mock_print:
            app.display_help()
            mock_print.assert_called()
            # Check that help text was printed
            calls = [str(call_obj) for call_obj in mock_print.call_args_list]
            all_output = " ".join(calls).lower()
            assert "help" in all_output
            assert "models" in all_output
            assert "changemodel" in all_output
            assert "quit" in all_output

    @pytest.mark.asyncio
    async def test_help_specific_command(self):
        """Test help <command> displays command-specific help."""
        app = Application()

        with patch.object(app, "display_command_help") as mock_cmd_help:
            await app.handle_command("help models")
            mock_cmd_help.assert_called_once_with("models")

    def test_display_command_help_models(self):
        """Test display_command_help for models command."""
        app = Application()

        with patch("builtins.print") as mock_print:
            app.display_command_help("models")
            mock_print.assert_called()
            calls = [str(call_obj) for call_obj in mock_print.call_args_list]
            all_output = " ".join(calls).lower()
            assert "models" in all_output
            assert "usage" in all_output

    def test_display_command_help_changemodel(self):
        """Test display_command_help for changemodel command."""
        app = Application()

        with patch("builtins.print") as mock_print:
            app.display_command_help("changemodel")
            mock_print.assert_called()
            calls = [str(call_obj) for call_obj in mock_print.call_args_list]
            all_output = " ".join(calls).lower()
            assert "changemodel" in all_output
            assert "model-name" in all_output

    def test_display_command_help_install(self):
        """Test display_command_help for install command."""
        app = Application()

        with patch("builtins.print") as mock_print:
            app.display_command_help("install")
            mock_print.assert_called()
            calls = [str(call_obj) for call_obj in mock_print.call_args_list]
            all_output = " ".join(calls).lower()
            assert "install" in all_output
            assert "source" in all_output

    def test_display_command_help_unknown(self):
        """Test display_command_help for unknown command."""
        app = Application()
        app.ui = Mock()

        app.display_command_help("unknowncommand")
        app.ui.display_error.assert_called_once()
        error_msg = app.ui.display_error.call_args[0][0]
        assert "unknowncommand" in error_msg


class TestAdditionalCommands:
    """Tests for additional commands."""

    @pytest.mark.asyncio
    async def test_clear_command(self):
        """Test clear command."""
        app = Application()
        app.agent = Mock()
        app.agent.clear_memory = Mock()

        await app.handle_command("clear")
        app.agent.clear_memory.assert_called_once()

    @pytest.mark.asyncio
    async def test_clearmemory_command(self):
        """Test clearmemory command (alias)."""
        app = Application()
        app.agent = Mock()
        app.agent.clear_memory = Mock()

        await app.handle_command("clearmemory")
        app.agent.clear_memory.assert_called_once()

    @pytest.mark.asyncio
    async def test_servers_command(self):
        """Test servers command."""
        app = Application()
        app.mcp_manager = Mock()

        with patch.object(app, "display_servers") as mock_display:
            await app.handle_command("servers")
            mock_display.assert_called_once()

    @pytest.mark.asyncio
    async def test_tools_command(self):
        """Test tools command."""
        app = Application()
        app.mcp_manager = Mock()

        with patch.object(app, "display_tools") as mock_display:
            await app.handle_command("tools")
            mock_display.assert_called_once()

    @pytest.mark.asyncio
    async def test_exit_command(self):
        """Test exit command (alias for quit)."""
        app = Application()

        await app.handle_command("exit")
        assert app.ui.running is False

    @pytest.mark.asyncio
    async def test_unknown_command_shows_help_hint(self):
        """Test unknown command suggests help."""
        app = Application()

        with patch.object(app.ui, "display_error") as mock_error:
            await app.handle_command("unknown")
            mock_error.assert_called()
            call_args = str(mock_error.call_args[0][0])
            assert "help" in call_args.lower()


class TestDisplayMethods:
    """Tests for display methods."""

    def test_display_servers_with_servers(self):
        """Test displaying servers when servers exist."""
        app = Application()
        app.mcp_manager = Mock()
        app.mcp_manager.list_servers.return_value = ["server1", "server2"]

        mock_client1 = Mock()
        mock_client1.connected = True
        mock_client2 = Mock()
        mock_client2.connected = False

        app.mcp_manager.get_client.side_effect = [mock_client1, mock_client2]

        with patch("builtins.print") as mock_print:
            app.display_servers()
            assert mock_print.call_count >= 3  # Header + 2 servers

    def test_display_servers_no_servers(self):
        """Test displaying servers when no servers configured."""
        app = Application()
        app.mcp_manager = Mock()
        app.mcp_manager.list_servers.return_value = []

        with patch("builtins.print") as mock_print:
            app.display_servers()
            # Check all print calls for the expected message
            calls = [str(call_obj) for call_obj in mock_print.call_args_list]
            all_output = " ".join(calls).lower()
            assert "no mcp servers" in all_output or "no servers" in all_output

    def test_display_tools_with_tools(self):
        """Test displaying tools when tools exist."""
        app = Application()
        app.mcp_manager = Mock()
        app.mcp_manager.tool_registry.list_tools.return_value = ["tool1", "tool2"]
        app.mcp_manager.tool_registry.get_tool.side_effect = [
            {"server": "server1", "description": "Tool 1"},
            {"server": "server2", "description": "Tool 2"},
        ]

        with patch("builtins.print") as mock_print:
            app.display_tools()
            assert mock_print.call_count >= 7  # Header + 2 tools with details

    def test_display_tools_no_tools(self):
        """Test displaying tools when no tools available."""
        app = Application()
        app.mcp_manager = Mock()
        app.mcp_manager.tool_registry.list_tools.return_value = []

        with patch("builtins.print") as mock_print:
            app.display_tools()
            # Check all print calls for the expected message
            calls = [str(call_obj) for call_obj in mock_print.call_args_list]
            all_output = " ".join(calls).lower()
            assert "no tools" in all_output
