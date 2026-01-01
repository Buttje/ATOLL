# ATOLL System Requirements Specification
**Version**: 2.0.0
**Date**: January 1, 2026
**Status**: Implemented (Core Features) / Planned (Advanced Features)
**Implementation Coverage**: ~70% (35/50 requirements fully implemented)

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 2.0.0 | 2026-01-01 | ATOLL Team | Initial hierarchical + server architecture requirements |
| 2.0.1 | 2026-01-01 | ATOLL Team | Updated with implementation status and phase clarifications |

---

## Implementation Status Legend

- ✅ **IMPLEMENTED**: Feature is fully implemented and tested
- ⚠️ **PARTIAL**: Core functionality implemented, some advanced features pending
- 📋 **PLANNED**: Design complete, implementation scheduled for future release
- 🔮 **FUTURE**: Conceptual feature for consideration in v3.0+
## 1. Introduction

### 1.1 Purpose
This document specifies the requirements for ATOLL (Agentic Tools Orchestration on OLLama) version 2.0, which introduces:
- Hierarchical agent architecture with parent-child relationships
- REST API server mode with load balancing support
- Distributed deployment system with central controller
- Agent isolation via virtual environments

### 1.2 Scope
This specification covers:
- Hierarchical agent system architecture
- REST API server implementation
- Deployment controller and agent system
- Virtual environment management
- Load balancing and resource management
- Security and authentication
- Monitoring and observability

### 1.3 Definitions

| Term | Definition |
|------|------------|
| ATOLL Agent | An AI agent with LLM connection, MCP servers, and optional sub-agents |
| Root Agent | The top-level ATOLL agent providing initial user interface |
| Sub-Agent | Child agent in the hierarchy, specialized for specific tasks |
| Deployment Server | Service running on remote machines managing local ATOLL agents |
| Deployment Controller | Central service coordinating multiple deployment servers |
| Agent Server | ATOLL agent running in REST API server mode |
| Agent Context | Runtime state including current agent, navigation stack, session data |

---

## 2. Functional Requirements - Hierarchical Agent System

### FR-H001: Root Agent Initialization ✅ IMPLEMENTED
**Status**: ✅ Fully implemented in v2.0.0
**Implementation**: `src/atoll/agent/root_agent.py`

**Specific**: System SHALL initialize a root ATOLL agent on startup that provides the primary user interface.
**Measurable**: Root agent successfully loads within 5 seconds and responds to first command within 2 seconds.
**Achievable**: Using existing Application class with ATOLLAgent base class implementation.
**Relevant**: Ensures consistent entry point for all user interactions.
**Time-bound**: ✅ Completed in v2.0.0

**Acceptance Criteria**:
- Root agent inherits from ATOLLAgent base class
- Root agent has connection to configured Ollama LLM
- Root agent can discover and load sub-agents
- Root agent provides command and prompt modes
- Root agent displays breadcrumb navigation in UI header

### FR-H002: ATOLLAgent Base Class ✅ IMPLEMENTED
**Status**: ✅ Fully implemented in v2.0.0
**Implementation**: `src/atoll/plugins/base.py` (456 lines)

**Specific**: System SHALL provide an ATOLLAgent base class that all agents (including root) inherit from.
**Measurable**: Base class defines abstract methods: `process()`, `get_capabilities()`, `get_supported_mcp_servers()`.
**Achievable**: Extend existing `atoll/plugins/base.py` with LLM integration.
**Relevant**: Ensures uniform behavior across all agents in hierarchy.
**Time-bound**: ✅ Completed in v2.0.0

**Implementation Notes**:
- Base class includes full LLM integration (OllamaMCPAgent functionality migrated)
- Each agent has independent LLM config, conversation memory, and MCP server access
- Includes `check_server_connection()`, `check_model_available()`, `list_models()` methods
- Supports both local and distributed deployment modes

**Acceptance Criteria**:
- Base class includes OllamaMCPAgent functionality
- Each agent instance has its own LLM connection
- Each agent can have independent MCP servers
- Each agent maintains its own conversation memory
- Base class supports both local and server deployment modes

### FR-H003: Agent LLM Configuration
**Specific**: Each ATOLL agent SHALL have its own LLM configuration (model, temperature, system prompt).
**Measurable**: Agent configuration loaded from `.toml` file with validated parameters.
**Achievable**: Extend agent.json to .toml format with LLM settings section.
**Relevant**: Enables specialized agents with different model optimizations.
**Time-bound**: To be implemented in Sprint 1 (Weeks 1-2).

**Acceptance Criteria**:
- Agent .toml specifies `llm_model`, `llm_temperature`, `llm_top_p`, `system_prompt`
- Agent can override default Ollama server URL
- Agent validates LLM connectivity on initialization
- Agent falls back to parent LLM config if not specified
- Configuration changes persist without code modification

### FR-H004: Sub-Agent Discovery
**Specific**: System SHALL discover sub-agents in configured agent directory and build hierarchical tree.
**Measurable**: Discovers all valid .toml agent definitions and establishes parent-child relationships.
**Achievable**: Extend ATOLLAgentManager with recursive discovery.
**Relevant**: Enables multi-level agent hierarchies.
**Time-bound**: To be implemented in Sprint 2 (Weeks 3-4).

**Acceptance Criteria**:
- Scans agent directory recursively for agent.toml files
- Builds tree structure based on directory hierarchy or explicit parent references
- Detects circular references and prevents infinite loops
- Loads sub-agents lazily (on first access)
- Supports hot-reload when new agents added

### FR-H005: Agent Context Navigation - Switch To
**Specific**: User SHALL navigate to sub-agents using `switchto <agent-name>` command.
**Measurable**: Context switches within 500ms, updating UI breadcrumbs and available tools.
**Achievable**: Implement context stack management in ATOLLAgentManager.
**Relevant**: Enables user to access specialized agent capabilities.
**Time-bound**: To be implemented in Sprint 2 (Weeks 3-4).

**Acceptance Criteria**:
- Command accepts agent name (case-insensitive)
- Context stack stores previous agent context
- UI updates to show current agent in breadcrumb
- Available tools/MCP servers reflect current agent
- Current agent becomes target for prompt mode inputs
- Sub-agents of switched agent become visible in `list agents`

### FR-H006: Agent Context Navigation - Back
**Specific**: User SHALL return to parent agent using `back` command.
**Measurable**: Context restores previous agent within 200ms.
**Achievable**: Pop from context stack and restore state.
**Relevant**: Enables navigation back up the hierarchy.
**Time-bound**: To be implemented in Sprint 2 (Weeks 3-4).

**Acceptance Criteria**:
- Restores previous agent from context stack
- Updates breadcrumb to reflect current position
- Tools/MCP servers revert to parent agent's
- Cannot go back from root agent (displays warning)
- Memory of sub-agent preserved if switched back

### FR-H007: Breadcrumb Navigation Display
**Specific**: UI header SHALL display breadcrumb trail showing current position in agent hierarchy.
**Measurable**: Breadcrumb updates within 100ms of context change, format: `Main > Agent1 > Agent2`.
**Achievable**: Modify TerminalUI.display_header() to accept agent path.
**Relevant**: Provides visual context of current location.
**Time-bound**: To be implemented in Sprint 2 (Weeks 3-4).

**Acceptance Criteria**:
- Shows full path from root to current agent
- Truncates long paths with ellipsis if > 80 chars
- Updates on every `switchto` and `back` command
- Displays "Main ATOLL" for root agent
- Color-codes current agent vs. ancestors

### FR-H008: Context-Aware Tool Listing
**Specific**: `list tools` command SHALL display only tools from current agent's MCP servers.
**Measurable**: Lists tools from current agent context, not parent or children.
**Achievable**: Query current_context.mcp_manager.tool_registry.
**Relevant**: Prevents confusion about which tools are available.
**Time-bound**: To be implemented in Sprint 2 (Weeks 3-4).

**Acceptance Criteria**:
- Shows tools only from current agent's MCP servers
- Indicates which agent context tools belong to
- Does not recurse into sub-agent tools
- Updates immediately on context switch
- Shows "(no tools)" if agent has no MCP servers

### FR-H009: Context-Aware MCP Server Listing
**Specific**: `list mcp` command SHALL display only MCP servers from current agent.
**Measurable**: Lists servers from current agent context with connection status.
**Achievable**: Query current_context.mcp_manager.list_servers().
**Relevant**: Shows which MCP capabilities are available in current context.
**Time-bound**: To be implemented in Sprint 2 (Weeks 3-4).

**Acceptance Criteria**:
- Shows only current agent's MCP servers
- Displays connection status (connected/disconnected)
- Shows server type (stdio/http/sse)
- Indicates agent context in header
- Empty list if agent has no MCP configuration

### FR-H010: Context-Aware Sub-Agent Listing
**Specific**: `list agents` command SHALL display only direct children of current agent.
**Measurable**: Lists immediate sub-agents, not siblings or grandchildren.
**Achievable**: Query current_context.child_agents.
**Relevant**: Shows next level of specialization available.
**Time-bound**: To be implemented in Sprint 2 (Weeks 3-4).

**Acceptance Criteria**:
- Shows direct children only (no recursion)
- Displays agent name and description from .toml
- Shows capabilities list for each sub-agent
- Indicates if agent is already loaded
- Shows "(no sub-agents)" if current agent is leaf node

### FR-H011: Prompt Routing to Current Agent
**Specific**: Prompt mode input SHALL be routed to current agent's `process()` method.
**Measurable**: Prompt processed by correct agent, with response from that agent's LLM.
**Achievable**: Modify handle_prompt() to use current_context.agent.process().
**Relevant**: Ensures specialized agent handles prompts when active.
**Time-bound**: To be implemented in Sprint 3 (Weeks 5-6).

**Acceptance Criteria**:
- Root agent handles prompts when at top level
- Sub-agent handles prompts when switched to
- Agent uses its own LLM model and configuration
- Agent accesses its own MCP tools
- Agent reasoning appears in UI
- Response indicates which agent processed prompt

### FR-H012: Agent Memory Isolation
**Specific**: Each agent SHALL maintain independent conversation memory.
**Measurable**: Switching agents does not transfer conversation history.
**Achievable**: Store messages in agent instance, not global state.
**Relevant**: Prevents context pollution between specialized agents.
**Time-bound**: To be implemented in Sprint 3 (Weeks 5-6).

**Acceptance Criteria**:
- Each agent has separate `messages` list
- Switching agents starts fresh conversation with that agent
- `clear` command clears only current agent's memory
- Memory persists when switching away and back
- Optional: Serialize memory for persistence across sessions

---

## 3. Functional Requirements - REST API Server Mode

### Implementation Status: REST API Server
**Overall**: ⚠️ 60% Complete - Ollama-compatible endpoints implemented, ATOLL extensions and authentication planned

**Implemented** (`src/atoll/server/api.py`):
- ✅ `/` - Root endpoint
- ✅ `GET /health` - Health check
- ✅ `POST /api/generate` - Ollama-compatible generation
- ✅ `POST /api/chat` - Ollama-compatible chat
- ✅ `GET /api/tags` - List available models
- ✅ Session management with 30-minute timeout (`src/atoll/server/session.py`)
- ✅ `GET /api/sessions/stats` - Session statistics
- ✅ `POST /api/sessions/cleanup` - Clean expired sessions

**Not Implemented** (planned for v2.1):
- 📋 `GET /atoll/agents` - Agent hierarchy exploration
- 📋 `PUT /atoll/agents/{name}/activate` - Context switching via API
- 📋 `POST /atoll/tools/{tool-name}` - Direct tool invocation
- 📋 `GET /atoll/status?detailed=true` - Detailed health metrics
- 📋 JWT authentication (config field exists, no enforcement)
- 📋 Rate limiting per user
- 📋 `/api/embeddings` endpoint

---

### FR-S001: Ollama API Compatibility - Generate ✅ IMPLEMENTED
**Specific**: Agent server SHALL implement `/api/generate` endpoint compatible with Ollama API.
**Measurable**: Accepts same JSON request format, returns streaming or complete response.
**Achievable**: Wrap agent.process_prompt() with Ollama-compatible interface.
**Relevant**: Enables existing Ollama clients to use ATOLL agents.
**Time-bound**: To be implemented in Sprint 4 (Weeks 7-8).

**Acceptance Criteria**:
- Accepts POST /api/generate with `model`, `prompt`, `stream`, `options` fields
- Returns JSON with `response`, `model`, `created_at`, `done` fields
- Supports streaming responses (JSON lines)
- Handles `system` prompt injection
- Returns appropriate HTTP status codes (200, 400, 500)

**Request Example**:
```json
POST /api/generate
{
  "model": "agent-name",
  "prompt": "Analyze this binary",
  "stream": false,
  "options": {
    "temperature": 0.7
  }
}
```

**Response Example**:
```json
{
  "model": "agent-name",
  "created_at": "2026-01-01T12:00:00Z",
  "response": "Analysis result...",
  "done": true
}
```

### FR-S002: Ollama API Compatibility - Chat
**Specific**: Agent server SHALL implement `/api/chat` endpoint with conversation history support.
**Measurable**: Accepts messages array, maintains session state, returns chat response.
**Achievable**: Map messages to agent conversation memory.
**Relevant**: Supports multi-turn conversations in server mode.
**Time-bound**: To be implemented in Sprint 4 (Weeks 7-8).

**Acceptance Criteria**:
- Accepts POST /api/chat with `model`, `messages` array
- Supports `system`, `user`, `assistant` roles
- Maintains session state via session ID or auth token
- Returns message in Ollama chat response format
- Supports streaming chat responses

### FR-S003: Ollama API Compatibility - Model List
**Specific**: Agent server SHALL implement `/api/tags` endpoint listing available agents as models.
**Measurable**: Returns list of agent names with metadata.
**Achievable**: Query agent_manager.discovered_agents.
**Relevant**: Allows clients to discover available agents.
**Time-bound**: To be implemented in Sprint 4 (Weeks 7-8).

**Acceptance Criteria**:
- GET /api/tags returns JSON with `models` array
- Each model entry has `name`, `modified_at`, `size` (estimated)
- Includes agent capabilities in tags/metadata
- Only lists agents available to authenticated user
- Updates dynamically as agents are deployed/removed

### FR-S004: Ollama API Compatibility - Embeddings
**Specific**: Agent server SHALL implement `/api/embeddings` for text embedding generation.
**Measurable**: Delegates to agent's LLM embedding capability.
**Achievable**: Use Ollama embeddings API via agent LLM connection.
**Relevant**: Enables semantic search and RAG capabilities.
**Time-bound**: To be implemented in Sprint 5 (Weeks 9-10).

**Acceptance Criteria**:
- Accepts POST /api/embeddings with `model`, `prompt` fields
- Returns `embedding` array of floats
- Uses agent's configured LLM for embedding generation
- Handles errors gracefully (model doesn't support embeddings)
- Performance: < 1 second for typical text inputs

### FR-S005: ATOLL Extension - Agent Hierarchy Navigation
**Specific**: Agent server SHALL implement `/atoll/agents` endpoint for hierarchy exploration.
**Measurable**: Returns agent tree structure with navigation capabilities.
**Achievable**: Serialize agent_manager hierarchy to JSON.
**Relevant**: Enables clients to discover and navigate agent tree.
**Time-bound**: To be implemented in Sprint 5 (Weeks 9-10).

**Acceptance Criteria**:
- GET /atoll/agents returns root agent and children
- GET /atoll/agents/{name} returns specific agent details
- Includes agent capabilities, MCP servers, sub-agents
- PUT /atoll/agents/{name}/activate switches context to agent
- DELETE /atoll/agents/{name}/activate goes back (deactivates)

**Response Example**:
```json
{
  "name": "RootAgent",
  "capabilities": ["general_reasoning", "tool_orchestration"],
  "llm_model": "llama2",
  "mcp_servers": ["filesystem", "web_search"],
  "sub_agents": [
    {
      "name": "GhidraAgent",
      "capabilities": ["binary_analysis", "decompilation"],
      "description": "Specialized in reverse engineering"
    }
  ]
}
```

### FR-S006: ATOLL Extension - MCP Tool Invocation
**Specific**: Agent server SHALL implement `/atoll/tools/{tool-name}` endpoint for direct tool calls.
**Measurable**: Executes MCP tool and returns result within 30 seconds.
**Achievable**: Use agent's mcp_manager.execute_tool().
**Relevant**: Allows programmatic tool execution without LLM overhead.
**Time-bound**: To be implemented in Sprint 5 (Weeks 9-10).

**Acceptance Criteria**:
- POST /atoll/tools/{tool-name} accepts `arguments` JSON
- Returns tool result or error message
- Respects current agent context (only current agent's tools)
- Validates tool input schema before execution
- Includes execution time and tool source server in response

### FR-S007: ATOLL Extension - Agent Status
**Specific**: Agent server SHALL implement `/atoll/status` health check endpoint.
**Measurable**: Returns agent health within 100ms.
**Achievable**: Check LLM connectivity, MCP server status, memory usage.
**Relevant**: Enables load balancer health checks and monitoring.
**Time-bound**: To be implemented in Sprint 5 (Weeks 9-10).

**Acceptance Criteria**:
- GET /atoll/status returns 200 if healthy, 503 if unhealthy
- Includes LLM connection status, MCP server statuses
- Shows memory usage, active sessions, request queue length
- Returns within 100ms (no expensive checks)
- Supports optional detailed health check (?detailed=true)

### FR-S008: Session Management
**Specific**: Agent server SHALL maintain stateful sessions with conversation history.
**Measurable**: Sessions identified by session ID or JWT token, persist across requests.
**Achievable**: Store session data in memory with expiration (optional Redis backend).
**Relevant**: Enables multi-turn conversations in REST API.
**Time-bound**: To be implemented in Sprint 6 (Weeks 11-12).

**Acceptance Criteria**:
- Creates new session on first request (returns session ID)
- Subsequent requests include session ID in header or cookie
- Session stores agent context, conversation history, state
- Sessions expire after 30 minutes of inactivity (configurable)
- Supports explicit session termination (DELETE /atoll/sessions/{id})
- Maximum 1000 active sessions per agent server (configurable)

### FR-S009: Authentication and Authorization
**Specific**: Agent server SHALL require JWT token authentication for all non-public endpoints.
**Measurable**: Validates JWT signature, checks expiration, extracts user claims.
**Achievable**: Use PyJWT library with configurable secret/public key.
**Relevant**: Secures agent servers in multi-tenant deployments.
**Time-bound**: To be implemented in Sprint 6 (Weeks 11-12).

**Acceptance Criteria**:
- Public endpoints: /atoll/status, /api/tags (read-only)
- Protected endpoints: /api/generate, /api/chat, /atoll/tools/*
- Accepts Bearer token in Authorization header
- Validates token signature against configured public key
- Returns 401 for invalid/expired tokens
- Supports configurable token issuer and audience validation
- Optional: Role-based access control (RBAC) for agent access

### FR-S010: Request Rate Limiting
**Specific**: Agent server SHALL enforce per-user rate limits to prevent abuse.
**Measurable**: Maximum 100 requests per minute per user (configurable).
**Achievable**: Use token bucket or sliding window algorithm with Redis backend.
**Relevant**: Protects server resources from denial of service.
**Time-bound**: To be implemented in Sprint 6 (Weeks 11-12).

**Acceptance Criteria**:
- Tracks requests per user (identified by JWT token or IP)
- Returns 429 Too Many Requests when limit exceeded
- Includes Retry-After header with seconds to wait
- Configurable limits per endpoint and per user
- Admin users exempt from rate limiting
- Logged rate limit violations for monitoring

---

## 4. Functional Requirements - Deployment System

### Implementation Status: Deployment System
**Overall**: ⚠️ 85% Complete - Core deployment features implemented, controller layer planned for v2.1

**Implemented**:
- ✅ ZIP package deployment with MD5 checksums (`src/atoll/deployment/api.py`)
- ✅ Virtual environment isolation per agent
- ✅ Agent lifecycle management (start/stop/restart)
- ✅ REST API for deployment operations (port 8080)
- ✅ Deployment client library (`src/atoll/deployment/client.py`)
- ✅ Dynamic port allocation
- ✅ Comprehensive error diagnostics

**Partial**:
- ⚠️ Health monitoring (logic exists but background scheduler not active)
- ⚠️ Auto-restart on failure (implemented but requires health monitoring)

**Planned for v2.1**:
- 📋 Deployment controller (centralized coordination)
- 📋 Multi-server registration and discovery
- 📋 Load balancing across deployment servers

---

### FR-D001: Deployment Controller 📋 PLANNED
**Specific**: System SHALL provide a deployment controller service that coordinates multiple deployment servers.
**Measurable**: Controller manages at least 100 deployment servers, responds to health checks within 1 second.
**Achievable**: Python FastAPI service with SQLite/PostgreSQL backend.
**Relevant**: Central coordination point for distributed agent deployment.
**Time-bound**: To be implemented in Sprint 7 (Weeks 13-14).

**Acceptance Criteria**:
- Runs as standalone service (atoll-controller)
- Accepts deployment server registration requests
- Maintains inventory of registered servers and their agents
- Provides REST API for deployment operations
- Persists configuration to database
- Supports high availability (active-passive failover)

### FR-D002: Deployment Server Registration
**Specific**: Deployment servers SHALL register with controller on startup.
**Measurable**: Registration completes within 5 seconds, includes server capabilities.
**Achievable**: POST /controller/servers with server metadata.
**Relevant**: Controller maintains up-to-date inventory of available servers.
**Time-bound**: To be implemented in Sprint 7 (Weeks 13-14).

**Acceptance Criteria**:
- Deployment server sends heartbeat every 30 seconds
- Registration includes: hostname, IP, OS, CPU cores, RAM, disk space
- Controller assigns unique server ID
- Supports server deregistration on shutdown
- Controller detects unresponsive servers (no heartbeat for 90 seconds)
- Re-registration allowed after server restart

### FR-D003: Agent Deployment Request
**Specific**: Users SHALL request agent deployment via controller API.
**Measurable**: Controller selects appropriate deployment server and initiates deployment within 10 seconds.
**Achievable**: POST /controller/agents with agent .toml file.
**Relevant**: Enables automated agent provisioning.
**Time-bound**: To be implemented in Sprint 7 (Weeks 13-14).

**Acceptance Criteria**:
- Accepts agent .toml and optional sub-agent definitions
- Validates .toml format and requirements
- Selects deployment server based on:
  - Resource availability (CPU, RAM)
  - Geographic proximity (optional)
  - Current load (active agents)
- Delegates deployment to selected server
- Returns deployment status and agent URL
- Supports deployment rollback on failure

**Request Example**:
```json
POST /controller/agents
{
  "agent_toml": "base64-encoded-toml",
  "sub_agents": ["agent1.toml", "agent2.toml"],
  "preferences": {
    "region": "us-west",
    "high_memory": true
  }
}
```

### FR-D004: Deployment Server - Agent Provisioning
**Specific**: Deployment server SHALL provision agent by creating venv, installing dependencies, and starting agent server.
**Measurable**: Provisioning completes within 2 minutes for typical agent (< 50 MB dependencies).
**Achievable**: Automated script using venv, pip, subprocess management.
**Relevant**: Isolates agent dependencies and enables multi-tenancy.
**Time-bound**: To be implemented in Sprint 8 (Weeks 15-16).

**Acceptance Criteria**:
- Creates virtual environment at `~/.atoll/agents/{agent-name}/venv`
- Parses .toml `[dependencies]` section
- Installs Python packages via pip
- Validates successful installation (import checks)
- Configures agent-specific environment variables
- Starts agent server as background process
- Records process PID for management
- Captures stdout/stderr to log files
- Rolls back (deletes venv) if provisioning fails

### FR-D005: Deployment Server - Multiple Agent Management
**Specific**: Deployment server SHALL manage multiple agents concurrently, each in isolated venv.
**Measurable**: Supports at least 10 concurrent agents per server (hardware dependent).
**Achievable**: Process management with resource limits per agent.
**Relevant**: Maximizes hardware utilization.
**Time-bound**: To be implemented in Sprint 8 (Weeks 15-16).

**Acceptance Criteria**:
- Tracks all managed agents with status (starting/running/stopped/failed)
- Enforces resource limits per agent (CPU, memory from .toml)
- Prevents port conflicts (assigns unique port per agent)
- Monitors agent health (periodic status checks)
- Restarts failed agents (up to 3 retries)
- Logs all agent lifecycle events

### FR-D006: Deployment Server - Graceful Shutdown
**Specific**: Deployment server SHALL gracefully shutdown all managed agents on termination.
**Measurable**: All agents receive SIGTERM, allowed 30 seconds for cleanup, then SIGKILL if necessary.
**Achievable**: Signal handling with timeout management.
**Relevant**: Prevents data loss and resource leaks.
**Time-bound**: To be implemented in Sprint 8 (Weeks 15-16).

**Acceptance Criteria**:
- Intercepts SIGTERM/SIGINT signals
- Sends SIGTERM to all agent processes
- Waits up to 30 seconds per agent for graceful shutdown
- Sends SIGKILL to unresponsive agents
- Deregisters from controller before exiting
- Logs shutdown sequence and any errors
- Exit code indicates successful vs. forced shutdown

### FR-D007: Agent TOML Specification Format
**Specific**: Agent configuration SHALL use .toml format with standardized sections.
**Measurable**: Schema validation with pydantic models, generates helpful error messages.
**Achievable**: Define ATOLLAgentConfig dataclass and TOML parser.
**Relevant**: Provides consistent, readable agent configuration format.
**Time-bound**: To be implemented in Sprint 7 (Weeks 13-14).

**Acceptance Criteria**:
- Supports sections: `[agent]`, `[llm]`, `[dependencies]`, `[resources]`, `[mcp_servers.*]`
- Validates all required fields present
- Provides default values for optional fields
- Includes helpful error messages for invalid config
- Supports environment variable interpolation (${VAR})
- Backwards compatible with existing agent.json (conversion utility)

**Example agent.toml**:
```toml
[agent]
name = "GhidraAgent"
version = "1.0.0"
description = "Binary analysis specialist"
capabilities = ["binary_analysis", "decompilation", "reverse_engineering"]

[llm]
model = "codellama:13b"
base_url = "http://localhost:11434"
temperature = 0.3
top_p = 0.9
system_prompt = "You are an expert reverse engineer analyzing binaries with Ghidra."

[dependencies]
python = ">=3.9,<3.13"
packages = [
    "ghidra-bridge>=0.3.0",
    "capstone>=5.0.0",
    "pydantic>=2.0.0"
]

[resources]
cpu_limit = 2.0  # cores
memory_limit = "4GB"
max_concurrent_requests = 10
health_check_interval = 30  # seconds

[mcp_servers.ghidramcp]
type = "stdio"
command = "python"
args = ["-m", "ghidra_mcp_server"]
env = { GHIDRA_HOME = "/opt/ghidra" }

[deployment]
port = 0  # 0 = auto-assign
auto_restart = true
max_restarts = 3
restart_delay = 5  # seconds
```

### FR-D008: Agent Dependency Installation
**Specific**: Deployment server SHALL install agent dependencies from .toml specification.
**Measurable**: Installs within 5 minutes, validates installation success.
**Achievable**: Use pip with requirements parsed from .toml.
**Relevant**: Ensures agent has all required libraries.
**Time-bound**: To be implemented in Sprint 8 (Weeks 15-16).

**Acceptance Criteria**:
- Parses `[dependencies]` section from .toml
- Validates Python version compatibility
- Creates requirements.txt from packages list
- Runs `pip install -r requirements.txt` in venv
- Retries failed installations (up to 3 attempts)
- Validates imports after installation
- Logs installation output for troubleshooting
- Supports private PyPI repositories (credentials from config)

### FR-D009: Agent Resource Limits
**Specific**: Deployment server SHALL enforce resource limits specified in agent .toml.
**Measurable**: Agent process limited to specified CPU and memory.
**Achievable**: Use cgroups (Linux) or resource.setrlimit (Python).
**Relevant**: Prevents resource starvation from misbehaving agents.
**Time-bound**: To be implemented in Sprint 9 (Weeks 17-18).

**Acceptance Criteria**:
- Reads `[resources]` section from .toml
- Sets CPU limit (cgroups cpu.cfs_quota_us)
- Sets memory limit (cgroups memory.limit_in_bytes)
- Kills agent if memory limit exceeded
- Throttles CPU if limit exceeded (no kill)
- Logs resource violations
- Supports Windows resource limits (job objects)
- Graceful degradation if cgroups unavailable

### FR-D010: Agent Health Monitoring
**Specific**: Deployment server SHALL monitor agent health and restart if unhealthy.
**Measurable**: Health check every 30 seconds, restart within 10 seconds of failure detection.
**Achievable**: Periodic GET /atoll/status to agent server.
**Relevant**: Ensures high availability of agent services.
**Time-bound**: To be implemented in Sprint 9 (Weeks 17-18).

**Acceptance Criteria**:
- Checks /atoll/status endpoint at configured interval
- Considers agent unhealthy if:
  - HTTP status != 200
  - Response time > 10 seconds
  - 3 consecutive check failures
- Restarts agent process (SIGTERM then SIGKILL)
- Increments restart counter (max from .toml)
- Notifies controller of agent state changes
- Logs all health check results

---

## 5. Functional Requirements - Hierarchical Distributed Mode

### Implementation Status: Distributed Hierarchical
**Overall**: 📋 20% Complete - Configuration exists, HTTP delegation not implemented

**Implemented**:
- ✅ Agent TOML configuration with `[sub_agents.*]` sections
- ✅ Sub-agent URL and auth_token fields in config
- ✅ Local hierarchical navigation (switchto/back commands)
- ✅ Agent discovery from directory structure

**Not Implemented** (requires architectural changes):
- 📋 HTTP communication between parent and child agents
- 📋 Parent-to-child request delegation
- 📋 Load balancing across multiple agent instances
- 📋 Service discovery API
- 📋 Deployment controller for multi-server coordination

**Note**: The current implementation supports hierarchical agents in **local mode only** (all agents in same process). Distributed mode with HTTP communication between agents is planned for v2.1.

---

### FR-HD001: Parent-Child Agent Communication 📋 PLANNED
**Specific**: Parent agent SHALL communicate with child agent via HTTP REST API when in distributed mode.
**Measurable**: HTTP request/response completes within 5 seconds, includes authentication.
**Achievable**: Parent stores child agent URLs, makes HTTP calls to child's /api/generate or /atoll/tools/*.
**Relevant**: Enables parent to delegate complex tasks to specialized children.
**Time-bound**: To be implemented in Sprint 10 (Weeks 19-20).

**Acceptance Criteria**:
- Parent agent knows child agent URLs (from deployment controller)
- Parent can invoke child via POST /api/generate with prompt
- Parent receives child's response and reasoning
- Parent includes auth token in requests to child
- Parent handles child agent failures gracefully (timeout, retry)
- Parent can delegate specific tool calls to child

### FR-HD002: Agent Connection Configuration
**Specific**: Agent .toml SHALL specify connection details for sub-agents in distributed mode.
**Measurable**: .toml includes `[sub_agents.*]` sections with URLs or service discovery config.
**Achievable**: Extend .toml schema with sub-agent configuration.
**Relevant**: Parent needs to know how to reach children.
**Time-bound**: To be implemented in Sprint 10 (Weeks 19-20).

**Acceptance Criteria**:
- Supports explicit URL: `url = "http://child-agent.example.com:8080"`
- Supports service discovery: `service_name = "ghidra-agent"`
- Supports local mode: `mode = "local"` (in-process child)
- Parent validates child connectivity on startup
- Parent caches child connections
- Parent re-establishes connections on failure

**Example .toml with sub-agents**:
```toml
[agent]
name = "RootAgent"

[sub_agents.ghidra]
name = "GhidraAgent"
url = "http://10.0.1.5:8080"
auth_token = "${GHIDRA_AGENT_TOKEN}"

[sub_agents.web_research]
name = "WebResearchAgent"
service_name = "web-research-agent"
discovery_endpoint = "http://controller:9000/discover"
```

### FR-HD003: Load Balancing - Deployment Server
**Specific**: Deployment server SHALL load-balance requests across its managed agents of the same type.
**Measurable**: Distributes requests using round-robin or least-connections algorithm.
**Achievable**: Deployment server acts as reverse proxy for its agents.
**Relevant**: Maximizes throughput on single machine with multiple agent instances.
**Time-bound**: To be implemented in Sprint 11 (Weeks 21-22).

**Acceptance Criteria**:
- Supports multiple instances of same agent (e.g., 3x GhidraAgent)
- Exposes single endpoint for agent type
- Routes requests to instance with:
  - Fewest active requests (least-connections)
  - Or round-robin if loads equal
- Excludes unhealthy instances from rotation
- Tracks request distribution statistics
- Configurable algorithm via deployment server config

### FR-HD004: Load Balancing - External
**Specific**: System documentation SHALL describe external load balancer configuration for multi-machine deployment.
**Measurable**: Provides nginx/HAProxy example configs for round-robin across deployment servers.
**Achievable**: Documentation with configuration examples.
**Relevant**: Enables horizontal scaling across machines.
**Time-bound**: To be completed in Sprint 11 (Weeks 21-22).

**Acceptance Criteria**:
- Nginx example config provided
- HAProxy example config provided
- Documents health check endpoint for LB
- Describes session affinity (sticky sessions) setup
- Provides Kubernetes Ingress example
- Includes SSL/TLS termination at LB

### FR-HD005: Service Discovery
**Specific**: Deployment controller SHALL provide service discovery API for agent location.
**Measurable**: Returns agent URL(s) within 100ms given agent name/capabilities.
**Achievable**: Query controller's agent registry by name or capability filter.
**Relevant**: Enables dynamic agent discovery without hardcoded URLs.
**Time-bound**: To be implemented in Sprint 11 (Weeks 21-22).

**Acceptance Criteria**:
- GET /controller/discover?name={agent-name} returns agent URLs
- GET /controller/discover?capability={capability} returns matching agents
- Returns list of URLs (multiple instances if load-balanced)
- Includes health status of each instance
- Supports filtering by region, version, tags
- Caches results for 10 seconds to reduce load

---

## 6. Non-Functional Requirements

### NFR-P001: Performance - Response Time
**Specific**: Agent shall respond to prompts within 5 seconds for simple queries (< 100 tokens) on standard hardware (4 core, 8GB RAM).
**Measurable**: 95th percentile response time < 5s in benchmark tests.
**Achievable**: Optimize LLM invocation, avoid synchronous blocking operations.
**Relevant**: Ensures responsive user experience.
**Time-bound**: Validated in Sprint 12 (Weeks 23-24) via load testing.

### NFR-P002: Performance - Throughput
**Specific**: Agent server shall handle at least 50 concurrent requests with <10% degradation.
**Measurable**: Load test with 50 concurrent users, measure throughput drop.
**Achievable**: Async request handling, connection pooling.
**Relevant**: Supports multi-user deployments.
**Time-bound**: Validated in Sprint 12 (Weeks 23-24) via load testing.

### NFR-P003: Performance - Agent Startup
**Specific**: Agent shall initialize and be ready within 10 seconds of deployment.
**Measurable**: Time from deployment request to /atoll/status returning 200.
**Achievable**: Lazy load sub-agents, optimize LLM connection.
**Relevant**: Enables rapid scaling.
**Time-bound**: Validated in Sprint 9 (Weeks 17-18).

### NFR-S001: Security - Authentication
**Specific**: All agent servers SHALL use JWT token authentication with RS256 signing.
**Measurable**: Tokens validated using public key, expired tokens rejected.
**Achievable**: PyJWT library with RSA key pair.
**Relevant**: Prevents unauthorized access.
**Time-bound**: Implemented in Sprint 6 (Weeks 11-12).

### NFR-S002: Security - Transport Encryption
**Specific**: All HTTP communication SHALL use TLS 1.2 or higher in production.
**Measurable**: SSL Labs test scores A or higher.
**Achievable**: Nginx/HAProxy as TLS termination proxy.
**Relevant**: Protects data in transit.
**Time-bound**: Documented in Sprint 11 (Weeks 21-22).

### NFR-S003: Security - Secrets Management
**Specific**: Agent .toml SHALL NOT contain plaintext secrets; use environment variables or secret stores.
**Measurable**: .toml files pass secret scanner (detect-secrets).
**Achievable**: Environment variable interpolation, integration with HashiCorp Vault (optional).
**Relevant**: Prevents credential leakage.
**Time-bound**: Implemented in Sprint 7 (Weeks 13-14).

### NFR-S004: Security - Resource Limits
**Specific**: Agent processes SHALL be isolated with enforced CPU/memory limits.
**Measurable**: Agent cannot exceed limits specified in .toml.
**Achievable**: cgroups (Linux), job objects (Windows).
**Relevant**: Prevents DoS from malicious/buggy agents.
**Time-bound**: Implemented in Sprint 9 (Weeks 17-18).

### NFR-R001: Reliability - Availability
**Specific**: Agent servers SHALL achieve 99.5% uptime in production.
**Measurable**: Uptime monitoring shows <3.6 hours downtime per month.
**Achievable**: Health monitoring, auto-restart, load balancing.
**Relevant**: Critical for production workloads.
**Time-bound**: Measured after production deployment (Month 7+).

### NFR-R002: Reliability - Graceful Degradation
**Specific**: System SHALL continue operating if sub-agents fail, with clear error messages.
**Measurable**: Parent agent returns error if child unreachable, but remains functional.
**Achievable**: Exception handling, timeout management.
**Relevant**: Partial system failure doesn't cause total outage.
**Time-bound**: Tested in Sprint 10 (Weeks 19-20).

### NFR-R003: Reliability - Data Persistence
**Specific**: Agent conversation history SHALL persist across agent restarts (optional feature).
**Measurable**: Memory restored from disk/database after restart.
**Achievable**: Serialize messages to JSON/SQLite on shutdown.
**Relevant**: Enables long-running conversations.
**Time-bound**: Implemented in Sprint 13 (Weeks 25-26).

### NFR-M001: Maintainability - Logging
**Specific**: All components SHALL log to structured format (JSON) with configurable levels.
**Measurable**: Logs parseable by Elasticsearch, includes trace IDs.
**Achievable**: Python logging with structlog library.
**Relevant**: Enables troubleshooting and monitoring.
**Time-bound**: Implemented in Sprint 6 (Weeks 11-12).

### NFR-M002: Maintainability - Metrics
**Specific**: Agent servers SHALL expose Prometheus metrics at /metrics endpoint.
**Measurable**: Metrics include: request count, response time, active sessions, error rate.
**Achievable**: prometheus_client library.
**Relevant**: Enables monitoring and alerting.
**Time-bound**: Implemented in Sprint 9 (Weeks 17-18).

### NFR-M003: Maintainability - Configuration Reload
**Specific**: Agent servers SHALL support configuration reload without restart (SIGHUP).
**Measurable**: Changes to .toml applied within 5 seconds without downtime.
**Achievable**: Watch .toml file, reload on change.
**Relevant**: Reduces downtime for config updates.
**Time-bound**: Implemented in Sprint 13 (Weeks 25-26).

### NFR-U001: Usability - Error Messages
**Specific**: Error messages SHALL include actionable advice for resolution.
**Measurable**: Error messages follow format: "Error: [problem]. Suggestion: [solution]."
**Achievable**: Structured exception handling with user-friendly text.
**Relevant**: Reduces support burden.
**Time-bound**: Standardized in Sprint 3 (Weeks 5-6).

### NFR-U002: Usability - Documentation
**Specific**: All features SHALL have user documentation with examples.
**Measurable**: README.md, API docs, deployment guide cover all user-facing features.
**Achievable**: Markdown documentation in docs/ directory.
**Relevant**: Enables self-service user onboarding.
**Time-bound**: Continuously updated, reviewed in Sprint 12 (Weeks 23-24).

### NFR-C001: Compatibility - Python Versions
**Specific**: System SHALL support Python 3.9, 3.10, 3.11, 3.12.
**Measurable**: CI tests pass on all versions.
**Achievable**: Avoid Python 3.13+ only features.
**Relevant**: Broad compatibility for deployment.
**Time-bound**: Maintained continuously via CI.

### NFR-C002: Compatibility - Operating Systems
**Specific**: System SHALL run on Linux, macOS, Windows.
**Measurable**: Installation and tests pass on Ubuntu 22.04, macOS 13+, Windows 11.
**Achievable**: Cross-platform libraries, platform-specific code isolated.
**Relevant**: Supports diverse deployment environments.
**Time-bound**: Maintained continuously via CI.

### NFR-C003: Compatibility - Ollama API Version
**Specific**: REST API SHALL maintain compatibility with Ollama API v0.1.x.
**Measurable**: Ollama clients (ollama-python, ollama-js) work without modification.
**Achievable**: Follow Ollama API spec for implemented endpoints.
**Relevant**: Enables existing tooling integration.
**Time-bound**: Validated in Sprint 4 (Weeks 7-8).

---

## 7. Implementation Phases

### Phase 1: Hierarchical Foundation (Sprints 1-3, Weeks 1-6)
- FR-H001 to FR-H012: Complete hierarchical agent system
- Root agent, base class, navigation, breadcrumbs
- Context-aware tool/server/agent listing
- Prompt routing to current agent

### Phase 2: REST API Foundation (Sprints 4-6, Weeks 7-12)
- FR-S001 to FR-S010: REST API server mode
- Ollama API compatibility endpoints
- ATOLL extension endpoints
- Authentication, sessions, rate limiting

### Phase 3: Deployment System (Sprints 7-9, Weeks 13-18)
- FR-D001 to FR-D010: Deployment controller and server
- Agent provisioning, dependency management
- Resource limits, health monitoring
- TOML specification format

### Phase 4: Distributed Hierarchical (Sprints 10-11, Weeks 19-22)
- FR-HD001 to FR-HD005: Distributed agent communication
- Parent-child HTTP communication
- Load balancing, service discovery
- External LB configuration

### Phase 5: Hardening (Sprints 12-13, Weeks 23-26)
- Performance testing and optimization
- Security audits and fixes
- Comprehensive documentation
- Production deployment guides

---

## 8. Acceptance Criteria Summary

Each requirement SHALL be considered complete when:
1. **Implementation**: Code written, reviewed, merged
2. **Unit Tests**: >80% code coverage, all tests passing
3. **Integration Tests**: End-to-end scenarios validated
4. **Documentation**: User-facing docs updated
5. **Acceptance Tests**: Specific scenarios from test spec passing

---

## 9. Dependencies and Constraints

### External Dependencies
- Ollama: LLM runtime (version 0.1.7+)
- Python: 3.9-3.12
- Operating Systems: Linux (primary), macOS, Windows
- Libraries: FastAPI, PyJWT, aiohttp, pydantic, structlog

### Constraints
- Backward compatibility: Existing agent.json must continue working
- Performance: Must not degrade existing terminal UI responsiveness
- Security: No plaintext secrets in configuration files
- Resource limits: Configurable per-agent to prevent DoS

---

## 10. Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Hierarchical navigation depth | 5+ levels | Manual testing |
| Agent startup time | <10 seconds | Automated timing |
| REST API response time (95th %ile) | <5 seconds | Load testing |
| Deployment success rate | >95% | Deployment logs |
| System uptime | >99.5% | Monitoring tools |
| User satisfaction | >4/5 rating | Post-deployment survey |

---

## Appendix A: Glossary

See Section 1.3 for term definitions.

---

## Appendix B: References

1. Ollama API Documentation: https://github.com/ollama/ollama/blob/main/docs/api.md
2. Jenkins Architecture: https://www.jenkins.io/doc/book/architecting/
3. MCP Protocol Specification: https://spec.modelcontextprotocol.io/
4. SMART Requirements Guide: https://en.wikipedia.org/wiki/SMART_criteria
5. Python Virtual Environments: https://docs.python.org/3/tutorial/venv.html

---

**Document Version History**

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 2.0.0 | 2026-01-01 | Initial hierarchical + server requirements | ATOLL Team |

---

**Approval Signatures**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Owner | | | |
| Technical Lead | | | |
| QA Lead | | | |

---
