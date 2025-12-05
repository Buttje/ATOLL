"""Installation script for Ollama MCP Agent."""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description, ignore_errors=False):
    """Run a command and handle errors."""
    print(f"\n{description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0 and not ignore_errors:
            # Check if it's just a pip notice
            if "notice" in result.stderr.lower() and "pip" in result.stderr.lower():
                print(f"✓ {description} completed (with pip update notice)")
                return True
            print(f"Error: {result.stderr}")
            return False
        print(f"✓ {description} completed")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """Main installation process."""
    print("=" * 60)
    print("Ollama MCP Agent Installation")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("Error: Python 3.9+ is required")
        sys.exit(1)
    
    print(f"Python {sys.version}")
    
    # Check if venv already exists
    venv_path = Path("venv")
    if not venv_path.exists():
        # Create virtual environment
        if not run_command("python -m venv venv", "Creating virtual environment"):
            sys.exit(1)
    else:
        print("✓ Virtual environment already exists")
    
    # Determine activation script and pip path
    if os.name == 'nt':  # Windows
        python = "venv\\Scripts\\python.exe"
        pip = "venv\\Scripts\\pip.exe"
    else:  # Unix/Linux/Mac
        python = "venv/bin/python"
        pip = "venv/bin/pip"
    
    # Upgrade pip (ignore errors as it's optional)
    run_command(f"{python} -m pip install --upgrade pip", "Upgrading pip", ignore_errors=True)
    
    # Install package in editable mode with dev dependencies
    if not run_command(f"{pip} install -e \".[dev]\"", "Installing package"):
        sys.exit(1)
    
    # Install pre-commit hooks (optional)
    if os.name == 'nt':
        pre_commit_cmd = "venv\\Scripts\\pre-commit.exe install"
    else:
        pre_commit_cmd = "venv/bin/pre-commit install"
    
    run_command(pre_commit_cmd, "Installing pre-commit hooks", ignore_errors=True)
    
    print("\n" + "=" * 60)
    print("✓ Installation complete!")
    print("\nTo activate the environment:")
    if os.name == 'nt':
        print("  venv\\Scripts\\activate")
    else:
        print("  source venv/bin/activate")
    print("\nTo run the agent:")
    print("  ollama-mcp-agent")
    print("=" * 60)


if __name__ == "__main__":
    main()