"""Extended tests for color scheme module."""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from ollama_mcp_agent.ui.colors import ColorScheme, Fore, Back, Style


class TestColorSchemeExtended:
    """Extended tests for ColorScheme."""
    
    def test_format_multiple_codes(self):
        """Test formatting with multiple color codes."""
        scheme = ColorScheme()
        scheme.enabled = True
        
        result = scheme._format("test", Fore.RED, Back.WHITE, Style.BRIGHT)
        assert Fore.RED in result
        assert Back.WHITE in result
        assert Style.BRIGHT in result
        assert "test" in result
        assert Style.RESET_ALL in result
    
    def test_all_formatting_methods(self):
        """Test all formatting methods return strings."""
        scheme = ColorScheme()
        
        methods = [
            scheme.header,
            scheme.user_input,
            scheme.reasoning,
            scheme.final_response,
            scheme.error,
            scheme.info,
            scheme.warning,
        ]
        
        for method in methods:
            result = method("test")
            assert isinstance(result, str)
            assert "test" in result
    
    def test_color_detection_with_no_color_env(self):
        """Test color detection with NO_COLOR environment variable."""
        with patch.dict(os.environ, {'NO_COLOR': '1'}):
            scheme = ColorScheme()
            assert scheme.enabled is False
    
    def test_color_detection_without_no_color_env(self):
        """Test color detection without NO_COLOR environment variable."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('sys.stdout.isatty', return_value=True):
                scheme = ColorScheme()
                assert scheme.enabled is True
    
    def test_format_with_empty_string(self):
        """Test formatting empty string."""
        scheme = ColorScheme()
        result = scheme.header("")
        assert isinstance(result, str)
    
    def test_format_with_special_characters(self):
        """Test formatting with special characters."""
        scheme = ColorScheme()
        special_text = "test\n\t\r"
        result = scheme.error(special_text)
        assert special_text in result
    
    @patch('platform.system', return_value='Windows')
    def test_windows_color_support(self, mock_platform):
        """Test Windows color support detection."""
        with patch('sys.stdout.isatty', return_value=True):
            with patch.dict(os.environ, {}, clear=True):
                scheme = ColorScheme()
                assert scheme.enabled is True
    
    @patch('platform.system', return_value='Linux')
    def test_unix_color_support(self, mock_platform):
        """Test Unix color support detection."""
        with patch('sys.stdout.isatty', return_value=True):
            with patch.dict(os.environ, {}, clear=True):
                scheme = ColorScheme()
                assert scheme.enabled is True
    
    def test_disabled_colors_return_plain_text(self):
        """Test that disabled colors return plain text."""
        scheme = ColorScheme()
        scheme.enabled = False
        
        text = "test message"
        assert scheme.header(text) == text
        assert scheme.error(text) == text
        assert scheme.info(text) == text