# Migration Guide to v2.0

**Version:** 2.0.0  
**Last Updated:** January 2025

This guide helps you migrate from ATOLL v1.x to v2.0, covering breaking changes, new features, and migration steps.

---

## Table of Contents

1. [Overview](#overview)
2. [Breaking Changes](#breaking-changes)
3. [Migration Steps](#migration-steps)
4. [Configuration Changes](#configuration-changes)
5. [API Changes](#api-changes)
6. [Deployment Server Changes](#deployment-server-changes)
7. [Testing Changes](#testing-changes)
8. [Troubleshooting](#troubleshooting)

---

## Overview

ATOLL v2.0 is a major release that introduces:
- **REST API** for remote agent management
- **ZIP package deployment** with checksum tracking
- **Virtual environment isolation** for each agent
- **Modernized architecture** with `ATOLLAgent` base class
- **Enhanced deployment server** with automatic port allocation
- **Comprehensive documentation** and developer guides

### Key Benefits
- ✅ Production-ready agent management
- ✅ Better isolation and security
- ✅ Remote deployment capabilities
- ✅ Improved developer experience
- ✅ Cross-platform reliability

---

## Breaking Changes

### 1. Agent Class Architecture

**v1.x:**
```python
from atoll.agent.agent import OllamaMCPAgent

agent = OllamaMCPAgent(ollama_config, mcp_config)
```

**v2.0:**
```python
from atoll.agent.root_agent import RootAgent

# For user interaction (replaces OllamaMCPAgent)
agent = RootAgent(ollama_config, mcp_manager)

# For custom agents
from atoll.agent.agent import ATOLLAgent

class MyAgent(ATOLLAgent):
    def __init__(self, ollama_config):
        super().__init__(ollama_config)
```

**Migration:**
- Replace `OllamaMCPAgent` imports with `RootAgent` for user-facing agents
- Extend `ATOLLAgent` for custom agent implementations
- Legacy import `OllamaMCPAgent` is aliased to `ATOLLAgent` for compatibility but deprecated

### 2. Configuration File Locations

**v1.x:**
- Ollama config: `./ollama_config.json` (working directory)
- MCP config: `./mcp.json` (working directory)

**v2.0:**
- Ollama config: `~/.ollama_server/.ollama_config.json` (user home)
- MCP config: `./mcp.json` (working directory - unchanged)

**Migration:**
```bash
# Linux/macOS
mkdir -p ~/.ollama_server
mv ollama_config.json ~/.ollama_server/.ollama_config.json

# Windows (PowerShell)
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.ollama_server"
Move-Item ollama_config.json "$env:USERPROFILE\.ollama_server\.ollama_config.json"
```

### 3. Package Structure

**v1.x:**
```
atoll/
├── agent.py
├── config.py
├── mcp_client.py
└── main.py
```

**v2.0:**
```
src/atoll/
├── agent/           # Agent classes
├── config/          # Configuration models
├── deployment/      # Deployment server (NEW)
├── mcp/            # MCP integration
├── ui/             # Terminal interface
├── utils/          # Utilities (NEW)
└── main.py
```

**Migration:**
- Update imports to use new package structure
- Import from `atoll.agent.agent` instead of `atoll.agent`
- Import from `atoll.config.models` instead of `atoll.config`

### 4. Method Name Changes

| v1.x | v2.0 | Notes |
|------|------|-------|
| `clear_memory()` | `clear_conversation_memory()` | More descriptive name |
| `_create_llm()` | `_initialize_llm()` | Consistent with base class |
| Direct LLM access | Use strategies (future) | Prepare for multi-LLM support |

---

## Migration Steps

### Step 1: Update Installation

```bash
# Uninstall old version
pip uninstall atoll

# Install v2.0
pip install atoll==2.0.0

# Or install from source
git clone https://github.com/Buttje/ATOLL.git
cd ATOLL
pip install -e ".[dev]"
```

### Step 2: Migrate Configuration Files

```bash
# Create new config directory
mkdir -p ~/.ollama_server

# Move Ollama config
mv ollama_config.json ~/.ollama_server/.ollama_config.json

# MCP config stays in place
# Verify: cat mcp.json
```

### Step 3: Update Agent Code

**Old code (v1.x):**
```python
from atoll.agent import OllamaMCPAgent
from atoll.config import load_ollama_config, load_mcp_config

ollama_config = load_ollama_config()
mcp_config = load_mcp_config()
agent = OllamaMCPAgent(ollama_config, mcp_config)
```

**New code (v2.0):**
```python
from atoll.agent.root_agent import RootAgent
from atoll.config.manager import ConfigManager
from atoll.mcp.server_manager import MCPServerManager

# Load configurations
config_manager = ConfigManager()
ollama_config = config_manager.get_ollama_config()

# Initialize MCP server manager
mcp_manager = MCPServerManager()
await mcp_manager.connect_all()

# Create agent
agent = RootAgent(ollama_config, mcp_manager)
```

### Step 4: Update Custom Agents

If you have custom agents, update them to extend the new base class:

```python
from atoll.agent.agent import ATOLLAgent

class MyCustomAgent(ATOLLAgent):
    """Custom agent implementation."""
    
    def __init__(self, ollama_config):
        super().__init__(ollama_config)
        # Your custom initialization
    
    async def process_prompt(self, prompt: str) -> str:
        """Process a user prompt."""
        # Your custom logic
        return await self.invoke_agent(prompt)
```

### Step 5: Update Tests

Update test imports and mocks:

```python
# Old
from atoll.agent import OllamaMCPAgent
mock_agent = Mock(spec=OllamaMCPAgent)

# New
from atoll.agent.agent import ATOLLAgent
mock_agent = Mock(spec=ATOLLAgent)
```

### Step 6: Verify Installation

```bash
# Check version
atoll --version  # Should show 2.0.0

# Run deployment server
atoll-deploy --help

# Run tests
pytest

# Check coverage
pytest --cov=src --cov-report=term
```

---

## Configuration Changes

### Ollama Configuration

**v1.x format:**
```json
{
  "server": "http://localhost:11434",
  "model": "llama2"
}
```

**v2.0 format:**
```json
{
  "base_url": "http://localhost",
  "port": 11434,
  "model": "llama2",
  "request_timeout": 30,
  "max_tokens": 2048
}
```

**Migration script:**
```python
import json
from pathlib import Path

old_config = json.loads(Path("ollama_config.json").read_text())
new_config = {
    "base_url": old_config.get("server", "http://localhost").rsplit(":", 1)[0],
    "port": int(old_config.get("server", "http://localhost:11434").rsplit(":", 1)[1]),
    "model": old_config.get("model", "llama2"),
    "request_timeout": 30,
    "max_tokens": 2048
}

config_dir = Path.home() / ".ollama_server"
config_dir.mkdir(parents=True, exist_ok=True)
(config_dir / ".ollama_config.json").write_text(json.dumps(new_config, indent=2))
```

### MCP Configuration

MCP configuration format remains compatible, but v2.0 adds support for additional options:

```json
{
  "servers": {
    "my-server": {
      "type": "stdio",
      "command": "python",
      "args": ["server.py"],
      "env": {
        "API_KEY": "${API_KEY}"
      },
      "cwd": "${workspaceFolder}",
      "envFile": ".env"  // NEW in v2.0
    }
  }
}
```

### Agent Configuration (agent.toml)

New in v2.0 for packaged agents:

```toml
[agent]
name = "my_agent"
version = "1.0.0"
description = "My custom agent"
author = "Your Name"
license = "MIT"

[agent.runtime]
python_version = ">=3.9"
entry_point = "main.py"

[agent.server]
host = "localhost"
# port auto-assigned

[agent.capabilities]
tools = ["tool1", "tool2"]
```

---

## API Changes

### Deployment Server API (NEW)

v2.0 introduces a REST API for remote agent management:

```bash
# Start deployment server
atoll-deploy --port 8080

# Health check
curl http://localhost:8080/health

# List agents
curl http://localhost:8080/agents

# Deploy agent package
curl -X POST http://localhost:8080/agents/deploy \
  -F "file=@agent.zip" \
  -F "name=my_agent"

# Start agent
curl -X POST http://localhost:8080/agents/my_agent/start

# Get agent status
curl http://localhost:8080/agents/my_agent
```

See [API_USAGE_GUIDE.md](API_USAGE_GUIDE.md) for complete API documentation.

---

## Deployment Server Changes

### Port Allocation

**v1.x:**
- Fixed port assignment
- Manual port management
- Port conflicts common

**v2.0:**
- Dynamic port allocation using OS APIs
- Automatic conflict resolution
- Persistent port registry
- Ports released on agent shutdown

**Migration:**
- Remove hardcoded ports from agent configurations
- Let deployment server assign ports automatically
- Use `agent.toml` without specifying port

### Agent Packaging

**v1.x:**
```
my_agent/
├── agent.py
└── requirements.txt
```

**v2.0 (ZIP package):**
```
my_agent.zip
├── agent.toml           # Configuration (required)
├── main.py              # Entry point (required)
├── requirements.txt     # Dependencies (required)
└── other_files/         # Additional files
```

**Create package:**
```bash
cd my_agent
zip -r ../my_agent.zip .
```

### Virtual Environment Isolation

**v1.x:**
- Shared Python environment
- Dependency conflicts possible

**v2.0:**
- Each agent in isolated venv
- Independent dependency management
- MD5 checksum tracking
- No reinstall if checksum matches

**Migration:**
- Package dependencies in `requirements.txt`
- Server creates `.venv` automatically
- Dependencies installed in isolation

---

## Testing Changes

### Test Structure

**v1.x:**
```
tests/
├── test_agent.py
└── test_config.py
```

**v2.0:**
```
tests/
├── unit/              # Unit tests
│   ├── test_agent.py
│   ├── test_deployment_api.py
│   └── ...
├── integration/       # Integration tests
│   └── test_integration.py
└── conftest.py       # Shared fixtures
```

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit

# Integration tests
pytest tests/integration

# With coverage
pytest --cov=src --cov-report=html

# Coverage threshold check
pytest --cov=src --cov-fail-under=90
```

---

## Troubleshooting

### Issue: Import errors after upgrade

**Symptom:**
```
ImportError: cannot import name 'OllamaMCPAgent' from 'atoll.agent'
```

**Solution:**
```python
# Option 1: Use new import
from atoll.agent.root_agent import RootAgent

# Option 2: Use compatibility alias
from atoll.agent.agent import ATOLLAgent as OllamaMCPAgent
```

### Issue: Config file not found

**Symptom:**
```
FileNotFoundError: Ollama config not found
```

**Solution:**
```bash
# Check config location
ls -la ~/.ollama_server/.ollama_config.json

# If missing, ATOLL creates default on first run
atoll

# Or create manually
mkdir -p ~/.ollama_server
cat > ~/.ollama_server/.ollama_config.json << 'EOF'
{
  "base_url": "http://localhost",
  "port": 11434,
  "model": "llama2",
  "request_timeout": 30,
  "max_tokens": 2048
}
EOF
```

### Issue: Port conflicts

**Symptom:**
```
OSError: [Errno 98] Address already in use
```

**Solution:**
v2.0 auto-resolves port conflicts. If still occurring:

```bash
# Check what's using the port
netstat -tlnp | grep 8080  # Linux
netstat -ano | findstr 8080  # Windows

# Let deployment server auto-assign
# Remove port from agent.toml or config

# Or specify different port
atoll-deploy --port 8090
```

### Issue: Tests failing after migration

**Solution:**
```bash
# Clear pytest cache
pytest --cache-clear

# Reinstall dependencies
pip install -e ".[dev]"

# Update test imports
# Replace OllamaMCPAgent → ATOLLAgent or RootAgent

# Run specific failing test
pytest tests/unit/test_agent.py -v
```

### Issue: Agent package deployment fails

**Symptom:**
```
ValidationError: agent.toml not found
```

**Solution:**
```bash
# Verify package structure
unzip -l agent.zip

# Should contain:
# - agent.toml (required)
# - main.py (required)
# - requirements.txt (required)

# Fix package
cd my_agent
# Add missing files
zip -r ../my_agent.zip .
```

---

## Additional Resources

- [Installation Guide](INSTALLATION.md) - Detailed installation instructions
- [Developer Guide](DEVELOPER_GUIDE.md) - Creating custom agents
- [API Usage Guide](API_USAGE_GUIDE.md) - REST API documentation
- [Deployment Server Architecture](DEPLOYMENT_SERVER_ARCHITECTURE.md) - Technical details
- [Changelog](../CHANGELOG.md) - Complete version history

---

## Getting Help

If you encounter issues not covered in this guide:

1. **Check Documentation**: [docs/](.) directory
2. **Search Issues**: [GitHub Issues](https://github.com/Buttje/ATOLL/issues)
3. **Ask Community**: [GitHub Discussions](https://github.com/Buttje/ATOLL/discussions)
4. **Report Bug**: Create new issue with:
   - Python version
   - Operating system
   - v1.x version you're migrating from
   - Error messages
   - Steps to reproduce

---

**Happy migrating! Welcome to ATOLL v2.0! 🚀**
