# Migration Guide: v1.x to v2.0

This guide helps you migrate from ATOLL v1.x to v2.0, covering breaking changes, new features, and migration steps.

## Table of Contents
1. [Breaking Changes](#breaking-changes)
2. [New Features](#new-features)
3. [Migration Steps](#migration-steps)
4. [Configuration Changes](#configuration-changes)
5. [API Changes](#api-changes)
6. [Troubleshooting](#troubleshooting)

---

## Breaking Changes

### 1. Agent Architecture

**v1.x:**
```python
from atoll.agent import OllamaMCPAgent

# Old agent class
agent = OllamaMCPAgent(config)
```

**v2.0:**
```python
from atoll.agent import RootAgent, ATOLLAgent

# New architecture
root_agent = RootAgent(config)  # For user interaction
# Or extend ATOLLAgent for custom agents
```

**Impact:** The `OllamaMCPAgent` class has been removed. All functionality is now in the `ATOLLAgent` base class.

**Migration:** Replace `OllamaMCPAgent` imports with `RootAgent` or `ATOLLAgent`.

### 2. Method Names

Several methods have been renamed for consistency:

| v1.x | v2.0 |
|------|------|
| `clear_memory()` | `clear_conversation_memory()` |
| `_create_llm()` | `_initialize_llm()` |

**Migration:** Update method calls to use new names.

### 3. Configuration Format

**v1.x:** Agent configuration used `agent.json`

**v2.0:** Agent configuration now uses `agent.toml` format

**Example v1.x (agent.json):**
```json
{
  "name": "my_agent",
  "description": "My agent",
  "entry_point": "main.py"
}
```

**Example v2.0 (agent.toml):**
```toml
[agent]
name = "my_agent"
description = "My agent"
entry_point = "main.py"
version = "1.0.0"

[dependencies]
python = ">=3.9"
packages = ["langchain", "ollama"]

[llm]
model = "llama2"
temperature = 0.7
```

**Migration:** Convert `agent.json` files to `agent.toml` format.

### 4. Port Allocation

**v1.x:** Fixed port assignment starting from base port

**v2.0:** Dynamic port allocation using OS-level socket binding

**Impact:** Agents may receive different port numbers on each restart.

**Migration:** Update any hardcoded port references to use dynamic discovery.

---

## New Features

### 1. REST API Authentication

v2.0 introduces API key authentication for secure remote access.

**Enable Authentication:**
```bash
# Set API key via environment variable
export ATOLL_API_KEY="your-secure-api-key"

# Start deployment server
atoll-deploy serve
```

**Disable Authentication (internal networks):**
```python
# In deployment server configuration
api = DeploymentServerAPI(
    deployment_server,
    storage_path,
    require_auth=False  # Disable authentication
)
```

**Using Authenticated API:**
```bash
# Include API key in requests
curl -H "X-API-Key: your-secure-api-key" http://localhost:8080/agents
```

### 2. ZIP Package Deployment

Deploy agents as self-contained ZIP packages:

```bash
# Package structure
my_agent.zip
├── agent.toml
├── main.py
├── requirements.txt
└── README.md

# Deploy via API
curl -X POST -H "X-API-Key: your-key" \
  -F "file=@my_agent.zip" \
  http://localhost:8080/deploy
```

### 3. MD5 Checksum Tracking

v2.0 automatically tracks package checksums to prevent duplicate deployments:

```bash
# Check if package exists
curl -X POST -H "X-API-Key: your-key" \
  "http://localhost:8080/check?checksum=abc123..."
```

### 4. Diagnostics API

Get detailed diagnostic information for failed agents:

```bash
# Get diagnostics for an agent
curl -H "X-API-Key: your-key" \
  http://localhost:8080/agents/my_agent/diagnostics
```

Returns:
- Configuration validation
- Python version compatibility
- Port conflicts
- Dependency issues
- Captured stdout/stderr logs

### 5. Virtual Environment Isolation

Each agent runs in its own Python virtual environment, ensuring dependency isolation.

---

## Migration Steps

### Step 1: Backup Existing Installation

```bash
# Backup configuration
cp ~/.ollama_server/.ollama_config.json ~/.ollama_server/.ollama_config.json.backup
cp mcp.json mcp.json.backup

# Backup agent directories
tar -czf agents_backup.tar.gz atoll_agents/
```

### Step 2: Update ATOLL

```bash
# Pull latest version
git pull origin main

# Reinstall
pip install -e ".[dev]"
```

### Step 3: Convert Agent Configurations

**Automated Conversion Script:**

```python
#!/usr/bin/env python3
"""Convert agent.json to agent.toml format."""

import json
from pathlib import Path
import tomli_w

def convert_agent_config(json_path: Path):
    """Convert agent.json to agent.toml."""
    with open(json_path) as f:
        old_config = json.load(f)
    
    # Create new TOML structure
    new_config = {
        "agent": {
            "name": old_config.get("name", "unnamed"),
            "description": old_config.get("description", ""),
            "entry_point": old_config.get("entry_point", "main.py"),
            "version": "1.0.0",
        },
        "dependencies": {
            "python": ">=3.9",
            "packages": old_config.get("dependencies", []),
        },
    }
    
    # Add LLM config if present
    if "llm" in old_config:
        new_config["llm"] = old_config["llm"]
    
    # Write TOML file
    toml_path = json_path.parent / "agent.toml"
    with open(toml_path, "wb") as f:
        tomli_w.dump(new_config, f)
    
    print(f"Converted {json_path} -> {toml_path}")

# Convert all agent.json files
for json_file in Path("atoll_agents").rglob("agent.json"):
    convert_agent_config(json_file)
```

### Step 4: Update Code References

**Find and Replace:**

```bash
# Search for old imports
grep -r "OllamaMCPAgent" your_code/

# Replace with new imports
sed -i 's/from atoll.agent import OllamaMCPAgent/from atoll.agent import RootAgent/g' your_code/*.py
sed -i 's/OllamaMCPAgent/RootAgent/g' your_code/*.py
```

### Step 5: Update Deployment Scripts

If you have custom deployment scripts, update them to use the new REST API:

**Old v1.x:**
```python
# Direct deployment
agent = deploy_agent(config_path)
agent.start()
```

**New v2.0:**
```python
# Use deployment client
from atoll.deployment.client import DeploymentClient

client = DeploymentClient("http://localhost:8080", api_key="your-key")
client.deploy_agent("my_agent.zip")
client.start_agent("my_agent")
```

### Step 6: Configure Authentication

```bash
# Generate secure API key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set environment variable
echo 'export ATOLL_API_KEY="your-generated-key"' >> ~/.bashrc
source ~/.bashrc
```

### Step 7: Test Migration

```bash
# Start ATOLL
atoll

# Verify agents load
# In command mode:
> Servers
> Tools

# Test deployment server
atoll-deploy serve

# Test API
curl -H "X-API-Key: $ATOLL_API_KEY" http://localhost:8080/health
```

---

## Configuration Changes

### Deployment Server Configuration

**New Options in v2.0:**

```toml
[deployment_server]
enabled = true
host = "localhost"
api_port = 8080  # REST API port
base_port = 8100  # Starting port for agents
auto_discover_port = true  # Dynamic port allocation
restart_on_failure = true
max_restarts = 3

# NEW: Authentication settings
require_auth = true  # Enable API authentication
```

### Environment Variables

**New in v2.0:**

- `ATOLL_API_KEY` - API key for REST API authentication
- `ATOLL_STORAGE_PATH` - Custom storage path for agent packages

---

## API Changes

### REST API Endpoints

**New Endpoints in v2.0:**

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/health` | GET | Health check | No |
| `/agents` | GET | List all agents | Yes |
| `/check` | POST | Check if agent exists (by checksum) | Yes |
| `/deploy` | POST | Deploy agent ZIP package | Yes |
| `/agents/{name}/start` | POST | Start agent | Yes |
| `/agents/{name}/stop` | POST | Stop agent | Yes |
| `/agents/{name}/restart` | POST | Restart agent | Yes |
| `/agents/{name}/diagnostics` | GET | Get diagnostics | Yes |
| `/status/{name}` | GET | Get agent status | Yes |

### Python API

**Deployment Client:**

```python
from atoll.deployment.client import DeploymentClient

# Create client with authentication
client = DeploymentClient(
    base_url="http://localhost:8080",
    api_key="your-api-key"
)

# Deploy agent
response = client.deploy_agent("my_agent.zip")

# Start agent
client.start_agent("my_agent")

# Get diagnostics
diagnostics = client.get_diagnostics("my_agent")
```

---

## Troubleshooting

### Issue: "OllamaMCPAgent not found"

**Cause:** Code still references old class name.

**Solution:**
```python
# Replace
from atoll.agent import OllamaMCPAgent

# With
from atoll.agent import RootAgent
```

### Issue: "Agent configuration file not found"

**Cause:** v2.0 looks for `agent.toml`, not `agent.json`.

**Solution:** Convert configuration files using the script in Step 3.

### Issue: "Authentication failed" 

**Cause:** API key not set or incorrect.

**Solution:**
```bash
# Set API key
export ATOLL_API_KEY="your-key"

# Or disable auth for testing
# In code: require_auth=False
```

### Issue: "Port already in use"

**Cause:** Dynamic port allocation failed.

**Solution:**
- Check `auto_discover_port` is enabled
- Verify no processes are blocking the port range (8080-8200)
- Check deployment server logs for port assignment

### Issue: Tests failing after migration

**Cause:** Test fixtures may reference old classes.

**Solution:**
```python
# Update test fixtures
@pytest.fixture
def agent():
    # Old
    # return OllamaMCPAgent(config)
    
    # New
    from atoll.agent import RootAgent
    return RootAgent(config)
```

---

## Need Help?

- **Documentation:** See [docs/](../docs/) for detailed guides
- **Issues:** Report problems at https://github.com/Buttje/ATOLL/issues
- **Discussions:** Ask questions at https://github.com/Buttje/ATOLL/discussions

---

## Checklist

- [ ] Backup existing installation
- [ ] Update ATOLL to v2.0
- [ ] Convert agent.json → agent.toml
- [ ] Update code references (OllamaMCPAgent → RootAgent)
- [ ] Configure API authentication
- [ ] Update deployment scripts
- [ ] Test agents and deployment
- [ ] Update CI/CD pipelines (if applicable)
- [ ] Review new features (diagnostics, checksum tracking)

---

**Congratulations!** You've successfully migrated to ATOLL v2.0. Enjoy the new features and improved architecture!
