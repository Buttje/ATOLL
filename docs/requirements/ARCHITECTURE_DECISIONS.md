# ATOLL Architecture Decision Records (ADRs)
**Version**: 2.0.0
**Date**: January 1, 2026

---

## Introduction

This document captures the key architectural decisions made for ATOLL v2.0, including the rationale, alternatives considered, and consequences of each decision.

---

## ADR-001: Hierarchical Agent Architecture with Base Class

**Status**: Accepted
**Date**: 2026-01-01
**Deciders**: Architecture Team

### Context
ATOLL needs to support specialized agents for different domains (e.g., binary analysis, web research) while maintaining a consistent interface. We need to decide on the architecture pattern for agent hierarchy.

### Decision
Implement hierarchical agent tree with ATOLLAgent base class that all agents (including root) inherit from. Each agent can have sub-agents, forming a tree structure.

### Alternatives Considered
1. **Flat Plugin System**: All agents at same level, no hierarchy
   - Rejected: Doesn't support specialization hierarchies or delegation patterns

2. **Strategy Pattern**: Root agent delegates to strategy objects
   - Rejected: Too limiting, doesn't support multi-level hierarchies

3. **Microservices**: Each agent as independent service from the start
   - Rejected: Over-engineering for initial use case, adds unnecessary complexity

### Consequences

**Positive**:
- Uniform interface for all agents (root and children)
- Natural delegation model (parent to specialized child)
- Supports arbitrary depth hierarchies
- Each agent can have independent configuration (LLM model, MCP servers)
- Testable in isolation

**Negative**:
- Root agent requires refactoring (currently not inheriting from ATOLLAgent)
- Navigation complexity increases with depth
- Need careful memory management (each agent stores conversation history)

**Neutral**:
- Requires UI changes for breadcrumb navigation
- Need to define parent-child communication protocol

### Implementation Notes
- ATOLLAgent base class extends existing plugins/base.py
- Root agent wraps current Application.agent functionality
- AgentContext stores parent-child relationships
- Navigation stack manages current context

---

## ADR-002: Dual-Mode Operation (Local Interactive + Distributed Server)

**Status**: Accepted
**Date**: 2026-01-01
**Deciders**: Architecture Team, Product Owner

### Context
ATOLL currently operates in terminal mode only. We need to support both interactive development and production deployment with load balancing.

### Decision
Support two operational modes:
1. **Local Interactive Mode**: Terminal UI with navigation commands (current behavior + enhancements)
2. **Distributed Server Mode**: REST API servers with HTTP communication between agents

Both modes use the same ATOLLAgent base class and hierarchical structure.

### Alternatives Considered
1. **Server Mode Only**: Remove terminal UI, force REST API for all interactions
   - Rejected: Loses developer-friendly interactive experience

2. **Separate Codebases**: Maintain separate implementations for local vs. server
   - Rejected: Duplication, maintenance burden, inconsistent behavior

3. **Terminal-Only**: Keep current architecture, no server mode
   - Rejected: Doesn't support load balancing requirement

### Consequences

**Positive**:
- Developers can iterate quickly with local terminal mode
- Production deployments can scale horizontally
- Single codebase reduces maintenance
- Gradual migration path (start local, deploy to server)

**Negative**:
- Increased code complexity (two operational paths)
- Need to abstract communication layer (local vs. HTTP)
- Testing requires both modes

**Neutral**:
- Configuration must specify mode (local/server)
- Some features may be mode-specific (e.g., breadcrumbs only in terminal)

### Implementation Notes
- Agent base class provides both `process()` (local) and REST endpoints
- Communication abstracted behind interface (LocalAgentClient vs. HTTPAgentClient)
- Mode specified in deployment configuration

---

## ADR-003: Jenkins-Style Deployment Architecture

**Status**: Accepted
**Date**: 2026-01-01
**Deciders**: Architecture Team, Ops Team

### Context
ATOLL agents need to be deployed across multiple machines for load balancing. We need a deployment architecture that's scalable, resilient, and manageable.

### Decision
Implement controller-agent pattern inspired by Jenkins:
- **Deployment Controller**: Central service managing agent inventory and deployment
- **Deployment Server**: Service on each machine managing local ATOLL agents

Controller delegates deployment requests to appropriate deployment servers based on resource availability.

### Alternatives Considered
1. **Kubernetes Native**: Deploy agents as K8s pods, use K8s orchestration
   - Rejected: Requires K8s cluster, overly complex for smaller deployments

2. **Serverless (AWS Lambda/GCP Functions)**: Run agents as serverless functions
   - Rejected: Stateful LLM conversations don't fit serverless model, cold starts problematic

3. **No Central Controller**: Each deployment server operates independently
   - Rejected: Difficult to coordinate deployments, no global visibility

4. **Configuration Management Tools (Ansible/Salt)**: Use existing CM tools for deployment
   - Rejected: Not designed for dynamic runtime management, lacks health monitoring

### Consequences

**Positive**:
- Centralized visibility and control
- Proven pattern (Jenkins has been stable for years)
- Supports both small (single server) and large (hundreds of servers) deployments
- Deployment servers can operate semi-autonomously (continue if controller down)
- Easy to add new deployment servers

**Negative**:
- Controller is single point of failure (mitigation: HA controller)
- Additional component to maintain (controller + deployment servers)
- Network latency between controller and deployment servers

**Neutral**:
- Requires controller-server communication protocol (REST API)
- Need monitoring and heartbeat mechanism

### Implementation Notes
- Controller: FastAPI service with PostgreSQL backend
- Deployment Server: Python service managing local processes
- Communication: REST API with 30-second heartbeats
- HA: Active-passive controller failover (future enhancement)

---

## ADR-004: TOML for Agent Configuration

**Status**: Accepted
**Date**: 2026-01-01
**Deciders**: Architecture Team

### Context
Currently, agents use agent.json for metadata and mcp.json for MCP servers. We need a comprehensive configuration format that includes dependencies, resources, and deployment settings.

### Decision
Adopt TOML format for agent configuration (agent.toml), consolidating all agent-related configuration into a single file.

### Alternatives Considered
1. **Keep Separate JSON Files**: agent.json, mcp.json, requirements.txt
   - Rejected: Fragmented configuration, difficult to manage

2. **YAML**: Another popular configuration format
   - Rejected: Whitespace-sensitive, more error-prone than TOML

3. **Python (.py)**: Configuration as code
   - Rejected: Security risk (arbitrary code execution), difficult to validate

4. **Extended JSON**: Add sections to agent.json
   - Rejected: JSON is verbose, doesn't support comments

### Consequences

**Positive**:
- Single source of truth for agent configuration
- TOML supports comments (better documentation)
- Human-readable and writable
- Strong Python support (tomli/tomllib)
- Type validation via pydantic
- Environment variable interpolation built-in

**Negative**:
- Breaking change from agent.json (need migration path)
- Team needs to learn TOML syntax (minimal learning curve)
- Slightly larger file size than JSON

**Neutral**:
- Need backward compatibility layer (support agent.json for transition period)
- Tooling needed for validation and conversion

### Implementation Notes
- Schema defined via pydantic dataclasses (ATOLLAgentConfig)
- Parser validates on load and provides helpful error messages
- Conversion tool: `atoll convert agent.json agent.toml`
- Sections: [agent], [llm], [dependencies], [resources], [mcp_servers.*], [sub_agents.*]

---

## ADR-005: Ollama API Extension Pattern

**Status**: Accepted
**Date**: 2026-01-01
**Deciders**: Architecture Team, Product Owner

### Context
ATOLL agent servers need a REST API. We want compatibility with existing Ollama clients but also need ATOLL-specific functionality (hierarchy navigation, direct tool invocation).

### Decision
Implement core Ollama API endpoints (/api/generate, /api/chat, /api/tags, /api/embeddings) for compatibility, and add ATOLL-specific extensions under /atoll/* namespace.

### Alternatives Considered
1. **Full Ollama Compatibility**: Implement all ~15 Ollama endpoints
   - Rejected: Significant effort for rarely-used endpoints

2. **ATOLL-Only API**: Custom API with no Ollama compatibility
   - Rejected: Loses compatibility with existing tools (ollama-python, etc.)

3. **GraphQL**: Single endpoint with flexible queries
   - Rejected: Overhead not justified, REST API simpler for this use case

4. **gRPC**: Binary protocol for performance
   - Rejected: Harder to debug, limited tooling, HTTP/2 not always available

### Consequences

**Positive**:
- Existing Ollama clients work without modification
- Clear separation between compatible and ATOLL-specific features
- Easy to document (Ollama docs + ATOLL extensions)
- HTTP/REST is universal, no special client libraries needed

**Negative**:
- Need to maintain Ollama API compatibility as Ollama evolves
- Two API surface areas to document and test
- Some redundancy (e.g., /api/tags and /atoll/agents)

**Neutral**:
- Version endpoints to allow breaking changes (/atoll/v1/agents)
- OpenAPI/Swagger spec for documentation

### Implementation Notes
- Ollama endpoints: Delegate to agent.process_prompt() with format conversion
- ATOLL endpoints: Direct access to agent manager and MCP tools
- Middleware layer for authentication, rate limiting, logging
- FastAPI for implementation (automatic OpenAPI generation)

---

## ADR-006: Virtual Environment Per Agent Isolation

**Status**: Accepted
**Date**: 2026-01-01
**Deciders**: Architecture Team, Security Team

### Context
Multiple agents on a single deployment server need dependency isolation to prevent conflicts and limit security impact of compromised agents.

### Decision
Each agent runs in its own Python virtual environment (venv), created and managed by the deployment server. Resource limits enforced via cgroups (Linux) or job objects (Windows).

### Alternatives Considered
1. **Shared Environment**: All agents use same Python environment
   - Rejected: Dependency conflicts inevitable, security boundary weak

2. **Docker Containers**: Each agent in separate container
   - Rejected: Resource overhead, deployment complexity, requires container runtime

3. **Conda Environments**: Use conda instead of venv
   - Rejected: Heavier than venv, additional dependency (conda), slower

4. **Language-Level Sandboxing**: Restrict Python imports/modules
   - Rejected: Difficult to implement correctly, bypassable

### Consequences

**Positive**:
- Strong dependency isolation (no version conflicts)
- Security boundary between agents
- Easy to delete agent (rm -rf venv directory)
- Resource limits prevent DoS from misbehaving agent
- Familiar pattern for Python developers

**Negative**:
- Disk space overhead (multiple venvs)
- Installation time per agent (not shared)
- Need cgroups or equivalent for resource limits

**Neutral**:
- Deployment server manages venv lifecycle
- Agent specifies dependencies in [dependencies] section

### Implementation Notes
- Venv location: `~/.atoll/agents/{agent-name}/venv`
- Created via `python -m venv`
- Dependencies installed via pip from agent.toml
- Cgroups (Linux) or job objects (Windows) for limits
- Cleanup on agent removal

---

## ADR-007: Stateful Session Management in Server Mode

**Status**: Accepted
**Date**: 2026-01-01
**Deciders**: Architecture Team

### Context
LLM agents benefit from conversation context. REST APIs are typically stateless, but we need to maintain conversation history across requests.

### Decision
Implement stateful session management with session IDs. Sessions store conversation history, agent context, and navigation state. Sessions expire after 30 minutes of inactivity (configurable).

### Alternatives Considered
1. **Stateless**: Client includes full conversation history in each request
   - Rejected: Large request payloads, inefficient, client complexity

2. **Database-Backed Sessions**: Store all session data in PostgreSQL
   - Rejected: Overkill for typical deployments, latency overhead

3. **Redis-Backed Sessions**: Use Redis for session storage
   - Accepted for future: Good for multi-instance deployments, but adds dependency

4. **JWT-Encoded State**: Encode session state in JWT token
   - Rejected: Token size grows unbounded, security issues (client can see history)

### Consequences

**Positive**:
- Natural conversation flow (like terminal mode)
- Efficient (no redundant history transfer)
- Server controls session lifecycle
- Can implement session limits per user

**Negative**:
- Server becomes stateful (harder to scale horizontally)
- Memory usage grows with active sessions
- Need session cleanup on server restart
- Sticky sessions required if multi-instance (load balancer configuration)

**Neutral**:
- Session ID in cookie or Authorization header
- Optional Redis backend for production deployments
- Session limits configurable (max 1000 per server default)

### Implementation Notes
- In-memory sessions: Python dict with LRU eviction
- Session model: user_id, agent_context, messages, created_at, last_activity
- Cleanup task: Every 5 minutes, remove expired sessions
- Redis backend (optional): Use aioredis for async operations

---

## ADR-008: Load Balancing at Deployment Server Level

**Status**: Accepted
**Date**: 2026-01-01
**Deciders**: Architecture Team, Ops Team

### Context
To support load balancing, we need to determine where load balancing decisions are made: at the deployment controller, deployment server, external load balancer, or combination.

### Decision
Implement **two-tier load balancing**:
1. **Deployment Server Level**: If multiple instances of same agent on one server, deployment server load-balances between them (least connections algorithm)
2. **External Load Balancer Level**: Nginx/HAProxy distributes across deployment servers (round-robin or least-conn)

Hierarchical architecture preserved: Parent agent knows child agent URLs (from deployment controller discovery).

### Alternatives Considered
1. **Controller-Level Only**: Controller makes all routing decisions
   - Rejected: Controller becomes bottleneck, single point of failure for request path

2. **Client-Side Load Balancing**: Clients implement retry/failover logic
   - Rejected: Duplicates logic in every client, no centralized control

3. **No Load Balancing**: Single instance per agent, scale vertically only
   - Rejected: Doesn't meet requirement for horizontal scaling

4. **Service Mesh (Istio/Linkerd)**: Use service mesh for routing
   - Rejected: Over-engineering, requires Kubernetes, adds complexity

### Consequences

**Positive**:
- Deployment server optimizes intra-machine load distribution
- External LB provides machine-level distribution
- No single bottleneck in request path
- Supports heterogeneous deployments (different agents on different servers)
- Parent agents can cache child URLs for performance

**Negative**:
- Two load balancing layers to configure and monitor
- Need service discovery for parent agents to find children
- Sticky sessions required for stateful connections

**Neutral**:
- External LB configuration documented but not provided by ATOLL
- Deployment controller provides /discover endpoint for service discovery

### Implementation Notes
- Deployment server: Maintain pool of agent instances, route to least-loaded
- Parent agent: Query controller on startup for child URLs, cache with TTL
- Health checks: Deployment server checks instance health, external LB checks deployment server health
- Nginx example config provided in documentation

---

## ADR-009: JWT with RS256 for Authentication

**Status**: Accepted
**Date**: 2026-01-01
**Deciders**: Architecture Team, Security Team

### Context
Agent servers need authentication in multi-tenant deployments. We need a secure, scalable authentication mechanism.

### Decision
Use JWT (JSON Web Tokens) with RS256 (RSA signature) for authentication. Agent servers validate tokens using public key, tokens issued by external auth service.

### Alternatives Considered
1. **API Keys**: Static keys per user
   - Rejected: Difficult to rotate, no expiration, limited metadata

2. **OAuth 2.0**: Full OAuth implementation with authorization server
   - Rejected: Overkill for initial version, can layer on top of JWT later

3. **JWT with HS256**: Symmetric key signing
   - Rejected: Requires sharing secret key across all agent servers (security risk)

4. **mTLS**: Mutual TLS with client certificates
   - Rejected: Complex to manage, limited by TLS termination at load balancer

### Consequences

**Positive**:
- Stateless authentication (no server-side session lookup)
- RS256 allows distributed validation (servers only need public key)
- Token carries user metadata (claims) without database lookup
- Standard, well-understood protocol
- Token expiration built-in

**Negative**:
- Requires external auth service to issue tokens (not part of ATOLL)
- Token revocation difficult (need blacklist or short expiration)
- Clock skew issues if server times not synchronized

**Neutral**:
- Public key distribution: Configuration file or JWKS endpoint
- Token expiration: 1 hour default, configurable
- Optional RBAC: Roles in token claims

### Implementation Notes
- PyJWT library for validation
- Public key in agent configuration or fetched from JWKS URL
- Validate: signature, expiration, issuer, audience
- Extract user_id from 'sub' claim for session/rate limiting
- Middleware applies authentication to protected endpoints

---

## ADR-010: Prometheus for Metrics, Structured Logs for Observability

**Status**: Accepted
**Date**: 2026-01-01
**Deciders**: Architecture Team, SRE Team

### Context
Production deployments need observability: metrics for monitoring/alerting, logs for troubleshooting.

### Decision
Expose Prometheus metrics at /metrics endpoint (agent servers and deployment servers). Use structured JSON logging for all components.

### Alternatives Considered
1. **StatsD**: Alternative metrics protocol
   - Rejected: Less popular than Prometheus, push-based (less efficient)

2. **OpenTelemetry**: Unified observability framework
   - Considered for future: More comprehensive but also more complex

3. **Plain Text Logs**: Traditional log formats
   - Rejected: Difficult to parse, limited querying capability

4. **Custom Metrics API**: ATOLL-specific metrics endpoint
   - Rejected: Reinventing wheel, Prometheus is industry standard

### Consequences

**Positive**:
- Prometheus widely adopted, rich ecosystem (Grafana, Alertmanager)
- Structured logs easily parsed by ELK/Splunk/CloudWatch
- Trace IDs link logs across distributed requests
- /metrics endpoint self-documenting (includes metric descriptions)

**Negative**:
- Prometheus pull model requires all instances reachable
- Structured logging increases log size vs. plain text
- Need log aggregation service (not provided by ATOLL)

**Neutral**:
- Metrics: request count, duration, active sessions, MCP tool calls, error rate
- Logs: timestamp, level, message, trace_id, agent_name, user_id
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Implementation Notes
- prometheus_client library for metrics
- structlog for structured logging
- Trace ID generated per request (UUID), propagated via X-Trace-ID header
- Example Grafana dashboards provided in docs
- Log format: `{"timestamp": "2026-01-01T12:00:00Z", "level": "INFO", "message": "...", "trace_id": "...", ...}`

---

## ADR-011: Graceful Degradation for Sub-Agent Failures

**Status**: Accepted
**Date**: 2026-01-01
**Deciders**: Architecture Team

### Context
In hierarchical distributed mode, child agents may become unavailable. We need to decide how parent agents handle these failures.

### Decision
Implement graceful degradation: If child agent unavailable, parent returns clear error message to user for tasks requiring that child, but continues to function for other tasks.

### Alternatives Considered
1. **Fail Fast**: Parent agent returns error for ALL requests if any child unavailable
   - Rejected: Too fragile, partial failures cause total outage

2. **Silent Failure**: Parent agent omits unavailable child capabilities from responses
   - Rejected: Confusing for users, hidden failures difficult to debug

3. **Automatic Retry**: Parent retries child requests indefinitely
   - Rejected: Can cause cascading failures, resource exhaustion

4. **Circuit Breaker**: Temporarily disable child after failures, auto-retry later
   - Accepted for future enhancement: Good pattern but adds complexity

### Consequences

**Positive**:
- System remains partially functional during outages
- Clear error messages help users understand limitations
- Parent agent doesn't cascade failures
- Easy to diagnose issues (explicit errors)

**Negative**:
- User experience degraded (some features unavailable)
- Need to communicate availability to users
- Retry logic must be carefully tuned (timeouts, max retries)

**Neutral**:
- Error format: "Agent 'GhidraAgent' unavailable. Binary analysis features temporarily disabled."
- Health check endpoint shows child agent status
- Parent caches child availability status (avoid repeated failed connections)

### Implementation Notes
- Timeout: 5 seconds for child agent requests
- Max retries: 1 (fail fast after initial timeout)
- Error bubbled to user with actionable message
- Child status cached for 30 seconds (avoid hammering failed child)
- Circuit breaker (future): Open after 5 failures, half-open after 60 seconds

---

## Summary of Key Decisions

| ADR | Decision | Impact |
|-----|----------|--------|
| ADR-001 | Hierarchical agent base class | High - Core architecture |
| ADR-002 | Dual-mode (local + server) | High - Operational flexibility |
| ADR-003 | Jenkins-style deployment | High - Deployment strategy |
| ADR-004 | TOML configuration | Medium - Config management |
| ADR-005 | Ollama API extension | Medium - API compatibility |
| ADR-006 | Venv per agent | High - Security & isolation |
| ADR-007 | Stateful sessions | High - User experience |
| ADR-008 | Two-tier load balancing | High - Scalability |
| ADR-009 | JWT RS256 auth | High - Security |
| ADR-010 | Prometheus + structured logs | Medium - Observability |
| ADR-011 | Graceful degradation | High - Reliability |

---

## Future Considerations

### Potential Future ADRs

1. **ADR-012: Kubernetes Native Deployment**
   - When to consider: When users demand K8s support, requiring Helm charts

2. **ADR-013: Redis for Session Storage**
   - When to consider: When horizontal scaling requires shared session store

3. **ADR-014: Circuit Breaker Pattern for Child Agents**
   - When to consider: After production experience with failure patterns

4. **ADR-015: OpenTelemetry for Distributed Tracing**
   - When to consider: When trace correlation across services becomes critical

5. **ADR-016: gRPC for Internal Communication**
   - When to consider: If HTTP overhead becomes performance bottleneck

---

**Document Version History**

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 2.0.0 | 2026-01-01 | Initial ADRs for hierarchical + server architecture | Architecture Team |

---
