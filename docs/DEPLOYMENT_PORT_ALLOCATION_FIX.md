# Deployment Server Port Allocation Fix

## Issue
The deployment server was incorrectly reported as "Running on localhost:8100", causing confusion because:

1. The deployment server itself doesn't listen on any port - it's a process manager
2. The first agent (GhidraATOLL) was also assigned port 8100
3. This made it appear as if both were on the same port

## Root Cause
The `validate_local_server()` method was finding an available port and reporting it as the deployment server's port, but it's actually the starting port for agent allocation.

## Changes Made

### 1. Port Allocation Improvement
**File:** `src/atoll/deployment/server.py`

Changed `_allocate_port()` to actually check for port availability:

```python
def _allocate_port(self) -> int:
    """Allocate a port for a new agent instance."""
    # Find next available port
    port = self.find_available_port(self.next_port)
    if port is None:
        # Fallback to incrementing if search fails
        port = self.next_port
        self.next_port += 1
    else:
        self.next_port = port + 1
    return port
```

**Before:** Simply incremented port counter without checking availability
**After:** Actually checks if port is free using socket binding

### 2. Clarified Deployment Server Role
Updated `validate_local_server()` documentation:

```python
async def validate_local_server(self) -> tuple[bool, str, Optional[int]]:
    """Validate that local deployment server can start.

    Note: The deployment server itself doesn't listen on a port - it manages
    agent subprocesses. This validation ensures we can allocate ports for agents.

    Returns:
        Tuple of (success, message, base_port_for_agents)
    """
```

### 3. Improved Status Reporting
**File:** `src/atoll/deployment/server.py`

Changed startup report to clearly show:
- Deployment server as a **manager** (not a listener)
- Agent port assignments separately
- Agent status (Running/Failed/Stopped)
- Error messages for failed agents

**Before:**
```
[LOCAL DEPLOYMENT SERVER]
  Status: ✓ Running on localhost:8100
  Agents Directory: atoll_agents
  Active Agents: 1
    ○ GhidraATOLL (Port: 8100)
```

**After:**
```
[LOCAL DEPLOYMENT SERVER]
  Status: ✓ Running (Managing 1 agent(s))
  Agents Directory: atoll_agents
  Agent Port Range: Starting from 8100

  Managed Agents:
    ● GhidraATOLL: Running (Port 8100)
```

Or if agent failed:
```
  Managed Agents:
    ✗ GhidraATOLL: Failed to start (Port 8100)
       Error: [error message truncated to 200 chars]
```

### 4. Better Error Reporting
Agent startup failures now store the error message in the `AgentInstance` for display in the status report.

## Testing

All deployment server tests pass:
- ✅ `test_server_starts_successfully`
- ✅ `test_discover_agents_from_toml`
- ✅ `test_discover_agents_from_json`
- ✅ `test_discover_agents_with_string_path_from_json`

## Example Output

### Successful Agent Start
```
Starting ATOLL...
Connecting to Ollama...
✓ Ollama server is reachable at http://localhost:11434
✓ Model 'llama3.2' is available

Discovering ATOLL agents...
  Using default agents directory: D:\GitHub\ATOLL\src\atoll_agents
✓ Detected 1 ATOLL agent(s):
  • GhidraATOLL
    Specialized agent for binary reverse engineering
    Capabilities: binary_analysis, decompilation

Starting deployment server...

=====================================================================
DEPLOYMENT SERVER STARTUP REPORT
=====================================================================

[LOCAL DEPLOYMENT SERVER]
  Status: ✓ Running (Managing 1 agent(s))
  Agents Directory: atoll_agents
  Agent Port Range: Starting from 8100

  Managed Agents:
    ● GhidraATOLL: Running (Port 8100)

[REMOTE DEPLOYMENT SERVERS]
  No remote servers configured

=====================================================================
```

### Failed Agent Start
```
[LOCAL DEPLOYMENT SERVER]
  Status: ✓ Running (Managing 1 agent(s))
  Agents Directory: atoll_agents
  Agent Port Range: Starting from 8100

  Managed Agents:
    ✗ GhidraATOLL: Failed to start (Port 8100)
       Error: ModuleNotFoundError: No module named 'ghidra_mcp'
```

## Remaining Issues

### Current Limitations
The deployment server still operates within the main ATOLL process. This is intentional for v1.x but will change in v2.0:

1. **No separate process** - Deployment server runs in main ATOLL process
2. **No REST API** - Cannot be accessed remotely
3. **No package management** - Agents must be manually installed
4. **No virtual environments** - Agents share Python environment

### Future Architecture (v2.0)
See [DEPLOYMENT_SERVER_ARCHITECTURE.md](DEPLOYMENT_SERVER_ARCHITECTURE.md) for the full vision of:
- Separate deployment server process
- REST API for remote management
- Agent package (ZIP) deployment
- MD5 checksum verification
- Virtual environment isolation
- Multi-tenant support

## Related Files
- `src/atoll/deployment/server.py` - Deployment server implementation
- `src/atoll/main.py` - ATOLL application startup
- `docs/DEPLOYMENT_SERVER_ARCHITECTURE.md` - Full architecture documentation
- `tests/unit/test_deployment_server.py` - Test suite
