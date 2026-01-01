"""Installation script for ATOLL."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def get_agents_directory():
    """Ask user for ATOLL agents directory location."""
    print("\n" + "=" * 60)
    print("ATOLL Agents Directory Configuration")
    print("=" * 60)
    print("\nATOLL agents are specialized plugins that extend capabilities.")
    print("You can store them in a custom location for easier management.")
    print("\nOptions:")
    print("  1. Use default location (package installation directory)")
    print("  2. Specify a custom directory path")
    print()

    while True:
        choice = input("Enter your choice (1 or 2): ").strip()
        if choice == "1":
            return None  # None means use default
        elif choice == "2":
            while True:
                path = input("\nEnter the full path for agents directory: ").strip()
                if not path:
                    print("Path cannot be empty. Please try again.")
                    continue

                # Expand user path (~ on Unix)
                path = os.path.expanduser(path)
                agents_path = Path(path)

                # Ask if user wants to create it if it doesn't exist
                if not agents_path.exists():
                    create = (
                        input(f"Directory '{agents_path}' does not exist. Create it? (y/n): ")
                        .strip()
                        .lower()
                    )
                    if create == "y":
                        try:
                            agents_path.mkdir(parents=True, exist_ok=True)
                            print(f"[OK] Created directory: {agents_path}")
                            return str(agents_path)
                        except Exception as e:
                            print(f"[ERROR] Failed to create directory: {e}")
                            continue
                    else:
                        continue
                else:
                    print(f"[OK] Using directory: {agents_path}")
                    return str(agents_path)
        else:
            print("Invalid choice. Please enter 1 or 2.")


def save_agents_config(agents_dir):
    """Save agents directory configuration."""
    config_dir = Path.home() / ".atoll"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "atoll.json"

    config = {}
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
        except:
            pass

    config["agents_directory"] = agents_dir

    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        print(f"[OK] Saved agents configuration to {config_path}")
        return True
    except Exception as e:
        print(f"[WARNING] Could not save agents config: {e}")
        return False


def run_command(cmd, description, ignore_errors=False):
    """Run a command and handle errors."""
    print(f"\n{description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0 and not ignore_errors:
            # Check if it's just a pip notice
            if "notice" in result.stderr.lower() and "pip" in result.stderr.lower():
                print(f"[OK] {description} completed (with pip update notice)")
                return True
            print(f"Error: {result.stderr}")
            return False
        print(f"[OK] {description} completed")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def get_user_choice():
    """Ask user to choose installation type."""
    print("\nInstallation Options:")
    print("  1. Install in virtual environment (recommended)")
    print("  2. Install on host system")
    print()

    while True:
        choice = input("Enter your choice (1 or 2): ").strip()
        if choice in ["1", "2"]:
            return choice == "1"
        print("Invalid choice. Please enter 1 or 2.")


def install_in_venv():
    """Install ATOLL in a virtual environment."""
    print("\n==> Installing in virtual environment...")

    # Check if venv already exists and is functional
    venv_path = Path(".venv")
    venv_valid = False

    if venv_path.exists():
        # Verify that critical executables exist
        if os.name == "nt":  # Windows
            python_exe = venv_path / "Scripts" / "python.exe"
            pip_exe = venv_path / "Scripts" / "pip.exe"
        else:  # Unix/Linux/Mac
            python_exe = venv_path / "bin" / "python"
            pip_exe = venv_path / "bin" / "pip"

        if python_exe.exists() and pip_exe.exists():
            venv_valid = True
            print("[OK] Virtual environment already exists")
        else:
            print("[WARNING] Virtual environment exists but is incomplete, recreating...")
            # Remove incomplete venv
            shutil.rmtree(venv_path)

    if not venv_valid and not run_command("python -m venv .venv", "Creating virtual environment"):
        return False

    # Determine activation script and pip path
    if os.name == "nt":  # Windows
        python = ".venv\\Scripts\\python.exe"
        pip = ".venv\\Scripts\\pip.exe"
        activate_cmd = ".venv\\Scripts\\activate"
    else:  # Unix/Linux/Mac
        python = ".venv/bin/python"
        pip = ".venv/bin/pip"
        activate_cmd = "source .venv/bin/activate"

    # Upgrade pip (ignore errors as it's optional)
    run_command(f"{python} -m pip install --upgrade pip", "Upgrading pip", ignore_errors=True)

    # Install package in editable mode with dev dependencies
    if not run_command(f'{pip} install -e ".[dev]"', "Installing ATOLL with dev dependencies"):
        return False

    # Install pre-commit hooks (optional)
    if os.name == "nt":
        pre_commit_cmd = ".venv\\Scripts\\pre-commit.exe install"
    else:
        pre_commit_cmd = ".venv/bin/pre-commit install"

    run_command(pre_commit_cmd, "Installing pre-commit hooks", ignore_errors=True)

    print("\n" + "=" * 60)
    print("[OK] Installation complete!")
    print("\nTo activate the environment:")
    print(f"  {activate_cmd}")
    print("\nTo run ATOLL:")
    print("  atoll")
    print("=" * 60)
    return True


def install_on_host():
    """Install ATOLL on the host system."""
    print("\n==> Installing on host system...")

    # Get system python and pip
    python = sys.executable

    # Upgrade pip (ignore errors as it's optional)
    run_command(f"{python} -m pip install --upgrade pip", "Upgrading pip", ignore_errors=True)

    # Install package in editable mode with dev dependencies
    if not run_command(
        f'{python} -m pip install -e ".[dev]"', "Installing ATOLL with dev dependencies"
    ):
        return False

    # Install pre-commit hooks (optional)
    run_command("pre-commit install", "Installing pre-commit hooks", ignore_errors=True)

    print("\n" + "=" * 60)
    print("[OK] Installation complete!")
    print("\nTo run ATOLL:")
    print("  atoll")
    print("=" * 60)
    return True


def main():
    """Main installation process."""
    print("=" * 60)
    print("ATOLL - Agentic Tools Orchestration on OLLama")
    print("Installation Script")
    print("=" * 60)

    # Check Python version
    if sys.version_info < (3, 9):  # noqa: UP036
        print("Error: Python 3.9+ is required")
        print(f"Current version: Python {sys.version}")
        sys.exit(1)

    print(f"[OK] Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    # Ask for agents directory location
    agents_dir = get_agents_directory()
    if agents_dir:
        save_agents_config(agents_dir)

    # Ask user for installation preference
    use_venv = get_user_choice()

    # Perform installation based on user choice
    success = install_in_venv() if use_venv else install_on_host()

    if not success:
        print("\n[ERROR] Installation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
