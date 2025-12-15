"""Modern input handling using prompt_toolkit for cross-platform support."""

from pathlib import Path
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys


class AtollInput:
    """Advanced input handler using prompt_toolkit for cross-platform support.

    Provides:
    - Full readline-style editing (Ctrl+A, Ctrl+E, Ctrl+W, Ctrl+K, Ctrl+U, Ctrl+R)
    - Arrow key history navigation
    - Persistent history saved to file
    - Insert/overtype mode toggle
    - ESC and Ctrl+V detection
    - Cross-platform compatibility (Windows, Linux, macOS)
    """

    def __init__(
        self,
        history_file: Optional[str] = None,
        max_history_entries: int = 1000,
    ):
        """Initialize the input handler.

        Args:
            history_file: Path to history file (default: ~/.atoll_history)
            max_history_entries: Maximum number of history entries to save
        """
        # Set up history file
        if history_file is None:
            history_file = str(Path.home() / ".atoll_history")

        self.history_path = Path(history_file)
        self.max_history_entries = max_history_entries

        # Ensure history directory exists
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

        # Create history object
        self.history = FileHistory(str(self.history_path))

        # Create key bindings
        self.kb = self._create_key_bindings()

        # Create prompt session (will be recreated for each prompt)
        self.session: Optional[PromptSession] = None

        # Insert/overtype mode tracking
        self.insert_mode = True

    def _create_key_bindings(self) -> KeyBindings:
        """Create custom key bindings for ESC and Ctrl+V."""
        kb = KeyBindings()

        # ESC key - return special marker
        @kb.add(Keys.Escape)
        def _(event):
            """Handle ESC key."""
            event.app.exit(result="ESC")

        # Ctrl+V - return special marker
        @kb.add("c-v")
        def _(event):
            """Handle Ctrl+V key."""
            event.app.exit(result="CTRL_V")

        # Insert key - toggle insert/overtype mode
        @kb.add(Keys.Insert)
        def _(event):
            """Handle Insert key to toggle insert/overtype mode."""
            # Toggle the mode
            self.insert_mode = not self.insert_mode
            # Update the input processor's mode
            if hasattr(event.app.current_buffer, "insert_mode"):
                event.app.current_buffer.insert_mode = self.insert_mode

        return kb

    def read_line(self, prompt: str = "> ") -> str:
        """Read a line of input from the user.

        Args:
            prompt: Prompt string to display

        Returns:
            User input string, or special commands "ESC" or "CTRL_V"

        Raises:
            KeyboardInterrupt: When Ctrl+C is pressed
            EOFError: When Ctrl+D is pressed (Unix) or Ctrl+Z (Windows)
        """
        # Create a new session for this prompt
        # This ensures each call gets fresh state
        self.session = PromptSession(
            history=self.history,
            key_bindings=self.kb,
            enable_history_search=True,  # Enable Ctrl+R for history search
            vi_mode=False,  # Use Emacs mode (readline-style)
        )

        try:
            # Get input from user
            result = self.session.prompt(prompt)
            return result
        except (EOFError, KeyboardInterrupt):
            # Re-raise these for the caller to handle
            raise

    def load_history(self) -> None:
        """Load history from file.

        Note: prompt_toolkit's FileHistory loads automatically,
        so this is mainly for API compatibility.
        """
        # History is automatically loaded by FileHistory
        pass

    def save_history(self) -> None:
        """Save history to file.

        Note: prompt_toolkit's FileHistory saves automatically,
        so this is mainly for API compatibility.
        """
        # History is automatically saved by FileHistory after each input
        # Optionally, we could truncate to max_history_entries here
        if self.history_path.exists():
            self._truncate_history()

    def _truncate_history(self) -> None:
        """Truncate history file to max_history_entries."""
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if len(lines) > self.max_history_entries:
                # Keep only the most recent entries
                lines = lines[-self.max_history_entries :]

                with open(self.history_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)
        except Exception:
            # Ignore errors during truncation
            pass

    def get_input(self, prompt: str = "> ", history: list[str] = None) -> str:
        """Get input from user (backwards compatibility method).

        This method maintains compatibility with the old InputHandler interface.

        Args:
            prompt: Prompt text to display
            history: Ignored (we use FileHistory instead)

        Returns:
            User input string or special commands (ESC, CTRL_V)
        """
        return self.read_line(prompt)
