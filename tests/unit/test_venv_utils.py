"""Tests for cross-platform virtual environment utilities."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from atoll.utils.venv_utils import (
    find_venv_in_directory,
    get_venv_executable_path,
    get_venv_pip_path,
    get_venv_python_path,
    get_venv_site_packages,
    verify_venv_exists,
)


class TestVenvPathHelpers:
    """Test virtual environment path helper functions."""

    def test_get_venv_python_path_unix(self):
        """Test Python path generation on Unix systems."""
        with patch("sys.platform", "linux"):
            venv_path = Path("/home/user/project/.venv")
            python_path = get_venv_python_path(venv_path)
            assert python_path == Path("/home/user/project/.venv/bin/python")
            assert "Scripts" not in str(python_path)

    def test_get_venv_python_path_windows(self):
        """Test Python path generation on Windows."""
        with patch("sys.platform", "win32"):
            venv_path = Path("C:/Users/user/project/.venv")
            python_path = get_venv_python_path(venv_path)
            assert python_path == Path("C:/Users/user/project/.venv/Scripts/python.exe")
            assert "bin" not in str(python_path)

    def test_get_venv_pip_path_unix(self):
        """Test pip path generation on Unix systems."""
        with patch("sys.platform", "linux"):
            venv_path = Path("/home/user/project/.venv")
            pip_path = get_venv_pip_path(venv_path)
            assert pip_path == Path("/home/user/project/.venv/bin/pip")
            assert "Scripts" not in str(pip_path)

    def test_get_venv_pip_path_windows(self):
        """Test pip path generation on Windows."""
        with patch("sys.platform", "win32"):
            venv_path = Path("C:/Users/user/project/.venv")
            pip_path = get_venv_pip_path(venv_path)
            assert pip_path == Path("C:/Users/user/project/.venv/Scripts/pip.exe")
            assert "bin" not in str(pip_path)

    def test_get_venv_executable_path_unix(self):
        """Test arbitrary executable path on Unix."""
        with patch("sys.platform", "linux"):
            venv_path = Path("/home/user/project/.venv")
            pytest_path = get_venv_executable_path(venv_path, "pytest")
            assert pytest_path == Path("/home/user/project/.venv/bin/pytest")
            assert not str(pytest_path).endswith(".exe")

    def test_get_venv_executable_path_windows(self):
        """Test arbitrary executable path on Windows."""
        with patch("sys.platform", "win32"):
            venv_path = Path("C:/Users/user/project/.venv")
            pytest_path = get_venv_executable_path(venv_path, "pytest")
            assert pytest_path == Path("C:/Users/user/project/.venv/Scripts/pytest.exe")
            assert str(pytest_path).endswith(".exe")

    def test_get_venv_executable_path_windows_with_exe(self):
        """Test executable path on Windows when .exe is already in name."""
        with patch("sys.platform", "win32"):
            venv_path = Path("C:/Users/user/project/.venv")
            pytest_path = get_venv_executable_path(venv_path, "pytest.exe")
            assert pytest_path == Path("C:/Users/user/project/.venv/Scripts/pytest.exe")
            # Should not add .exe twice
            assert not str(pytest_path).endswith(".exe.exe")


class TestVenvVerification:
    """Test virtual environment verification functions."""

    def test_verify_venv_exists_nonexistent(self):
        """Test verification fails for nonexistent venv."""
        venv_path = Path("/nonexistent/path/.venv")
        assert not verify_venv_exists(venv_path)

    def test_verify_venv_exists_no_python(self, tmp_path):
        """Test verification fails when Python interpreter is missing."""
        venv_path = tmp_path / ".venv"
        venv_path.mkdir()
        assert not verify_venv_exists(venv_path)

    def test_verify_venv_exists_valid_unix(self, tmp_path):
        """Test verification succeeds with valid Unix venv structure."""
        with patch("sys.platform", "linux"):
            venv_path = tmp_path / ".venv"
            venv_path.mkdir()
            bin_dir = venv_path / "bin"
            bin_dir.mkdir()
            python_exe = bin_dir / "python"
            python_exe.touch()

            assert verify_venv_exists(venv_path)

    def test_verify_venv_exists_valid_windows(self, tmp_path):
        """Test verification succeeds with valid Windows venv structure."""
        with patch("sys.platform", "win32"):
            venv_path = tmp_path / ".venv"
            venv_path.mkdir()
            scripts_dir = venv_path / "Scripts"
            scripts_dir.mkdir()
            python_exe = scripts_dir / "python.exe"
            python_exe.touch()

            assert verify_venv_exists(venv_path)


class TestVenvDiscovery:
    """Test virtual environment discovery functions."""

    def test_find_venv_in_directory_none(self, tmp_path):
        """Test finding venv returns None when none exists."""
        assert find_venv_in_directory(tmp_path) is None

    def test_find_venv_in_directory_dotenv(self, tmp_path):
        """Test finding .venv directory."""
        with patch("sys.platform", "linux"):
            venv_path = tmp_path / ".venv"
            venv_path.mkdir()
            bin_dir = venv_path / "bin"
            bin_dir.mkdir()
            python_exe = bin_dir / "python"
            python_exe.touch()

            found = find_venv_in_directory(tmp_path)
            assert found == venv_path

    def test_find_venv_in_directory_venv(self, tmp_path):
        """Test finding venv directory."""
        with patch("sys.platform", "linux"):
            venv_path = tmp_path / "venv"
            venv_path.mkdir()
            bin_dir = venv_path / "bin"
            bin_dir.mkdir()
            python_exe = bin_dir / "python"
            python_exe.touch()

            found = find_venv_in_directory(tmp_path)
            assert found == venv_path

    def test_find_venv_prefers_dotenv(self, tmp_path):
        """Test that .venv is preferred over venv."""
        with patch("sys.platform", "linux"):
            # Create both .venv and venv
            for name in [".venv", "venv"]:
                venv_path = tmp_path / name
                venv_path.mkdir()
                bin_dir = venv_path / "bin"
                bin_dir.mkdir()
                python_exe = bin_dir / "python"
                python_exe.touch()

            found = find_venv_in_directory(tmp_path)
            # Should prefer .venv since it's first in the search list
            assert found == tmp_path / ".venv"


class TestSitePackages:
    """Test site-packages directory discovery."""

    def test_get_venv_site_packages_nonexistent(self, tmp_path):
        """Test getting site-packages for nonexistent venv."""
        venv_path = tmp_path / ".venv"
        assert get_venv_site_packages(venv_path) is None

    def test_get_venv_site_packages_unix(self, tmp_path):
        """Test getting site-packages on Unix."""
        with patch("sys.platform", "linux"):
            venv_path = tmp_path / ".venv"
            lib_dir = venv_path / "lib" / "python3.9"
            site_packages = lib_dir / "site-packages"
            site_packages.mkdir(parents=True)

            result = get_venv_site_packages(venv_path)
            assert result == site_packages

    def test_get_venv_site_packages_windows(self, tmp_path):
        """Test getting site-packages on Windows."""
        with patch("sys.platform", "win32"):
            venv_path = tmp_path / ".venv"
            site_packages = venv_path / "Lib" / "site-packages"
            site_packages.mkdir(parents=True)

            result = get_venv_site_packages(venv_path)
            assert result == site_packages

    def test_get_venv_site_packages_no_lib_dir(self, tmp_path):
        """Test getting site-packages when lib directory doesn't exist."""
        with patch("sys.platform", "linux"):
            venv_path = tmp_path / ".venv"
            venv_path.mkdir()

            result = get_venv_site_packages(venv_path)
            assert result is None


class TestCrossPlatformCompatibility:
    """Test cross-platform compatibility."""

    def test_paths_use_pathlib(self):
        """Test that all functions return pathlib.Path objects."""
        venv_path = Path("/tmp/.venv")

        python_path = get_venv_python_path(venv_path)
        assert isinstance(python_path, Path)

        pip_path = get_venv_pip_path(venv_path)
        assert isinstance(pip_path, Path)

        exe_path = get_venv_executable_path(venv_path, "pytest")
        assert isinstance(exe_path, Path)

    def test_windows_backslash_handling(self):
        """Test that Windows paths work correctly."""
        with patch("sys.platform", "win32"):
            # Windows path with backslashes
            venv_path = Path("C:\\Users\\user\\project\\.venv")
            python_path = get_venv_python_path(venv_path)

            # pathlib should handle conversion automatically
            assert "Scripts" in str(python_path)
            assert python_path.name == "python.exe"

    def test_unix_forward_slash_handling(self):
        """Test that Unix paths work correctly."""
        with patch("sys.platform", "linux"):
            venv_path = Path("/home/user/project/.venv")
            python_path = get_venv_python_path(venv_path)

            assert "bin" in str(python_path)
            assert python_path.name == "python"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_venv_path(self):
        """Test behavior with empty venv path."""
        venv_path = Path("")
        # Should not crash, just return invalid paths
        python_path = get_venv_python_path(venv_path)
        assert isinstance(python_path, Path)

    def test_relative_venv_path(self):
        """Test behavior with relative paths."""
        venv_path = Path(".venv")
        python_path = get_venv_python_path(venv_path)
        pip_path = get_venv_pip_path(venv_path)

        assert isinstance(python_path, Path)
        assert isinstance(pip_path, Path)

    def test_nested_venv_path(self):
        """Test behavior with deeply nested venv paths."""
        venv_path = Path("/very/deep/nested/directory/structure/.venv")
        python_path = get_venv_python_path(venv_path)

        assert isinstance(python_path, Path)
        assert ".venv" in str(python_path)
