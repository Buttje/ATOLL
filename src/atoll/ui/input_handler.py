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

    def get_input(self, prompt: str = "") -> str:
        """Get input from user with ESC detection."""
        if prompt:
            print(prompt, end="", flush=True)

        result = []
        try:
            while True:
                char = self._get_char_windows() if self.is_windows else self._get_char_unix()

                if char == "\x1b":  # ESC key
                    return "ESC"
                elif char == "\x16":  # Ctrl+V
                    return "CTRL_V"
                elif char in ("\r", "\n"):  # Enter key
                    print()  # New line after input
                    return "".join(result)
                elif char == "\x08" or char == "\x7f":  # Backspace
                    if result:
                        result.pop()
                        print("\b \b", end="", flush=True)
                elif char == "\x03":  # Ctrl+C
                    raise KeyboardInterrupt
                else:
                    result.append(char)
                    print(char, end="", flush=True)
        except KeyboardInterrupt:
            # Re-raise to be handled by the main loop
            raise

    def _get_char_windows(self) -> str:
        """Get single character on Windows."""
        while True:
            if msvcrt.kbhit():
                char = msvcrt.getch()
                # Handle special keys
                if char in (b"\x00", b"\xe0"):  # Special key (arrows, function keys, etc.)
                    msvcrt.getch()  # Discard second byte
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
