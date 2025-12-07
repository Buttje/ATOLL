"""Comprehensive tests for main module."""

from unittest.mock import patch

import pytest

from atoll.main import Application, main


class TestMainComprehensive:
    """Comprehensive tests for main module."""

    @pytest.mark.asyncio
    async def test_handle_command_invalid(self):
        """Test handling invalid command."""
        app = Application()

        with patch.object(app.ui, "display_error") as mock_error:
            await app.handle_command("invalid_command")
            mock_error.assert_called()

    def test_main_function_exception(self):
        """Test main function with exception."""
        with patch("asyncio.run") as mock_run:
            mock_run.side_effect = Exception("Test error")

            with patch("sys.exit") as mock_exit:
                main()
                mock_exit.assert_called_with(1)
