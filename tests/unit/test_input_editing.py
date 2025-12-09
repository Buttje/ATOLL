"""Comprehensive tests for terminal input editing requirements."""

import platform
from unittest.mock import patch

import pytest

from atoll.ui.input_handler import InputHandler


class TestBasicInput:
    """Test basic input functionality."""

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    @patch("builtins.print")
    def test_1_basic_insertion(self, mock_print, mock_getch, mock_kbhit, mock_platform):
        """Test 1 - Basic insertion: h, e, l, l, o, Enter → 'hello'"""
        mock_getch.side_effect = [b"h", b"e", b"l", b"l", b"o", b"\r"]

        handler = InputHandler()
        result = handler.get_input()

        assert result == "hello"

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    @patch("builtins.print")
    def test_2_cursor_movement_and_insertion(
        self, mock_print, mock_getch, mock_kbhit, mock_platform
    ):
        """Test 2 - Cursor movement: h,e,l,l,o,←,←,y,Enter → 'helylo'"""
        mock_getch.side_effect = [
            b"h",
            b"e",
            b"l",
            b"l",
            b"o",
            b"\xe0",
            b"K",  # Left
            b"\xe0",
            b"K",  # Left
            b"y",
            b"\r",
        ]

        handler = InputHandler()
        result = handler.get_input()

        assert result == "helylo"

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    @patch("builtins.print")
    def test_3_home_key(self, mock_print, mock_getch, mock_kbhit, mock_platform):
        """Test 3 - Home key: a,b,c,Home,X,Enter → 'Xabc'"""
        mock_getch.side_effect = [b"a", b"b", b"c", b"\xe0", b"G", b"X", b"\r"]

        handler = InputHandler()
        result = handler.get_input()

        assert result == "Xabc"

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    @patch("builtins.print")
    def test_4_end_key(self, mock_print, mock_getch, mock_kbhit, mock_platform):
        """Test 4 - End key: a,b,c,←,←,End,d,Enter → 'abcd'"""
        mock_getch.side_effect = [
            b"a",
            b"b",
            b"c",
            b"\xe0",
            b"K",  # Left
            b"\xe0",
            b"K",  # Left
            b"\xe0",
            b"O",  # End
            b"d",
            b"\r",
        ]

        handler = InputHandler()
        result = handler.get_input()

        assert result == "abcd"


class TestDeletion:
    """Test deletion operations."""

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    @patch("builtins.print")
    def test_5_backspace(self, mock_print, mock_getch, mock_kbhit, mock_platform):
        """Test 5 - Backspace: a,b,c,BS,Enter → 'ab'"""
        mock_getch.side_effect = [b"a", b"b", b"c", b"\x08", b"\r"]

        handler = InputHandler()
        result = handler.get_input()

        assert result == "ab"

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    @patch("builtins.print")
    def test_6_delete_key(self, mock_print, mock_getch, mock_kbhit, mock_platform):
        """Test 6 - Delete: a,b,c,←,←,Del,Enter → 'ac'"""
        mock_getch.side_effect = [
            b"a",
            b"b",
            b"c",
            b"\xe0",
            b"K",  # Left
            b"\xe0",
            b"K",  # Left
            b"\xe0",
            b"S",  # Delete
            b"\r",
        ]

        handler = InputHandler()
        result = handler.get_input()

        assert result == "ac"


class TestOvertypeMode:
    """Test insert/overtype mode toggling."""

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    @patch("builtins.print")
    def test_7_insert_toggle(self, mock_print, mock_getch, mock_kbhit, mock_platform):
        """Test 7 - Insert toggle: a,b,c,←,Ins,X,Ins,Y,Enter → 'abXY'
        
        Corrected from spec: After abc and left arrow, cursor is at pos 2.
        Overtyping X replaces 'c', cursor advances to pos 3.
        Toggle to insert, type Y at pos 3 gives 'abXY'.
        """
        mock_getch.side_effect = [
            b"a",
            b"b",
            b"c",
            b"\xe0",
            b"K",  # Left (cursor at position 2, before 'c')
            b"\xe0",
            b"R",  # Insert (toggle to overtype)
            b"X",  # Overwrite 'c' with 'X', cursor advances to 3
            b"\xe0",
            b"R",  # Insert (toggle back to insert)
            b"Y",  # Insert 'Y' at position 3
            b"\r",
        ]

        handler = InputHandler()
        result = handler.get_input()

        assert result == "abXY"

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    @patch("builtins.print")
    def test_8_overtype_at_end(self, mock_print, mock_getch, mock_kbhit, mock_platform):
        """Test 8 - Overtype at end: a,b,c,End,Ins,X,Enter → 'abcX'"""
        mock_getch.side_effect = [
            b"a",
            b"b",
            b"c",
            b"\xe0",
            b"O",  # End
            b"\xe0",
            b"R",  # Insert (toggle to overtype)
            b"X",
            b"\r",
        ]

        handler = InputHandler()
        result = handler.get_input()

        assert result == "abcX"


class TestBoundaryConditions:
    """Test boundary conditions."""

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    @patch("builtins.print")
    def test_9_backspace_at_start(self, mock_print, mock_getch, mock_kbhit, mock_platform):
        """Test 9 - Backspace at start: a,b,Home,BS,Enter → 'ab'"""
        mock_getch.side_effect = [b"a", b"b", b"\xe0", b"G", b"\x08", b"\r"]

        handler = InputHandler()
        result = handler.get_input()

        assert result == "ab"

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    @patch("builtins.print")
    def test_10_delete_at_end(self, mock_print, mock_getch, mock_kbhit, mock_platform):
        """Test 10 - Delete at end: a,b,c,Del,Enter → 'abc'"""
        mock_getch.side_effect = [b"a", b"b", b"c", b"\xe0", b"S", b"\r"]

        handler = InputHandler()
        result = handler.get_input()

        assert result == "abc"


class TestComplexOvertype:
    """Test complex overtype scenarios."""

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    @patch("builtins.print")
    def test_11_overtype_multiple(self, mock_print, mock_getch, mock_kbhit, mock_platform):
        """Test 11 - Overtype multiple: 1,2,3,4,Home,Ins,A,B,C,Enter → 'ABC4'"""
        mock_getch.side_effect = [
            b"1",
            b"2",
            b"3",
            b"4",
            b"\xe0",
            b"G",  # Home
            b"\xe0",
            b"R",  # Insert (toggle to overtype)
            b"A",
            b"B",
            b"C",
            b"\r",
        ]

        handler = InputHandler()
        result = handler.get_input()

        assert result == "ABC4"

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    @patch("builtins.print")
    def test_12_insert_after_overtype(self, mock_print, mock_getch, mock_kbhit, mock_platform):
        """Test 12 - Insert after overtype: h,e,l,l,o,Home,Ins,X,Ins,Y,Enter → 'XYello'
        
        Corrected from spec: After hello and Home, cursor is at pos 0.
        Overtyping X replaces 'h', cursor advances to pos 1.
        Toggle to insert, type Y at pos 1 gives 'XYello'.
        """
        mock_getch.side_effect = [
            b"h",
            b"e",
            b"l",
            b"l",
            b"o",
            b"\xe0",
            b"G",  # Home (position 0)
            b"\xe0",
            b"R",  # Insert (toggle to overtype)
            b"X",  # Replace 'h' with 'X', cursor advances to 1
            b"\xe0",
            b"R",  # Insert (toggle back to insert)
            b"Y",  # Insert 'Y' at position 1
            b"\r",
        ]

        handler = InputHandler()
        result = handler.get_input()

        assert result == "XYello"


class TestSpecialKeys:
    """Test special key behaviors."""

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    @patch("builtins.print")
    def test_13_esc_key(self, mock_print, mock_getch, mock_kbhit, mock_platform):
        """Test 13 - ESC key: a,ESC → 'ESC'"""
        mock_getch.side_effect = [b"a", b"\x1b"]

        handler = InputHandler()
        result = handler.get_input()

        assert result == "ESC"

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    @patch("builtins.print")
    def test_14_ctrl_v(self, mock_print, mock_getch, mock_kbhit, mock_platform):
        """Test 14 - Ctrl+V: a,Ctrl+V → 'CTRL_V'"""
        mock_getch.side_effect = [b"a", b"\x16"]

        handler = InputHandler()
        result = handler.get_input()

        assert result == "CTRL_V"

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    @patch("builtins.print")
    def test_15_ctrl_c(self, mock_print, mock_getch, mock_kbhit, mock_platform):
        """Test 15 - Ctrl+C raises KeyboardInterrupt"""
        mock_getch.side_effect = [b"\x03"]

        handler = InputHandler()

        with pytest.raises(KeyboardInterrupt):
            handler.get_input()


class TestHistory:
    """Test history navigation."""

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    @patch("builtins.print")
    def test_16_history_up(self, mock_print, mock_getch, mock_kbhit, mock_platform):
        """Test 16 - History up: Up,Enter → 'third'"""
        mock_getch.side_effect = [b"\xe0", b"H", b"\r"]  # Up arrow, Enter

        handler = InputHandler()
        history = ["first", "second", "third"]
        result = handler.get_input(history=history)

        assert result == "third"

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    @patch("builtins.print")
    def test_16_history_up_twice(self, mock_print, mock_getch, mock_kbhit, mock_platform):
        """Test 16 - History up twice: Up,Up,Enter → 'second'"""
        mock_getch.side_effect = [b"\xe0", b"H", b"\xe0", b"H", b"\r"]  # Up, Up, Enter

        handler = InputHandler()
        history = ["first", "second", "third"]
        result = handler.get_input(history=history)

        assert result == "second"

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    @patch("builtins.print")
    def test_16_history_down(self, mock_print, mock_getch, mock_kbhit, mock_platform):
        """Test 16 - History down: Up,Up,Down,Enter → 'third'"""
        mock_getch.side_effect = [
            b"\xe0",
            b"H",  # Up
            b"\xe0",
            b"H",  # Up
            b"\xe0",
            b"P",  # Down
            b"\r",
        ]

        handler = InputHandler()
        history = ["first", "second", "third"]
        result = handler.get_input(history=history)

        assert result == "third"

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    @patch("builtins.print")
    def test_16_history_down_to_blank(self, mock_print, mock_getch, mock_kbhit, mock_platform):
        """Test 16 - History down to blank: Up,Down,Down,Enter → ''"""
        mock_getch.side_effect = [
            b"\xe0",
            b"H",  # Up
            b"\xe0",
            b"P",  # Down
            b"\xe0",
            b"P",  # Down (past end)
            b"\r",
        ]

        handler = InputHandler()
        history = ["first", "second", "third"]
        result = handler.get_input(history=history)

        assert result == ""


class TestBoundaryMovement:
    """Test boundary cursor movement."""

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    @patch("builtins.print")
    def test_17_left_at_start(self, mock_print, mock_getch, mock_kbhit, mock_platform):
        """Test 17 - Left at start: a,←,←,BS,Enter → ''"""
        mock_getch.side_effect = [
            b"a",
            b"\xe0",
            b"K",  # Left
            b"\xe0",
            b"K",  # Left (should stop at position 0)
            b"\x08",  # Backspace at start (no effect)
            b"\r",
        ]

        handler = InputHandler()
        result = handler.get_input()

        # Cursor moves left once (from pos 1 to pos 0)
        # Second left has no effect (already at 0)
        # Backspace at pos 0 has no effect
        # Result should be "a"
        assert result == "a"

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    @patch("builtins.print")
    def test_17_right_at_end(self, mock_print, mock_getch, mock_kbhit, mock_platform):
        """Test 17 - Right at end: a,→,→,b,Enter → 'ab'"""
        mock_getch.side_effect = [
            b"a",
            b"\xe0",
            b"M",  # Right (no effect, at end)
            b"\xe0",
            b"M",  # Right (no effect, at end)
            b"b",
            b"\r",
        ]

        handler = InputHandler()
        result = handler.get_input()

        assert result == "ab"


class TestMultipleInsertToggles:
    """Test multiple insert/overtype toggles."""

    @patch("platform.system", return_value="Windows")
    @patch("msvcrt.kbhit", return_value=True)
    @patch("msvcrt.getch")
    @patch("builtins.print")
    def test_18_multiple_toggles(self, mock_print, mock_getch, mock_kbhit, mock_platform):
        """Test 18 - Multiple toggles: a,b,c,Ins,Ins,Ins,X,Enter → 'abcX'"""
        mock_getch.side_effect = [
            b"a",
            b"b",
            b"c",
            b"\xe0",
            b"R",  # Insert (insert→overtype)
            b"\xe0",
            b"R",  # Insert (overtype→insert)
            b"\xe0",
            b"R",  # Insert (insert→overtype)
            b"X",  # At end in overtype mode, append
            b"\r",
        ]

        handler = InputHandler()
        result = handler.get_input()

        assert result == "abcX"


class TestUnixPlatform:
    """Test Unix-specific input handling."""

    @patch("platform.system", return_value="Linux")
    @patch("builtins.print")
    def test_unix_basic_insertion(self, mock_print, mock_platform):
        """Test basic insertion on Unix platform."""

        def mock_get_char():
            chars = list("hello") + ["\r"]
            for char in chars:
                yield char

        char_gen = mock_get_char()

        with patch.object(InputHandler, "_get_char_unix", side_effect=lambda: next(char_gen)):
            handler = InputHandler()
            result = handler.get_input()

            assert result == "hello"

    @patch("platform.system", return_value="Linux")
    @patch("builtins.print")
    def test_unix_cursor_movement(self, mock_print, mock_platform):
        """Test cursor movement on Unix platform."""

        def mock_get_char():
            chars = ["h", "e", "l", "l", "o", "\x1b[D", "\x1b[D", "y", "\r"]
            for char in chars:
                yield char

        char_gen = mock_get_char()

        with patch.object(InputHandler, "_get_char_unix", side_effect=lambda: next(char_gen)):
            handler = InputHandler()
            result = handler.get_input()

            assert result == "helylo"

    @patch("platform.system", return_value="Linux")
    @patch("builtins.print")
    def test_unix_delete_key(self, mock_print, mock_platform):
        """Test delete key on Unix platform."""

        def mock_get_char():
            chars = ["a", "b", "c", "\x1b[D", "\x1b[D", "\x1b[3~", "\r"]
            for char in chars:
                yield char

        char_gen = mock_get_char()

        with patch.object(InputHandler, "_get_char_unix", side_effect=lambda: next(char_gen)):
            handler = InputHandler()
            result = handler.get_input()

            assert result == "ac"

    @patch("platform.system", return_value="Linux")
    @patch("builtins.print")
    def test_unix_insert_toggle(self, mock_print, mock_platform):
        """Test insert toggle on Unix platform."""

        def mock_get_char():
            chars = [
                "a",
                "b",
                "c",
                "\x1b[D",  # Left arrow
                "\x1b[2~",  # Insert toggle
                "X",  # Overtype 'c' with 'X'
                "\x1b[2~",  # Insert toggle back
                "Y",  # Insert 'Y'
                "\r",
            ]
            for char in chars:
                yield char

        char_gen = mock_get_char()

        with patch.object(InputHandler, "_get_char_unix", side_effect=lambda: next(char_gen)):
            handler = InputHandler()
            result = handler.get_input()

            # After overtyping at pos 2, cursor is at 3, inserting Y gives "abXY"
            assert result == "abXY"
