"""Comprehensive tests for main module."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from atoll.main import Application, main


class TestMainComprehensive:
    """Comprehensive tests for main module."""
    
    @pytest.mark.asyncio
    async def test_handle_command_invalid(self):
        """Test handling invalid command."""
        app = Application()
        
        with patch.object(app.ui, 'display_error') as mock_error:
            await app.handle_command("invalid_command")
            mock_error.assert_called()
    
    def test_main_function_exception(self):
        """Test main function with exception."""
        with patch('atoll.main.Application') as mock_app_class:
            mock_app = Mock()
            mock_app.run = AsyncMock(side_effect=Exception("Test error"))
            mock_app_class.return_value = mock_app
            
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_with(1)