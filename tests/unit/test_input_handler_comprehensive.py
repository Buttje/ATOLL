"""Comprehensive tests for input handler."""

from unittest.mock import patch

from atoll.ui.input_handler import InputHandler


class TestInputHandlerComprehensive:
    """Comprehensive tests for input handler."""

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    def test_newline_handling(self, mock_getch, mock_kbhit, mock_platform):
        """Test handling newline character."""
        mock_getch.side_effect = [b"t", b"e", b"s", b"t", b"\n"]

        handler = InputHandler()
        result = handler.get_input()

        assert result == "test"

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    def test_delete_key_handling(self, mock_getch, mock_kbhit, mock_platform):
        """Test handling delete key (0x7f)."""
        mock_getch.side_effect = [b"t", b"e", b"s", b"t", b"\x7f", b"\r"]

        handler = InputHandler()
        result = handler.get_input()

        assert result == "tes"

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    def test_function_key_handling(self, mock_getch, mock_kbhit, mock_platform):
        """Test handling function keys."""
        # F1 key is \x00 followed by ;
        mock_getch.side_effect = [b"\x00", b";", b"t", b"\r"]

        handler = InputHandler()
        result = handler.get_input()

        assert result == "t"

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    def test_multiple_backspaces(self, mock_getch, mock_kbhit, mock_platform):
        """Test multiple backspaces."""
        mock_getch.side_effect = [b"t", b"e", b"s", b"t", b"\x08", b"\x08", b"\r"]

        handler = InputHandler()
        result = handler.get_input()

        assert result == "te"

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    def test_empty_input(self, mock_getch, mock_kbhit, mock_platform):
        """Test empty input (just Enter)."""
        mock_getch.return_value = b"\r"

        handler = InputHandler()
        result = handler.get_input()

        assert result == ""
