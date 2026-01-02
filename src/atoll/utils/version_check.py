"""Version compatibility checking utilities.

This module provides functions to check Python version and library compatibility
to prevent runtime failures and provide helpful warnings.
"""

import sys
import warnings
from importlib.metadata import version
from typing import Optional, Tuple

from .logger import get_logger

logger = get_logger(__name__)


def check_python_version(
    min_version: Tuple[int, int] = (3, 9),
    max_version: Optional[Tuple[int, int]] = None,
) -> bool:
    """Check if Python version is compatible.

    Args:
        min_version: Minimum required Python version (major, minor)
        max_version: Maximum supported Python version (major, minor), None for no limit

    Returns:
        True if version is compatible, False otherwise

    Examples:
        >>> check_python_version((3, 9))  # doctest: +SKIP
        True
        >>> check_python_version((3, 9), (3, 13))  # doctest: +SKIP
        True
    """
    current_version = (sys.version_info.major, sys.version_info.minor)

    if current_version < min_version:
        min_ver_str = f"{min_version[0]}.{min_version[1]}"
        current_ver_str = f"{current_version[0]}.{current_version[1]}"
        logger.error(
            f"Python {min_ver_str}+ required, but running Python {current_ver_str}. "
            f"Please upgrade Python."
        )
        return False

    if max_version and current_version > max_version:
        max_ver_str = f"{max_version[0]}.{max_version[1]}"
        current_ver_str = f"{current_version[0]}.{current_version[1]}"
        logger.warning(
            f"Python {current_ver_str} detected. Maximum tested version is {max_ver_str}. "
            f"Some features may not work correctly."
        )
        return True  # Warning only, not an error

    return True


def check_pydantic_version() -> bool:
    """Check for Pydantic V1/V2 compatibility issues.

    Python 3.14+ has known compatibility issues with Pydantic V1.
    This function checks for this specific incompatibility.

    Returns:
        True if compatible, False if incompatible

    Examples:
        >>> check_pydantic_version()  # doctest: +SKIP
        True
    """
    if sys.version_info >= (3, 14):
        try:
            pydantic_version = version("pydantic")
            major_version = int(pydantic_version.split(".")[0])

            if major_version < 2:
                logger.error(
                    f"Python 3.14+ detected with Pydantic V{major_version}. "
                    f"Pydantic V2 is required for Python 3.14+. "
                    f"Please upgrade: pip install 'pydantic>=2.0.0'"
                )
                return False
        except Exception as e:
            logger.warning(f"Could not check Pydantic version: {e}")
            return True

    return True


def check_dependency_version(
    package: str,
    min_version: Optional[str] = None,
    max_version: Optional[str] = None,
) -> bool:
    """Check if a package version meets requirements.

    Args:
        package: Package name
        min_version: Minimum version string (e.g., "0.2.0")
        max_version: Maximum version string (e.g., "1.0.0")

    Returns:
        True if version is compatible, False otherwise

    Examples:
        >>> check_dependency_version("pydantic", "2.0.0")  # doctest: +SKIP
        True
    """
    try:
        current = version(package)
    except Exception as e:
        logger.warning(f"Could not check version of {package}: {e}")
        return True  # Package might not be installed yet

    def parse_version(ver: str) -> Tuple[int, ...]:
        """Parse version string to tuple."""
        return tuple(int(x) for x in ver.split("."))

    current_tuple = parse_version(current)

    if min_version:
        min_tuple = parse_version(min_version)
        if current_tuple < min_tuple:
            logger.error(
                f"{package} {min_version}+ required, but {current} installed. "
                f"Please upgrade: pip install --upgrade {package}>={min_version}"
            )
            return False

    if max_version:
        max_tuple = parse_version(max_version)
        if current_tuple > max_tuple:
            logger.warning(
                f"{package} {current} installed. Maximum tested version is {max_version}. "
                f"Some features may not work correctly."
            )

    return True


def check_all_compatibility() -> bool:
    """Run all compatibility checks.

    Returns:
        True if all checks pass, False if any critical check fails

    This function is called on application startup to ensure environment compatibility.
    """
    checks_passed = True

    # Check Python version (3.9 - 3.13 tested, 3.14+ with warnings)
    if not check_python_version((3, 9)):
        checks_passed = False

    # Warn for Python 3.14+ (some libraries may have issues)
    if sys.version_info >= (3, 14):
        logger.warning(
            f"Python {sys.version_info.major}.{sys.version_info.minor} detected. "
            f"This version is newer than officially supported versions. "
            f"Please report any issues to: https://github.com/Buttje/ATOLL/issues"
        )

    # Check Pydantic compatibility (critical for Python 3.14+)
    if not check_pydantic_version():
        checks_passed = False

    # Check key dependencies
    critical_deps = {
        "langchain": ("0.2.0", None),
        "langchain-ollama": ("0.1.0", None),
        "fastapi": ("0.109.0", None),
    }

    for package, (min_ver, max_ver) in critical_deps.items():
        if not check_dependency_version(package, min_ver, max_ver):
            logger.warning(
                f"Dependency {package} version check failed. "
                f"ATOLL may not function correctly."
            )
            # Don't fail on dependency checks, just warn

    if not checks_passed:
        logger.error(
            "Critical compatibility checks failed. "
            "Please resolve the issues above before using ATOLL."
        )

    return checks_passed


def get_version_info() -> dict:
    """Get version information for all key components.

    Returns:
        Dictionary with version information

    Examples:
        >>> info = get_version_info()
        >>> 'python_version' in info
        True
        >>> 'atoll_version' in info
        True
    """
    info = {
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": sys.platform,
    }

    # Get package versions
    packages = [
        "atoll",
        "langchain",
        "langchain-ollama",
        "pydantic",
        "fastapi",
        "ollama",
    ]

    for package in packages:
        try:
            info[f"{package}_version"] = version(package)
        except Exception:
            info[f"{package}_version"] = "not installed"

    return info


def log_version_info() -> None:
    """Log version information for debugging.

    This function logs all version information to help with troubleshooting.
    """
    info = get_version_info()
    logger.info("=== Version Information ===")
    for key, value in info.items():
        logger.info(f"  {key}: {value}")
    logger.info("===========================")
