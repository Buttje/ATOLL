# ATOLL REST API Usage Guide

**Version:** 2.0.0  
**Last Updated:** January 2025

Complete guide for interacting with the ATOLL Deployment Server REST API.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
4. [Python Client Examples](#python-client-examples)
5. [cURL Examples](#curl-examples)
6. [Error Handling](#error-handling)
7. [Best Practices](#best-practices)

---

## Getting Started

### Prerequisites

- ATOLL Deployment Server running (default: `http://localhost:8080`)
- Agent package (ZIP format) ready for deployment
- HTTP client (requests, httpx, cURL, etc.)

### Starting the Deployment Server

**Option 1: Using CLI**
```bash
# Start with defaults
atoll-deploy

# Custom configuration
atoll-deploy --host 0.0.0.0 --port 8090 --agents-dir /opt/agents
```

**Option 2: Programmatically**
```python
from atoll.deployment.cli import main
import asyncio

asyncio.run(main())
```

### Base URL

All API endpoints are relative to: `http://localhost:8080` (default)

---

## Authentication

**Current Version:** No authentication required (development)

**Future Versions (Task 2.2):** Will support:
- API Key authentication
- Token-based authentication
- Optional for internal networks

---

## API Endpoints

### 1. Health Check

**GET `/health`**

Check if the deployment server is running.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "agents_count": 3
}
```

**Status Codes:**
- `200 OK` - Server is healthy

---

### 2. List All Agents

**GET `/agents`**

Get list of all discovered and deployed agents.

**Response:**
```json
{
  "agents": [
    {
      "name": "ghidra_agent",
      "status": "running",
      "port": 8100,
      "pid": 12345,
      "checksum": "a1b2c3d4e5f6..."
    },
    {
      "name": "custom_agent",
      "status": "stopped",
      "port": null,
      "pid": null,
      "checksum": "f6e5d4c3b2a1..."
    }
  ],
  "count": 2
}
```

**Status Codes:**
- `200 OK` - Successfully retrieved agent list

---

### 3. Check Agent Existence

**GET `/agents/check/{agent_name}`**

Check if an agent exists and get its checksum.

**Path Parameters:**
- `agent_name` (string) - Name of the agent

**Response (Exists):**
```json
{
  "exists": true,
  "agent_name": "ghidra_agent",
  "checksum": "a1b2c3d4e5f6..."
}
```

**Response (Not Exists):**
```json
{
  "exists": false,
  "agent_name": "nonexistent_agent",
  "checksum": null
}
```

**Status Codes:**
- `200 OK` - Check completed

---

### 4. Deploy Agent Package

**POST `/agents/upload`**

Upload and deploy an agent package (ZIP file).

**Request:**
- Content-Type: `multipart/form-data`
- Body:
  - `file` (binary) - ZIP file containing agent package
  - `name` (string, optional) - Override agent name
  - `force` (boolean, optional) - Force reinstall if exists (default: false)

**Response (Success):**
```json
{
  "status": "deployed",
  "agent_name": "my_agent",
  "checksum": "a1b2c3d4e5f6...",
  "path": "/home/user/.atoll_deployment/agents/my_agent"
}
```

**Response (Already Exists):**
```json
{
  "status": "exists",
  "agent_name": "my_agent",
  "checksum": "a1b2c3d4e5f6...",
  "message": "Agent already deployed with matching checksum"
}
```

**Status Codes:**
- `200 OK` - Agent deployed successfully or already exists
- `400 Bad Request` - Invalid package format
- `500 Internal Server Error` - Deployment failed

---

### 5. Start Agent

**POST `/agents/start`**

Start a deployed agent instance.

**Request Body:**
```json
{
  "agent_name": "ghidra_agent"
}
```

**Response (Success):**
```json
{
  "status": "started",
  "name": "ghidra_agent",
  "port": 8100,
  "pid": 12345
}
```

**Status Codes:**
- `200 OK` - Agent started successfully
- `404 Not Found` - Agent not found
- `500 Internal Server Error` - Failed to start agent

---

### 6. Stop Agent

**POST `/agents/stop`**

Stop a running agent instance.

**Request Body:**
```json
{
  "agent_name": "ghidra_agent"
}
```

**Response:**
```json
{
  "status": "stopped",
  "name": "ghidra_agent"
}
```

**Status Codes:**
- `200 OK` - Agent stopped successfully
- `404 Not Found` - Agent not found
- `500 Internal Server Error` - Failed to stop agent

---

### 7. Restart Agent

**POST `/agents/restart`**

Restart a running agent (stop then start).

**Request Body:**
```json
{
  "agent_name": "ghidra_agent"
}
```

**Response:**
```json
{
  "status": "restarted",
  "name": "ghidra_agent",
  "port": 8100,
  "pid": 12456
}
```

**Status Codes:**
- `200 OK` - Agent restarted successfully
- `404 Not Found` - Agent not found
- `500 Internal Server Error` - Failed to restart agent

---

### 8. Get Agent Status

**GET `/status/{agent_name}`**

Get detailed status of a specific agent.

**Path Parameters:**
- `agent_name` (string) - Name of the agent

**Response:**
```json
{
  "name": "ghidra_agent",
  "status": "running",
  "port": 8100,
  "pid": 12345,
  "checksum": "a1b2c3d4e5f6...",
  "error_message": null
}
```

**Status Codes:**
- `200 OK` - Status retrieved successfully
- `404 Not Found` - Agent not found

---

## Python Client Examples

### Using ATOLL's Built-in Client

```python
from atoll.deployment.client import DeploymentClient
import asyncio

async def example_usage():
    # Initialize client
    client = DeploymentClient("http://localhost:8080")
    
    # Health check
    health = await client.health_check()
    print(f"Server status: {health['status']}")
    
    # List all agents
    agents = await client.list_agents()
    print(f"Found {len(agents)} agents")
    
    # Deploy an agent
    result = await client.deploy_agent("path/to/agent.zip")
    print(f"Deployment: {result['status']}")
    
    # Start an agent
    await client.start_agent("my_agent")
    print("Agent started")
    
    # Get agent status
    status = await client.get_agent_status("my_agent")
    print(f"Agent status: {status['status']} on port {status['port']}")
    
    # Stop an agent
    await client.stop_agent("my_agent")
    print("Agent stopped")

# Run async code
asyncio.run(example_usage())
```

### Using httpx (Async)

```python
import httpx
import asyncio

async def deploy_and_start_agent():
    """Deploy and start an agent using httpx."""
    base_url = "http://localhost:8080"
    
    async with httpx.AsyncClient() as client:
        # Upload agent package
        with open("my_agent.zip", "rb") as f:
            files = {"file": ("my_agent.zip", f, "application/zip")}
            response = await client.post(
                f"{base_url}/agents/upload",
                files=files
            )
            deploy_result = response.json()
            print(f"Deployed: {deploy_result}")
        
        # Start agent
        response = await client.post(
            f"{base_url}/agents/start",
            json={"agent_name": "my_agent"}
        )
        start_result = response.json()
        print(f"Started on port: {start_result['port']}")

asyncio.run(deploy_and_start_agent())
```

### Using requests (Sync)

```python
import requests

def manage_agents():
    """Manage agents using synchronous requests."""
    base_url = "http://localhost:8080"
    
    # Health check
    response = requests.get(f"{base_url}/health")
    print(f"Health: {response.json()}")
    
    # List agents
    response = requests.get(f"{base_url}/agents")
    agents = response.json()["agents"]
    print(f"Agents: {[a['name'] for a in agents]}")
    
    # Check if agent exists
    response = requests.get(f"{base_url}/agents/check/my_agent")
    exists = response.json()["exists"]
    
    if not exists:
        # Deploy agent
        with open("my_agent.zip", "rb") as f:
            files = {"file": ("my_agent.zip", f)}
            response = requests.post(
                f"{base_url}/agents/upload",
                files=files
            )
            print(f"Deploy: {response.json()}")
    
    # Start agent
    response = requests.post(
        f"{base_url}/agents/start",
        json={"agent_name": "my_agent"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Agent running on port {result['port']}")

manage_agents()
```

---

## cURL Examples

### Health Check

```bash
curl -X GET http://localhost:8080/health
```

### List All Agents

```bash
curl -X GET http://localhost:8080/agents | jq
```

### Check Agent Existence

```bash
curl -X GET http://localhost:8080/agents/check/ghidra_agent
```

### Deploy Agent Package

```bash
# Basic deployment
curl -X POST http://localhost:8080/agents/upload \
  -F "file=@my_agent.zip"

# Force reinstall
curl -X POST http://localhost:8080/agents/upload \
  -F "file=@my_agent.zip" \
  -F "force=true"

# Override agent name
curl -X POST http://localhost:8080/agents/upload \
  -F "file=@my_agent.zip" \
  -F "name=custom_name"
```

### Start Agent

```bash
curl -X POST http://localhost:8080/agents/start \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "ghidra_agent"}'
```

### Stop Agent

```bash
curl -X POST http://localhost:8080/agents/stop \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "ghidra_agent"}'
```

### Restart Agent

```bash
curl -X POST http://localhost:8080/agents/restart \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "ghidra_agent"}'
```

### Get Agent Status

```bash
curl -X GET http://localhost:8080/status/ghidra_agent
```

---

## Error Handling

### HTTP Status Codes

- `200 OK` - Request successful
- `400 Bad Request` - Invalid request data
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

### Error Response Format

```json
{
  "detail": "Agent not found: nonexistent_agent"
}
```

### Python Error Handling

```python
from atoll.deployment.client import DeploymentClient
import httpx

async def safe_deployment():
    client = DeploymentClient("http://localhost:8080")
    
    try:
        result = await client.deploy_agent("agent.zip")
        print(f"Success: {result}")
    except httpx.HTTPStatusError as e:
        print(f"HTTP Error: {e.response.status_code}")
        print(f"Detail: {e.response.json()}")
    except Exception as e:
        print(f"Error: {e}")
```

### cURL Error Handling

```bash
# Show HTTP status code
curl -w "\nHTTP Status: %{http_code}\n" \
  -X GET http://localhost:8080/agents

# Fail on HTTP errors
curl --fail -X GET http://localhost:8080/agents || echo "Request failed"
```

---

## Best Practices

### 1. Check Before Deploying

Always check if an agent exists before deploying to avoid unnecessary uploads:

```python
# Check existence
check_result = await client.check_agent("my_agent")

if check_result["exists"]:
    print("Agent already deployed")
else:
    # Deploy
    await client.deploy_agent("my_agent.zip")
```

### 2. Use Checksums for Validation

Compare checksums to verify package integrity:

```python
import hashlib

def calculate_checksum(filepath):
    """Calculate MD5 checksum of file."""
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
    return md5.hexdigest()

# Compare with deployed agent
local_checksum = calculate_checksum("my_agent.zip")
remote_checksum = check_result["checksum"]

if local_checksum != remote_checksum:
    print("Agent package has changed, redeploying...")
    await client.deploy_agent("my_agent.zip", force=True)
```

### 3. Monitor Agent Status

Regularly check agent health:

```python
async def monitor_agents():
    """Monitor all agents and restart if needed."""
    client = DeploymentClient("http://localhost:8080")
    
    agents = await client.list_agents()
    
    for agent in agents:
        status = await client.get_agent_status(agent["name"])
        
        if status["status"] == "failed":
            print(f"Agent {agent['name']} failed, restarting...")
            await client.restart_agent(agent["name"])
```

### 4. Use Async for Multiple Operations

Perform multiple operations concurrently:

```python
import asyncio

async def deploy_multiple_agents():
    """Deploy multiple agents concurrently."""
    client = DeploymentClient("http://localhost:8080")
    
    agents = ["agent1.zip", "agent2.zip", "agent3.zip"]
    
    # Deploy all concurrently
    tasks = [client.deploy_agent(agent) for agent in agents]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Check results
    for agent, result in zip(agents, results):
        if isinstance(result, Exception):
            print(f"Failed to deploy {agent}: {result}")
        else:
            print(f"Deployed {agent}: {result['status']}")
```

### 5. Graceful Shutdown

Stop all agents before shutting down server:

```python
async def shutdown_all_agents():
    """Stop all running agents."""
    client = DeploymentClient("http://localhost:8080")
    
    agents = await client.list_agents()
    
    # Stop all running agents
    for agent in agents:
        if agent["status"] == "running":
            await client.stop_agent(agent["name"])
            print(f"Stopped {agent['name']}")
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy ATOLL Agents

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install httpx
      
      - name: Deploy agent
        run: |
          python - <<EOF
          import httpx
          import asyncio
          
          async def deploy():
              async with httpx.AsyncClient() as client:
                  with open("agents/my_agent.zip", "rb") as f:
                      files = {"file": f}
                      response = await client.post(
                          "${{ secrets.ATOLL_SERVER }}/agents/upload",
                          files=files
                      )
                      print(response.json())
          
          asyncio.run(deploy())
          EOF
```

### Docker Compose Example

```yaml
version: '3.8'

services:
  atoll-server:
    image: atoll:latest
    command: atoll-deploy --host 0.0.0.0 --port 8080
    ports:
      - "8080:8080"
    volumes:
      - ./agents:/opt/agents
    environment:
      - AGENTS_DIR=/opt/agents

  agent-deployer:
    image: python:3.9
    depends_on:
      - atoll-server
    command: |
      python -c "
      import httpx, asyncio
      async def deploy():
          async with httpx.AsyncClient() as client:
              await asyncio.sleep(5)  # Wait for server
              with open('/agents/my_agent.zip', 'rb') as f:
                  files = {'file': f}
                  r = await client.post('http://atoll-server:8080/agents/upload', files=files)
                  print(r.json())
      asyncio.run(deploy())
      "
    volumes:
      - ./agents:/agents
```

---

## Troubleshooting

### Connection Refused

```bash
# Check if server is running
curl http://localhost:8080/health

# If failed, start deployment server
atoll-deploy
```

### Package Upload Fails

```bash
# Verify ZIP file structure
unzip -l my_agent.zip

# Ensure agent.toml or agent.json exists
# Ensure main.py exists
```

### Agent Won't Start

```bash
# Check agent status for error details
curl http://localhost:8080/status/my_agent

# Common issues:
# - Missing dependencies in requirements.txt
# - Port already in use
# - Invalid Python code in main.py
```

---

## Additional Resources

- **Main README**: [../README.md](../README.md)
- **Developer Guide**: [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
- **Installation Guide**: [INSTALLATION.md](INSTALLATION.md)
- **Deployment Server Documentation**: [DEPLOYMENT_SERVER_V2_USAGE.md](DEPLOYMENT_SERVER_V2_USAGE.md)

---

**Document Version:** 2.0.0  
**API Version:** 2.0  
**Last Tested:** January 2025

---

*This REST API usage guide fulfills Task 5.3 of the ATOLL v2.0 roadmap.*
