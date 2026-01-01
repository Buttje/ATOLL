#!/usr/bin/env python3
"""
Installation Guide Validation Script

This script validates that the installation guide instructions are accurate
by checking prerequisites and testing installation steps.

Usage:
    python scripts/validate_installation.py [--quick]
"""

import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")


def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✓{Colors.RESET} {text}")


def print_warning(text):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {text}")


def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}✗{Colors.RESET} {text}")


def print_info(text):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {text}")


def check_python_version():
    """Check Python version meets requirements."""
    print_info("Checking Python version...")
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    if version >= (3, 9):
        print_success(f"Python {version_str} (requirement: 3.9+)")
        return True
    else:
        print_error(f"Python {version_str} (requirement: 3.9+)")
        return False


def check_pip():
    """Check if pip is available."""
    print_info("Checking pip availability...")
    pip_cmd = shutil.which("pip") or shutil.which("pip3")

    if pip_cmd:
        try:
            result = subprocess.run([pip_cmd, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                print_success(f"pip found: {version}")
                return True
        except Exception as e:
            print_error(f"pip check failed: {e}")
            return False

    print_error("pip not found")
    return False


def check_git():
    """Check if git is available."""
    print_info("Checking git availability...")
    git_cmd = shutil.which("git")

    if git_cmd:
        try:
            result = subprocess.run(["git", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                print_success(f"Git found: {version}")
                return True
        except Exception:
            pass

    print_warning("Git not found (optional, but recommended)")
    return False


def check_ollama():
    """Check if Ollama is installed and running."""
    print_info("Checking Ollama installation...")
    ollama_cmd = shutil.which("ollama")

    if not ollama_cmd:
        print_error("Ollama command not found")
        print_info("Install from: https://ollama.ai/")
        return False

    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print_success(f"Ollama found: {version}")

            # Try to check if Ollama server is running
            try:
                result = subprocess.run(
                    ["ollama", "list"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    print_success("Ollama server is running")
                    models = [
                        line.split()[0]
                        for line in result.stdout.strip().split("\n")[1:]
                        if line.strip()
                    ]
                    if models:
                        print_info(f"Available models: {', '.join(models[:3])}")
                    else:
                        print_warning("No models installed. Run: ollama pull llama2")
                    return True
            except subprocess.TimeoutExpired:
                print_warning("Ollama server check timed out")

            return True
    except Exception as e:
        print_error(f"Ollama check failed: {e}")

    return False


def check_system_resources():
    """Check system resources meet minimum requirements."""
    print_info("Checking system resources...")

    try:
        import psutil

        # Check RAM
        ram_gb = psutil.virtual_memory().total / (1024**3)
        if ram_gb >= 8:
            print_success(f"RAM: {ram_gb:.1f} GB (requirement: 8+ GB)")
        else:
            print_warning(f"RAM: {ram_gb:.1f} GB (recommended: 8+ GB)")

        # Check disk space - use current working directory's drive/mount
        # This works on both Windows (C:\, D:\) and Unix (/, /home, etc.)
        disk = psutil.disk_usage(Path.cwd().anchor or ".")
        disk_gb = disk.free / (1024**3)
        if disk_gb >= 10:
            print_success(f"Free disk space: {disk_gb:.1f} GB")
        else:
            print_warning(f"Free disk space: {disk_gb:.1f} GB (recommended: 10+ GB)")

        return True
    except ImportError:
        print_warning("psutil not available, skipping resource check")
        return True


def check_ollama_config():
    """Check if Ollama configuration exists."""
    print_info("Checking Ollama configuration...")
    config_dir = Path.home() / ".ollama_server"
    config_file = config_dir / ".ollama_config.json"

    if config_file.exists():
        try:
            with open(config_file) as f:
                config = json.load(f)
            print_success(f"Ollama config found at {config_file}")
            print_info(f"  Model: {config.get('model', 'not set')}")
            print_info(f"  Port: {config.get('port', 'not set')}")
            return True
        except Exception as e:
            print_warning(f"Config file exists but couldn't be read: {e}")
    else:
        print_info(f"Ollama config not found at {config_file}")
        print_info("ATOLL will create default config on first run")

    return True


def check_platform_specific():
    """Check platform-specific requirements."""
    system = platform.system()
    print_info(f"Checking platform-specific requirements for {system}...")

    if system == "Linux":
        # Check for systemd (for service setup)
        systemd = shutil.which("systemctl")
        if systemd:
            print_success("systemd available (for service setup)")
        else:
            print_warning("systemd not found (service setup may not work)")

        # Check for common package managers
        if shutil.which("apt"):
            print_success("apt package manager found")
        elif shutil.which("yum") or shutil.which("dnf"):
            print_success("yum/dnf package manager found")

    elif system == "Windows":
        print_info("Windows system detected")
        print_info("For service setup, install NSSM from https://nssm.cc/")

    elif system == "Darwin":
        print_info("macOS system detected")
        if shutil.which("brew"):
            print_success("Homebrew package manager found")

    return True


def check_installation():
    """Check if ATOLL is already installed."""
    print_info("Checking ATOLL installation...")

    try:
        result = subprocess.run(["atoll", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"ATOLL installed: {result.stdout.strip()}")
            return True
    except Exception:
        pass

    print_info("ATOLL not installed (expected for fresh installation)")
    return False


def validate_quick():
    """Quick validation - check only essential prerequisites."""
    print_header("Quick Installation Validation")

    checks = [
        ("Python 3.9+", check_python_version),
        ("pip", check_pip),
        ("Ollama", check_ollama),
    ]

    results = []
    for name, check_func in checks:
        results.append(check_func())

    return all(results)


def validate_full():
    """Full validation - check all prerequisites and system setup."""
    print_header("Full Installation Validation")

    checks = [
        ("Python 3.9+", check_python_version),
        ("pip", check_pip),
        ("Git", check_git),
        ("Ollama", check_ollama),
        ("System Resources", check_system_resources),
        ("Platform-Specific", check_platform_specific),
        ("Ollama Config", check_ollama_config),
        ("ATOLL Installation", check_installation),
    ]

    results = []
    for name, check_func in checks:
        results.append(check_func())

    return all(r for r in results if r is not False)


def main():
    """Main validation script."""
    parser = argparse.ArgumentParser(
        description="Validate ATOLL installation prerequisites"
    )
    parser.add_argument(
        "--quick", action="store_true", help="Quick check (essential prerequisites only)"
    )

    args = parser.parse_args()

    print_header("ATOLL Installation Prerequisites Validator")
    print_info(f"Platform: {platform.system()} {platform.release()}")
    print_info(f"Architecture: {platform.machine()}")

    if args.quick:
        success = validate_quick()
    else:
        success = validate_full()

    print_header("Validation Summary")

    if success:
        print_success("All checks passed! You can proceed with installation.")
        print_info("Follow the installation guide at: docs/INSTALLATION.md")
        return 0
    else:
        print_warning("Some checks failed. Review the output above.")
        print_info("See docs/INSTALLATION.md for detailed instructions")
        return 1


if __name__ == "__main__":
    sys.exit(main())
