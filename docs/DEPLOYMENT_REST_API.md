# Deployment REST API

## Overview

The Deployment Server exposes a REST API on **port 8080** (by default) for remote agent management. This API is automatically started when ATOLL starts and provides endpoints for deploying, managing, and monitoring ATOLL agents.

## Architecture

### Local Deployment Server
- **Type**: Process Manager + REST API
- **Default API Port**: 8080
- **Default Agent Port Range**: 8100-8109 (configurable)
- **Host**: localhost (configurable)
- **Auto-start**: Always starts with ATOLL

### Remote Deployment Servers
Remote deployment servers are configured in `deployment_servers.json` and represent other ATOLL instances running their own deployment servers. These can be accessed through the same REST API.

## Configuration

### Local Server Configuration

**File**: `~/.atoll_deployment/deployment_servers.json` or in workspace

```json
{
  "enabled": true,
  "host": "localhost",
  "api_port": 8080,
  "base_port": 8100,
  "max_agents": 10,
  "health_check_interval": 30,
  "restart_on_failure": true,
  "max_restarts": 3,
  "auto_discover_port": true,
  "agents_directory": "atoll_agents",
  "remote_servers": []
}
```

### Remote Servers Configuration

```json
{
  "remote_servers": [
    {
      "name": "production-server-1",
      "host": "192.168.1.100",
      "port": 8080,
      "enabled": true,
      "description": "Production ATOLL deployment server"
    },
    {
      "name": "dev-server",
      "host": "dev.example.com",
      "port": 8080,
      "enabled": false,
      "description": "Development server (disabled)"
    }
  ]
}
```

## REST API Endpoints

### Health Check
```bash
GET http://localhost:8080/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-01T21:30:00.123456"
}
```

### List All Agents
```bash
GET http://localhost:8080/agents
```

**Response:**
```json
{
  "agents": [
    {
      "name": "GhidraAgent",
      "status": "running",
      "port": 8100,
      "pid": 12345,
      "checksum": "abc123...",
      "error_message": null
    }
  ]
}
```

### Deploy Agent Package
```bash
POST http://localhost:8080/agents/deploy
Content-Type: multipart/form-data
```

**Parameters:**
- `file`: ZIP file containing agent package
- `name` (optional): Agent name (inferred from package if not provided)
- `force` (optional): Force reinstall even if checksum matches

**Example using PowerShell:**
```powershell
$file = Get-Item "ghidra_agent.zip"
$uri = "http://localhost:8080/agents/deploy"

$form = @{
    file = $file
    force = "false"
}

Invoke-RestMethod -Uri $uri -Method Post -Form $form
```

**Response:**
```json
{
  "name": "GhidraAgent",
  "status": "deployed",
  "port": 8100,
  "checksum": "abc123...",
  "message": "Agent deployed and started successfully"
}
```

### Start Agent
```bash
POST http://localhost:8080/agents/GhidraAgent/start
```

**Response:**
```json
{
  "name": "GhidraAgent",
  "status": "running",
  "port": 8100,
  "pid": 12345
}
```

### Stop Agent
```bash
POST http://localhost:8080/agents/GhidraAgent/stop
```

**Response:**
```json
{
  "name": "GhidraAgent",
  "status": "stopped",
  "port": null,
  "pid": null
}
```

### Restart Agent
```bash
POST http://localhost:8080/agents/GhidraAgent/restart
```

**Response:**
```json
{
  "name": "GhidraAgent",
  "status": "running",
  "port": 8100,
  "pid": 12346
}
```

### Get Agent Status
```bash
GET http://localhost:8080/agents/GhidraAgent
```

**Response:**
```json
{
  "name": "GhidraAgent",
  "status": "running",
  "port": 8100,
  "pid": 12345,
  "checksum": "abc123...",
  "error_message": null,
  "start_time": "2026-01-01T21:30:00",
  "restart_count": 0
}
```

## Command Line Examples

### Check if Deployment Server is Running
```powershell
curl http://localhost:8080/health
```

### List All Agents
```powershell
Invoke-RestMethod -Uri http://localhost:8080/agents | ConvertTo-Json -Depth 3
```

### Deploy an Agent
```powershell
$file = Get-Item "ghidra_agent.zip"
Invoke-RestMethod -Uri http://localhost:8080/agents/deploy -Method Post -Form @{ file = $file }
```

### Check Agent Status
```powershell
curl http://localhost:8100/health  # Check GhidraAgent on port 8100
```

### Check Multiple Agent Ports
```powershell
8100..8102 | ForEach-Object {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$_/health" -TimeoutSec 2 -ErrorAction Stop
        Write-Host "Port ${_}: ✓ Running" -ForegroundColor Green
    } catch {
        Write-Host "Port ${_}: ✗ Not responding" -ForegroundColor Red
    }
}
```

## Port Structure

| Service | Port | Purpose |
|---------|------|---------|
| Deployment Server API | 8080 | REST API for agent management |
| Agent Server 1 | 8100 | First agent API endpoint (e.g., GhidraAgent) |
| Agent Server 2 | 8101 | Second agent API endpoint |
| Agent Server 3 | 8102 | Third agent API endpoint |
| ... | ... | Up to max_agents (default: 10) |

## Agent Package Structure

An agent package is a ZIP file containing:

```
agent_package.zip
├── agent.toml          # Agent configuration (required)
├── main.py             # Entry point (optional)
├── requirements.txt    # Python dependencies (optional)
├── README.md          # Documentation (optional)
└── agent_module/      # Agent implementation
    ├── __init__.py
    └── agent.py
```

## Deployment Process

When an agent is deployed via the REST API:

1. **Upload**: ZIP file uploaded to deployment server
2. **Checksum**: MD5 calculated to detect duplicates
3. **Extract**: Package extracted to agents directory
4. **Validate**: Configuration file validated
5. **Virtual Environment**: Python venv created
6. **Dependencies**: requirements.txt installed
7. **Register**: Agent registered with deployment server
8. **Start**: Agent process started on assigned port

All steps are logged with verbose output showing progress.

## Error Handling

The API returns standard HTTP status codes:

- **200 OK**: Success
- **400 Bad Request**: Invalid parameters or package
- **404 Not Found**: Agent not found
- **409 Conflict**: Agent already exists (use force=true to override)
- **500 Internal Server Error**: Server error (check logs)

Error responses include details:
```json
{
  "detail": "Agent not found: UnknownAgent",
  "error_code": "AGENT_NOT_FOUND"
}
```

## Security Considerations

### Local Deployment
- API binds to localhost by default (not exposed externally)
- No authentication required for local access
- File system permissions protect agent files

### Remote Deployment
- Configure firewall rules to restrict access to port 8080
- Consider using reverse proxy with authentication (nginx, Apache)
- Use HTTPS for production environments
- Implement API key authentication for remote servers

## Monitoring

### Health Checks
The deployment server performs automatic health checks every 30 seconds (configurable):
- Checks if agent processes are alive
- Restarts failed agents (if `restart_on_failure: true`)
- Limits restart attempts (default: 3 max)

### Logging
All deployment operations are logged to:
- Console output (user-facing)
- Python logging (debug details)
- Separate log files for each agent

## Integration with ATOLL

The deployment server integrates seamlessly with ATOLL:

1. **Auto-start**: Deployment server starts automatically with ATOLL
2. **Discovery**: Automatically discovers agents in `atoll_agents/` directory
3. **Management**: Agents can be managed through ATOLL commands or REST API
4. **Monitoring**: Real-time status in ATOLL startup report

## Startup Output

When ATOLL starts, you'll see:

```
======================================================================
STARTING LOCAL DEPLOYMENT SERVER
======================================================================
  → Host: localhost
  → REST API Port: 8080
  → Agents Directory: atoll_agents
  → Agent Port Range: 8100-8109
    (First agent will use port 8100)

🌐 Starting REST API...
   ✓ REST API running on http://localhost:8080

📂 Discovering agent configurations...
   ✓ Found 1 agent configuration(s)

======================================================================
STARTING AGENT SERVERS
======================================================================

  🚀 Starting Agent Server: GhidraAgent
     → Agent will listen on port: 8100
     → Working directory: atoll_agents\ghidra_agent
     → Process ID: 12345

  ✓ Agent Server running: GhidraAgent
     → API endpoint: http://localhost:8100
     → Process ID: 12345
     → Status: running

======================================================================
✓ DEPLOYMENT SERVER STARTED
======================================================================
  → Managing 1 agent(s)
  → Running agents: 1
======================================================================
```

## Troubleshooting

### Port Already in Use
If port 8080 is already in use, change `api_port` in configuration:
```json
{
  "api_port": 8081
}
```

### Agent Won't Start
Check the deployment server logs and agent stderr/stdout in the startup report. Common issues:
- Python version incompatibility (use Python 3.11-3.13)
- Missing dependencies (check requirements.txt)
- Invalid configuration (validate agent.toml)

### Remote Server Not Responding
Verify network connectivity:
```powershell
Test-NetConnection -ComputerName 192.168.1.100 -Port 8080
```

Check if remote server is configured and enabled in `deployment_servers.json`.

## Best Practices

1. **Local Development**: Use default localhost:8080 configuration
2. **Production**: Configure firewall, use HTTPS, implement authentication
3. **Agent Packages**: Always include requirements.txt and README.md
4. **Versioning**: Use semantic versioning in agent.toml
5. **Testing**: Test agents locally before deploying to remote servers
6. **Monitoring**: Implement health check automation
7. **Backups**: Keep backup copies of agent packages

## Future Enhancements

Planned features for the deployment REST API:
- API key authentication
- Role-based access control (RBAC)
- Agent metrics and analytics
- Deployment rollback functionality
- Multi-instance agent support
- Load balancing across remote servers
- WebSocket support for real-time status updates
