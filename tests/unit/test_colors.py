"""Unit tests for color scheme."""

from unittest.mock import patch

from atoll.ui.colors import ColorScheme, Fore, Style


class TestColorScheme:
    """Test ColorScheme class."""

    def test_initialization(self):
        """Test color scheme initialization."""
        scheme = ColorScheme()
        assert scheme.enabled in [True, False]

    @patch("sys.stdout.isatty")
    def test_color_detection_no_tty(self, mock_isatty):
        """Test color detection when not a TTY."""
        mock_isatty.return_value = False
        scheme = ColorScheme()
        assert scheme.enabled is False

    @patch("sys.stdout.isatty")
    @patch.dict("os.environ", {"NO_COLOR": "1"})
    def test_color_detection_no_color_env(self, mock_isatty):
        """Test color detection with NO_COLOR environment variable."""
        mock_isatty.return_value = True
        scheme = ColorScheme()
        assert scheme.enabled is False

    @patch("sys.stdout.isatty")
    @patch("platform.system")
    def test_color_detection_windows(self, mock_system, mock_isatty):
        """Test color detection on Windows."""
        mock_isatty.return_value = True
        mock_system.return_value = "Windows"

        with patch.dict("os.environ", {}, clear=True):
            scheme = ColorScheme()
            assert scheme.enabled is True

    @patch("sys.stdout.isatty")
    @patch("platform.system")
    def test_color_detection_unix(self, mock_system, mock_isatty):
        """Test color detection on Unix."""
        mock_isatty.return_value = True
        mock_system.return_value = "Linux"

        with patch.dict("os.environ", {}, clear=True):
            scheme = ColorScheme()
            assert scheme.enabled is True

    def test_format_with_colors_enabled(self):
        """Test formatting with colors enabled."""
        scheme = ColorScheme()
        scheme.enabled = True

        result = scheme._format("test", Fore.RED)
        assert "test" in result
        assert Style.RESET_ALL in result

    def test_format_with_colors_disabled(self):
        """Test formatting with colors disabled."""
        scheme = ColorScheme()
        scheme.enabled = False

        result = scheme._format("test", Fore.RED)
        assert result == "test"

    def test_all_color_methods(self):
        """Test all color formatting methods."""
        scheme = ColorScheme()

        methods = [
            "header",
            "user_input",
            "reasoning",
            "final_response",
            "error",
            "info",
            "warning",
        ]

        for method_name in methods:
            method = getattr(scheme, method_name)
            result = method("test")
            assert "test" in result
