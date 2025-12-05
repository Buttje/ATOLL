"""Comprehensive tests for colors module."""

import pytest
import os
import sys
from unittest.mock import patch
from atoll.ui.colors import ColorScheme, Fore, Back, Style


class TestColorSchemeComprehensive:
    """Comprehensive tests for color scheme."""
    
    def test_all_fore_colors_exist(self):
        """Test all foreground colors are defined."""
        assert hasattr(Fore, 'BLACK')
        assert hasattr(Fore, 'RED')
        assert hasattr(Fore, 'GREEN')
        assert hasattr(Fore, 'YELLOW')
        assert hasattr(Fore, 'BLUE')
        assert hasattr(Fore, 'MAGENTA')
        assert hasattr(Fore, 'CYAN')
        assert hasattr(Fore, 'WHITE')
        assert hasattr(Fore, 'RESET')
    
    def test_all_back_colors_exist(self):
        """Test all background colors are defined."""
        assert hasattr(Back, 'BLACK')
        assert hasattr(Back, 'RED')
        assert hasattr(Back, 'GREEN')
        assert hasattr(Back, 'YELLOW')
        assert hasattr(Back, 'BLUE')
        assert hasattr(Back, 'MAGENTA')
        assert hasattr(Back, 'CYAN')
        assert hasattr(Back, 'WHITE')
        assert hasattr(Back, 'RESET')
    
    def test_all_styles_exist(self):
        """Test all styles are defined."""
        assert hasattr(Style, 'DIM')
        assert hasattr(Style, 'NORMAL')
        assert hasattr(Style, 'BRIGHT')
        assert hasattr(Style, 'RESET_ALL')
    
    @patch('sys.stdout.isatty', return_value=False)
    def test_no_tty_disables_colors(self, mock_isatty):
        """Test colors disabled when not a TTY."""
        with patch.dict(os.environ, {}, clear=True):
            scheme = ColorScheme()
            assert scheme.enabled is False
    
    @patch('sys.stdout.isatty', return_value=True)
    def test_tty_enables_colors(self, mock_isatty):
        """Test colors enabled when TTY."""
        with patch.dict(os.environ, {}, clear=True):
            scheme = ColorScheme()
            assert scheme.enabled is True
    
    def test_warning_method(self):
        """Test warning formatting."""
        scheme = ColorScheme()
        result = scheme.warning("test warning")
        assert "test warning" in result
    
    def test_multiple_format_calls(self):
        """Test multiple formatting calls."""
        scheme = ColorScheme()
        scheme.enabled = True
        
        results = [
            scheme.header("header"),
            scheme.user_input("input"),
            scheme.reasoning("reasoning"),
            scheme.final_response("response"),
            scheme.error("error"),
            scheme.info("info"),
            scheme.warning("warning"),
        ]
        
        for result in results:
            assert isinstance(result, str)
            assert len(result) > 0