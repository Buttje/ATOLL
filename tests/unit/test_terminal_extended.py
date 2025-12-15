"""Extended tests for terminal UI."""

from unittest.mock import Mock, patch

from atoll.ui.terminal import TerminalUI, UIMode


class TestTerminalUIExtended:
    """Extended tests for TerminalUI."""

    def test_clear_screen(self):
        """Test clearing screen."""
        # Patch print before creating TerminalUI so it captures the __init__ clear
        with patch("builtins.print") as mock_print:
            TerminalUI()
            # Clear screen is called in __init__ using ANSI escape codes
            # The first call should be the ANSI clear sequence
            first_call_args = mock_print.call_args_list[0][0]
            assert len(first_call_args) > 0
            assert "\033[2J\033[H" in first_call_args[0]

    def test_display_header(self):
        """Test displaying header."""
        ui = TerminalUI()

        with patch("builtins.print") as mock_print:
            ui.display_header()
            assert mock_print.call_count > 0

    def test_display_user_input(self):
        """Test displaying user input."""
        ui = TerminalUI()

        with patch("builtins.print") as mock_print:
            ui.display_user_input("test input")
            mock_print.assert_called_once()

    def test_display_reasoning_short(self):
        """Test displaying short reasoning."""
        ui = TerminalUI()

        with patch("builtins.print") as mock_print:
            ui.display_reasoning("Short reasoning")
            mock_print.assert_called_once()

    def test_display_reasoning_long(self):
        """Test displaying long reasoning (summarized)."""
        ui = TerminalUI()

        long_text = "\n".join([f"Line {i}" for i in range(10)])

        with patch("builtins.print") as mock_print:
            ui.display_reasoning(long_text)
            mock_print.assert_called_once()
            # Check that it was summarized
            call_args = str(mock_print.call_args)
            assert "..." in call_args

    def test_display_response(self):
        """Test displaying response."""
        ui = TerminalUI()

        with patch("builtins.print") as mock_print:
            ui.display_response("test response")
            mock_print.assert_called_once()

    def test_display_error(self):
        """Test displaying error."""
        ui = TerminalUI()

        with patch("builtins.print") as mock_print:
            ui.display_error("test error")
            mock_print.assert_called_once()

    def test_display_info(self):
        """Test displaying info."""
        ui = TerminalUI()

        with patch("builtins.print") as mock_print:
            ui.display_info("test info")
            mock_print.assert_called_once()

    def test_display_models(self):
        """Test displaying models."""
        ui = TerminalUI()

        models = ["model1", "model2", "model3"]
        current = "model2"

        with patch("builtins.print") as mock_print:
            ui.display_models(models, current)
            assert mock_print.call_count >= len(models) + 1

    def test_get_input_prompt_mode(self):
        """Test getting input in prompt mode."""
        ui = TerminalUI()
        ui.mode = UIMode.PROMPT

        with patch.object(ui.input_handler, "get_input", return_value="test"):
            result = ui.get_input()
            assert result == "test"

    def test_get_input_command_mode(self):
        """Test getting input in command mode."""
        ui = TerminalUI()
        ui.mode = UIMode.COMMAND

        with patch.object(ui.input_handler, "get_input", return_value="test"):
            result = ui.get_input()
            assert result == "test"

    def test_handle_escape_key_with_callback(self):
        """Test handling escape key with callback."""
        ui = TerminalUI()

        callback = Mock()
        ui.handle_escape_key(callback)

        callback.assert_called_once()

    def test_handle_escape_key_without_callback(self):
        """Test handling escape key without callback."""
        ui = TerminalUI()
        original_mode = ui.mode

        ui.handle_escape_key()

        # Mode should have toggled
        assert ui.mode != original_mode
