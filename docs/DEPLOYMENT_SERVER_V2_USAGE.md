# ATOLL v2.0 Deployment Server Usage Guide

## Overview

ATOLL v2.0 introduces a powerful deployment server system that enables remote management of ATOLL agent instances. This guide covers the new features and how to use them.

## New Features in v2.0

### 1. REST API for Remote Management

The deployment server now exposes a REST API for managing agents remotely.

**Starting the API Server:**

```python
from atoll.deployment import run_api_server, DeploymentServer, DeploymentServerConfig
from pathlib import Path

# Create deployment server
config = DeploymentServerConfig(
    agents_directory=Path("./agents"),
    start_port=8001,
    auto_restart_on_failure=True
)
server = DeploymentServer(config)

# Start API server (runs on port 8080 by default)
await run_api_server(
    deployment_server=server,
    host="localhost",
    port=8080,
    storage_path=Path("./storage")
)
```

### 2. ZIP Package Deployment

Deploy agents as ZIP packages with automatic extraction and validation.

**Package Structure:**

```
my-agent.zip
├── agent.toml or agent.json    # Agent configuration
├── main.py                     # Agent implementation
├── requirements.txt            # Python dependencies (optional)
└── ... (other files)
```

**agent.toml Example:**

```toml
[agent]
name = "my-agent"
description = "My custom agent"
version = "1.0.0"

[llm]
model = "llama2"
temperature = 0.7
```

**agent.json Example:**

```json
{
  "agent": {
    "name": "my-agent",
    "description": "My custom agent",
    "version": "1.0.0"
  },
  "llm": {
    "model": "llama2",
    "temperature": 0.7
  }
}
```

### 3. MD5 Checksum Tracking

Agents are tracked by MD5 checksums to prevent duplicate deployments.

- Checksums stored in `checksums.json`
- Automatic detection of existing installations
- Force reinstall option available

### 4. Virtual Environment Isolation

Each agent gets its own isolated Python environment.

- Automatic `venv` creation
- Dependencies installed from `requirements.txt`
- Platform-aware (Windows/Linux)

### 5. Deployment Client

Interact with deployment servers from Python code.

```python
from atoll.deployment import DeploymentClient
from pathlib import Path

# Create client
client = DeploymentClient("http://localhost:8080")

# Check server health
health = await client.health_check()
print(f"Server status: {health['status']}")

# List agents
agents = await client.list_agents()
for agent in agents:
    print(f"Agent: {agent['name']} - Status: {agent['status']}")

# Deploy new agent
result = await client.deploy_agent(Path("./my-agent.zip"))
print(f"Deployed: {result['name']}")

# Start agent
await client.start_agent("my-agent")

# Get agent status
status = await client.get_agent_status("my-agent")
print(f"Agent port: {status['port']}, PID: {status['pid']}")

# Stop agent
await client.stop_agent("my-agent")
```

**Synchronous API:**

```python
# Synchronous wrappers available
health = client.health_check_sync()
agents = client.list_agents_sync()
client.deploy_agent_sync(Path("./my-agent.zip"))
client.start_agent_sync("my-agent")
```

## REST API Endpoints

### Health Check

```http
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "version": "2.0.0"
}
```

### List Agents

```http
GET /agents
```

**Response:**

```json
{
  "agents": [
    {
      "name": "agent1",
      "status": "running",
      "port": 8001,
      "pid": 1234,
      "checksum": "abc123...",
      "config_path": "/path/to/agent1.toml"
    }
  ],
  "count": 1
}
```

### Check Agent Exists

```http
POST /check?checksum=abc123...
```

**Response (exists):**

```json
{
  "exists": true,
  "name": "agent1",
  "status": "running",
  "port": 8001,
  "running": true
}
```

**Response (not found):**

```json
{
  "exists": false,
  "message": "Agent not found. Upload required."
}
```

### Deploy Agent

```http
POST /deploy?force=false
Content-Type: multipart/form-data

file: <ZIP package>
```

**Response:**

```json
{
  "status": "deployed",
  "name": "my-agent",
  "checksum": "abc123...",
  "config_path": "/storage/agent_abc123/agent.toml",
  "message": "Agent my-agent deployed successfully"
}
```

### Start Agent

```http
POST /start
Content-Type: application/json

{
  "agent_name": "my-agent"
}
```

**Response:**

```json
{
  "status": "started",
  "name": "my-agent",
  "port": 8001,
  "pid": 1234
}
```

### Stop Agent

```http
POST /stop
Content-Type: application/json

{
  "agent_name": "my-agent"
}
```

**Response:**

```json
{
  "status": "stopped",
  "name": "my-agent"
}
```

### Restart Agent

```http
POST /restart
Content-Type: application/json

{
  "agent_name": "my-agent"
}
```

**Response:**

```json
{
  "status": "restarted",
  "name": "my-agent",
  "port": 8001,
  "pid": 5678
}
```

### Get Agent Status

```http
GET /status/{agent_name}
```

**Response:**

```json
{
  "name": "my-agent",
  "status": "running",
  "port": 8001,
  "pid": 1234,
  "checksum": "abc123...",
  "error_message": null
}
```

## Command Line Usage

### Using curl

**Deploy agent:**

```bash
curl -X POST http://localhost:8080/deploy \
  -F "file=@my-agent.zip" \
  -F "force=false"
```

**Start agent:**

```bash
curl -X POST http://localhost:8080/start \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "my-agent"}'
```

**Get status:**

```bash
curl http://localhost:8080/status/my-agent
```

## Integration Examples

### CI/CD Pipeline

```python
import asyncio
from atoll.deployment import DeploymentClient
from pathlib import Path

async def deploy_to_production():
    """Deploy agent to production server."""
    client = DeploymentClient("http://prod-server:8080", timeout=60)

    # Check if agent exists
    checksum = calculate_checksum(Path("./dist/agent.zip"))
    check_result = await client.check_agent(checksum)

    if check_result["exists"]:
        print(f"Agent already deployed: {check_result['name']}")
        # Restart to pick up config changes
        await client.restart_agent(check_result['name'])
    else:
        # Deploy new version
        result = await client.deploy_agent(Path("./dist/agent.zip"))
        print(f"Deployed new agent: {result['name']}")

        # Start agent
        await client.start_agent(result['name'])

    # Verify running
    status = await client.get_agent_status(result['name'])
    assert status['status'] == 'running', "Agent failed to start"
    print(f"Agent running on port {status['port']}")

asyncio.run(deploy_to_production())
```

### Multi-Agent Orchestration

```python
async def deploy_agent_cluster():
    """Deploy multiple coordinated agents."""
    client = DeploymentClient("http://localhost:8080")

    agents = [
        ("coordinator.zip", "coordinator"),
        ("worker1.zip", "worker-1"),
        ("worker2.zip", "worker-2"),
    ]

    # Deploy all agents
    for package, name in agents:
        await client.deploy_agent(Path(package))

    # Start coordinator first
    await client.start_agent("coordinator")

    # Wait for coordinator to be ready
    await asyncio.sleep(2)

    # Start workers
    await asyncio.gather(
        client.start_agent("worker-1"),
        client.start_agent("worker-2"),
    )

    # Check all running
    agents = await client.list_agents()
    for agent in agents:
        print(f"{agent['name']}: {agent['status']} (port {agent['port']})")
```

## Best Practices

### 1. Agent Packaging

- Include `requirements.txt` for dependencies
- Use semantic versioning in agent metadata
- Test locally before deploying
- Keep package size reasonable (<100MB)

### 2. Configuration Management

- Use environment variables for secrets
- Store configs in version control (without secrets)
- Use different configs for dev/staging/prod

### 3. Health Monitoring

- Poll `/status/{name}` endpoint regularly
- Set up alerts for failed agents
- Use auto-restart feature in production

### 4. Security

- Use HTTPS in production
- Implement authentication middleware
- Restrict API access by IP/network
- Validate uploaded packages

### 5. Deployment Strategy

- Blue-green deployments: Deploy new version, test, switch traffic
- Canary releases: Deploy to subset of servers first
- Rollback plan: Keep previous versions available

## Troubleshooting

### Agent Won't Start

Check error message in status endpoint:

```python
status = await client.get_agent_status("my-agent")
print(f"Error: {status['error_message']}")
```

Common issues:
- Port already in use → Check `start_port` in config
- Missing dependencies → Verify `requirements.txt`
- Invalid configuration → Validate `agent.toml`/`agent.json`

### Virtual Environment Issues

Manually inspect venv:

```bash
cd ~/.atoll_deployment/agents/agent_abc123/.venv

# Windows
Scripts\python.exe -m pip list

# Linux/Mac
bin/python -m pip list
```

### Checksum Conflicts

Force reinstall if needed:

```python
await client.deploy_agent(Path("my-agent.zip"), force=True)
```

Or clear checksum database:

```bash
rm ~/.atoll_deployment/agents/checksums.json
```

## Migration from v1.x

v1.x deployment servers ran agents locally only. v2.0 adds:

1. **REST API** - Remote management capability
2. **ZIP deployment** - Package-based installation
3. **Checksums** - Duplicate detection
4. **Virtual envs** - Dependency isolation

Existing v1.x configurations work without changes. To use v2.0 features:

1. Create agent ZIP packages
2. Start deployment server with API
3. Use deployment client for management

## Next Steps

- See [Deployment Server Architecture](./DEPLOYMENT_SERVER_ARCHITECTURE.md) for design details
- Check [API Reference](../api/README.md) for complete endpoint documentation
- Review examples in `examples/` directory
