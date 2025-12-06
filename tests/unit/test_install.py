"""Tests for the installation script."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

# Add scripts directory to path to import install module
scripts_path = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_path))

import install  # noqa: E402


def test_venv_validation_complete(tmp_path):
    """Test that a complete venv is recognized as valid."""
    # Create a complete venv structure
    if os.name == "nt":
        bin_dir = tmp_path / "venv" / "Scripts"
        python_exe = bin_dir / "python.exe"
        pip_exe = bin_dir / "pip.exe"
    else:
        bin_dir = tmp_path / "venv" / "bin"
        python_exe = bin_dir / "python"
        pip_exe = bin_dir / "pip"

    bin_dir.mkdir(parents=True, exist_ok=True)
    python_exe.touch()
    pip_exe.touch()

    # Change to tmp_path for testing
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)

        with patch("install.run_command") as mock_run:
            mock_run.return_value = True
            with patch("sys.exit"):
                # Should not recreate venv
                install.main()

                # Verify venv creation was not called
                calls = [
                    call
                    for call in mock_run.call_args_list
                    if "venv" in str(call) and "Creating" in str(call)
                ]
                assert len(calls) == 0, "Should not recreate complete venv"
    finally:
        os.chdir(original_cwd)


def test_venv_validation_incomplete(tmp_path):
    """Test that an incomplete venv is recreated."""
    # Create an incomplete venv structure (only directory, no executables)
    venv_dir = tmp_path / "venv"
    venv_dir.mkdir(parents=True, exist_ok=True)

    # Change to tmp_path for testing
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)

        with patch("install.run_command") as mock_run:
            mock_run.return_value = True
            with patch("sys.exit"):
                # Should recreate venv
                install.main()

                # Verify venv creation was called
                calls = [
                    call
                    for call in mock_run.call_args_list
                    if "venv" in str(call) and "Creating" in str(call)
                ]
                assert len(calls) == 1, "Should recreate incomplete venv"
    finally:
        os.chdir(original_cwd)


def test_venv_validation_partial(tmp_path):
    """Test that a partial venv (only python, no pip) is recreated."""
    # Create a partial venv structure (only python executable)
    if os.name == "nt":
        bin_dir = tmp_path / "venv" / "Scripts"
        python_exe = bin_dir / "python.exe"
    else:
        bin_dir = tmp_path / "venv" / "bin"
        python_exe = bin_dir / "python"

    bin_dir.mkdir(parents=True, exist_ok=True)
    python_exe.touch()
    # Note: pip executable is NOT created

    # Change to tmp_path for testing
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)

        with patch("install.run_command") as mock_run:
            mock_run.return_value = True
            with patch("sys.exit"):
                # Should recreate venv
                install.main()

                # Verify venv creation was called
                calls = [
                    call
                    for call in mock_run.call_args_list
                    if "venv" in str(call) and "Creating" in str(call)
                ]
                assert len(calls) == 1, "Should recreate partial venv"
    finally:
        os.chdir(original_cwd)


def test_venv_validation_no_venv(tmp_path):
    """Test that a missing venv is created."""
    # No venv directory exists

    # Change to tmp_path for testing
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)

        with patch("install.run_command") as mock_run:
            mock_run.return_value = True
            with patch("sys.exit"):
                # Should create venv
                install.main()

                # Verify venv creation was called
                calls = [
                    call
                    for call in mock_run.call_args_list
                    if "venv" in str(call) and "Creating" in str(call)
                ]
                assert len(calls) == 1, "Should create new venv"
    finally:
        os.chdir(original_cwd)
