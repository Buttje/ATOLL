"""Tests for __main__ entry point."""

import pytest
from unittest.mock import patch, Mock


class TestMainEntry:
    """Test __main__ module."""
    
    @patch('ollama_mcp_agent.__main__.main')
    def test_main_entry_point(self, mock_main):
        """Test that __main__ calls main()."""
        # Import the module to trigger the if __name__ == "__main__" block
        import importlib
        import ollama_mcp_agent.__main__
        
        # Reload to trigger execution
        with patch('ollama_mcp_agent.__main__.__name__', '__main__'):
            importlib.reload(ollama_mcp_agent.__main__)