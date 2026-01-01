# ATOLL Deployment Server Architecture

## Overview

The ATOLL Deployment Server is a **separate service** from ATOLL client instances. It manages the lifecycle of ATOLL agent instances on a machine, handling installation, configuration, port allocation, and process management.

## Key Concepts

### 1. **Deployment Server** (Server)
- A standalone service that runs on a machine
- Manages ATOLL agent instances on that machine
- Provides REST API for remote management
- Does NOT execute agent logic itself

### 2. **ATOLL Client** (Client)
- The main ATOLL application users interact with
- Can connect to deployment servers to use remote agents
- Can send agent packages to deployment servers for installation
- Configures agents as sub-agents in its hierarchy

### 3. **ATOLL Agent** (Agent)
- A specialized ATOLL instance with specific capabilities
- Runs as an independent process with its own port
- Managed by a deployment server
- Has its own virtual environment and dependencies

## Current State vs. Target Architecture

### Current Implementation (v1.x)
- ✅ Deployment server runs locally within main ATOLL process
- ✅ Discovers agents from local directory
- ✅ Starts agents as subprocesses
- ✅ Allocates ports for each agent
- ✅ Monitors agent health
- ❌ No REST API for remote management
- ❌ No agent package deployment
- ❌ No MD5 checksum verification
- ❌ No remote deployment server support

### Target Architecture (v2.0)

#### Deployment Server Features
1. **Agent Package Management**
   - Accept agent packages as ZIP files from clients
   - Calculate and store MD5 checksums of installed agents
   - Compare checksums to avoid redundant installations
   - Store agents in isolated directories

2. **Virtual Environment Management**
   - Create virtual environment for each agent
   - Install agent dependencies in isolated environment
   - Manage Python interpreter versions per agent

3. **Port Allocation**
   - Maintain registry of used ports
   - Automatically find available ports
   - Ensure no port conflicts

4. **Agent Lifecycle**
   - Start/stop/restart agents on demand
   - Health monitoring
   - Auto-restart on failure (configurable)
   - Clean shutdown on server stop

5. **REST API**
   - List installed agents
   - Deploy new agent packages
   - Start/stop agents
   - Query agent status
   - Get agent logs

#### Client-Server Protocol

```
Client                    Deployment Server                Agent Process
  |                              |                              |
  |--1. Check Agent Exists------>|                              |
  |   (send MD5 checksum)        |                              |
  |                              |                              |
  |<-2. Response----------------|                              |
  |   (exists: yes/no)           |                              |
  |                              |                              |
  |--3. Upload ZIP (if new)----->|                              |
  |                              |                              |
  |                              |--4. Extract & Install------->|
  |                              |     Create venv              |
  |                              |     Install dependencies     |
  |                              |     Store MD5 checksum       |
  |                              |                              |
  |<-5. Installation Complete----|                              |
  |                              |                              |
  |--6. Start Agent Request----->|                              |
  |                              |                              |
  |                              |--7. Allocate Port----------->|
  |                              |--8. Start Process----------->|
  |                              |                              |--Running
  |                              |<-9. Process Started----------|
  |                              |                              |
  |<-10. Agent Info--------------|                              |
  |    (host, port)              |                              |
  |                              |                              |
  |======== Direct Communication with Agent ====================>|
  |                              |                              |
```

## Port Allocation Strategy

### Deployment Server
- **Does NOT listen on a port** in current implementation
- Future: Will have REST API on configurable port (default: 8080)

### Agents
- Each agent gets its own unique port
- Port range: Configurable (default: 8100-8199)
- Port allocation uses OS socket checking for availability
- Ports released when agents stop

### Example Configuration
```json
{
  "deployment_server": {
    "api_port": 8080,          // Deployment server REST API
    "agent_base_port": 8100,   // Starting port for agents
    "max_agents": 10           // Max 10 agents (ports 8100-8109)
  },
  "agents": [
    {
      "name": "GhidraATOLL",
      "port": 8100,            // Assigned port
      "status": "running"
    },
    {
      "name": "SQLAnalyzerATOLL",
      "port": 8101,            // Next available port
      "status": "running"
    }
  ]
}
```

## Agent Package Format

### ZIP Structure
```
agent-package.zip
├── agent.toml                 # Agent configuration
├── requirements.txt           # Python dependencies
├── README.md                  # Documentation
├── agent_implementation.py    # Main agent code
├── mcp.json                   # MCP server configuration (optional)
└── ...                        # Additional resources
```

### MD5 Checksum
- Calculated for entire ZIP file
- Stored by deployment server: `{agent_name}.md5`
- Used to detect if agent package has changed
- Avoids re-installation of identical agents

## Installation Process

1. **Client sends MD5 checksum** to deployment server
2. **Server checks** if agent with that checksum exists
   - If exists and running: Return connection info
   - If exists but stopped: Start and return info
   - If doesn't exist: Request ZIP file upload
3. **Client uploads ZIP file** (only if needed)
4. **Server extracts** to isolated directory
5. **Server creates venv** for agent
6. **Server installs** dependencies from requirements.txt
7. **Server stores** MD5 checksum
8. **Server starts** agent process
9. **Server returns** agent connection info to client

## Security Considerations

1. **Package Verification**
   - Verify ZIP file integrity
   - Scan for malicious code (future enhancement)
   - Validate agent.toml schema

2. **Isolation**
   - Each agent runs in separate process
   - Each agent has isolated virtual environment
   - Agents cannot access each other's files

3. **Authentication** (future)
   - REST API authentication
   - Client certificates
   - Token-based access

## Migration Path

### Phase 1 (Current - v1.x)
- ✅ Local deployment server
- ✅ Local agent discovery
- ✅ Subprocess management
- ✅ Basic port allocation

### Phase 2 (v1.5)
- 🔲 REST API for deployment server
- 🔲 Remote server registration
- 🔲 Agent package upload endpoint
- 🔲 MD5 checksum tracking

### Phase 3 (v2.0)
- 🔲 Full remote deployment
- 🔲 Virtual environment management
- 🔲 Authentication/authorization
- 🔲 Agent package marketplace

## Error Handling

### Agent Start Failures
- Capture stderr from agent process
- Store error message in agent instance
- Report in deployment server status
- Retry with backoff (if configured)

### Port Conflicts
- Automatically find next available port
- Report port conflicts in logs
- Fail gracefully if no ports available

### Package Installation Failures
- Rollback on failure
- Preserve previous version (if exists)
- Detailed error reporting to client

## Implementation Notes

### Current Limitations
1. Deployment server embedded in main ATOLL process
2. No REST API (yet)
3. No remote agent deployment
4. No virtual environment isolation
5. No package management

### Future Enhancements
1. Separate deployment server binary
2. REST API with OpenAPI specification
3. Agent package registry
4. Resource monitoring (CPU, memory)
5. Agent update management
6. Horizontal scaling support

## See Also
- [Deployment Server Implementation](DEPLOYMENT_SERVER_IMPLEMENTATION.md)
- [MCP Specification](https://github.com/modelcontextprotocol/specification)
- [ATOLL Agent System](AGENT_SYSTEM.md)
