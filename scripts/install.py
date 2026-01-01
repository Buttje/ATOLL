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


def create_default_configs():
    """Create default configuration files if they don't exist."""
    # Create ~/.atoll directory and mcp.json if they don't exist
    atoll_config_dir = Path.home() / ".atoll"
    atoll_config_dir.mkdir(parents=True, exist_ok=True)

    mcp_config_path = atoll_config_dir / "mcp.json"
    if not mcp_config_path.exists():
        default_mcp_config = {"servers": {}}
        try:
            with open(mcp_config_path, "w") as f:
                json.dump(default_mcp_config, f, indent=2)
            print(f"[OK] Created default mcp.json at {mcp_config_path}")
        except Exception as e:
            print(f"[WARN] Could not create mcp.json: {e}")
    else:
        print(f"[OK] mcp.json already exists at {mcp_config_path}")

    # Check if .ollama_config.json exists in ~/.ollama_server/
    ollama_config_dir = Path.home() / ".ollama_server"
    ollama_config_path = ollama_config_dir / ".ollama_config.json"

    if ollama_config_path.exists():
        print("[OK] .ollama_config.json already exists (leaving untouched)")
    else:
        print("[INFO] .ollama_config.json does not exist (will be created on first run)")


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


def main():
    """Main installation process."""
    print("=" * 60)
    print("ATOLL Installation")
    print("=" * 60)

    # Check Python version
    if sys.version_info < (3, 9):  # noqa: UP036
        print("Error: Python 3.9+ is required")
        sys.exit(1)

    print(f"Python {sys.version}")

    # Create default configuration files
    print("\nChecking configuration files...")
    create_default_configs()

    # Ask for agents directory location
    agents_dir = get_agents_directory()
    if agents_dir:
        save_agents_config(agents_dir)

    # Check if venv already exists and is functional
    venv_path = Path("venv")
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
            print("[WARN] Virtual environment exists but is incomplete, recreating...")
            # Remove incomplete venv
            shutil.rmtree(venv_path)

    if not venv_valid and not run_command("python -m venv venv", "Creating virtual environment"):
        sys.exit(1)

    # Determine activation script and pip path
    if os.name == "nt":  # Windows
        python = "venv\\Scripts\\python.exe"
        pip = "venv\\Scripts\\pip.exe"
    else:  # Unix/Linux/Mac
        python = "venv/bin/python"
        pip = "venv/bin/pip"

    # Upgrade pip (ignore errors as it's optional)
    run_command(f"{python} -m pip install --upgrade pip", "Upgrading pip", ignore_errors=True)

    # Install package in editable mode with dev dependencies
    if not run_command(f'{pip} install -e ".[dev]"', "Installing package"):
        sys.exit(1)

    # Install pre-commit hooks (optional)
    if os.name == "nt":
        pre_commit_cmd = "venv\\Scripts\\pre-commit.exe install"
    else:
        pre_commit_cmd = "venv/bin/pre-commit install"

    run_command(pre_commit_cmd, "Installing pre-commit hooks", ignore_errors=True)

    print("\n" + "=" * 60)
    print("[OK] Installation complete!")
    print("\nTo activate the environment:")
    if os.name == "nt":
        print("  venv\\Scripts\\activate")
    else:
        print("  source venv/bin/activate")
    print("\nTo run the agent:")
    print("  atoll")
    print("=" * 60)


if __name__ == "__main__":
    main()
