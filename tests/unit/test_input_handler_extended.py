"""Extended tests for input handler module."""

from unittest.mock import patch

import pytest

from atoll.ui.input_handler import InputHandler


class TestInputHandlerExtended:
    """Extended tests for InputHandler."""

    def test_platform_detection(self):
        """Test platform detection."""
        handler = InputHandler()
        assert isinstance(handler.is_windows, bool)

    @patch("platform.system", return_value="Windows")
    def test_windows_platform_detection(self, mock_platform):
        """Test Windows platform is detected."""
        handler = InputHandler()
        assert handler.is_windows is True

    @patch("platform.system", return_value="Linux")
    def test_unix_platform_detection(self, mock_platform):
        """Test Unix platform is detected."""
        handler = InputHandler()
        assert handler.is_windows is False

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    def test_get_input_enter_key(self, mock_getch, mock_kbhit, mock_platform):
        """Test handling Enter key."""
        mock_getch.side_effect = [b"t", b"e", b"s", b"t", b"\r"]

        handler = InputHandler()
        result = handler.get_input()

        assert result == "test"

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    def test_get_input_escape_key(self, mock_getch, mock_kbhit, mock_platform):
        """Test handling ESC key."""
        mock_getch.return_value = b"\x1b"

        handler = InputHandler()
        result = handler.get_input()

        assert result == "ESC"

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    def test_get_input_backspace(self, mock_getch, mock_kbhit, mock_platform):
        """Test handling backspace (0x08)."""
        # Type "test", backspace once, type "t" again
        mock_getch.side_effect = [b"t", b"e", b"s", b"t", b"\x08", b"t", b"\r"]

        handler = InputHandler()
        result = handler.get_input()

        # After typing "test", backspace removes 't', then add 't' again = "test"
        assert result == "test"

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    def test_get_input_ctrl_c(self, mock_getch, mock_kbhit, mock_platform):
        """Test handling Ctrl+C."""
        mock_getch.return_value = b"\x03"

        handler = InputHandler()

        with pytest.raises(KeyboardInterrupt):
            handler.get_input()

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    def test_get_input_with_prompt(self, mock_getch, mock_kbhit, mock_platform):
        """Test get_input with prompt."""
        mock_getch.side_effect = [b"t", b"\r"]

        handler = InputHandler()
        with patch("builtins.print") as mock_print:
            handler.get_input("Enter: ")
            mock_print.assert_called()

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    def test_get_char_windows_special_key_handling(self, mock_getch, mock_kbhit, mock_platform):
        """Test Windows special key handling."""
        # Simulate arrow key (special key sequence)
        mock_getch.side_effect = [b"\xe0", b"H", b"t", b"\r"]

        handler = InputHandler()
        result = handler.get_input()

        assert result == "t"

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    def test_backspace_on_empty_input(self, mock_getch, mock_kbhit, mock_platform):
        """Test backspace on empty input."""
        mock_getch.side_effect = [b"\x08", b"t", b"\r"]

        handler = InputHandler()
        result = handler.get_input()

        assert result == "t"

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=False)
    def test_check_for_escape_no_key_pressed(self, mock_kbhit, mock_platform):
        """Test check_for_escape when no key is pressed."""
        handler = InputHandler()
        result = handler.check_for_escape()

        assert result is False

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch", return_value=b"\x1b")
    def test_check_for_escape_esc_pressed(self, mock_getch, mock_kbhit, mock_platform):
        """Test check_for_escape when ESC is pressed."""
        handler = InputHandler()
        result = handler.check_for_escape()

        assert result is True

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch", return_value=b"t")
    @patch("msvcrt.ungetch")
    def test_check_for_escape_other_key_pressed(
        self, mock_ungetch, mock_getch, mock_kbhit, mock_platform
    ):
        """Test check_for_escape when other key is pressed."""
        handler = InputHandler()
        result = handler.check_for_escape()

        assert result is False
        mock_ungetch.assert_called_once_with(b"t")
        mock_ungetch.assert_called_once_with(b"t")
