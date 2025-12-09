"""Test Delete key functionality."""

import platform
from unittest.mock import patch

import pytest

from atoll.ui.input_handler import InputHandler

# Skip on non-Windows since we're testing Windows-specific behavior
pytestmark = pytest.mark.skipif(
    platform.system() != "Windows", reason="Testing Windows Delete key behavior"
)


class TestDeleteKey:
    """Test Delete key handling."""

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    @patch("builtins.print")
    def test_delete_key_removes_char_at_cursor(
        self, mock_print, mock_getch, mock_kbhit, mock_platform
    ):
        """Test that Delete key removes character at cursor position."""
        # Type "test", move left twice, press Delete (should remove 's'), then Enter
        mock_getch.side_effect = [
            b"t",
            b"e",
            b"s",
            b"t",  # Type "test"
            b"\xe0",
            b"K",  # Left arrow
            b"\xe0",
            b"K",  # Left arrow (cursor now between 'e' and 's')
            b"\xe0",
            b"S",  # Delete key (should delete 's')
            b"\r",  # Enter
        ]

        handler = InputHandler()
        result = handler.get_input()

        # Should get "tet" (deleted the 's')
        assert result == "tet"

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    @patch("builtins.print")
    def test_delete_key_at_end_does_nothing(
        self, mock_print, mock_getch, mock_kbhit, mock_platform
    ):
        """Test that Delete key at end of line does nothing."""
        # Type "test", press Delete at end, then Enter
        mock_getch.side_effect = [
            b"t",
            b"e",
            b"s",
            b"t",  # Type "test"
            b"\xe0",
            b"S",  # Delete key (cursor at end, should do nothing)
            b"\r",  # Enter
        ]

        handler = InputHandler()
        result = handler.get_input()

        # Should still get "test"
        assert result == "test"

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    @patch("builtins.print")
    def test_delete_key_at_beginning(self, mock_print, mock_getch, mock_kbhit, mock_platform):
        """Test Delete key at beginning of line."""
        # Type "test", move to beginning, press Delete
        mock_getch.side_effect = [
            b"t",
            b"e",
            b"s",
            b"t",  # Type "test"
            b"\xe0",
            b"G",  # Home key (move to beginning)
            b"\xe0",
            b"S",  # Delete key (should delete 't')
            b"\r",  # Enter
        ]

        handler = InputHandler()
        result = handler.get_input()

        # Should get "est"
        assert result == "est"

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    @patch("builtins.print")
    def test_delete_key_with_prompt(self, mock_print, mock_getch, mock_kbhit, mock_platform):
        """Test Delete key with a prompt containing emoji."""
        # Type "test", move left twice, press Delete
        mock_getch.side_effect = [
            b"t",
            b"e",
            b"s",
            b"t",  # Type "test"
            b"\xe0",
            b"K",  # Left arrow
            b"\xe0",
            b"K",  # Left arrow (cursor between 'e' and 's')
            b"\xe0",
            b"S",  # Delete key (should delete 's')
            b"\r",  # Enter
        ]

        handler = InputHandler()
        # Use a prompt with emoji like the actual application
        result = handler.get_input(prompt="⚙️  Enter command: ")

        # Should get "tet"
        assert result == "tet"
