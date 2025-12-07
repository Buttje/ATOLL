"""Unit tests for terminal UI."""

from unittest.mock import patch

from atoll.ui.colors import ColorScheme
from atoll.ui.terminal import TerminalUI, UIMode


class TestTerminalUI:
    """Test the TerminalUI class."""

    @patch("platform.system", return_value="Linux")
    @patch("os.system")
    def test_toggle_mode(self, mock_system, mock_platform):
        """Test toggling UI mode."""
        ui = TerminalUI()

        # Start in PROMPT mode
        assert ui.mode == UIMode.PROMPT

        ui.toggle_mode()
        assert ui.mode == UIMode.COMMAND

        ui.toggle_mode()
        assert ui.mode == UIMode.PROMPT


class TestColorScheme:
    """Test the ColorScheme class."""

    def test_initialization(self):
        """Test color scheme initialization."""
        colors = ColorScheme()
        assert colors is not None

    def test_color_methods(self):
        """Test color formatting methods."""
        colors = ColorScheme()

        # Test each color method
        assert "test" in colors.header("test")
        assert "test" in colors.user_input("test")
        assert "test" in colors.reasoning("test")
        assert "test" in colors.final_response("test")
        assert "test" in colors.error("test")
        assert "test" in colors.info("test")
