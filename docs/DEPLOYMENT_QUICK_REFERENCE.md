# Quick Reference: Deployment Server

## Port Structure

| Service | Port | Purpose | Check Health |
|---------|------|---------|--------------|
| **Deployment Server API** | **8080** | Management REST API | `curl http://localhost:8080/health` |
| Agent Server 1 | 8100 | GhidraAgent (example) | `curl http://localhost:8100/health` |
| Agent Server 2 | 8101 | Second agent | `curl http://localhost:8101/health` |
| Agent Server N | 810N | Nth agent | `curl http://localhost:810N/health` |

## Quick Commands

### Check Deployment Server Status
```powershell
# Health check
curl http://localhost:8080/health

# List all agents
curl http://localhost:8080/agents
```

### Check Agent Server Status
```powershell
# Check if GhidraAgent (port 8100) is running
curl http://localhost:8100/health

# Check all agent ports
8100..8109 | ForEach-Object {
    try {
        Invoke-WebRequest -Uri "http://localhost:$_/health" -TimeoutSec 1 -ErrorAction Stop | Out-Null
        Write-Host "Port ${_}: ✓" -ForegroundColor Green
    } catch {
        Write-Host "Port ${_}: ✗" -ForegroundColor Red
    }
}
```

### Deploy Agent
```powershell
$file = Get-Item "ghidra_agent.zip"
Invoke-RestMethod -Uri http://localhost:8080/agents/deploy -Method Post -Form @{ file = $file }
```

### Start/Stop Agent
```powershell
# Start
Invoke-RestMethod -Uri http://localhost:8080/agents/GhidraAgent/start -Method Post

# Stop
Invoke-RestMethod -Uri http://localhost:8080/agents/GhidraAgent/stop -Method Post

# Restart
Invoke-RestMethod -Uri http://localhost:8080/agents/GhidraAgent/restart -Method Post
```

## Configuration

**File**: `~/.atoll_deployment/deployment_servers.json`

```json
{
  "enabled": true,
  "host": "localhost",
  "api_port": 8080,
  "base_port": 8100,
  "max_agents": 10,
  "agents_directory": "atoll_agents",
  "remote_servers": [
    {
      "name": "production",
      "host": "192.168.1.100",
      "port": 8080,
      "enabled": true
    }
  ]
}
```

## Architecture

```
┌─────────────────────────────────────────┐
│  ATOLL Application                      │
│  ┌───────────────────────────────────┐  │
│  │ Deployment Server (localhost)     │  │
│  │ ┌───────────────────────────────┐ │  │
│  │ │ REST API (Port 8080)          │ │  │
│  │ │ - /health                      │ │  │
│  │ │ - /agents                      │ │  │
│  │ │ - /agents/deploy              │ │  │
│  │ │ - /agents/{name}/start        │ │  │
│  │ └───────────────────────────────┘ │  │
│  │                                   │  │
│  │ Process Manager                   │  │
│  │ ├─ GhidraAgent (PID 12345)       │  │
│  │ ├─ SecondAgent (PID 12346)       │  │
│  │ └─ ThirdAgent  (PID 12347)       │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
           │
           ├── Port 8100: GhidraAgent API
           ├── Port 8101: SecondAgent API
           └── Port 8102: ThirdAgent API
```

## Startup Output

```
======================================================================
STARTING LOCAL DEPLOYMENT SERVER
======================================================================
  → Host: localhost
  → REST API Port: 8080
  → Agents Directory: atoll_agents
  → Agent Port Range: 8100-8109

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

======================================================================
DEPLOYMENT INFRASTRUCTURE STATUS
======================================================================

[DEPLOYMENT SERVER]
  Type: Local Process Manager + REST API
  Function: Manages agent lifecycle and provides remote deployment API
  Status: ✓ Running
  Host: localhost
  REST API: http://localhost:8080
  API Endpoints:
    → POST /agents/deploy - Deploy agent package
    → GET /agents - List all agents
    → POST /agents/{name}/start - Start agent
    → POST /agents/{name}/stop - Stop agent
  Agents Directory: atoll_agents
  Agent Port Range: 8100-8109
  Managed Agents: 1
  Running Agents: 1

[AGENT SERVERS] (Individual API Endpoints)

  ✓ GhidraAgent
     → API Endpoint: http://localhost:8100
     → Port: 8100
     → Process ID: 12345
     → Status: Running

======================================================================
```

## Common Issues

### Port 8080 Already in Use
Change `api_port` in configuration:
```json
{
  "api_port": 8081
}
```

### Can't Connect to Agent
1. Check if deployment server is running: `curl http://localhost:8080/health`
2. Check agent status: `curl http://localhost:8080/agents`
3. Check agent health: `curl http://localhost:8100/health` (replace 8100 with actual port)

### Agent Failed to Start
Check the startup report for detailed error diagnostics including:
- Exit code
- STDERR output
- STDOUT output
- Python version warnings
- Dependency issues
- Configuration problems

## See Also

- Full documentation: `/docs/DEPLOYMENT_REST_API.md`
- Example configuration: `/examples/deployment_servers.json`
- Error diagnostics: `/docs/VERBOSE_ERROR_DIAGNOSTICS.md`
- Verbose output: `/docs/VERBOSE_DEPLOYMENT_OUTPUT.md`
