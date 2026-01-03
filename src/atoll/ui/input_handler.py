"""Input handling for terminal UI."""

import platform
import sys

if platform.system() == "Windows":
    import msvcrt
else:
    import select
    import termios
    import tty


class InputHandler:
    """Handles keyboard input across different platforms."""

    def __init__(self):
        """Initialize input handler."""
        self.is_windows = platform.system() == "Windows"
        self.insert_mode = True  # True for insert mode, False for overtype mode

    def get_input(self, prompt: str = "", history: list[str] = None) -> str:
        """Get input from user with ESC detection, cursor movement, and history navigation.

        Args:
            prompt: Prompt text to display
            history: Command history for up/down arrow navigation

        Returns:
            User input string or special commands (ESC, CTRL_B)
        """
        if history is None:
            history = []

        if prompt:
            print(prompt, end="", flush=True)

        result = []
        cursor_pos = 0  # Position in result buffer
        history_index = len(history)  # Start at end of history (most recent)

        try:
            while True:
                char = self._get_char_windows() if self.is_windows else self._get_char_unix()

                # Handle escape sequences (from Windows conversion or Unix terminals)
                if char.startswith("\x1b["):
                    # Parse the escape sequence
                    if char == "\x1b[A":  # Up arrow
                        if history and history_index > 0:
                            self._clear_line(result, cursor_pos)
                            history_index -= 1
                            result = list(history[history_index])
                            cursor_pos = len(result)
                            print("".join(result), end="", flush=True)
                    elif char == "\x1b[B":  # Down arrow
                        if history_index < len(history):
                            self._clear_line(result, cursor_pos)
                            history_index += 1
                            if history_index < len(history):
                                result = list(history[history_index])
                            else:
                                result = []
                            cursor_pos = len(result)
                            print("".join(result), end="", flush=True)
                    elif char == "\x1b[C":  # Right arrow
                        if cursor_pos < len(result):
                            cursor_pos += 1
                            print("\x1b[C", end="", flush=True)
                    elif char == "\x1b[D":  # Left arrow
                        if cursor_pos > 0:
                            cursor_pos -= 1
                            print("\x1b[D", end="", flush=True)
                    elif char == "\x1b[H":  # Home key (Pos1)
                        if cursor_pos > 0:
                            # Move cursor to start of buffer
                            print(f"\x1b[{cursor_pos}D", end="", flush=True)
                            cursor_pos = 0
                    elif char == "\x1b[F":  # End key
                        if cursor_pos < len(result):
                            moves = len(result) - cursor_pos
                            print(f"\x1b[{moves}C", end="", flush=True)
                            cursor_pos = len(result)
                    elif char == "\x1b[2~":  # Insert key (Einfg)
                        # Toggle insert/overtype mode
                        self.insert_mode = not self.insert_mode
                    elif char == "\x1b[3~" and cursor_pos < len(result):  # Delete key (Entf)
                        result.pop(cursor_pos)
                        self._redraw_from_cursor(result, cursor_pos)
                    # Ignore other escape sequences (Page Up/Down, etc.)
                    continue
                elif char == "\x1b":  # Plain ESC key
                    return "ESC"
                elif char == "\x02":  # Ctrl+B
                    return "CTRL_B"
                elif char in ("\r", "\n"):  # Enter key
                    print()  # New line after input
                    return "".join(result)
                elif char == "\x08" or char == "\x7f":  # Backspace
                    if cursor_pos > 0:
                        # Remove character before cursor
                        result.pop(cursor_pos - 1)
                        cursor_pos -= 1
                        # Move cursor back and redraw
                        print("\x1b[D", end="", flush=True)
                        self._redraw_from_cursor(result, cursor_pos)
                elif char == "\x03":  # Ctrl+C
                    raise KeyboardInterrupt
                else:
                    # Handle character input based on mode
                    if self.insert_mode:
                        # Insert mode: insert character at cursor position
                        result.insert(cursor_pos, char)
                        cursor_pos += 1
                        # Redraw from cursor if not at end
                        if cursor_pos < len(result):
                            # Need to redraw from before insertion point
                            print(char, end="", flush=True)
                            self._redraw_from_cursor(result, cursor_pos)
                        else:
                            print(char, end="", flush=True)
                    else:
                        # Overtype mode: replace character at cursor position
                        if cursor_pos < len(result):
                            result[cursor_pos] = char
                            cursor_pos += 1
                            print(char, end="", flush=True)
                        else:
                            # At end of buffer, append
                            result.append(char)
                            cursor_pos += 1
                            print(char, end="", flush=True)
        except KeyboardInterrupt:
            # Re-raise to be handled by the main loop
            raise

    def _clear_line(self, result: list[str], cursor_pos: int) -> None:
        """Clear the current input line."""
        # Move cursor to beginning
        if cursor_pos > 0:
            print("\r", end="", flush=True)
        # Clear entire line
        print(" " * len(result), end="", flush=True)
        # Move back to beginning
        print("\r", end="", flush=True)

    def _redraw_from_cursor(self, result: list[str], cursor_pos: int) -> None:
        """Redraw line from cursor position."""
        remaining = "".join(result[cursor_pos:])
        # Print remaining characters plus a space to clear any deleted character
        print(remaining + " ", end="", flush=True)
        # Move cursor back to correct position using ANSI escape codes
        moves_back = len(remaining) + 1
        if moves_back > 0:
            # Use ANSI escape sequence for moving left instead of backspace
            print(f"\x1b[{moves_back}D", end="", flush=True)

    def _get_char_windows(self) -> str:
        """Get single character on Windows."""
        while True:
            if msvcrt.kbhit():
                char = msvcrt.getch()
                # Handle special keys (arrows, function keys, etc.)
                if char in (b"\x00", b"\xe0"):
                    second = msvcrt.getch()
                    # Arrow keys: Up=72, Down=80, Left=75, Right=77
                    key_map = {
                        b"H": "\x1b[A",  # Up arrow
                        b"P": "\x1b[B",  # Down arrow
                        b"M": "\x1b[C",  # Right arrow
                        b"K": "\x1b[D",  # Left arrow
                        b"S": "\x1b[3~",  # Delete key
                        b"R": "\x1b[2~",  # Insert key
                        b"G": "\x1b[H",  # Home key
                        b"O": "\x1b[F",  # End key
                        b"I": "\x1b[5~",  # Page Up
                        b"Q": "\x1b[6~",  # Page Down
                    }
                    if second in key_map:
                        return key_map[second]
                    # Ignore other special keys (F1-F12, etc.)
                    continue
                return char.decode("utf-8", errors="ignore")

    def _get_char_unix(self) -> str:
        """Get single character on Unix-like systems, building complete escape sequences."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            char = sys.stdin.read(1)

            # If it's an escape sequence, read the rest
            if char == "\x1b":
                # Check if there's more input (non-blocking)
                if select.select([sys.stdin], [], [], 0.01)[0]:
                    next_char = sys.stdin.read(1)
                    if next_char == "[":
                        # Read the sequence character
                        seq_char = sys.stdin.read(1)
                        # For sequences ending with ~, read the ~
                        if seq_char in "2356":
                            tilde = sys.stdin.read(1)
                            if tilde == "~":
                                return f"\x1b[{seq_char}~"
                        return f"\x1b[{seq_char}"
                    # Not a complete sequence, return just ESC
                return char
            return char
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def check_for_escape(self) -> bool:
        """Check if ESC key was pressed (non-blocking)."""
        if self.is_windows:
            if msvcrt.kbhit():
                char = msvcrt.getch()
                if char == b"\x1b":
                    return True
                # Put the character back
                msvcrt.ungetch(char)
        else:
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                char = sys.stdin.read(1)
                if char == "\x1b":
                    return True
        return False
