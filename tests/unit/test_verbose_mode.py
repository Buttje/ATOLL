"""Tests for verbose mode functionality."""

from unittest.mock import patch

from atoll.ui.input_handler import InputHandler
from atoll.ui.terminal import TerminalUI


class TestVerboseMode:
    """Tests for verbose mode functionality."""

    def test_verbose_mode_initial_state(self):
        """Test that verbose mode is initially off."""
        ui = TerminalUI()
        assert ui.verbose is False

    def test_toggle_verbose_on(self):
        """Test toggling verbose mode on."""
        ui = TerminalUI()

        with patch.object(ui, "display_header"):
            ui.toggle_verbose()

        assert ui.verbose is True

    def test_toggle_verbose_off(self):
        """Test toggling verbose mode off after it was on."""
        ui = TerminalUI()
        ui.verbose = True

        with patch.object(ui, "display_header"):
            ui.toggle_verbose()

        assert ui.verbose is False

    def test_toggle_verbose_multiple_times(self):
        """Test toggling verbose mode multiple times."""
        ui = TerminalUI()

        with patch.object(ui, "display_header"):
            # Toggle on
            ui.toggle_verbose()
            assert ui.verbose is True

            # Toggle off
            ui.toggle_verbose()
            assert ui.verbose is False

            # Toggle on again
            ui.toggle_verbose()
            assert ui.verbose is True

    def test_display_verbose_when_enabled(self):
        """Test that verbose output is displayed when verbose mode is on."""
        ui = TerminalUI()
        ui.verbose = True

        with patch("builtins.print") as mock_print:
            ui.display_verbose("Test verbose message", prefix="TEST")
            mock_print.assert_called_once()
            # Check that the message contains our text
            call_args = str(mock_print.call_args)
            assert "Test verbose message" in call_args

    def test_display_verbose_when_disabled(self):
        """Test that verbose output is NOT displayed when verbose mode is off."""
        ui = TerminalUI()
        ui.verbose = False

        with patch("builtins.print") as mock_print:
            ui.display_verbose("Test verbose message", prefix="TEST")
            mock_print.assert_not_called()

    def test_display_verbose_without_prefix(self):
        """Test displaying verbose message without prefix."""
        ui = TerminalUI()
        ui.verbose = True

        with patch("builtins.print") as mock_print:
            ui.display_verbose("Test message without prefix")
            mock_print.assert_called_once()
            call_args = str(mock_print.call_args)
            assert "Test message without prefix" in call_args

    def test_header_shows_verbose_indicator_on(self):
        """Test that header displays verbose indicator when verbose is on."""
        ui = TerminalUI()
        ui.verbose = True

        with patch("builtins.print") as mock_print:
            ui.display_header()

            # Check that one of the print calls contains "Verbose: ON"
            printed_text = "".join(str(call) for call in mock_print.call_args_list)
            assert "Verbose: ON" in printed_text

    def test_header_no_verbose_indicator_off(self):
        """Test that header doesn't show verbose indicator when verbose is off."""
        ui = TerminalUI()
        ui.verbose = False

        with patch("builtins.print") as mock_print:
            ui.display_header()

            # Check that none of the print calls contain "Verbose: ON"
            printed_text = "".join(str(call) for call in mock_print.call_args_list)
            assert "Verbose: ON" not in printed_text


class TestInputHandlerCtrlB:
    """Tests for Ctrl+B detection in InputHandler."""

    @patch("platform.system", return_value="Linux")
    def test_ctrl_b_detection_unix(self, mock_platform):
        """Test Ctrl+B detection on Unix systems."""
        handler = InputHandler()

        # Mock the _get_char_unix method directly
        with patch.object(handler, "_get_char_unix", return_value="\x02"):
            result = handler.get_input()

        assert result == "CTRL_B"

    @patch("platform.system", return_value="Windows")
    def test_ctrl_b_detection_windows(self, mock_platform):
        """Test Ctrl+B detection on Windows (mocking at method level)."""
        handler = InputHandler()

        # Mock the _get_char_windows method directly
        with patch.object(handler, "_get_char_windows", return_value="\x02"):
            result = handler.get_input()

        assert result == "CTRL_B"

    @patch("platform.system", return_value="Linux")
    def test_regular_input_after_ctrl_b_added(self, mock_platform):
        """Test that regular input still works after adding Ctrl+B detection."""
        handler = InputHandler()

        # Mock the _get_char_unix method to simulate typing "test" and pressing enter
        with patch.object(handler, "_get_char_unix", side_effect=["t", "e", "s", "t", "\r"]):
            result = handler.get_input()

        assert result == "test"
