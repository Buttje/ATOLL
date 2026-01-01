# ATOLL Installation Guide

**Version:** 2.0.0  
**Last Updated:** January 2026

This comprehensive guide covers installation of ATOLL on Linux and Windows platforms, including prerequisites, installation methods, configuration, and running as a system service.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Platform-Specific Prerequisites](#platform-specific-prerequisites)
3. [Installation Methods](#installation-methods)
   - [Method 1: Using pip (Recommended)](#method-1-using-pip-recommended)
   - [Method 2: Automated Installer](#method-2-automated-installer)
   - [Method 3: Manual Installation from Source](#method-3-manual-installation-from-source)
4. [Configuration](#configuration)
5. [Running ATOLL](#running-atoll)
6. [Running as a System Service](#running-as-a-system-service)
   - [Linux (systemd)](#linux-systemd)
   - [Windows Service](#windows-service)
7. [Deployment Server Setup](#deployment-server-setup)
8. [Verification](#verification)
9. [Troubleshooting](#troubleshooting)
10. [Uninstallation](#uninstallation)

---

## Prerequisites

Before installing ATOLL, ensure you have the following:

### Required Software

1. **Python 3.9 or higher**
   - Check version: `python --version` or `python3 --version`
   - Download from: https://www.python.org/downloads/

2. **pip** (Python package manager)
   - Usually included with Python
   - Check version: `pip --version` or `pip3 --version`
   - Upgrade if needed: `python -m pip install --upgrade pip`

3. **Ollama** (Local LLM runtime)
   - Download and install from: https://ollama.ai/
   - Verify installation: `ollama --version`

### Optional but Recommended

- **Git** - For cloning repository and version control
- **Virtual Environment** - For isolated Python environment (venv, conda, etc.)

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Linux, Windows, macOS | Ubuntu 24.04 LTS, Windows 11 |
| **RAM** | 8 GB | 16 GB |
| **Disk Space** | 2 GB (+ LLM models) | 10 GB+ |
| **CPU** | 2 cores | 4+ cores |
| **Network** | Required for model downloads | Stable broadband |

---

## Platform-Specific Prerequisites

### Linux (Ubuntu 24.04 / Debian-based)

1. **Update System Packages**
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```

2. **Install Python and Development Tools**
   ```bash
   sudo apt install -y python3 python3-pip python3-venv git build-essential
   ```

3. **Install Ollama**
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

4. **Verify Ollama Service**
   ```bash
   # Check if Ollama service is running
   systemctl status ollama
   
   # If not running, start it
   sudo systemctl start ollama
   sudo systemctl enable ollama
   ```

5. **Configure Firewall (if applicable)**
   ```bash
   # Allow Ollama port
   sudo ufw allow 11434/tcp
   
   # Allow ATOLL deployment server port (optional)
   sudo ufw allow 8080/tcp
   ```

### Windows 11

1. **Install Python**
   - Download Python 3.9+ from https://www.python.org/downloads/
   - During installation:
     - ✅ Check "Add Python to PATH"
     - ✅ Check "Install pip"
   - Verify in PowerShell/CMD:
     ```powershell
     python --version
     pip --version
     ```

2. **Install Ollama**
   - Download installer from https://ollama.ai/download/windows
   - Run the installer
   - Verify installation:
     ```powershell
     ollama --version
     ```

3. **Install Git (Optional)**
   - Download from https://git-scm.com/download/win
   - Use default settings during installation

4. **Configure Windows Defender Firewall**
   - Ollama typically configures firewall rules automatically
   - If needed, manually allow port 11434:
     ```powershell
     # Run as Administrator
     New-NetFirewallRule -DisplayName "Ollama" -Direction Inbound -Protocol TCP -LocalPort 11434 -Action Allow
     ```

5. **Install NSSM (for Windows Service - Optional)**
   - Download from https://nssm.cc/download
   - Extract to a folder (e.g., `C:\nssm`)
   - Add to PATH or use full path when calling

---

## Installation Methods

### Method 1: Using pip (Recommended)

> **Note:** This method will be available once ATOLL is published to PyPI.

**For Production Use:**
```bash
# Install ATOLL from PyPI
pip install atoll

# Or install in a virtual environment
python -m venv atoll-env
source atoll-env/bin/activate  # On Windows: atoll-env\Scripts\activate
pip install atoll
```

**For Development:**
```bash
pip install atoll[dev]
```

### Method 2: Automated Installer

This method uses the included installation script for a guided setup.

#### Linux

```bash
# Clone the repository
git clone https://github.com/Buttje/ATOLL.git
cd ATOLL

# Run the installer
python install.py
```

The installer will:
1. Check Python version (requires 3.9+)
2. Ask for agents directory location
3. Offer virtual environment or system-wide installation
4. Install ATOLL and dependencies
5. Set up pre-commit hooks (optional)

#### Windows

```powershell
# Clone the repository
git clone https://github.com/Buttje/ATOLL.git
cd ATOLL

# Run the installer
python install.py
```

### Method 3: Manual Installation from Source

For maximum control over the installation process.

#### Linux

```bash
# 1. Clone the repository
git clone https://github.com/Buttje/ATOLL.git
cd ATOLL

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Upgrade pip
pip install --upgrade pip

# 5. Install ATOLL in editable mode
pip install -e ".[dev]"

# 6. Install pre-commit hooks (optional)
pre-commit install

# 7. Verify installation
atoll --version  # Should show version 2.0.0
```

#### Windows

```powershell
# 1. Clone the repository
git clone https://github.com/Buttje/ATOLL.git
cd ATOLL

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
venv\Scripts\activate

# 4. Upgrade pip
python -m pip install --upgrade pip

# 5. Install ATOLL in editable mode
pip install -e ".[dev]"

# 6. Install pre-commit hooks (optional)
pre-commit install

# 7. Verify installation
atoll --version  # Should show version 2.0.0
```

---

## Configuration

ATOLL requires two configuration files:

### 1. Ollama Configuration

**Location:** `~/.ollama_server/.ollama_config.json` (Linux/macOS)  
**Location:** `%USERPROFILE%\.ollama_server\.ollama_config.json` (Windows)

ATOLL will create this directory and a default configuration on first run, but you can create it manually:

#### Linux/macOS

```bash
# Create configuration directory
mkdir -p ~/.ollama_server

# Create configuration file
cat > ~/.ollama_server/.ollama_config.json <<EOF
{
  "base_url": "http://localhost",
  "port": 11434,
  "model": "llama2",
  "request_timeout": 30,
  "max_tokens": 2048
}
EOF
```

#### Windows (PowerShell)

```powershell
# Create configuration directory
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.ollama_server"

# Create configuration file
@"
{
  "base_url": "http://localhost",
  "port": 11434,
  "model": "llama2",
  "request_timeout": 30,
  "max_tokens": 2048
}
"@ | Out-File -FilePath "$env:USERPROFILE\.ollama_server\.ollama_config.json" -Encoding UTF8
```

**Configuration Options:**

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `base_url` | string | Ollama server URL | `http://localhost` |
| `port` | integer | Ollama server port | `11434` |
| `model` | string | LLM model name | `llama2` |
| `request_timeout` | integer | Request timeout (seconds) | `30` |
| `max_tokens` | integer | Max generation tokens | `2048` |

### 2. MCP Configuration (Optional)

**Location:** `mcp.json` (in working directory)

Create an MCP configuration file to connect to MCP servers:

```json
{
  "servers": {
    "example-stdio-server": {
      "type": "stdio",
      "command": "python",
      "args": ["path/to/server.py"],
      "cwd": "${workspaceFolder}",
      "env": {
        "API_KEY": "your-key-here"
      }
    },
    "example-http-server": {
      "type": "http",
      "url": "http://localhost:8080/mcp",
      "headers": {
        "Authorization": "Bearer token"
      }
    }
  }
}
```

**Server Types:**

- **`stdio`**: Process-based communication (local executables/scripts)
  - Required: `command`
  - Optional: `args`, `env`, `cwd`, `envFile`
- **`http`**: HTTP-based communication
  - Required: `url`
  - Optional: `headers`, `timeout`
- **`sse`**: Server-Sent Events (streaming)
  - Required: `url`
  - Optional: `headers`, `timeout`

> **Tip:** Start with an empty `servers` object if you don't have MCP servers yet: `{"servers": {}}`

### 3. Pull an Ollama Model

Before using ATOLL, download at least one model:

```bash
# Popular models
ollama pull llama2          # General purpose (3.8GB)
ollama pull mistral         # Fast and capable (4.1GB)
ollama pull codellama       # Code-focused (3.8GB)
ollama pull llama2:13b      # Larger model (7.3GB)

# List available models
ollama list
```

---

## Running ATOLL

### Interactive Mode

Start ATOLL in interactive terminal mode:

```bash
# Using the command-line entry point
atoll

# Or as a Python module
python -m atoll
```

**On First Run:**
- ATOLL checks Ollama server connectivity
- Verifies configured model availability
- Displays startup status and warnings

**Interface Modes:**

1. **Prompt Mode** (default): Natural language interaction
   ```
   💬 Enter prompt: Analyze this function
   ```

2. **Command Mode** (press ESC): System commands
   ```
   ⚡ Enter command: Models
   ```

**Available Commands:**

| Command | Description |
|---------|-------------|
| `Models` | List available Ollama models |
| `ChangeModel <model>` | Switch to a different model |
| `SetServer <url> [port]` | Configure Ollama server |
| `Servers` | List connected MCP servers |
| `Tools` | List available MCP tools |
| `help [server\|tool] <name>` | Get help information |
| `Clear` | Clear conversation memory |
| `Quit` / `Exit` | Exit application |

---

## Running as a System Service

For production deployments, run ATOLL as a system service that starts automatically on boot.

### Linux (systemd)

#### 1. Create Service File

```bash
sudo nano /etc/systemd/system/atoll.service
```

**Service Configuration:**

```ini
[Unit]
Description=ATOLL - Agentic Tools Orchestration on OLLama
After=network.target ollama.service
Wants=ollama.service

[Service]
Type=simple
User=atoll
Group=atoll
WorkingDirectory=/opt/atoll
Environment="PATH=/opt/atoll/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/opt/atoll/venv/bin/python -m atoll
Restart=on-failure
RestartSec=10s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### 2. Create Service User (Recommended)

```bash
# Create system user for ATOLL
sudo useradd -r -s /bin/false atoll

# Create installation directory
sudo mkdir -p /opt/atoll
sudo chown atoll:atoll /opt/atoll
```

#### 3. Install ATOLL for Service User

```bash
# Switch to service user
sudo -u atoll -s

# Navigate to installation directory
cd /opt/atoll

# Clone and install (or copy existing installation)
git clone https://github.com/Buttje/ATOLL.git .
python3 -m venv venv
source venv/bin/activate
pip install -e .

# Create configuration
mkdir -p ~/.ollama_server
# ... (create config files as shown above)

# Exit service user shell
exit
```

#### 4. Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable atoll.service

# Start service
sudo systemctl start atoll.service

# Check status
sudo systemctl status atoll.service

# View logs
sudo journalctl -u atoll.service -f
```

#### 5. Service Management Commands

```bash
# Start
sudo systemctl start atoll.service

# Stop
sudo systemctl stop atoll.service

# Restart
sudo systemctl restart atoll.service

# Status
sudo systemctl status atoll.service

# Enable auto-start
sudo systemctl enable atoll.service

# Disable auto-start
sudo systemctl disable atoll.service

# View logs (live)
sudo journalctl -u atoll.service -f

# View recent logs
sudo journalctl -u atoll.service -n 100
```

### Windows Service

#### Method 1: Using NSSM (Recommended)

NSSM (Non-Sucking Service Manager) is the easiest way to create Windows services.

**1. Install NSSM**

Download from https://nssm.cc/download and extract to `C:\nssm`.

**2. Create Service**

Open PowerShell or CMD as Administrator:

```powershell
# Navigate to NSSM directory
cd C:\nssm\win64

# Install ATOLL as a service
.\nssm.exe install ATOLL "C:\Python39\python.exe" "-m atoll"

# Configure service
.\nssm.exe set ATOLL AppDirectory "C:\ATOLL"
.\nssm.exe set ATOLL DisplayName "ATOLL Agent"
.\nssm.exe set ATOLL Description "Agentic Tools Orchestration on OLLama"
.\nssm.exe set ATOLL Start SERVICE_AUTO_START

# Set output logging (optional)
.\nssm.exe set ATOLL AppStdout "C:\ATOLL\logs\atoll-stdout.log"
.\nssm.exe set ATOLL AppStderr "C:\ATOLL\logs\atoll-stderr.log"

# Start service
.\nssm.exe start ATOLL
```

**3. Service Management**

```powershell
# Start service
Start-Service ATOLL

# Stop service
Stop-Service ATOLL

# Restart service
Restart-Service ATOLL

# Check status
Get-Service ATOLL

# View service details
.\nssm.exe status ATOLL

# Remove service
.\nssm.exe remove ATOLL confirm
```

#### Method 2: Using sc.exe (Advanced)

Built-in Windows service management tool.

**Create Service:**

```powershell
# Open PowerShell as Administrator
sc.exe create ATOLL binPath= "C:\Python39\python.exe -m atoll" start= auto
sc.exe description ATOLL "Agentic Tools Orchestration on OLLama"

# Start service
sc.exe start ATOLL

# Query service status
sc.exe query ATOLL
```

**Service Management:**

```powershell
# Start
sc.exe start ATOLL

# Stop
sc.exe stop ATOLL

# Delete service
sc.exe delete ATOLL
```

---

## Deployment Server Setup

ATOLL v2.0 includes a REST API deployment server for remote agent management.

### Configuration

Add deployment server configuration to ATOLL config:

**`~/.atoll/atoll.json`** (create if it doesn't exist):

```json
{
  "deployment_server": {
    "enabled": true,
    "host": "localhost",
    "api_port": 8080,
    "base_port": 8100,
    "max_agents": 10,
    "agents_directory": "/path/to/agents",
    "restart_on_failure": true
  }
}
```

### Starting Deployment Server

```bash
# Start ATOLL with deployment server enabled
atoll --deployment-server

# Or via Python
python -m atoll.deployment.api
```

### Using Deployment API

The REST API is available at `http://localhost:8080` by default.

**Health Check:**
```bash
curl http://localhost:8080/health
```

**List Agents:**
```bash
curl http://localhost:8080/agents
```

See [Deployment Server V2 Usage Guide](DEPLOYMENT_SERVER_V2_USAGE.md) for full API documentation.

---

## Verification

### Test Installation

```bash
# 1. Check ATOLL version
atoll --version

# 2. Test Ollama connection
ollama list

# 3. Start ATOLL in test mode
atoll
# Press ESC to enter command mode
# Type: Models
# You should see available Ollama models

# Type: SetServer http://localhost 11434
# Should confirm connection

# Type: Quit to exit
```

### Run Tests (Development Installation)

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

# Run test suite
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Open coverage report
# Linux/macOS: open htmlcov/index.html
# Windows: start htmlcov/index.html
```

### Verify Service (if installed)

**Linux:**
```bash
sudo systemctl status atoll.service
sudo journalctl -u atoll.service -n 50
```

**Windows:**
```powershell
Get-Service ATOLL
Get-EventLog -LogName Application -Source ATOLL -Newest 10
```

---

## Troubleshooting

### Installation Issues

#### Problem: "pip: command not found"

**Solution:**
```bash
# Linux
sudo apt install python3-pip

# Windows - Reinstall Python with pip checkbox enabled
```

#### Problem: "Permission denied" during installation

**Solution (Linux):**
```bash
# Use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -e .

# Or install to user directory
pip install --user -e .
```

**Solution (Windows):**
- Run Command Prompt/PowerShell as Administrator
- Or use virtual environment

#### Problem: Module import errors

**Solution:**
```bash
# Reinstall with all dependencies
pip install --upgrade --force-reinstall -e ".[dev]"

# Check installed packages
pip list | grep atoll
```

### Runtime Issues

#### Problem: "Cannot reach Ollama server"

**Symptoms:**
```
✗ Cannot reach Ollama server at http://localhost:11434
```

**Solutions:**

1. **Check if Ollama is running:**
   ```bash
   # Linux
   systemctl status ollama
   sudo systemctl start ollama
   
   # Windows - Check Task Manager for "Ollama" process
   # If not running, start from Start Menu
   ```

2. **Verify Ollama port:**
   ```bash
   # Linux/macOS
   netstat -an | grep 11434
   
   # Windows
   netstat -an | findstr 11434
   ```

3. **Test Ollama API:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

4. **Update ATOLL config:**
   ```bash
   # In ATOLL command mode:
   SetServer http://localhost 11434
   ```

#### Problem: "Model not found" or model unavailable

**Solution:**
```bash
# List available models
ollama list

# Pull missing model
ollama pull llama2

# In ATOLL, change model
# Command mode: ChangeModel llama2
```

#### Problem: Port conflicts (deployment server)

**Symptoms:**
```
Error: Address already in use: 8080
```

**Solution:**

1. **Find process using port:**
   ```bash
   # Linux/macOS
   lsof -i :8080
   sudo netstat -tulpn | grep :8080
   
   # Windows
   netstat -ano | findstr :8080
   ```

2. **Kill conflicting process:**
   ```bash
   # Linux/macOS
   kill -9 <PID>
   
   # Windows (as Administrator)
   taskkill /PID <PID> /F
   ```

3. **Or configure different port:**
   Edit `~/.atoll/atoll.json` and change `api_port`.

#### Problem: Service won't start (Linux)

**Diagnosis:**
```bash
# Check service status
sudo systemctl status atoll.service

# View detailed logs
sudo journalctl -u atoll.service -n 100 --no-pager

# Check service file syntax
sudo systemd-analyze verify atoll.service
```

**Common Fixes:**
1. Check paths in service file are correct
2. Verify user/group exists: `id atoll`
3. Check permissions: `ls -l /opt/atoll`
4. Ensure virtual environment is activated in ExecStart

#### Problem: Service won't start (Windows)

**Diagnosis:**
```powershell
# Check service status
Get-Service ATOLL | Format-List *

# View event logs
Get-EventLog -LogName Application -Source ATOLL -Newest 10
```

**Common Fixes:**
1. Verify Python path in service configuration
2. Run NSSM GUI: `nssm.exe edit ATOLL`
3. Check log files at configured locations
4. Ensure user has permissions to Python and ATOLL directories

### MCP Server Issues

#### Problem: MCP server connection failed

**Solution:**

1. **Verify MCP config:**
   ```bash
   # Check mcp.json syntax
   python -m json.tool mcp.json
   ```

2. **Test MCP server independently:**
   ```bash
   # For stdio server
   python path/to/server.py
   ```

3. **Check environment variables:**
   - Ensure `${workspaceFolder}` and other variables resolve correctly
   - Use absolute paths for testing

4. **Review ATOLL logs:**
   - Look for MCP connection errors
   - Check server output in stderr

### Performance Issues

#### Problem: Slow response times

**Solutions:**

1. **Use smaller/faster models:**
   ```bash
   ollama pull mistral  # Generally faster than llama2
   ```

2. **Check system resources:**
   ```bash
   # Linux
   htop
   free -h
   
   # Windows
   # Open Task Manager (Ctrl+Shift+Esc)
   ```

3. **Adjust timeout in config:**
   ```json
   {
     "request_timeout": 60,
     "max_tokens": 1024
   }
   ```

4. **Use GPU acceleration (if available):**
   - Ensure Ollama uses GPU: `ollama info`

---

## Uninstallation

### Remove ATOLL

**pip installation:**
```bash
pip uninstall atoll
```

**Source installation:**
```bash
# Navigate to ATOLL directory
cd ATOLL

# Uninstall
pip uninstall atoll

# Remove directory
cd ..
rm -rf ATOLL  # Linux/macOS
# OR
rmdir /s ATOLL  # Windows
```

### Remove Service

**Linux:**
```bash
# Stop and disable service
sudo systemctl stop atoll.service
sudo systemctl disable atoll.service

# Remove service file
sudo rm /etc/systemd/system/atoll.service

# Reload systemd
sudo systemctl daemon-reload

# Remove service user and files (optional)
sudo userdel atoll
sudo rm -rf /opt/atoll
```

**Windows (NSSM):**
```powershell
# Stop and remove service
C:\nssm\win64\nssm.exe stop ATOLL
C:\nssm\win64\nssm.exe remove ATOLL confirm
```

**Windows (sc.exe):**
```powershell
# Stop and delete service
sc.exe stop ATOLL
sc.exe delete ATOLL
```

### Remove Configuration

**Linux/macOS:**
```bash
rm -rf ~/.ollama_server
rm -rf ~/.atoll
rm -f mcp.json  # If in working directory
```

**Windows:**
```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\.ollama_server"
Remove-Item -Recurse -Force "$env:USERPROFILE\.atoll"
Remove-Item -Force mcp.json  # If in working directory
```

---

## Additional Resources

- **Repository:** https://github.com/Buttje/ATOLL
- **Documentation:** https://github.com/Buttje/ATOLL/tree/main/docs
- **Issues:** https://github.com/Buttje/ATOLL/issues
- **Deployment Server Guide:** [DEPLOYMENT_SERVER_V2_USAGE.md](DEPLOYMENT_SERVER_V2_USAGE.md)
- **API Reference:** [docs/api/](api/)
- **Contributing:** [CONTRIBUTING.md](../CONTRIBUTING.md)

### External Resources

- **Ollama Documentation:** https://ollama.ai/docs
- **MCP Specification:** https://github.com/modelcontextprotocol/specification
- **LangChain Documentation:** https://python.langchain.com/

---

## Getting Help

If you encounter issues:

1. **Check troubleshooting section** above
2. **Search existing issues:** https://github.com/Buttje/ATOLL/issues
3. **Check discussions:** https://github.com/Buttje/ATOLL/discussions
4. **Create new issue** with:
   - Python version: `python --version`
   - OS details: `uname -a` (Linux) or `systeminfo` (Windows)
   - Installation method used
   - Full error messages and logs
   - Steps to reproduce

---

**Document Version:** 2.0.0  
**Tested On:**
- Ubuntu 24.04 LTS (Kernel 6.8+)
- Windows 11 (Build 22H2+)
- Python 3.9, 3.10, 3.11, 3.12

---

*This installation guide fulfills Task 1.1 of the ATOLL v2.0 roadmap: "Define cross-platform installation guide."*
