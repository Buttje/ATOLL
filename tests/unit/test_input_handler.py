"""Unit tests for input handler."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from ollama_mcp_agent.ui.input_handler import InputHandler


class TestInputHandler:
    """Test InputHandler class."""
    
    def test_initialization(self):
        """Test input handler initialization."""
        handler = InputHandler()
        assert handler.is_windows in [True, False]
    
    @patch('platform.system')
    def test_windows_detection(self, mock_system):
        """Test Windows platform detection."""
        mock_system.return_value = 'Windows'
        handler = InputHandler()
        assert handler.is_windows is True
        
        mock_system.return_value = 'Linux'
        handler = InputHandler()
        assert handler.is_windows is False
    
    @patch('platform.system')
    @patch('msvcrt.kbhit')
    @patch('msvcrt.getch')
    def test_get_char_windows(self, mock_getch, mock_kbhit, mock_system):
        """Test getting character on Windows."""
        mock_system.return_value = 'Windows'
        handler = InputHandler()
        
        # Simulate key press
        mock_kbhit.return_value = True
        mock_getch.return_value = b'a'
        
        char = handler._get_char_windows()
        assert char == 'a'
    
    @patch('platform.system')
    @patch('msvcrt.kbhit')
    @patch('msvcrt.getch')
    def test_get_char_windows_special_key(self, mock_getch, mock_kbhit, mock_system):
        """Test handling special keys on Windows."""
        mock_system.return_value = 'Windows'
        handler = InputHandler()
        
        # Simulate special key (arrow key)
        mock_kbhit.side_effect = [True, True, True]
        mock_getch.side_effect = [b'\xe0', b'H', b'a']  # Arrow up, then 'a'
        
        char = handler._get_char_windows()
        assert char == 'a'
    
    @patch('platform.system')
    def test_check_for_escape_no_input(self, mock_system):
        """Test checking for escape with no input."""
        mock_system.return_value = 'Windows'
        handler = InputHandler()
        
        with patch('msvcrt.kbhit', return_value=False):
            assert handler.check_for_escape() is False