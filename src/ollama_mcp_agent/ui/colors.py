"""Color scheme for terminal UI."""

import sys
import platform
from typing import Optional

# Check if we're on Windows and import colorama if needed
if platform.system() == 'Windows':
    try:
        from colorama import init, Fore, Back, Style
        init(autoreset=True)
    except ImportError:
        # Fallback if colorama is not installed
        class Fore:
            BLACK = ''
            RED = ''
            GREEN = ''
            YELLOW = ''
            BLUE = ''
            MAGENTA = ''
            CYAN = ''
            WHITE = ''
            RESET = ''
        
        class Back:
            BLACK = ''
            RED = ''
            GREEN = ''
            YELLOW = ''
            BLUE = ''
            MAGENTA = ''
            CYAN = ''
            WHITE = ''
            RESET = ''
        
        class Style:
            DIM = ''
            NORMAL = ''
            BRIGHT = ''
            RESET_ALL = ''
else:
    # Use ANSI codes on Unix-like systems
    class Fore:
        BLACK = '\033[30m'
        RED = '\033[31m'
        GREEN = '\033[32m'
        YELLOW = '\033[33m'
        BLUE = '\033[34m'
        MAGENTA = '\033[35m'
        CYAN = '\033[36m'
        WHITE = '\033[37m'
        RESET = '\033[39m'
    
    class Back:
        BLACK = '\033[40m'
        RED = '\033[41m'
        GREEN = '\033[42m'
        YELLOW = '\033[43m'
        BLUE = '\033[44m'
        MAGENTA = '\033[45m'
        CYAN = '\033[46m'
        WHITE = '\033[47m'
        RESET = '\033[49m'
    
    class Style:
        DIM = '\033[2m'
        NORMAL = '\033[22m'
        BRIGHT = '\033[1m'
        RESET_ALL = '\033[0m'


class ColorScheme:
    """Manages color schemes for terminal output."""
    
    def __init__(self):
        """Initialize color scheme."""
        self.enabled = True
        self._detect_color_support()
    
    def _detect_color_support(self):
        """Detect if terminal supports colors."""
        # Check if output is a TTY
        if not sys.stdout.isatty():
            self.enabled = False
            return
        
        # Check for NO_COLOR environment variable
        import os
        if os.environ.get('NO_COLOR'):
            self.enabled = False
            return
        
        # Windows terminals generally support color with colorama
        if platform.system() == 'Windows':
            self.enabled = True
            return
        
        # Unix terminals generally support color
        self.enabled = True
    
    def _format(self, text: str, *codes) -> str:
        """Format text with color codes if enabled."""
        if not self.enabled:
            return text
        
        formatted = ''.join(codes) + text + Style.RESET_ALL
        return formatted
    
    def header(self, text: str) -> str:
        """Format header text (cyan, bright)."""
        return self._format(text, Fore.CYAN, Style.BRIGHT)
    
    def user_input(self, text: str) -> str:
        """Format user input text (white)."""
        return self._format(text, Fore.WHITE)
    
    def reasoning(self, text: str) -> str:
        """Format reasoning/thinking text (yellow, dim)."""
        return self._format(text, Fore.YELLOW, Style.DIM)
    
    def answer_text(self, text: str) -> str:
        """Format answer text (green, bright)."""
        return self._format(text, Fore.GREEN, Style.BRIGHT)
    
    def final_response(self, text: str) -> str:
        """Format final response text (cyan) - kept for backward compatibility."""
        return self._format(text, Fore.CYAN)
    
    def error(self, text: str) -> str:
        """Format error text (red, bright)."""
        return self._format(text, Fore.RED, Style.BRIGHT)
    
    def info(self, text: str) -> str:
        """Format info text (blue)."""
        return self._format(text, Fore.BLUE)
    
    def warning(self, text: str) -> str:
        """Format warning text (yellow, bright)."""
        return self._format(text, Fore.YELLOW, Style.BRIGHT)