# ATOLL Deployment Server

## Overview

ATOLL includes a built-in deployment server that manages agent lifecycle both locally and remotely. The deployment server automatically starts with ATOLL and provides infrastructure for distributed agent execution.

## Architecture

- **Local Deployment Server**: Always runs on the machine where ATOLL is started
- **Remote Deployment Servers**: Optional external servers that can host additional agents
- **Agent Discovery**: Automatic discovery and reporting of agents across all deployment servers

## Local Deployment Server

### Automatic Startup

The local deployment server starts automatically when ATOLL launches:

1. **Port Discovery**: Automatically finds an available port starting from 8100
2. **Validation**: Verifies server can start before proceeding
3. **Error Handling**: If startup fails, ATOLL exits with detailed error message

### Configuration

The deployment server configuration is managed in `~/.atoll/deployment_servers.json`:

```json
{
  "enabled": true,
  "host": "localhost",
  "base_port": 8100,
  "max_agents": 10,
  "health_check_interval": 30,
  "restart_on_failure": true,
  "max_restarts": 3,
  "auto_discover_port": true,
  "agents_directory": null,
  "remote_servers": []
}
```

**Configuration Options:**

- `enabled`: Enable/disable deployment server (default: true)
- `host`: Server hostname (default: "localhost")
- `base_port`: Starting port for server (default: 8100)
- `auto_discover_port`: Automatically find available port if base_port is in use (default: true)
- `agents_directory`: Directory containing agent configurations

### Troubleshooting Local Server

If the local deployment server fails to start, ATOLL will display a detailed error message:

**Common Issues:**

1. **Port Already in Use**:
   - Error: "Port 8100 is already in use and auto-discovery is disabled"
   - Solution: Enable `auto_discover_port` or change `base_port` in configuration

2. **No Available Ports**:
   - Error: "No available ports found starting from 8100"
   - Solution: Check for port conflicts, or specify a different `base_port`

3. **Agents Directory Missing**:
   - Warning: Directory will be created automatically if it doesn't exist
   - Agents will not be available until configurations are added

## Remote Deployment Servers

### Configuration

Remote deployment servers are configured in `~/.atoll/deployment_servers.json`:

```json
{
  "enabled": true,
  "host": "localhost",
  "base_port": 8100,
  "auto_discover_port": true,
  "agents_directory": null,
  "remote_servers": [
    {
      "name": "production-server-1",
      "host": "192.168.1.100",
      "port": 8100,
      "enabled": true,
      "description": "Production deployment server in datacenter"
    },
    {
      "name": "dev-server",
      "host": "dev.example.com",
      "port": 8100,
      "enabled": false,
      "description": "Development server (currently disabled)"
    }
  ]
}
```

**Remote Server Options:**

- `name`: Unique identifier for the remote server
- `host`: Hostname or IP address of remote server
- `port`: Port number where remote deployment server is listening
- `enabled`: Enable/disable this remote server (default: true)
- `description`: Human-readable description of the server

### Remote Server Status

At startup, ATOLL checks the status of all configured remote servers:

- **Running**: Server is accessible and responding
- **Registered but Not Running**: Server is configured but not reachable
- **Disabled**: Server is configured but explicitly disabled
- **Error**: Server check failed with error message

### Agent Discovery on Remote Servers

**Current Status**: Remote agent discovery is planned but not yet implemented.

**Planned Features:**
- Query remote server REST API for installed agents
- Display agent capabilities and status
- Execute agents on remote servers via ATOLL

**Temporary Behavior**: Remote servers that are running will show "No agents discovered (REST API not yet implemented)"

## Startup Report

ATOLL displays a comprehensive startup report showing the deployment infrastructure:

```
======================================================================
DEPLOYMENT SERVER STARTUP REPORT
======================================================================

[LOCAL DEPLOYMENT SERVER]
  Status: ✓ Running on localhost:8100
  Agents Directory: /home/user/atoll_agents
  Active Agents: 2
    ● ghidra_agent (Port: 8101)
    ● custom_agent (Port: 8102)

[REMOTE DEPLOYMENT SERVERS] (2 configured)

  production-server-1 (192.168.1.100:8100)
    Status: ✓ Running and accessible
    Agents: No agents discovered (REST API not yet implemented)
    Description: Production deployment server in datacenter

  dev-server (dev.example.com:8100)
    Status: ○ Disabled in configuration
    Description: Development server (currently disabled)

======================================================================
```

**Status Icons:**
- `✓` - Operational/Successful
- `✗` - Error/Failed
- `○` - Disabled or Not Running
- `●` - Active agent process

## Commands

### Deployment Server Commands

**List Agents**:
```
agents
```
Shows all agents available on the local deployment server.

**Agent Status**:
```
agent status <agent_name>
```
Display detailed status of a specific agent.

**Start Agent**:
```
agent start <agent_name>
```
Start an agent instance on the local deployment server.

**Stop Agent**:
```
agent stop <agent_name>
```
Stop a running agent instance.

## Advanced Topics

### Configuration File Format

To set up a remote deployment server on another machine:

1. Install ATOLL on the remote machine
2. Start ATOLL with deployment server enabled
3. Note the hostname/IP and port
4. Add remote server configuration to `~/.atoll/deployment_servers.json` on your local machine
5. Restart local ATOLL to discover remote server

**Example ~/.atoll/deployment_servers.json**:
```json
{
  "enabled": true,
  "host": "localhost",
  "base_port": 8100,
  "auto_discover_port": true,
  "agents_directory": null,
  "remote_servers": [
    {
      "name": "prod-server-1",
      "host": "192.168.1.100",
      "port": 8100,
      "enabled": true,
      "description": "Production server"
    }
  ]
}
```

### Security Considerations

**Current Implementation:**
- No authentication or encryption
- Suitable for trusted local networks only
- Do not expose deployment servers to public internet

**Future Enhancements:**
- TLS/SSL encryption for remote connections
- API key authentication
- Role-based access control

### Port Management

The deployment server uses a range of ports:
- **Base Port** (e.g., 8100): Deployment server control interface
- **Agent Ports** (e.g., 8101, 8102, ...): Individual agent instances

Ensure firewall rules allow:
- Local deployment server base port (outbound only for local)
- Remote deployment server ports (outbound for client, inbound for server)

## Troubleshooting

### Remote Server Not Reachable

**Symptoms:**
```
Status: ○ Registered but not running
Error: Cannot connect to 192.168.1.100:8100
```

**Solutions:**
1. Verify remote server is running: `telnet <host> <port>`
2. Check firewall rules on remote server
3. Verify network connectivity: `ping <host>`
4. Check remote ATOLL logs for startup errors

### Hostname Resolution Failure

**Symptoms:**
```
Status: ○ Registered but not running
Error: Cannot resolve hostname: dev.example.com
```

**Solutions:**
1. Check DNS configuration
2. Use IP address instead of hostname
3. Add entry to `/etc/hosts` (Linux/Mac) or `C:\Windows\System32\drivers\etc\hosts` (Windows)

### Port Conflicts

**Symptoms:**
```
Status: ✗ FAILED - Port 8100 is already in use
```

**Solutions:**
1. Enable `auto_discover_port` in configuration
2. Change `base_port` to a different value
3. Stop other services using the port: `netstat -ano | findstr :8100` (Windows) or `lsof -i :8100` (Linux/Mac)

## Future Enhancements

- **REST API**: Query remote deployment servers for agent information
- **Agent Migration**: Move agents between deployment servers
- **Load Balancing**: Distribute agent workload across multiple servers
- **Health Monitoring**: Continuous health checks and alerting
- **Web Dashboard**: Visual interface for deployment server management
