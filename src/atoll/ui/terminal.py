"""Terminal UI implementation."""

import os
import sys
from enum import Enum
from typing import Optional, List, Callable
import platform
import textwrap

if platform.system() == 'Windows':
    import msvcrt
else:
    import termios
    import tty

from .colors import ColorScheme
from .input_handler import InputHandler


class UIMode(Enum):
    """UI operation modes."""
    
    PROMPT = "Prompt"
    COMMAND = "Command"


class TerminalUI:
    """Terminal user interface manager."""
    
    def __init__(self):
        """Initialize terminal UI."""
        self.mode = UIMode.PROMPT
        self.colors = ColorScheme()
        self.input_handler = InputHandler()
        self.running = True
        self._clear_screen()
        
    def _clear_screen(self):
        """Clear terminal screen."""
        os.system('cls' if platform.system() == 'Windows' else 'clear')
    
    def _wrap_text(self, text: str, width: int = 80, indent: str = "") -> str:
        """Wrap text to specified width with optional indent."""
        lines = []
        for paragraph in text.split('\n'):
            if paragraph.strip():
                wrapped = textwrap.fill(
                    paragraph,
                    width=width,
                    initial_indent=indent,
                    subsequent_indent=indent,
                    break_long_words=False,
                    break_on_hyphens=False
                )
                lines.append(wrapped)
            else:
                lines.append('')
        return '\n'.join(lines)
    
    def display_header(self):
        """Display application header with current mode."""
        self._clear_screen()
        print(self.colors.header("=" * 60))
        print(self.colors.header("Ollama MCP Agent"))
        print(self.colors.header(f"Mode: {self.mode.value} (Press ESC to toggle)"))
        if self.mode == UIMode.COMMAND:
            print(self.colors.info("Type 'help' for available commands"))
        print(self.colors.header("=" * 60))
        print()
    
    def display_user_input(self, text: str):
        """Display user input."""
        print(self.colors.user_input(f"\nUser: {text}"))
    
    def display_reasoning(self, text: str):
        """Display agent reasoning."""
        # Summarize reasoning if too long
        lines = text.split('\n')
        if len(lines) > 5:
            summary = '\n'.join(lines[:3]) + '\n...\n' + lines[-1]
            wrapped = self._wrap_text(summary, width=76, indent="  ")
            print(self.colors.reasoning(f"\nReasoning:\n{wrapped}"))
        else:
            wrapped = self._wrap_text(text, width=76, indent="  ")
            print(self.colors.reasoning(f"\nReasoning:\n{wrapped}"))
    
    def display_response(self, text: str):
        """Display final response."""
        wrapped = self._wrap_text(text, width=76, indent="  ")
        print(self.colors.final_response(f"\nAssistant:\n{wrapped}\n"))
    
    def display_error(self, text: str):
        """Display error message."""
        print(self.colors.error(f"\n❌ Error: {text}\n"))
    
    def display_info(self, text: str):
        """Display info message."""
        print(self.colors.info(f"\nℹ️  {text}\n"))
    
    def display_warning(self, text: str):
        """Display warning message."""
        print(self.colors.warning(f"\n⚠️  {text}\n"))
    
    def display_models(self, models: List[str], current_model: str):
        """Display available models."""
        print(self.colors.info("\nAvailable models:"))
        for model in models:
            if model == current_model:
                print(self.colors.final_response(f"  ✓ {model} (current)"))
            else:
                print(self.colors.user_input(f"  • {model}"))
        print()
    
    def toggle_mode(self):
        """Toggle between Prompt and Command modes."""
        self.mode = UIMode.COMMAND if self.mode == UIMode.PROMPT else UIMode.PROMPT
        self.display_header()
    
    def get_input(self, prompt: str = "") -> str:
        """Get user input based on current mode."""
        if self.mode == UIMode.PROMPT:
            prompt_text = "\n💬 Enter prompt: "
        else:
            prompt_text = "\n⚙️  Enter command: "
        
        return self.input_handler.get_input(prompt_text)
    
    def handle_escape_key(self, callback: Optional[Callable] = None):
        """Handle ESC key press."""
        if callback:
            callback()
        else:
            self.toggle_mode()