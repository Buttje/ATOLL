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

    def get_input(self, prompt: str = "", history: list[str] = None) -> str:
        """Get input from user with ESC detection, cursor movement, and history navigation.

        Args:
            prompt: Prompt text to display
            history: Command history for up/down arrow navigation

        Returns:
            User input string or special commands (ESC, CTRL_V)
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

                if char == "\x1b":  # ESC key or arrow key start
                    # Check for arrow keys (ESC [ X on Unix, special handling on Windows)
                    if not self.is_windows:
                        next_char = self._get_char_unix()
                        if next_char == "[":
                            arrow = self._get_char_unix()
                            if arrow == "A":  # Up arrow
                                if history and history_index > 0:
                                    # Clear current line
                                    self._clear_line(result, cursor_pos)
                                    # Move to previous history
                                    history_index -= 1
                                    result = list(history[history_index])
                                    cursor_pos = len(result)
                                    print("".join(result), end="", flush=True)
                            elif arrow == "B":  # Down arrow
                                if history_index < len(history):
                                    # Clear current line
                                    self._clear_line(result, cursor_pos)
                                    # Move to next history
                                    history_index += 1
                                    if history_index < len(history):
                                        result = list(history[history_index])
                                    else:
                                        result = []
                                    cursor_pos = len(result)
                                    print("".join(result), end="", flush=True)
                            elif arrow == "C":  # Right arrow
                                if cursor_pos < len(result):
                                    cursor_pos += 1
                                    print("\x1b[C", end="", flush=True)  # Move cursor right
                            elif arrow == "D":  # Left arrow
                                if cursor_pos > 0:
                                    cursor_pos -= 1
                                    print("\x1b[D", end="", flush=True)  # Move cursor left
                            continue
                    return "ESC"
                elif char == "\x16":  # Ctrl+V
                    return "CTRL_V"
                elif char in ("\r", "\n"):  # Enter key
                    print()  # New line after input
                    return "".join(result)
                elif char == "\x08" or char == "\x7f":  # Backspace
                    if cursor_pos > 0:
                        # Remove character before cursor
                        result.pop(cursor_pos - 1)
                        cursor_pos -= 1
                        # Redraw line from cursor position
                        self._redraw_from_cursor(result, cursor_pos)
                elif char == "\x03":  # Ctrl+C
                    raise KeyboardInterrupt
                elif char == "\x7f":  # Delete key (some terminals)
                    if cursor_pos < len(result):
                        result.pop(cursor_pos)
                        self._redraw_from_cursor(result, cursor_pos)
                else:
                    # Insert character at cursor position
                    result.insert(cursor_pos, char)
                    cursor_pos += 1
                    # Redraw from cursor if not at end
                    if cursor_pos < len(result):
                        self._redraw_from_cursor(result, cursor_pos)
                    else:
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
        # Save cursor position
        remaining = "".join(result[cursor_pos:])
        # Print remaining characters
        print(remaining + " ", end="", flush=True)
        # Move cursor back to correct position
        moves_back = len(remaining) + 1
        if moves_back > 0:
            print("\b" * moves_back, end="", flush=True)

    def _get_char_windows(self) -> str:
        """Get single character on Windows."""
        while True:
            if msvcrt.kbhit():
                char = msvcrt.getch()
                # Handle special keys (arrows, function keys, etc.)
                if char in (b"\x00", b"\xe0"):
                    second = msvcrt.getch()
                    # Arrow keys: Up=72, Down=80, Left=75, Right=77
                    if second == b"H":  # Up arrow
                        return "\x1b[A"
                    elif second == b"P":  # Down arrow
                        return "\x1b[B"
                    elif second == b"M":  # Right arrow
                        return "\x1b[C"
                    elif second == b"K":  # Left arrow
                        return "\x1b[D"
                    # Ignore other special keys
                    continue
                return char.decode("utf-8", errors="ignore")

    def _get_char_unix(self) -> str:
        """Get single character on Unix-like systems."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            char = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return char

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
