"""Unit tests for input handler."""

from unittest.mock import patch

from atoll.ui.input_handler import InputHandler


class TestInputHandler:
    """Test InputHandler class."""

    def test_initialization(self):
        """Test input handler initialization."""
        handler = InputHandler()
        assert handler.is_windows in [True, False]

    @patch("platform.system")
    def test_windows_detection(self, mock_system):
        """Test Windows platform detection."""
        mock_system.return_value = "Windows"
        handler = InputHandler()
        assert handler.is_windows is True

        mock_system.return_value = "Linux"
        handler = InputHandler()
        assert handler.is_windows is False

    @patch("platform.system")
    @patch("msvcrt.kbhit")
    @patch("msvcrt.getch")
    def test_get_char_windows(self, mock_getch, mock_kbhit, mock_system):
        """Test getting character on Windows."""
        mock_system.return_value = "Windows"
        handler = InputHandler()

        # Simulate key press
        mock_kbhit.return_value = True
        mock_getch.return_value = b"a"

        char = handler._get_char_windows()
        assert char == "a"

    @patch("platform.system")
    @patch("msvcrt.kbhit")
    @patch("msvcrt.getch")
    def test_get_char_windows_special_key(self, mock_getch, mock_kbhit, mock_system):
        """Test handling special keys on Windows."""
        mock_system.return_value = "Windows"
        handler = InputHandler()

        # Simulate special key (arrow up) - now returns escape sequence
        mock_kbhit.side_effect = [True]
        mock_getch.side_effect = [b"\xe0", b"H"]  # Arrow up

        char = handler._get_char_windows()
        assert char == "\x1b[A"  # Now returns ANSI escape sequence for up arrow

    @patch("platform.system")
    @patch("msvcrt.kbhit")
    @patch("msvcrt.getch")
    def test_get_char_windows_arrow_keys(self, mock_getch, mock_kbhit, mock_system):
        """Test all arrow keys on Windows."""
        mock_system.return_value = "Windows"
        handler = InputHandler()

        # Test up arrow
        mock_kbhit.return_value = True
        mock_getch.side_effect = [b"\xe0", b"H"]
        assert handler._get_char_windows() == "\x1b[A"

        # Test down arrow
        mock_getch.side_effect = [b"\xe0", b"P"]
        assert handler._get_char_windows() == "\x1b[B"

        # Test right arrow
        mock_getch.side_effect = [b"\xe0", b"M"]
        assert handler._get_char_windows() == "\x1b[C"

        # Test left arrow
        mock_getch.side_effect = [b"\xe0", b"K"]
        assert handler._get_char_windows() == "\x1b[D"

    @patch("platform.system")
    def test_check_for_escape_no_input(self, mock_system):
        """Test checking for escape with no input."""
        mock_system.return_value = "Windows"
        handler = InputHandler()

        with patch("msvcrt.kbhit", return_value=False):
            assert handler.check_for_escape() is False
