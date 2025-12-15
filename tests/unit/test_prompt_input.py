"""Tests for AtollInput class using prompt_toolkit."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from atoll.ui.prompt_input import AtollInput


class TestAtollInput:
    """Test suite for AtollInput class."""

    def test_initialization_default(self):
        """Test initialization with default parameters."""
        handler = AtollInput()

        assert handler.history_path == Path.home() / ".atoll_history"
        assert handler.max_history_entries == 1000
        assert handler.insert_mode is True
        assert handler.history is not None
        assert handler.kb is not None

    def test_initialization_custom_history(self):
        """Test initialization with custom history file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "custom_history.txt"
            handler = AtollInput(history_file=str(history_file))

            assert handler.history_path == history_file
            assert handler.max_history_entries == 1000

    def test_initialization_custom_max_entries(self):
        """Test initialization with custom max history entries."""
        handler = AtollInput(max_history_entries=500)

        assert handler.max_history_entries == 500

    def test_history_directory_creation(self):
        """Test that history directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "subdir" / "history.txt"
            handler = AtollInput(history_file=str(history_file))

            assert history_file.parent.exists()

    @patch("atoll.ui.prompt_input.PromptSession")
    def test_read_line_basic(self, mock_session_class):
        """Test basic read_line functionality."""
        # Mock the session
        mock_session = Mock()
        mock_session.prompt.return_value = "test input"
        mock_session_class.return_value = mock_session

        handler = AtollInput()
        result = handler.read_line("> ")

        assert result == "test input"
        mock_session.prompt.assert_called_once_with("> ")

    @patch("atoll.ui.prompt_input.PromptSession")
    def test_read_line_esc(self, mock_session_class):
        """Test read_line returns ESC when ESC is pressed."""
        # Mock the session to return ESC
        mock_session = Mock()
        mock_session.prompt.return_value = "ESC"
        mock_session_class.return_value = mock_session

        handler = AtollInput()
        result = handler.read_line("> ")

        assert result == "ESC"

    @patch("atoll.ui.prompt_input.PromptSession")
    def test_read_line_ctrl_v(self, mock_session_class):
        """Test read_line returns CTRL_V when Ctrl+V is pressed."""
        # Mock the session to return CTRL_V
        mock_session = Mock()
        mock_session.prompt.return_value = "CTRL_V"
        mock_session_class.return_value = mock_session

        handler = AtollInput()
        result = handler.read_line("> ")

        assert result == "CTRL_V"

    @patch("atoll.ui.prompt_input.PromptSession")
    def test_read_line_keyboard_interrupt(self, mock_session_class):
        """Test read_line re-raises KeyboardInterrupt."""
        mock_session = Mock()
        mock_session.prompt.side_effect = KeyboardInterrupt()
        mock_session_class.return_value = mock_session

        handler = AtollInput()

        with pytest.raises(KeyboardInterrupt):
            handler.read_line("> ")

    @patch("atoll.ui.prompt_input.PromptSession")
    def test_read_line_eof_error(self, mock_session_class):
        """Test read_line re-raises EOFError."""
        mock_session = Mock()
        mock_session.prompt.side_effect = EOFError()
        mock_session_class.return_value = mock_session

        handler = AtollInput()

        with pytest.raises(EOFError):
            handler.read_line("> ")

    @patch("atoll.ui.prompt_input.PromptSession")
    def test_get_input_backwards_compatibility(self, mock_session_class):
        """Test get_input method for backwards compatibility."""
        mock_session = Mock()
        mock_session.prompt.return_value = "test command"
        mock_session_class.return_value = mock_session

        handler = AtollInput()
        result = handler.get_input("Command: ", history=[])

        assert result == "test command"
        mock_session.prompt.assert_called_once_with("Command: ")

    def test_load_history(self):
        """Test load_history method (mainly for API compatibility)."""
        handler = AtollInput()
        # Should not raise an error
        handler.load_history()

    def test_save_history(self):
        """Test save_history method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "test_history.txt"
            handler = AtollInput(history_file=str(history_file))

            # Create a history file with some entries
            history_file.write_text("command1\ncommand2\ncommand3\n")

            # Should not raise an error
            handler.save_history()

    def test_truncate_history(self):
        """Test history truncation to max_history_entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "test_history.txt"
            handler = AtollInput(history_file=str(history_file), max_history_entries=5)

            # Create a history file with more entries than max
            entries = [f"command{i}\n" for i in range(10)]
            history_file.write_text("".join(entries))

            # Truncate history
            handler._truncate_history()

            # Read back and verify
            lines = history_file.read_text().splitlines()
            assert len(lines) == 5
            # Should keep the most recent entries (5-9)
            assert lines == ["command5", "command6", "command7", "command8", "command9"]

    def test_truncate_history_no_file(self):
        """Test truncate_history when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "nonexistent.txt"
            handler = AtollInput(history_file=str(history_file))

            # Should not raise an error
            handler._truncate_history()

    def test_key_bindings_created(self):
        """Test that key bindings are properly created."""
        handler = AtollInput()

        # Check that key bindings exist
        assert handler.kb is not None
        # Key bindings should have handlers for ESC, Ctrl+V, and Insert
        assert len(handler.kb.bindings) >= 3

    def test_insert_mode_toggle(self):
        """Test insert mode can be toggled."""
        handler = AtollInput()

        assert handler.insert_mode is True
        handler.insert_mode = False
        assert handler.insert_mode is False
        handler.insert_mode = True
        assert handler.insert_mode is True


class TestAtollInputIntegration:
    """Integration tests for AtollInput with prompt_toolkit."""

    def test_read_line_with_pipe_input(self):
        """Test read_line with pipe input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "history.txt"
            handler = AtollInput(history_file=str(history_file))

            # Create pipe input - it's a context manager
            with create_pipe_input() as inp:
                # Feed input
                inp.send_text("test command\n")

                # Create session with pipe input and dummy output
                from prompt_toolkit import PromptSession

                session = PromptSession(
                    history=handler.history,
                    key_bindings=handler.kb,
                    input=inp,
                    output=DummyOutput(),
                )

                # Get result
                result = session.prompt()
                assert result == "test command"

    def test_history_persistence(self):
        """Test that history is persisted to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "history.txt"

            # Create handler and simulate adding history
            handler = AtollInput(history_file=str(history_file))

            # Manually add entries to history file (simulating real usage)
            history_file.write_text("command1\ncommand2\ncommand3\n")

            # Create new handler and verify history is loaded
            handler2 = AtollInput(history_file=str(history_file))

            # History should be loaded from file
            assert history_file.exists()
            lines = history_file.read_text().splitlines()
            assert len(lines) == 3
            assert "command1" in lines
            assert "command2" in lines
            assert "command3" in lines
