# ATOLL Acceptance Test Specification
**Version**: 2.0.0
**Date**: January 1, 2026
**Status**: Draft for QA

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 2.0.0 | 2026-01-01 | QA Team | Initial acceptance tests for hierarchical + server architecture |

---

## 1. Introduction

### 1.1 Purpose
This document defines acceptance tests for ATOLL version 2.0 features, ensuring all requirements from SMART_REQUIREMENTS.md are properly validated.

### 1.2 Test Strategy
- **Unit Tests**: Automated via pytest, run on every commit
- **Integration Tests**: Automated end-to-end scenarios
- **Manual Tests**: Complex UI/UX validation, security audits
- **Performance Tests**: Load testing, stress testing, scalability
- **Security Tests**: Penetration testing, vulnerability scanning

### 1.3 Test Environment
- **Development**: Local machines, docker-compose stacks
- **Staging**: Cloud VMs mirroring production
- **Production**: Real deployment with canary releases

### 1.4 Test Data
- Sample agent .toml files (valid and invalid)
- Test LLM models (small models for fast testing)
- Mock MCP servers for integration tests
- Load test scripts (locust, k6)

---

## 2. Hierarchical Agent System Tests

### Test Suite: H - Hierarchical Agent System

#### TEST-H001: Root Agent Initialization
**Requirement**: FR-H001
**Type**: Automated Integration Test
**Priority**: P0 (Critical)

**Preconditions**:
- ATOLL installed with default configuration
- Ollama server running with llama2 model

**Test Steps**:
1. Start ATOLL: `atoll`
2. Verify startup completes within 5 seconds
3. Verify root agent displayed in UI header as "Main ATOLL"
4. Enter command mode (ESC)
5. Run `list agents` command
6. Verify response time < 2 seconds

**Expected Results**:
- Root agent initializes successfully
- Header shows "Main ATOLL" (no breadcrumbs yet)
- Command responses within target times
- No error messages in logs

**Pass/Fail Criteria**:
- All timing requirements met
- Zero errors in startup logs
- UI displays correctly

---

#### TEST-H002: ATOLLAgent Base Class Implementation
**Requirement**: FR-H002
**Type**: Automated Unit Test
**Priority**: P0 (Critical)

**Preconditions**:
- Root agent and sub-agent implementations available

**Test Steps**:
1. Verify root agent inherits from ATOLLAgent
2. Verify sub-agent (e.g., GhidraAgent) inherits from ATOLLAgent
3. Call `get_capabilities()` on both agents
4. Call `get_supported_mcp_servers()` on both agents
5. Call `process()` with test prompt on both agents

**Expected Results**:
- `isinstance(root_agent, ATOLLAgent)` returns True
- `isinstance(ghidra_agent, ATOLLAgent)` returns True
- All abstract methods implemented
- Process returns dict with required keys: `response`, `reasoning`

**Pass/Fail Criteria**:
- No TypeError or NotImplementedError exceptions
- Process returns valid response structure

---

#### TEST-H003: Agent LLM Configuration
**Requirement**: FR-H003
**Type**: Automated Integration Test
**Priority**: P0 (Critical)

**Preconditions**:
- GhidraAgent with custom LLM config in agent.toml:
  ```toml
  [llm]
  model = "codellama:7b"
  temperature = 0.3
  ```

**Test Steps**:
1. Load GhidraAgent
2. Verify agent.llm.model == "codellama:7b"
3. Verify agent.llm.temperature == 0.3
4. Switch to GhidraAgent: `switchto GhidraAgent`
5. Send prompt: "Analyze function"
6. Capture LLM model used from logs

**Expected Results**:
- Agent uses codellama:7b, not root agent's llama2
- Temperature setting applied
- LLM connectivity validated on agent load
- Prompt processed with agent-specific model

**Pass/Fail Criteria**:
- Logs confirm correct model used
- No fallback to root agent's LLM

---

#### TEST-H004: Sub-Agent Discovery
**Requirement**: FR-H004
**Type**: Automated Integration Test
**Priority**: P1 (High)

**Preconditions**:
- Agent directory structure:
  ```
  atoll_agents/
    ghidra_agent/
      agent.toml
    web_research_agent/
      agent.toml
      analyzer_sub/
        agent.toml
  ```

**Test Steps**:
1. Start ATOLL
2. Verify startup log shows: "Discovered agent: GhidraAgent"
3. Verify startup log shows: "Discovered agent: WebResearchAgent"
4. Run `list agents`
5. Verify both top-level agents displayed
6. Switch to WebResearchAgent
7. Run `list agents`
8. Verify analyzer_sub displayed as sub-agent

**Expected Results**:
- All agents discovered recursively
- Hierarchy structure correct (parent-child relationships)
- No circular reference errors
- Sub-agents lazy-loaded (not all loaded on startup)

**Pass/Fail Criteria**:
- Agent count matches directory structure
- Hierarchy depth correctly parsed

---

#### TEST-H005: Navigation - Switch To Command
**Requirement**: FR-H005
**Type**: Automated Integration Test
**Priority**: P0 (Critical)

**Preconditions**:
- GhidraAgent available as sub-agent of root

**Test Steps**:
1. Start ATOLL at root level
2. Measure start time
3. Run `switchto GhidraAgent`
4. Measure end time (should be <500ms)
5. Verify UI header shows breadcrumb: "Main > GhidraAgent"
6. Run `list tools`
7. Verify only GhidraAgent's tools shown
8. Run `list mcp`
9. Verify only GhidraAgent's MCP servers shown

**Expected Results**:
- Context switch completes within 500ms
- Breadcrumb updates immediately
- Current context is GhidraAgent (not root)
- Tools/servers reflect current agent

**Pass/Fail Criteria**:
- Timing requirement met
- Context fully switched (verified by tool list)

---

#### TEST-H006: Navigation - Back Command
**Requirement**: FR-H006
**Type**: Automated Integration Test
**Priority**: P0 (Critical)

**Preconditions**:
- User navigated to GhidraAgent (from TEST-H005)

**Test Steps**:
1. At GhidraAgent context
2. Measure start time
3. Run `back`
4. Measure end time (should be <200ms)
5. Verify breadcrumb shows "Main ATOLL" (no sub-agents)
6. Run `list tools`
7. Verify root agent's tools shown
8. Run `back` again at root level
9. Verify warning message displayed

**Expected Results**:
- Context restored to root within 200ms
- Breadcrumb updates
- Tools revert to root agent's
- Back at root shows "Already at top level"

**Pass/Fail Criteria**:
- Timing requirement met
- Correct warning at top level

---

#### TEST-H007: Breadcrumb Display
**Requirement**: FR-H007
**Type**: Manual Test
**Priority**: P1 (High)

**Preconditions**:
- Multi-level hierarchy: Root > WebResearch > Analyzer

**Test Steps**:
1. Start ATOLL
2. Verify header shows "Main ATOLL"
3. `switchto WebResearchAgent`
4. Verify header shows "Main > WebResearchAgent"
5. `switchto AnalyzerSubAgent`
6. Verify header shows "Main > WebResearchAgent > AnalyzerSubAgent"
7. Create deep hierarchy (5+ levels)
8. Navigate to deepest level
9. Verify breadcrumb truncated with ellipsis if >80 chars

**Expected Results**:
- Full path displayed at each level
- Separator: " > "
- Current agent color-coded (e.g., bright/bold)
- Truncation format: "Main > ... > Agent4 > Agent5"

**Pass/Fail Criteria**:
- Breadcrumb always visible and accurate
- Truncation preserves current and immediate parent

---

#### TEST-H008: Context-Aware Tool Listing
**Requirement**: FR-H008
**Type**: Automated Integration Test
**Priority**: P1 (High)

**Preconditions**:
- Root agent has tools: [filesystem_read, web_search]
- GhidraAgent has tools: [decompile_function, list_functions]

**Test Steps**:
1. At root level: `list tools`
2. Capture tool list (should be [filesystem_read, web_search])
3. `switchto GhidraAgent`
4. `list tools`
5. Capture tool list (should be [decompile_function, list_functions])
6. Verify NO root tools shown
7. `back`
8. `list tools`
9. Verify NO Ghidra tools shown

**Expected Results**:
- Tool listing reflects ONLY current agent
- No cross-contamination of tools
- Updates immediately on context switch

**Pass/Fail Criteria**:
- Tool lists match expected for each context
- Zero overlap when contexts different

---

#### TEST-H009: Context-Aware MCP Server Listing
**Requirement**: FR-H009
**Type**: Automated Integration Test
**Priority**: P1 (High)

**Preconditions**:
- Root agent has MCP servers: [filesystem, web]
- GhidraAgent has MCP servers: [ghidramcp]

**Test Steps**:
1. At root level: `list mcp`
2. Verify output shows: filesystem, web
3. Verify connection status shown for each
4. `switchto GhidraAgent`
5. `list mcp`
6. Verify output shows: ghidramcp only
7. Verify connection status shown

**Expected Results**:
- Server listing scoped to current agent
- Connection status accurate (connected/disconnected)
- Server type displayed (stdio/http/sse)

**Pass/Fail Criteria**:
- Server lists match agent configuration
- Status reflects actual connectivity

---

#### TEST-H010: Context-Aware Sub-Agent Listing
**Requirement**: FR-H010
**Type**: Automated Integration Test
**Priority**: P1 (High)

**Preconditions**:
- Root has children: [GhidraAgent, WebResearchAgent]
- WebResearchAgent has children: [AnalyzerSubAgent]

**Test Steps**:
1. At root: `list agents`
2. Verify shows: GhidraAgent, WebResearchAgent only
3. Verify does NOT show: AnalyzerSubAgent
4. `switchto WebResearchAgent`
5. `list agents`
6. Verify shows: AnalyzerSubAgent only
7. Verify does NOT show: GhidraAgent

**Expected Results**:
- Lists ONLY direct children
- No siblings, no grandchildren
- Shows agent descriptions and capabilities

**Pass/Fail Criteria**:
- Agent lists match expected hierarchy
- No incorrect agents shown

---

#### TEST-H011: Prompt Routing to Current Agent
**Requirement**: FR-H011
**Type**: Automated Integration Test
**Priority**: P0 (Critical)

**Preconditions**:
- GhidraAgent configured with codellama model
- Root agent configured with llama2 model

**Test Steps**:
1. At root level, enter prompt mode
2. Send prompt: "Hello"
3. Capture model used from logs (should be llama2)
4. Enter command mode, `switchto GhidraAgent`
5. Enter prompt mode
6. Send prompt: "Decompile function"
7. Capture model used from logs (should be codellama)
8. Verify response includes GhidraAgent's reasoning style

**Expected Results**:
- Root prompt processed by root agent's LLM
- GhidraAgent prompt processed by GhidraAgent's LLM
- Reasoning engine specific to agent executed
- Tool invocations use current agent's MCP servers

**Pass/Fail Criteria**:
- Logs confirm correct agent processed prompt
- Correct LLM model used

---

#### TEST-H012: Agent Memory Isolation
**Requirement**: FR-H012
**Type**: Automated Integration Test
**Priority**: P1 (High)

**Preconditions**:
- Root and GhidraAgent both available

**Test Steps**:
1. At root, prompt mode
2. Send: "My name is Alice"
3. Agent responds acknowledging name
4. Send: "What is my name?"
5. Verify agent responds "Alice"
6. `switchto GhidraAgent`
7. Prompt mode: "What is my name?"
8. Verify agent does NOT know name (fresh conversation)
9. Send: "My name is Bob"
10. `back` to root
11. Prompt: "What is my name?"
12. Verify agent responds "Alice" (not Bob)

**Expected Results**:
- Each agent has independent conversation memory
- Switching agents does not transfer history
- Returning to agent restores previous memory

**Pass/Fail Criteria**:
- Memory correctly isolated between agents
- Memory persists across navigation

---

## 3. REST API Server Mode Tests

### Test Suite: S - Server Mode

#### TEST-S001: Ollama API - Generate Endpoint
**Requirement**: FR-S001
**Type**: Automated API Test
**Priority**: P0 (Critical)

**Preconditions**:
- GhidraAgent running in server mode on port 8080

**Test Steps**:
```bash
curl -X POST http://localhost:8080/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ghidra-agent",
    "prompt": "Analyze binary",
    "stream": false
  }'
```

**Expected Results**:
- HTTP 200 response
- JSON body contains:
  ```json
  {
    "model": "ghidra-agent",
    "created_at": "<timestamp>",
    "response": "<analysis result>",
    "done": true
  }
  ```
- Response time < 5 seconds

**Pass/Fail Criteria**:
- Valid JSON response
- All required fields present
- Prompt processed correctly

---

#### TEST-S002: Ollama API - Streaming Generate
**Requirement**: FR-S001
**Type**: Automated API Test
**Priority**: P1 (High)

**Preconditions**:
- Agent server running

**Test Steps**:
```bash
curl -X POST http://localhost:8080/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agent-name",
    "prompt": "Long analysis task",
    "stream": true
  }'
```

**Expected Results**:
- HTTP 200 response
- Content-Type: application/x-ndjson
- Multiple JSON objects streamed
- Each object has `response` field
- Final object has `done: true`

**Pass/Fail Criteria**:
- Streaming works without buffering
- Final message received
- No connection timeouts

---

#### TEST-S003: Ollama API - Chat Endpoint
**Requirement**: FR-S002
**Type**: Automated API Test
**Priority**: P0 (Critical)

**Preconditions**:
- Agent server running with session management

**Test Steps**:
```bash
# First message
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "model": "agent-name",
    "messages": [
      {"role": "user", "content": "My name is Alice"}
    ]
  }'

# Capture session ID from response or Set-Cookie header

# Second message with same session
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -H "Cookie: session_id=<captured-id>" \
  -d '{
    "model": "agent-name",
    "messages": [
      {"role": "user", "content": "My name is Alice"},
      {"role": "assistant", "content": "Hello Alice!"},
      {"role": "user", "content": "What is my name?"}
    ]
  }'
```

**Expected Results**:
- First message creates session
- Second message retrieves session
- Agent responds "Alice" to name question
- Conversation history maintained

**Pass/Fail Criteria**:
- Session persistence works
- History correctly applied

---

#### TEST-S004: Ollama API - Model List
**Requirement**: FR-S003
**Type**: Automated API Test
**Priority**: P1 (High)

**Preconditions**:
- Deployment server managing 3 agents: ghidra, web-research, analyzer

**Test Steps**:
```bash
curl http://localhost:8080/api/tags
```

**Expected Results**:
- HTTP 200 response
- JSON body:
  ```json
  {
    "models": [
      {
        "name": "ghidra-agent",
        "modified_at": "2026-01-01T12:00:00Z",
        "size": 1234567890
      },
      {
        "name": "web-research-agent",
        "modified_at": "2026-01-01T12:05:00Z",
        "size": 987654321
      },
      {
        "name": "analyzer-agent",
        "modified_at": "2026-01-01T12:10:00Z",
        "size": 555666777
      }
    ]
  }
  ```

**Pass/Fail Criteria**:
- All available agents listed
- Metadata accurate

---

#### TEST-S005: Ollama API - Embeddings
**Requirement**: FR-S004
**Type**: Automated API Test
**Priority**: P2 (Medium)

**Preconditions**:
- Agent LLM supports embeddings

**Test Steps**:
```bash
curl -X POST http://localhost:8080/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agent-name",
    "prompt": "Binary analysis with Ghidra"
  }'
```

**Expected Results**:
- HTTP 200 response
- JSON body:
  ```json
  {
    "embedding": [0.123, -0.456, 0.789, ...]
  }
  ```
- Embedding dimension matches model (e.g., 4096 for llama2)
- Response time < 1 second

**Pass/Fail Criteria**:
- Embedding generated
- Correct dimensions
- Performance acceptable

---

#### TEST-S006: ATOLL Extension - Agent Hierarchy Endpoint
**Requirement**: FR-S005
**Type**: Automated API Test
**Priority**: P1 (High)

**Preconditions**:
- Root agent with GhidraAgent and WebResearchAgent children

**Test Steps**:
```bash
# Get root agent info
curl http://localhost:8080/atoll/agents

# Get specific agent
curl http://localhost:8080/atoll/agents/GhidraAgent
```

**Expected Results**:
- First request returns root agent with sub-agents list
- Second request returns GhidraAgent details:
  ```json
  {
    "name": "GhidraAgent",
    "capabilities": ["binary_analysis", "decompilation"],
    "llm_model": "codellama:7b",
    "mcp_servers": ["ghidramcp"],
    "sub_agents": []
  }
  ```

**Pass/Fail Criteria**:
- Hierarchy structure correct
- All metadata present

---

#### TEST-S007: ATOLL Extension - Context Switch via API
**Requirement**: FR-S005
**Type**: Automated API Test
**Priority**: P1 (High)

**Preconditions**:
- Agent server with session management

**Test Steps**:
```bash
# Switch to GhidraAgent
curl -X PUT http://localhost:8080/atoll/agents/GhidraAgent/activate \
  -H "Authorization: Bearer <token>" \
  -H "Cookie: session_id=<session>"

# Verify context switched
curl http://localhost:8080/atoll/status \
  -H "Cookie: session_id=<session>"

# Should show current_agent: GhidraAgent

# Switch back
curl -X DELETE http://localhost:8080/atoll/agents/GhidraAgent/activate \
  -H "Cookie: session_id=<session>"
```

**Expected Results**:
- PUT activates agent (equivalent to `switchto`)
- Subsequent requests in session use GhidraAgent context
- DELETE deactivates (equivalent to `back`)
- Session context persists across requests

**Pass/Fail Criteria**:
- Context switch reflected in session
- Tools/servers change accordingly

---

#### TEST-S008: ATOLL Extension - MCP Tool Invocation
**Requirement**: FR-S006
**Type**: Automated API Test
**Priority**: P1 (High)

**Preconditions**:
- GhidraAgent active with decompile_function tool

**Test Steps**:
```bash
curl -X POST http://localhost:8080/atoll/tools/decompile_function \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "address": "0x401000"
    }
  }'
```

**Expected Results**:
- HTTP 200 response
- JSON body:
  ```json
  {
    "result": "<decompiled C code>",
    "execution_time_ms": 1234,
    "tool_server": "ghidramcp"
  }
  ```
- Tool executed directly (no LLM invocation)
- Response time < 30 seconds

**Pass/Fail Criteria**:
- Tool executes successfully
- Result matches expected format
- Errors handled gracefully (e.g., invalid address)

---

#### TEST-S009: ATOLL Extension - Status Endpoint
**Requirement**: FR-S007
**Type**: Automated API Test
**Priority**: P0 (Critical)

**Preconditions**:
- Agent server running with healthy connections

**Test Steps**:
```bash
# Basic health check
curl http://localhost:8080/atoll/status

# Detailed health check
curl http://localhost:8080/atoll/status?detailed=true
```

**Expected Results**:
- Basic: HTTP 200, JSON:
  ```json
  {
    "status": "healthy",
    "llm_connected": true,
    "mcp_servers": {
      "ghidramcp": "connected"
    }
  }
  ```
- Detailed adds:
  ```json
  {
    "memory_usage_mb": 512,
    "active_sessions": 5,
    "request_queue_length": 0
  }
  ```
- Response time < 100ms

**Pass/Fail Criteria**:
- Always responds within 100ms
- Returns 503 if LLM disconnected

---

#### TEST-S010: Session Management
**Requirement**: FR-S008
**Type**: Automated API Test
**Priority**: P1 (High)

**Preconditions**:
- Agent server with session configuration (30 min timeout)

**Test Steps**:
1. Make request without session ID
2. Capture session ID from response
3. Make 5 requests with same session ID
4. Verify conversation history maintained
5. Wait 31 minutes (or adjust timeout to 1 min for test)
6. Make request with expired session ID
7. Verify new session created

**Expected Results**:
- New session created on first request
- Session persists across requests
- Session expires after timeout
- Max session limit enforced (e.g., 1000 sessions)

**Pass/Fail Criteria**:
- Session lifecycle correct
- Expiration works
- Memory doesn't leak from expired sessions

---

#### TEST-S011: Authentication - JWT Validation
**Requirement**: FR-S009
**Type**: Automated Security Test
**Priority**: P0 (Critical)

**Preconditions**:
- Agent server configured with JWT public key
- Valid JWT token generated

**Test Steps**:
```bash
# Valid token
curl -X POST http://localhost:8080/api/generate \
  -H "Authorization: Bearer <valid-token>" \
  -d '{"model": "agent", "prompt": "test"}'

# Invalid signature
curl -X POST http://localhost:8080/api/generate \
  -H "Authorization: Bearer <tampered-token>" \
  -d '{"model": "agent", "prompt": "test"}'

# Expired token
curl -X POST http://localhost:8080/api/generate \
  -H "Authorization: Bearer <expired-token>" \
  -d '{"model": "agent", "prompt": "test"}'

# No token
curl -X POST http://localhost:8080/api/generate \
  -d '{"model": "agent", "prompt": "test"}'
```

**Expected Results**:
- Valid token: HTTP 200
- Invalid signature: HTTP 401, message: "Invalid token signature"
- Expired token: HTTP 401, message: "Token expired"
- No token: HTTP 401, message: "Authorization required"

**Pass/Fail Criteria**:
- Only valid tokens accepted
- Appropriate error messages

---

#### TEST-S012: Rate Limiting
**Requirement**: FR-S010
**Type**: Automated Performance Test
**Priority**: P1 (High)

**Preconditions**:
- Agent server with rate limit: 100 req/min per user

**Test Steps**:
1. Generate valid JWT token
2. Send 100 requests within 30 seconds
3. Verify all succeed (HTTP 200)
4. Send 101st request
5. Verify rate limit error (HTTP 429)
6. Capture Retry-After header
7. Wait specified time
8. Retry request
9. Verify success

**Expected Results**:
- First 100 requests succeed
- 101st request: HTTP 429
- Response body: `{"error": "Rate limit exceeded"}`
- Retry-After header present (e.g., "Retry-After: 30")
- After wait, requests succeed again

**Pass/Fail Criteria**:
- Rate limiting works per user
- Headers correct
- Limit resets after window

---

## 4. Deployment System Tests

### Test Suite: D - Deployment System

#### TEST-D001: Deployment Controller Startup
**Requirement**: FR-D001
**Type**: Automated Integration Test
**Priority**: P0 (Critical)

**Preconditions**:
- PostgreSQL database running
- Controller configuration file present

**Test Steps**:
```bash
atoll-controller --config controller.yaml
```

**Expected Results**:
- Controller starts within 10 seconds
- Listens on configured port (default 9000)
- Database connection established
- Health endpoint responds:
  ```bash
  curl http://localhost:9000/health
  # Returns: {"status": "healthy"}
  ```

**Pass/Fail Criteria**:
- Startup completes successfully
- Health check passes

---

#### TEST-D002: Deployment Server Registration
**Requirement**: FR-D002
**Type**: Automated Integration Test
**Priority**: P0 (Critical)

**Preconditions**:
- Deployment controller running
- Deployment server starting up

**Test Steps**:
1. Start deployment server: `atoll-deployment-server --controller http://localhost:9000`
2. Verify registration request sent to controller
3. Query controller: `curl http://localhost:9000/controller/servers`
4. Verify deployment server appears in list
5. Stop deployment server
6. Wait 90 seconds (heartbeat timeout)
7. Query controller again
8. Verify server marked as offline

**Expected Results**:
- Registration completes within 5 seconds
- Server metadata includes: hostname, IP, CPU cores, RAM, disk
- Heartbeats sent every 30 seconds
- Server marked offline after missed heartbeats
- Deregistration on clean shutdown

**Pass/Fail Criteria**:
- Registration successful
- Heartbeat mechanism works
- Cleanup on shutdown/timeout

---

#### TEST-D003: Agent Deployment Request
**Requirement**: FR-D003
**Type**: Automated Integration Test
**Priority**: P0 (Critical)

**Preconditions**:
- Controller running with 2 registered deployment servers
- Server A: 4 CPU cores, 8GB RAM, 1 agent running
- Server B: 8 CPU cores, 16GB RAM, 0 agents running

**Test Steps**:
```bash
curl -X POST http://localhost:9000/controller/agents \
  -H "Content-Type: application/json" \
  -d '{
    "agent_toml": "<base64-encoded-ghidra-agent.toml>",
    "preferences": {
      "high_memory": true
    }
  }'
```

**Expected Results**:
- Controller selects Server B (more resources)
- Response within 10 seconds:
  ```json
  {
    "deployment_id": "deploy-12345",
    "agent_name": "GhidraAgent",
    "server_id": "server-B",
    "status": "provisioning",
    "agent_url": "http://server-b-ip:8080"
  }
  ```
- Agent provisioning begins on Server B

**Pass/Fail Criteria**:
- Correct server selected
- Deployment initiated
- Status trackable via deployment_id

---

#### TEST-D004: Agent Provisioning - Success Case
**Requirement**: FR-D004
**Type**: Automated Integration Test
**Priority**: P0 (Critical)

**Preconditions**:
- Deployment server receives agent deployment request
- Agent .toml specifies Python packages: pydantic, aiohttp

**Test Steps**:
1. Deployment server receives request
2. Creates venv at `~/.atoll/agents/GhidraAgent/venv`
3. Installs dependencies
4. Starts agent server process
5. Waits for agent /atoll/status to return 200
6. Reports success to controller

**Expected Results**:
- Venv created successfully
- All packages installed
- Agent process started with correct PID
- Agent responds to health checks within 10 seconds
- Provisioning completes within 2 minutes
- Logs captured to `~/.atoll/agents/GhidraAgent/logs/`

**Pass/Fail Criteria**:
- Agent accessible at assigned URL
- Health check passes
- No errors in provisioning logs

---

#### TEST-D005: Agent Provisioning - Failure Case
**Requirement**: FR-D004
**Type**: Automated Integration Test
**Priority**: P1 (High)

**Preconditions**:
- Deployment server receives request
- Agent .toml specifies invalid package: "nonexistent-package==1.0.0"

**Test Steps**:
1. Deployment server attempts provisioning
2. Venv creation succeeds
3. Pip install fails
4. Rollback triggered

**Expected Results**:
- Venv deleted after failure
- Error reported to controller:
  ```json
  {
    "deployment_id": "deploy-12345",
    "status": "failed",
    "error": "Failed to install dependencies: nonexistent-package==1.0.0 not found"
  }
  ```
- No orphaned processes or files
- Server remains in healthy state (can provision other agents)

**Pass/Fail Criteria**:
- Failure detected
- Cleanup successful
- Error message helpful

---

#### TEST-D006: Multiple Agent Management
**Requirement**: FR-D005
**Type**: Automated Integration Test
**Priority**: P1 (High)

**Preconditions**:
- Deployment server with capacity for 10 agents

**Test Steps**:
1. Deploy 10 agents of different types
2. Verify all start successfully
3. Verify each has unique port
4. Verify each has isolated venv
5. Check resource usage (CPU, memory per agent)
6. Stop one agent
7. Verify others continue running
8. Restart stopped agent

**Expected Results**:
- All 10 agents run concurrently
- Ports: 8080, 8081, ..., 8089 (auto-assigned)
- Each venv independent
- Resource limits enforced per agent
- Individual agent lifecycle doesn't affect others

**Pass/Fail Criteria**:
- All agents accessible
- No port conflicts
- Isolation verified

---

#### TEST-D007: Graceful Shutdown
**Requirement**: FR-D006
**Type**: Automated Integration Test
**Priority**: P1 (High)

**Preconditions**:
- Deployment server managing 3 agents
- Agents processing requests

**Test Steps**:
1. Send SIGTERM to deployment server
2. Monitor shutdown sequence
3. Verify each agent receives SIGTERM
4. Wait up to 30 seconds per agent
5. Verify all agents stopped
6. Verify deregistration from controller
7. Verify exit code 0

**Expected Results**:
- Deployment server intercepts SIGTERM
- Agents given time to finish requests
- Agents stopped within timeout
- Unresponsive agents killed (SIGKILL)
- Clean deregistration
- Logs show orderly shutdown

**Pass/Fail Criteria**:
- No data loss
- All processes terminated
- Controller updated

---

#### TEST-D008: Agent TOML Validation
**Requirement**: FR-D007
**Type**: Automated Unit Test
**Priority**: P1 (High)

**Preconditions**:
- TOML parser with pydantic validation

**Test Cases**:

**Valid TOML**:
```toml
[agent]
name = "TestAgent"
version = "1.0.0"

[llm]
model = "llama2"

[dependencies]
python = ">=3.9"
packages = ["pydantic"]

[resources]
cpu_limit = 1.0
memory_limit = "2GB"
```
Expected: Validation passes

**Missing Required Field**:
```toml
[agent]
# Missing 'name'
version = "1.0.0"
```
Expected: ValidationError: "Field 'name' is required"

**Invalid Python Version**:
```toml
[dependencies]
python = ">=3.6"  # Too old
```
Expected: ValidationError: "Python version must be >=3.9"

**Invalid Memory Format**:
```toml
[resources]
memory_limit = "2000"  # Should be "2GB" or "2000MB"
```
Expected: ValidationError: "Invalid memory format"

**Pass/Fail Criteria**:
- Valid configs pass
- Invalid configs rejected with helpful messages

---

#### TEST-D009: Resource Limit Enforcement
**Requirement**: FR-D009
**Type**: Automated Performance Test
**Priority**: P1 (High)

**Preconditions**:
- Linux with cgroups support
- Agent .toml specifies:
  ```toml
  [resources]
  cpu_limit = 1.0  # 1 core
  memory_limit = "1GB"
  ```

**Test Steps**:
1. Deploy agent
2. Verify cgroup created: `/sys/fs/cgroup/atoll/GhidraAgent/`
3. Check CPU limit: `cat cpu.cfs_quota_us` (should be 100000 for 1 core)
4. Check memory limit: `cat memory.limit_in_bytes` (should be ~1GB)
5. Send memory-intensive request to agent
6. Monitor memory usage
7. Verify agent killed if exceeds 1GB

**Expected Results**:
- Cgroup configured correctly
- Agent runs within limits normally
- Agent terminated if exceeds memory limit
- CPU throttled if exceeds CPU limit (not killed)
- Logs indicate resource limit violation

**Pass/Fail Criteria**:
- Limits enforced
- Violations detected and handled

---

#### TEST-D010: Health Monitoring and Restart
**Requirement**: FR-D010
**Type**: Automated Integration Test
**Priority**: P1 (High)

**Preconditions**:
- Agent deployed with health check interval 30s
- Max restarts: 3

**Test Steps**:
1. Agent running normally
2. Manually kill agent process (simulate crash)
3. Wait for next health check (up to 30s)
4. Verify deployment server detects failure
5. Verify auto-restart within 10 seconds
6. Repeat crash 3 more times
7. After 3rd restart, crash again
8. Verify agent not restarted (max reached)

**Expected Results**:
- Health check detects failure within interval
- Agent restarted automatically (up to 3 times)
- After max restarts, agent marked as failed
- Controller notified of failures
- Logs show restart attempts and reasons

**Pass/Fail Criteria**:
- Auto-restart works
- Max restarts enforced
- Notifications sent

---

## 5. Hierarchical Distributed Mode Tests

### Test Suite: HD - Hierarchical Distributed

#### TEST-HD001: Parent-Child HTTP Communication
**Requirement**: FR-HD001
**Type**: Automated Integration Test
**Priority**: P0 (Critical)

**Preconditions**:
- Root agent running on Server A (port 8080)
- GhidraAgent running on Server B (port 8080)
- Root agent configured with GhidraAgent URL

**Test Steps**:
1. User sends prompt to root agent via API
2. Root agent determines it needs binary analysis
3. Root agent delegates to GhidraAgent via POST /api/generate
4. GhidraAgent processes and responds
5. Root agent receives response
6. Root agent incorporates into final answer

**Expected Results**:
- HTTP request from parent to child succeeds
- Auth token included in request
- Response received within 5 seconds
- Parent agent handles child's response
- User sees combined result

**Pass/Fail Criteria**:
- Communication successful
- No auth failures
- Delegation transparent to user

---

#### TEST-HD002: Agent Connection Configuration in TOML
**Requirement**: FR-HD002
**Type**: Automated Integration Test
**Priority**: P1 (High)

**Preconditions**:
- Root agent .toml includes:
  ```toml
  [sub_agents.ghidra]
  name = "GhidraAgent"
  url = "http://192.168.1.100:8080"
  auth_token = "${GHIDRA_TOKEN}"
  ```
- Environment variable GHIDRA_TOKEN set

**Test Steps**:
1. Deploy root agent
2. Verify sub-agent config parsed
3. Verify environment variable interpolated
4. Verify connectivity test to child URL
5. Try accessing child via root

**Expected Results**:
- Child URL loaded from config
- Env var interpolation works
- Connectivity validated on startup
- Connection cached for reuse

**Pass/Fail Criteria**:
- Config parsing correct
- Connection established
- Env vars resolved

---

#### TEST-HD003: Load Balancing - Deployment Server Level
**Requirement**: FR-HD003
**Type**: Automated Performance Test
**Priority**: P1 (High)

**Preconditions**:
- Deployment server managing 3 instances of GhidraAgent
- Round-robin algorithm configured

**Test Steps**:
1. Send 30 requests to deployment server's GhidraAgent endpoint
2. Track which instance handled each request
3. Verify distribution: Instance A: 10, Instance B: 10, Instance C: 10
4. Mark Instance B as unhealthy
5. Send 20 more requests
6. Verify distribution: Instance A: 10, Instance C: 10, Instance B: 0

**Expected Results**:
- Even distribution when all healthy
- Failed instance excluded from rotation
- Minimal latency from routing logic (<10ms)

**Pass/Fail Criteria**:
- Distribution as expected
- Unhealthy instances excluded

---

#### TEST-HD004: Service Discovery via Controller
**Requirement**: FR-HD005
**Type**: Automated Integration Test
**Priority**: P1 (High)

**Preconditions**:
- Controller managing 5 deployment servers
- 3 instances of GhidraAgent deployed across servers

**Test Steps**:
```bash
curl http://localhost:9000/controller/discover?name=GhidraAgent
```

**Expected Results**:
- HTTP 200 response
- JSON body:
  ```json
  {
    "agent_name": "GhidraAgent",
    "instances": [
      {
        "url": "http://192.168.1.10:8080",
        "server_id": "server-1",
        "status": "healthy",
        "load": 0.3
      },
      {
        "url": "http://192.168.1.15:8081",
        "server_id": "server-2",
        "status": "healthy",
        "load": 0.5
      },
      {
        "url": "http://192.168.1.20:8080",
        "server_id": "server-3",
        "status": "degraded",
        "load": 0.9
      }
    ]
  }
  ```
- Response time < 100ms

**Pass/Fail Criteria**:
- All instances discovered
- Status accurate
- Performance acceptable

---

#### TEST-HD005: Capability-Based Discovery
**Requirement**: FR-HD005
**Type**: Automated Integration Test
**Priority**: P2 (Medium)

**Preconditions**:
- GhidraAgent with capabilities: ["binary_analysis", "decompilation"]
- WebResearchAgent with capabilities: ["web_search", "summarization"]

**Test Steps**:
```bash
curl http://localhost:9000/controller/discover?capability=decompilation
```

**Expected Results**:
- Returns only GhidraAgent instances
- Does not return WebResearchAgent

**Pass/Fail Criteria**:
- Capability filtering works
- Only matching agents returned

---

## 6. Non-Functional Requirement Tests

### Test Suite: NFR - Non-Functional

#### TEST-NFR-P001: Response Time Performance
**Requirement**: NFR-P001
**Type**: Automated Performance Test
**Priority**: P0 (Critical)

**Preconditions**:
- Agent on standard hardware (4 core, 8GB RAM)
- LLM model: llama2:7b

**Test Steps**:
1. Send 100 simple prompts (<100 tokens each)
2. Measure response time for each
3. Calculate 95th percentile

**Expected Results**:
- 95th percentile < 5 seconds
- Mean < 3 seconds
- No timeouts

**Pass/Fail Criteria**:
- 95th percentile meets target
- Standard deviation < 2 seconds

---

#### TEST-NFR-P002: Throughput Under Load
**Requirement**: NFR-P002
**Type**: Automated Load Test
**Priority**: P1 (High)

**Preconditions**:
- Agent server deployed
- Locust load testing tool configured

**Test Steps**:
1. Ramp up to 50 concurrent users over 2 minutes
2. Maintain 50 users for 10 minutes
3. Measure throughput (requests/second)
4. Compare to baseline (5 concurrent users)

**Expected Results**:
- Throughput with 50 users >= 90% of baseline throughput
- Error rate < 1%
- P95 response time < 10 seconds

**Pass/Fail Criteria**:
- Throughput degradation < 10%
- System stable under load

---

#### TEST-NFR-P003: Agent Startup Time
**Requirement**: NFR-P003
**Type**: Automated Performance Test
**Priority**: P1 (High)

**Test Steps**:
1. Initiate agent deployment
2. Start timer
3. Wait for /atoll/status to return 200
4. Stop timer

**Expected Results**:
- Startup time < 10 seconds
- Consistent across multiple deploys

**Pass/Fail Criteria**:
- 90% of deploys meet target
- No startups > 15 seconds

---

#### TEST-NFR-S001: JWT Authentication Security
**Requirement**: NFR-S001
**Type**: Manual Security Audit
**Priority**: P0 (Critical)

**Test Steps**:
1. Review JWT implementation
2. Verify RS256 algorithm used (not HS256)
3. Verify token expiration enforced
4. Attempt token tampering
5. Attempt replay attacks
6. Check for timing side-channel vulnerabilities

**Expected Results**:
- RS256 with public key validation
- Tokens expire after configured time
- Tampered tokens rejected
- Replayed expired tokens rejected

**Pass/Fail Criteria**:
- Security best practices followed
- No vulnerabilities found

---

#### TEST-NFR-S002: TLS Configuration
**Requirement**: NFR-S002
**Type**: Manual Security Audit
**Priority**: P0 (Critical)

**Test Steps**:
1. Configure nginx as TLS termination
2. Run SSL Labs test: https://www.ssllabs.com/ssltest/
3. Verify TLS 1.2+ only
4. Verify strong cipher suites
5. Verify HSTS header

**Expected Results**:
- SSL Labs grade: A or A+
- No SSL/TLS vulnerabilities (POODLE, BEAST, etc.)
- Forward secrecy enabled

**Pass/Fail Criteria**:
- Grade A minimum
- All known vulnerabilities mitigated

---

#### TEST-NFR-S003: Secrets Management
**Requirement**: NFR-S003
**Type**: Automated Security Scan
**Priority**: P0 (Critical)

**Test Steps**:
```bash
# Scan all .toml files for secrets
detect-secrets scan --all-files

# Check for common patterns
grep -r "password\|secret\|api_key" *.toml
```

**Expected Results**:
- No plaintext secrets in .toml files
- Environment variable placeholders used: `${VAR_NAME}`
- No secrets in git history

**Pass/Fail Criteria**:
- Zero secrets detected
- All configs use env vars or secret store

---

#### TEST-NFR-S004: Resource Isolation
**Requirement**: NFR-S004
**Type**: Automated Security Test
**Priority**: P1 (High)

**Test Steps**:
1. Deploy malicious agent that attempts:
   - Fork bomb (unlimited process creation)
   - Memory leak (allocate until OOM)
   - CPU spin (infinite loop)
2. Verify resource limits enforced
3. Verify agent terminated appropriately
4. Verify other agents unaffected

**Expected Results**:
- Fork bomb prevented (process limit)
- Memory leak triggers OOM killer
- CPU spin throttled to limit
- Other agents continue normally

**Pass/Fail Criteria**:
- Resource limits effective
- System remains stable

---

#### TEST-NFR-R001: Availability Target
**Requirement**: NFR-R001
**Type**: Long-running Monitoring Test
**Priority**: P1 (High)

**Test Steps**:
1. Deploy to production
2. Monitor uptime for 30 days
3. Calculate availability percentage

**Expected Results**:
- Uptime >= 99.5% (< 3.6 hours downtime/month)
- Downtime events logged and root-caused

**Pass/Fail Criteria**:
- Availability target met
- SLA compliance

---

#### TEST-NFR-R002: Graceful Degradation
**Requirement**: NFR-R002
**Type**: Automated Resilience Test
**Priority**: P1 (High)

**Test Steps**:
1. Root agent running with GhidraAgent child
2. Stop GhidraAgent
3. Send prompt requiring binary analysis
4. Verify root agent returns error
5. Send prompt NOT requiring binary analysis
6. Verify root agent still works

**Expected Results**:
- Clear error for tasks requiring unavailable child
- Other tasks continue working
- Error message: "Binary analysis agent unavailable. Please try again later."

**Pass/Fail Criteria**:
- Partial failure tolerated
- User experience acceptable

---

#### TEST-NFR-R003: Conversation Persistence
**Requirement**: NFR-R003
**Type**: Automated Integration Test
**Priority**: P2 (Medium)

**Test Steps**:
1. Start conversation with agent
2. Send 5 messages
3. Gracefully shutdown agent
4. Restart agent
5. Resume conversation
6. Verify history restored

**Expected Results**:
- Conversation history serialized on shutdown
- History restored on startup
- User can continue conversation

**Pass/Fail Criteria**:
- History correctly persisted
- No data loss

---

#### TEST-NFR-M001: Structured Logging
**Requirement**: NFR-M001
**Type**: Automated Logging Test
**Priority**: P1 (High)

**Test Steps**:
1. Configure agent with JSON logging
2. Send request with trace ID
3. Capture logs
4. Parse as JSON
5. Verify required fields present

**Expected Results**:
- All logs valid JSON
- Fields: timestamp, level, message, trace_id, agent_name
- Trace ID propagated through request chain

**Pass/Fail Criteria**:
- 100% of logs parseable
- Trace IDs correct

---

#### TEST-NFR-M002: Prometheus Metrics
**Requirement**: NFR-M002
**Type**: Automated Metrics Test
**Priority**: P1 (High)

**Test Steps**:
```bash
curl http://localhost:8080/metrics
```

**Expected Results**:
- HTTP 200 response
- Prometheus text format
- Metrics include:
  - `atoll_requests_total{agent="GhidraAgent",status="200"}`
  - `atoll_request_duration_seconds{quantile="0.95"}`
  - `atoll_active_sessions`
  - `atoll_mcp_tool_calls_total{tool="decompile_function"}`

**Pass/Fail Criteria**:
- All required metrics present
- Values accurate

---

#### TEST-NFR-M003: Configuration Reload
**Requirement**: NFR-M003
**Type**: Automated Integration Test
**Priority**: P2 (Medium)

**Test Steps**:
1. Agent running with temperature=0.7
2. Modify agent.toml: temperature=0.3
3. Send SIGHUP to agent
4. Wait 5 seconds
5. Send prompt
6. Verify new temperature used

**Expected Results**:
- Config reloaded without restart
- No downtime
- New config applied immediately

**Pass/Fail Criteria**:
- Reload works
- Zero downtime
- Config changes effective

---

#### TEST-NFR-U001: Error Message Quality
**Requirement**: NFR-U001
**Type**: Manual Usability Test
**Priority**: P2 (Medium)

**Test Scenarios**:

1. **Invalid Agent Name**: `switchto NonExistentAgent`
   - Expected: "Error: Agent 'NonExistentAgent' not found. Suggestion: Run 'list agents' to see available agents."

2. **LLM Connection Failed**: (Ollama server down)
   - Expected: "Error: Cannot connect to LLM server at http://localhost:11434. Suggestion: Ensure Ollama is running with 'ollama serve'."

3. **Tool Execution Failed**: decompile_function with invalid address
   - Expected: "Error: Tool 'decompile_function' failed: Invalid address 0xINVALID. Suggestion: Verify address format is hexadecimal (e.g., 0x401000)."

**Pass/Fail Criteria**:
- All errors follow format
- Suggestions actionable
- No stack traces shown to end users (logged only)

---

#### TEST-NFR-C001: Python Version Compatibility
**Requirement**: NFR-C001
**Type**: Automated CI Test
**Priority**: P1 (High)

**Test Steps**:
1. Run full test suite on Python 3.9, 3.10, 3.11, 3.12
2. Verify all tests pass on each version

**Expected Results**:
- Tests pass on all versions
- No deprecation warnings

**Pass/Fail Criteria**:
- 100% pass rate on all versions

---

#### TEST-NFR-C002: Cross-Platform Compatibility
**Requirement**: NFR-C002
**Type**: Automated CI Test
**Priority**: P1 (High)

**Test Steps**:
1. Run test suite on:
   - Ubuntu 22.04
   - macOS 13
   - Windows 11
2. Verify installation and tests succeed

**Expected Results**:
- Installation works on all platforms
- Tests pass with same behavior

**Pass/Fail Criteria**:
- Full compatibility on all platforms

---

#### TEST-NFR-C003: Ollama Client Compatibility
**Requirement**: NFR-C003
**Type**: Automated Integration Test
**Priority**: P1 (High)

**Test Steps**:
1. Start ATOLL agent in server mode
2. Use ollama-python client to connect
3. Execute common operations: generate, chat, list models
4. Verify responses match Ollama format

**Expected Results**:
- ollama-python client works without modification
- Responses identical to real Ollama server

**Pass/Fail Criteria**:
- Zero client code changes required
- Full API compatibility

---

## 7. Test Execution Guidelines

### 7.1 Test Phases

#### Phase 1: Component Tests (Weeks 1-6)
- Unit tests for each new class/function
- Coverage target: 85%
- Run on every commit via CI

#### Phase 2: Integration Tests (Weeks 7-12)
- End-to-end scenarios
- Multi-agent interactions
- REST API tests

#### Phase 3: System Tests (Weeks 13-18)
- Full deployment workflows
- Load and performance testing
- Security audits

#### Phase 4: Acceptance Tests (Weeks 19-24)
- User acceptance testing
- Production-like environment
- Final sign-off

### 7.2 Test Environments

#### Development
- Local machines
- Docker Compose for multi-agent setups
- Mock MCP servers

#### Staging
- Cloud VMs (AWS/GCP/Azure)
- Real Ollama servers
- Real MCP servers
- Load testing tools

#### Production
- Canary deployments
- Monitoring and alerting
- Rollback procedures

### 7.3 Defect Management

#### Severity Levels
- **P0 (Critical)**: Blocks release, requires immediate fix
- **P1 (High)**: Major feature broken, fix before release
- **P2 (Medium)**: Minor issue, can defer if needed
- **P3 (Low)**: Enhancement/nice-to-have

#### Bug Tracking
- Use GitHub Issues with labels: bug, test-failure, P0/P1/P2/P3
- Link bugs to failed test cases
- Track fix and retest in issue

### 7.4 Success Criteria

#### Test Coverage
- Unit: >= 85%
- Integration: >= 70%
- Manual: 100% of UI flows

#### Test Pass Rate
- Unit: 100% (no failures allowed)
- Integration: >= 95%
- Performance: 100% of targets met

#### Quality Gates
- No P0 bugs open
- No P1 bugs open for > 48 hours
- All acceptance tests passing

---

## 8. Test Automation Strategy

### 8.1 Tools
- **pytest**: Unit and integration tests
- **pytest-asyncio**: Async test support
- **httpx**: API testing
- **locust**: Load testing
- **detect-secrets**: Security scanning
- **GitHub Actions**: CI/CD pipelines

### 8.2 CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: ATOLL Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python: ['3.9', '3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: ${{ matrix.python }}
      - name: Install dependencies
        run: pip install -e ".[test]"
      - name: Run unit tests
        run: pytest tests/unit -v --cov=src

  integration-tests:
    runs-on: ubuntu-latest
    services:
      ollama:
        image: ollama/ollama
      postgres:
        image: postgres:14
    steps:
      - uses: actions/checkout@v2
      - name: Run integration tests
        run: pytest tests/integration -v

  performance-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v2
      - name: Run load tests
        run: locust -f tests/performance/load_test.py --headless -u 50 -r 10 -t 5m
```

---

## 9. Test Data and Fixtures

### 9.1 Sample Agent Configurations

#### Valid GhidraAgent TOML
```toml
[agent]
name = "GhidraAgent"
version = "1.0.0"
description = "Binary analysis specialist"
capabilities = ["binary_analysis", "decompilation"]

[llm]
model = "codellama:7b"
temperature = 0.3
system_prompt = "You are an expert reverse engineer."

[dependencies]
python = ">=3.9"
packages = ["pydantic>=2.0", "aiohttp>=3.9"]

[resources]
cpu_limit = 2.0
memory_limit = "4GB"
max_concurrent_requests = 10

[mcp_servers.ghidramcp]
type = "stdio"
command = "python"
args = ["-m", "ghidra_mcp_server"]
```

#### Invalid Agent TOML (Missing Required Fields)
```toml
[agent]
# Missing 'name'
version = "1.0.0"
```

### 9.2 Mock MCP Servers
- `tests/fixtures/mock_mcp_server.py`: Simple echo server
- `tests/fixtures/mock_ghidra_server.py`: Returns fake decompilation
- `tests/fixtures/failing_mcp_server.py`: Always returns errors

### 9.3 Test JWT Tokens
- Valid token (expires in 1 hour)
- Expired token
- Invalid signature token
- Admin role token

---

## 10. Appendix

### 10.1 Test Traceability Matrix

| Requirement ID | Test Case ID | Status | Priority |
|----------------|--------------|--------|----------|
| FR-H001 | TEST-H001 | Draft | P0 |
| FR-H002 | TEST-H002 | Draft | P0 |
| FR-H003 | TEST-H003 | Draft | P0 |
| ... | ... | ... | ... |

### 10.2 Test Execution Log Template

| Date | Test ID | Status | Duration | Notes |
|------|---------|--------|----------|-------|
| 2026-01-15 | TEST-H001 | Pass | 3.2s | |
| 2026-01-15 | TEST-H002 | Fail | 1.1s | TypeError in base class |

### 10.3 Defect Report Template

```markdown
## Bug Report

**ID**: BUG-123
**Title**: Agent crashes on invalid TOML
**Severity**: P1
**Reported By**: QA Team
**Date**: 2026-01-15

### Description
When deploying agent with invalid TOML (missing 'name' field), deployment server crashes instead of returning validation error.

### Steps to Reproduce
1. Create agent.toml without 'name' field
2. POST to /controller/agents
3. Observe server crash

### Expected Behavior
Validation error returned with helpful message

### Actual Behavior
Deployment server crashes with traceback

### Fix
Add TOML validation before deployment initiation

### Related Test Cases
- TEST-D008 (Agent TOML Validation)

### Status
Fixed in PR #456, retested and passing
```

---

**Document Version History**

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 2.0.0 | 2026-01-01 | Initial acceptance test specification | QA Team |

---

**Approval Signatures**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| QA Lead | | | |
| Technical Lead | | | |
| Product Owner | | | |

---
