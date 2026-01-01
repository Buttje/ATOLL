# GhidraAgent v2.0.0 - Deployment Instructions

## Package Information

- **Package Name**: GhidraAgent-2.0.0.zip
- **Package Size**: ~8 KB
- **Agent Version**: 2.0.0
- **ATOLL Compatibility**: v2.0.0+
- **Created**: January 1, 2026

## Package Contents

```
GhidraAgent-2.0.0.zip
├── agent.toml           # TOML configuration (v2.0 format)
├── ghidra_agent.py      # Agent implementation
├── requirements.txt     # Python dependencies
└── README.md           # Agent documentation
```

## Prerequisites

Before deploying, ensure you have:

1. **ATOLL Deployment Server v2.0+** running
2. **Ghidra** installed and accessible
3. **GhidraMCP Server** installed and configured
4. **Ollama** with CodeLlama model: `ollama pull codellama:7b`

## Deployment Methods

### Method 1: REST API (Recommended)

#### Step 1: Check if Agent Already Exists

```bash
# Calculate MD5 checksum
# PowerShell:
$md5 = Get-FileHash -Algorithm MD5 GhidraAgent-2.0.0.zip
$checksum = $md5.Hash.ToLower()

# Check if agent exists
curl -X POST "http://localhost:8080/check?checksum=$checksum"
```

#### Step 2: Deploy Agent

```bash
# Deploy the ZIP package
curl -X POST http://localhost:8080/deploy \
  -F "file=@GhidraAgent-2.0.0.zip" \
  -F "force=false"

# Expected response:
# {
#   "status": "deployed",
#   "name": "GhidraAgent",
#   "checksum": "abc123...",
#   "config_path": "/storage/agent_abc123/agent.toml",
#   "message": "Agent GhidraAgent deployed successfully"
# }
```

#### Step 3: Start Agent

```bash
curl -X POST http://localhost:8080/start \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "GhidraAgent"}'

# Expected response:
# {
#   "status": "started",
#   "name": "GhidraAgent",
#   "port": 8001,
#   "pid": 1234
# }
```

#### Step 4: Verify Status

```bash
curl http://localhost:8080/status/GhidraAgent

# Expected response:
# {
#   "name": "GhidraAgent",
#   "status": "running",
#   "port": 8001,
#   "pid": 1234,
#   "checksum": "abc123...",
#   "error_message": null
# }
```

### Method 2: Python Deployment Client

```python
import asyncio
from pathlib import Path
from atoll.deployment import DeploymentClient

async def deploy_ghidra_agent():
    """Deploy GhidraAgent to deployment server."""

    # Create client
    client = DeploymentClient("http://localhost:8080")

    # Health check
    health = await client.health_check()
    print(f"Server status: {health['status']}")

    # Deploy agent
    package_path = Path("GhidraAgent-2.0.0.zip")
    result = await client.deploy_agent(package_path)

    print(f"Deployment status: {result['status']}")
    print(f"Agent name: {result['name']}")
    print(f"Checksum: {result['checksum']}")

    # Start agent
    if result['status'] == 'deployed':
        start_result = await client.start_agent(result['name'])
        print(f"Agent started on port: {start_result['port']}")

        # Get status
        status = await client.get_agent_status(result['name'])
        print(f"Agent status: {status['status']}")

    return result

# Run deployment
asyncio.run(deploy_ghidra_agent())
```

### Method 3: Manual Installation (Development)

```bash
# Extract to ATOLL agents directory
mkdir -p ~/.atoll/agents/ghidra_agent
unzip GhidraAgent-2.0.0.zip -d ~/.atoll/agents/ghidra_agent

# Install dependencies
cd ~/.atoll/agents/ghidra_agent
pip install -r requirements.txt

# Start ATOLL with agent discovery
atoll --agents-dir ~/.atoll/agents
```

## Post-Deployment Configuration

### Update GhidraMCP Server Path

After deployment, update the agent.toml with your GhidraMCP server location:

1. Locate the deployed agent directory (shown in deployment response)
2. Edit `agent.toml`:

```toml
[mcp_servers.ghidramcp]
type = "stdio"
command = "python"
args = [
    "/your/path/to/GhidraMCP/bridge_mcp_ghidra.py",  # UPDATE THIS
    "--ghidra-server",
    "http://127.0.0.1:8080"  # UPDATE THIS IF NEEDED
]
```

3. Restart the agent:

```bash
curl -X POST http://localhost:8080/restart \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "GhidraAgent"}'
```

## Testing the Deployment

### Test 1: Agent Discovery

```bash
# List all agents
curl http://localhost:8080/agents

# Expected: GhidraAgent in the list with status "running"
```

### Test 2: Capabilities Check

Connect to ATOLL and verify agent capabilities:

```
User: What can you help me with for binary analysis?

Expected: Agent should list Ghidra capabilities including decompilation,
          symbol analysis, and vulnerability detection.
```

### Test 3: Decompilation Request

```
User: Decompile the main function

Expected: Agent should be selected (high confidence score) and attempt
          to use Ghidra for decompilation.
```

## Troubleshooting

### Deployment Failed: "Already Installed"

**Problem**: Agent with same checksum already exists

**Solution**:
```bash
# Force reinstall
curl -X POST "http://localhost:8080/deploy?force=true" \
  -F "file=@GhidraAgent-2.0.0.zip"
```

### Agent Failed to Start

**Problem**: Agent status shows "failed" or "stopped"

**Solution**:
1. Check agent logs in deployment server
2. Verify Python dependencies installed correctly
3. Check GhidraMCP server is accessible
4. Review agent.toml configuration

```bash
# Get detailed status
curl http://localhost:8080/status/GhidraAgent

# Check error message in response
```

### Virtual Environment Issues

**Problem**: Dependencies not found or import errors

**Solution**:
1. Check venv was created: `~/.atoll_deployment/agents/agent_abc123/.venv`
2. Manually install dependencies:
   ```bash
   source ~/.atoll_deployment/agents/agent_abc123/.venv/bin/activate
   pip install -r requirements.txt
   ```
3. Restart agent after fixing

### GhidraMCP Connection Failed

**Problem**: Agent cannot connect to GhidraMCP

**Solution**:
1. Verify Ghidra is running
2. Test GhidraMCP server independently
3. Update `agent.toml` with correct paths
4. Check firewall/network settings

## Advanced Configuration

### Custom LLM Model

Edit `agent.toml` to use different model:

```toml
[llm]
model = "codellama:13b"  # Larger model for better analysis
temperature = 0.2  # Even more deterministic
```

### Resource Limits

Adjust based on your system:

```toml
[resources]
cpu_limit = 4.0  # More CPU for parallel analysis
memory_limit = "8GB"  # More memory for large binaries
max_concurrent_requests = 10  # More concurrent requests
```

### Auto-Restart Configuration

```toml
[deployment]
auto_restart = true
max_restarts = 5  # Increase restart attempts
restart_delay = 10  # Wait longer between restarts
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy GhidraAgent

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Deploy to production
        run: |
          curl -X POST ${{ secrets.DEPLOYMENT_SERVER_URL }}/deploy \
            -F "file=@GhidraAgent-2.0.0.zip" \
            -F "force=false"

          curl -X POST ${{ secrets.DEPLOYMENT_SERVER_URL }}/start \
            -H "Content-Type: application/json" \
            -d '{"agent_name": "GhidraAgent"}'
```

## Monitoring

### Health Checks

```bash
# Periodic health check
while true; do
  curl -s http://localhost:8080/status/GhidraAgent | jq '.status'
  sleep 30
done
```

### Log Monitoring

```bash
# View deployment server logs
tail -f ~/.atoll_deployment/logs/deployment.log

# Filter for GhidraAgent
tail -f ~/.atoll_deployment/logs/deployment.log | grep GhidraAgent
```

## Rollback

If the new version has issues:

```bash
# Stop current version
curl -X POST http://localhost:8080/stop \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "GhidraAgent"}'

# Deploy previous version
curl -X POST "http://localhost:8080/deploy?force=true" \
  -F "file=@GhidraAgent-1.0.0.zip"

# Start previous version
curl -X POST http://localhost:8080/start \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "GhidraAgent"}'
```

## Support

- **Package**: `d:\GitHub\ATOLL\atoll_agents\GhidraAgent-2.0.0.zip`
- **Documentation**: See included README.md
- **ATOLL Docs**: https://github.com/Buttje/ATOLL
- **Issues**: https://github.com/Buttje/ATOLL/issues

## Version History

- **v2.0.0** (2026-01-01): Updated to ATOLL v2.0 specification with TOML config
- **v1.0.0** (2025-12-15): Initial release with JSON config

---

**Deployment Date**: January 1, 2026
**Deployed By**: ATOLL System
**Status**: ✅ Ready for Production
