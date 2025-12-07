"""Tests for __main__ entry point."""

from unittest.mock import patch


class TestMainEntry:
    """Test __main__ module."""

    @patch("atoll.__main__.main")
    def test_main_entry_point(self, mock_main):
        """Test that __main__ calls main()."""
        # Import the module to trigger the if __name__ == "__main__" block
        import importlib

        import atoll.__main__

        # Reload to trigger execution
        with patch("atoll.__main__.__name__", "__main__"):
            importlib.reload(atoll.__main__)
