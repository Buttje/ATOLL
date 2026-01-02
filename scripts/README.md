# ATOLL Scripts

This directory contains utility scripts for installation, validation, and maintenance of ATOLL.

## Available Scripts

### Installation

#### `install.py`
Automated installation script with guided setup.

**Usage:**
```bash
python install.py
```

**Features:**
- Interactive installation wizard
- Virtual environment or system-wide installation
- Custom agents directory configuration
- Automatic dependency installation
- Pre-commit hooks setup

**Options:**
- Choose between venv or host system installation
- Configure custom agents directory
- Automatic pip upgrade

---

### Validation

#### `validate_installation.py`
Validates installation prerequisites and system requirements.

**Usage:**
```bash
# Quick check (essential prerequisites only)
python scripts/validate_installation.py --quick

# Full validation (all checks)
python scripts/validate_installation.py
```

**Checks:**
- Python version (3.9+)
- pip availability
- Git installation (optional)
- Ollama installation and server status
- System resources (RAM, disk space)
- Platform-specific requirements (systemd, package managers)
- Existing Ollama configuration
- ATOLL installation status

**Exit Codes:**
- `0` - All checks passed
- `1` - One or more checks failed

**Example Output:**
```
============================================================
ATOLL Installation Prerequisites Validator
============================================================

ℹ Platform: Linux 5.15.0
ℹ Architecture: x86_64

============================================================
Quick Installation Validation
============================================================

✓ Python 3.11.0 (requirement: 3.9+)
✓ pip found: pip 23.0
✓ Ollama found: ollama version 0.1.0
✓ Ollama server is running
ℹ Available models: llama2, mistral

============================================================
Validation Summary
============================================================

✓ All checks passed! You can proceed with installation.
```

---

## Usage in Installation Workflow

### Recommended Installation Flow

1. **Validate Prerequisites**
   ```bash
   python scripts/validate_installation.py --quick
   ```

2. **Install ATOLL**
   ```bash
   python install.py
   ```

3. **Verify Installation**
   ```bash
   atoll --version
   python scripts/validate_installation.py
   ```

---

## Platform-Specific Notes

### Linux

All scripts are designed to work on Linux systems with Python 3.9+. Tested on:
- Ubuntu 20.04, 22.04, 24.04
- Debian 11, 12
- Fedora 38+
- CentOS 8+

### Windows

Scripts work on Windows with Python 3.9+ installed. Tested on:
- Windows 10 (build 19041+)
- Windows 11
- Windows Server 2019, 2022

**Note:** Use Command Prompt or PowerShell to run scripts.

### macOS

Scripts work on macOS with Python 3.9+ installed. Tested on:
- macOS Monterey (12.x)
- macOS Ventura (13.x)
- macOS Sonoma (14.x)

---

## Development Scripts

For contributors, additional development scripts:

#### `build_executable.py`
Build standalone executables using PyInstaller for distribution.

**Usage:**
```bash
# Build for current platform
python scripts/build_executable.py

# Build for specific platform
python scripts/build_executable.py --platform windows
python scripts/build_executable.py --platform linux
python scripts/build_executable.py --platform macos

# Build without cleaning first
python scripts/build_executable.py --no-clean
```

**Features:**
- Single-file executable with embedded Python runtime
- Includes all dependencies
- Cross-platform support (Windows .exe, Linux/macOS binary)
- Automatic PyInstaller spec file generation
- Size optimization with UPX compression

**Requirements:**
```bash
pip install pyinstaller
```

**Output:**
- Executable in `dist/` directory
- Target size: <100 MB (compressed)
- Platform: Windows (.exe), Linux, or macOS

---

### Future Development Scripts

- Linting and formatting scripts
- Database migration scripts
- Testing utilities

---

## Contributing

When adding new scripts:

1. Add a clear docstring at the top of the file
2. Include usage examples in comments
3. Update this README with script description
4. Make scripts executable on Linux/macOS: `chmod +x script.py`
5. Use `#!/usr/bin/env python3` shebang for cross-platform compatibility
6. Follow the project's coding standards (black, ruff)

---

## Support

For issues with installation scripts:

1. Check the [Installation Guide](../docs/INSTALLATION.md)
2. Review [Troubleshooting](../docs/INSTALLATION.md#troubleshooting)
3. Open an issue: https://github.com/Buttje/ATOLL/issues

---

**Last Updated:** January 2025  
**Version:** 2.0.0
