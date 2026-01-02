"""Cross-platform virtual environment utilities.

This module provides platform-agnostic helper functions to work with Python
virtual environments across Windows, Linux, and macOS.
"""

import sys
from pathlib import Path
from typing import Optional


def get_venv_python_path(venv_path: Path) -> Path:
    """Get the Python interpreter path in a virtual environment.

    Args:
        venv_path: Path to the virtual environment directory (.venv)

    Returns:
        Path to the Python interpreter (python.exe on Windows, python on Unix)

    Examples:
        >>> venv_path = Path("/home/user/project/.venv")
        >>> get_venv_python_path(venv_path)
        PosixPath('/home/user/project/.venv/bin/python')

        >>> venv_path = Path("C:\\\\Users\\\\user\\\\project\\\\.venv")
        >>> get_venv_python_path(venv_path)  # doctest: +SKIP
        WindowsPath('C:\\\\Users\\\\user\\\\project\\\\.venv\\\\Scripts\\\\python.exe')
    """
    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"


def get_venv_pip_path(venv_path: Path) -> Path:
    """Get the pip executable path in a virtual environment.

    Args:
        venv_path: Path to the virtual environment directory (.venv)

    Returns:
        Path to the pip executable (pip.exe on Windows, pip on Unix)

    Examples:
        >>> venv_path = Path("/home/user/project/.venv")
        >>> get_venv_pip_path(venv_path)
        PosixPath('/home/user/project/.venv/bin/pip')

        >>> venv_path = Path("C:\\\\Users\\\\user\\\\project\\\\.venv")
        >>> get_venv_pip_path(venv_path)  # doctest: +SKIP
        WindowsPath('C:\\\\Users\\\\user\\\\project\\\\.venv\\\\Scripts\\\\pip.exe')
    """
    if sys.platform == "win32":
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"


def get_venv_executable_path(venv_path: Path, executable_name: str) -> Path:
    """Get the path to any executable in a virtual environment.

    Args:
        venv_path: Path to the virtual environment directory (.venv)
        executable_name: Name of the executable (e.g., 'pytest', 'black')

    Returns:
        Path to the executable in the venv bin/Scripts directory

    Examples:
        >>> venv_path = Path("/home/user/project/.venv")
        >>> get_venv_executable_path(venv_path, "pytest")
        PosixPath('/home/user/project/.venv/bin/pytest')

        >>> venv_path = Path("C:\\\\Users\\\\user\\\\project\\\\.venv")
        >>> get_venv_executable_path(venv_path, "pytest")  # doctest: +SKIP
        WindowsPath('C:\\\\Users\\\\user\\\\project\\\\.venv\\\\Scripts\\\\pytest.exe')
    """
    if sys.platform == "win32":
        # On Windows, executables typically have .exe extension
        if not executable_name.endswith(".exe"):
            executable_name = f"{executable_name}.exe"
        return venv_path / "Scripts" / executable_name
    else:
        return venv_path / "bin" / executable_name


def verify_venv_exists(venv_path: Path) -> bool:
    """Verify that a virtual environment exists and is valid.

    Args:
        venv_path: Path to the virtual environment directory

    Returns:
        True if the venv exists and has a valid structure, False otherwise

    Examples:
        >>> from pathlib import Path
        >>> verify_venv_exists(Path("/nonexistent/path"))
        False
    """
    if not venv_path.exists():
        return False

    # Check for Python interpreter
    python_path = get_venv_python_path(venv_path)
    if not python_path.exists():
        return False

    # Check for pip (optional but recommended)
    pip_path = get_venv_pip_path(venv_path)

    # Consider venv valid even without pip, but log warning
    return True


def find_venv_in_directory(directory: Path) -> Optional[Path]:
    """Find a virtual environment directory in or near the given directory.

    Searches for common venv directory names (.venv, venv, env).

    Args:
        directory: Directory to search in

    Returns:
        Path to the virtual environment if found, None otherwise

    Examples:
        >>> from pathlib import Path
        >>> # Assuming a .venv exists in the project directory
        >>> find_venv_in_directory(Path.cwd())  # doctest: +SKIP
        PosixPath('/home/user/project/.venv')
    """
    common_names = [".venv", "venv", "env"]

    for name in common_names:
        venv_path = directory / name
        if verify_venv_exists(venv_path):
            return venv_path

    return None


def get_venv_site_packages(venv_path: Path) -> Optional[Path]:
    """Get the site-packages directory path for a virtual environment.

    Args:
        venv_path: Path to the virtual environment directory

    Returns:
        Path to site-packages directory if found, None otherwise

    Examples:
        >>> venv_path = Path("/home/user/project/.venv")
        >>> get_venv_site_packages(venv_path)  # doctest: +SKIP
        PosixPath('/home/user/project/.venv/lib/python3.9/site-packages')
    """
    if sys.platform == "win32":
        # Windows: .venv/Lib/site-packages
        site_packages = venv_path / "Lib" / "site-packages"
    else:
        # Unix: .venv/lib/pythonX.Y/site-packages
        lib_dir = venv_path / "lib"
        if not lib_dir.exists():
            return None

        # Find pythonX.Y directory
        python_dirs = list(lib_dir.glob("python*"))
        if not python_dirs:
            return None

        site_packages = python_dirs[0] / "site-packages"

    return site_packages if site_packages.exists() else None
