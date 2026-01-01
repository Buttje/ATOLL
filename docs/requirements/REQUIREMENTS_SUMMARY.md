# ATOLL v2.0 Requirements Package - Summary

**Version**: 2.0.0
**Date**: January 1, 2026
**Package Status**: Ready for Review

---

## Document Package Overview

This requirements package contains comprehensive specifications for ATOLL version 2.0, which introduces hierarchical agent architecture and distributed server deployment capabilities.

### Included Documents

| Document | Purpose | Pages | Audience |
|----------|---------|-------|----------|
| **SMART_REQUIREMENTS.md** | Detailed functional and non-functional requirements using SMART criteria | 45 | Development Team, Product Owner, QA |
| **ACCEPTANCE_TEST_SPECIFICATION.md** | Comprehensive test cases covering all requirements | 60 | QA Team, Development Team, Stakeholders |
| **ARCHITECTURE_DECISIONS.md** | Architecture Decision Records (ADRs) documenting key design choices | 15 | Architecture Team, Development Team |
| **REQUIREMENTS_SUMMARY.md** | This summary document | 8 | All Stakeholders |

**Total Package Size**: ~128 pages
**Review Deadline**: 2026-01-15
**Implementation Start**: 2026-01-22 (Sprint 1)

---

## Executive Summary

### What's New in ATOLL v2.0

ATOLL v2.0 transforms the system from a single-agent terminal application into a **hierarchical, distributed AI agent platform** with these major capabilities:

1. **Hierarchical Agent System**: Tree-structured agents with parent-child relationships, enabling specialization and delegation
2. **REST API Server Mode**: Agents run as HTTP servers with Ollama-compatible API
3. **Distributed Deployment**: Jenkins-inspired controller-agent deployment system
4. **Load Balancing**: Support for horizontal scaling with multi-instance agents
5. **Enhanced Security**: JWT authentication, resource isolation, TLS support

### Business Value

- **Scalability**: Deploy agents across multiple machines for load distribution
- **Specialization**: Task-specific agents (e.g., GhidraAgent for binary analysis)
- **Flexibility**: Supports both local development (terminal) and production (REST API)
- **Reliability**: Health monitoring, auto-restart, graceful degradation
- **Compatibility**: Works with existing Ollama clients (ollama-python, etc.)

### Timeline

- **Phase 1**: Hierarchical Foundation (Weeks 1-6)
- **Phase 2**: REST API Foundation (Weeks 7-12)
- **Phase 3**: Deployment System (Weeks 13-18)
- **Phase 4**: Distributed Hierarchical (Weeks 19-22)
- **Phase 5**: Hardening & Production Ready (Weeks 23-26)

**Estimated Completion**: ~6 months (26 weeks)

---

## Requirements Overview

### Functional Requirements Summary

Total: **46 Functional Requirements** across 4 major categories

#### 1. Hierarchical Agent System (FR-H001 to FR-H012) - 12 Requirements
**Sprint**: 1-3 (Weeks 1-6)
**Priority**: P0 (Critical)

Key capabilities:
- Root agent initialization with ATOLLAgent base class
- Per-agent LLM configuration (model, temperature, system prompt)
- Navigation commands: `switchto <agent>`, `back`
- Breadcrumb UI showing current position
- Context-aware tool/server/agent listing
- Prompt routing to current agent
- Agent memory isolation

**Success Metrics**:
- 5+ level hierarchy depth supported
- Context switch < 500ms
- Zero memory leakage between agents

#### 2. REST API Server Mode (FR-S001 to FR-S012) - 12 Requirements
**Sprint**: 4-6 (Weeks 7-12)
**Priority**: P0 (Critical)

Key capabilities:
- Ollama API compatibility: `/api/generate`, `/api/chat`, `/api/tags`, `/api/embeddings`
- ATOLL extensions: `/atoll/agents`, `/atoll/tools/*`, `/atoll/status`
- Stateful session management
- JWT authentication (RS256)
- Rate limiting per user

**Success Metrics**:
- Ollama clients work without modification
- Session management handles 1000+ concurrent sessions
- API response time < 5 seconds (95th percentile)

#### 3. Deployment System (FR-D001 to FR-D010) - 10 Requirements
**Sprint**: 7-9 (Weeks 13-18)
**Priority**: P0 (Critical)

Key capabilities:
- Deployment controller coordinating multiple servers
- Deployment server managing local agents
- Agent provisioning with virtual environments
- Resource limits (CPU, memory) enforcement
- Health monitoring and auto-restart
- Agent TOML configuration format

**Success Metrics**:
- Controller manages 100+ deployment servers
- Agent provisioning < 2 minutes
- Resource limits enforced with <5% overhead

#### 4. Hierarchical Distributed Mode (FR-HD001 to FR-HD005) - 5 Requirements
**Sprint**: 10-11 (Weeks 19-22)
**Priority**: P1 (High)

Key capabilities:
- Parent-child HTTP communication
- Sub-agent connection configuration in TOML
- Load balancing at deployment server level
- Service discovery via controller
- External load balancer support (nginx/HAProxy)

**Success Metrics**:
- Parent-child communication < 5 seconds
- Load distribution variance < 10%
- Service discovery response < 100ms

#### 5. Configuration Requirements (FR-D007) - 1 Requirement
**Sprint**: 7 (Weeks 13-14)
**Priority**: P1 (High)

Key capabilities:
- TOML configuration format
- Sections: [agent], [llm], [dependencies], [resources], [mcp_servers.*], [sub_agents.*]
- Environment variable interpolation
- Schema validation with helpful errors

**Example agent.toml**:
```toml
[agent]
name = "GhidraAgent"
version = "1.0.0"

[llm]
model = "codellama:7b"
temperature = 0.3

[dependencies]
python = ">=3.9"
packages = ["pydantic>=2.0", "aiohttp>=3.9"]

[resources]
cpu_limit = 2.0
memory_limit = "4GB"

[mcp_servers.ghidramcp]
type = "stdio"
command = "python"
args = ["-m", "ghidra_mcp_server"]
```

---

### Non-Functional Requirements Summary

Total: **16 Non-Functional Requirements** across 6 categories

#### Performance (NFR-P001 to NFR-P003)
- Response time: <5s for simple queries (95th percentile)
- Throughput: 50 concurrent users with <10% degradation
- Startup: Agent ready within 10 seconds

#### Security (NFR-S001 to NFR-S004)
- JWT RS256 authentication
- TLS 1.2+ for transport encryption
- No plaintext secrets (env vars or secret stores)
- cgroups for resource isolation

#### Reliability (NFR-R001 to NFR-R003)
- Uptime: 99.5% availability target
- Graceful degradation on sub-agent failure
- Optional conversation history persistence

#### Maintainability (NFR-M001 to NFR-M003)
- Structured JSON logging with trace IDs
- Prometheus metrics at /metrics
- Configuration hot-reload (SIGHUP)

#### Usability (NFR-U001 to NFR-U002)
- Actionable error messages
- Comprehensive documentation with examples

#### Compatibility (NFR-C001 to NFR-C003)
- Python 3.9-3.12 support
- Linux, macOS, Windows support
- Ollama API v0.1.x compatibility

---

## Test Coverage

### Test Statistics

| Category | Test Cases | Coverage Target | Priority |
|----------|-----------|-----------------|----------|
| Hierarchical System | 12 | 100% | P0 |
| REST API | 12 | 100% | P0 |
| Deployment System | 10 | 95% | P0 |
| Distributed Mode | 5 | 95% | P1 |
| Non-Functional | 16 | 90% | P1 |
| **TOTAL** | **55** | **95%+** | **Mixed** |

### Test Types

- **Automated Unit Tests**: 85%+ code coverage target
- **Automated Integration Tests**: End-to-end scenarios
- **Automated Performance Tests**: Load testing, stress testing
- **Manual Security Tests**: Penetration testing, audits
- **Manual Usability Tests**: UI/UX validation

### Test Environments

1. **Development**: Local machines, Docker Compose
2. **Staging**: Cloud VMs, real Ollama/MCP servers
3. **Production**: Canary deployments with monitoring

---

## Architecture Highlights

### Key Design Decisions (ADRs)

11 Architecture Decision Records document the major design choices:

1. **ADR-001**: Hierarchical agent base class
2. **ADR-002**: Dual-mode operation (local + server)
3. **ADR-003**: Jenkins-style deployment architecture
4. **ADR-004**: TOML configuration format
5. **ADR-005**: Ollama API extension pattern
6. **ADR-006**: Virtual environment per agent
7. **ADR-007**: Stateful session management
8. **ADR-008**: Two-tier load balancing
9. **ADR-009**: JWT RS256 authentication
10. **ADR-010**: Prometheus metrics + structured logs
11. **ADR-011**: Graceful degradation for failures

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      User / Client                          │
└─────────────┬───────────────────────────────────────────────┘
              │
              ├─ Terminal UI ──> Local ATOLL (Interactive Mode)
              │                   └─> Root Agent
              │                       └─> Sub-Agents (in-process)
              │
              └─ HTTP/REST ──> External Load Balancer (nginx)
                               │
        ┌──────────────────────┴──────────────────────┐
        │                                             │
        v                                             v
  Deployment Server A                       Deployment Server B
  ┌─────────────────┐                      ┌─────────────────┐
  │ Root Agent #1   │                      │ Root Agent #2   │
  │ GhidraAgent #1  │                      │ GhidraAgent #2  │
  │ GhidraAgent #2  │◄─────HTTP────────────┤ WebAgent #1     │
  └────────┬────────┘                      └────────┬────────┘
           │                                         │
           │              Registration               │
           └───────────────> Deployment Controller <─┘
                            (Service Discovery)
                            (Heartbeat Monitoring)
                            (Agent Orchestration)
```

### Component Responsibilities

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| **Root Agent** | User interface, task delegation | Python, ATOLLAgent |
| **Sub-Agent** | Specialized task execution | Python, ATOLLAgent |
| **Agent Server** | REST API, session management | FastAPI |
| **Deployment Server** | Agent lifecycle, local load balancing | Python, asyncio |
| **Deployment Controller** | Global orchestration, service discovery | FastAPI, PostgreSQL |
| **External LB** | Machine-level load distribution | nginx/HAProxy |

---

## Implementation Plan

### Sprint Structure (2-week sprints)

#### Phase 1: Hierarchical Foundation (Sprints 1-3)
**Weeks 1-6** | **Team**: 2 Backend, 1 Frontend

- **Sprint 1**: ATOLLAgent base class, root agent refactor
- **Sprint 2**: Navigation (switchto/back), breadcrumbs, context-aware listings
- **Sprint 3**: Prompt routing, memory isolation, testing

**Deliverables**: Working hierarchical system in terminal mode

#### Phase 2: REST API Foundation (Sprints 4-6)
**Weeks 7-12** | **Team**: 3 Backend, 1 QA

- **Sprint 4**: Ollama API endpoints (/api/generate, /api/chat)
- **Sprint 5**: ATOLL extensions (/atoll/agents, /atoll/tools)
- **Sprint 6**: Authentication, sessions, rate limiting

**Deliverables**: Agent server mode with REST API

#### Phase 3: Deployment System (Sprints 7-9)
**Weeks 13-18** | **Team**: 2 Backend, 1 DevOps, 1 QA

- **Sprint 7**: Deployment controller, TOML config
- **Sprint 8**: Deployment server, agent provisioning
- **Sprint 9**: Resource limits, health monitoring

**Deliverables**: Complete deployment system

#### Phase 4: Distributed Hierarchical (Sprints 10-11)
**Weeks 19-22** | **Team**: 2 Backend, 1 DevOps

- **Sprint 10**: Parent-child HTTP communication
- **Sprint 11**: Load balancing, service discovery

**Deliverables**: Distributed deployment working

#### Phase 5: Hardening (Sprints 12-13)
**Weeks 23-26** | **Team**: Full Team

- **Sprint 12**: Performance testing, optimization
- **Sprint 13**: Security audit, documentation, final fixes

**Deliverables**: Production-ready v2.0

---

## Risk Assessment

### High Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Complexity Underestimation** | Schedule slip | Medium | Phased approach, MVP per phase |
| **Ollama API Changes** | Compatibility break | Low | Version lock, abstraction layer |
| **Performance at Scale** | User dissatisfaction | Medium | Early load testing, profiling |
| **Security Vulnerabilities** | Data breach | Low | Security audits, penetration testing |

### Medium Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Team Velocity Lower than Expected** | Delayed release | Medium | Buffer time in Phase 5 |
| **Third-party Dependency Issues** | Development blocked | Low | Lock dependencies, fallback plans |
| **Windows Compatibility Issues** | Platform limitation | Medium | CI on Windows, early testing |

---

## Success Criteria

### Release Criteria (All must be met)

1. ✅ All P0 requirements implemented and tested
2. ✅ Test coverage: Unit (85%+), Integration (70%+)
3. ✅ All P0/P1 bugs resolved
4. ✅ Performance targets met (NFR-P001, NFR-P002)
5. ✅ Security audit passed (no critical/high vulnerabilities)
6. ✅ Documentation complete (user guide, API docs, deployment guide)
7. ✅ Backward compatibility maintained (existing agent.json works)
8. ✅ CI/CD pipeline green on all supported platforms

### Post-Release Success Metrics (Month 1-3)

- **Adoption**: 50+ production deployments
- **Uptime**: 99.5%+ availability
- **Performance**: <5s response time (95th %ile)
- **Support**: <10 critical bugs reported per month
- **User Satisfaction**: >4/5 rating in surveys

---

## Dependencies and Prerequisites

### External Dependencies

- **Ollama**: v0.1.7+ (LLM runtime)
- **Python**: 3.9-3.12
- **Database**: PostgreSQL 14+ (deployment controller)
- **Load Balancer**: nginx/HAProxy (production deployment)
- **Container Runtime**: Docker/Podman (optional, for MCP servers)

### Internal Dependencies

- **Existing ATOLL**: v1.x codebase as foundation
- **MCP Protocol**: Existing MCP client/server implementation
- **Configuration Management**: Extend current ConfigManager

### Team Requirements

- **Backend Engineers**: 3 (Python, FastAPI, asyncio)
- **Frontend Engineer**: 1 (Terminal UI, user experience)
- **DevOps Engineer**: 1 (Deployment, monitoring, infrastructure)
- **QA Engineer**: 1 (Test automation, load testing)
- **Security Specialist**: 0.5 FTE (audits, best practices)

**Total Team Size**: 6.5 FTE for 6 months

---

## Open Questions and Clarifications

### Resolved (per user confirmation)

1. ✅ **Hierarchical mode**: Option C - Support both local and distributed
2. ✅ **Deployment pattern**: Option A - Controller-agent (Jenkins-style)
3. ✅ **Load balancing**: Option D - Deployment server intra-machine LB
4. ✅ **TOML format**: Option B - Comprehensive agent config
5. ✅ **API compatibility**: Option C - Ollama core + ATOLL extensions
6. ✅ **Virtual environments**: Option A - Auto-managed by deployment server
7. ✅ **Communication protocol**: Option A - HTTP REST
8. ✅ **Session management**: Stateful with 30min timeout
9. ✅ **Resource limits**: Yes to all (CPU, memory, health checks)

### Remaining Questions

1. **Budget**: What is the allocated budget for this project?
2. **Cloud Infrastructure**: AWS/GCP/Azure preference for staging/production?
3. **Existing Users**: How many existing ATOLL v1.x users to migrate?
4. **Licensing**: Any licensing implications for production deployments?
5. **SLA Commitments**: Are formal SLAs required for production version?

---

## Approval and Sign-off

### Document Review Process

1. **Initial Review**: Architecture Team (Jan 5-8, 2026)
2. **Stakeholder Review**: Product Owner, Management (Jan 9-12, 2026)
3. **Final Approval**: Jan 15, 2026
4. **Implementation Kickoff**: Sprint 1 starts Jan 22, 2026

### Sign-off Required From

| Role | Name | Status | Date |
|------|------|--------|------|
| **Product Owner** | | ☐ Pending | |
| **Technical Lead** | | ☐ Pending | |
| **Architecture Lead** | | ☐ Pending | |
| **QA Lead** | | ☐ Pending | |
| **Security Lead** | | ☐ Pending | |
| **Engineering Manager** | | ☐ Pending | |

---

## Appendix: Document Navigation

### Quick Reference Links

- **Full Requirements**: [SMART_REQUIREMENTS.md](./SMART_REQUIREMENTS.md)
- **Test Specifications**: [ACCEPTANCE_TEST_SPECIFICATION.md](./ACCEPTANCE_TEST_SPECIFICATION.md)
- **Architecture Decisions**: [ARCHITECTURE_DECISIONS.md](./ARCHITECTURE_DECISIONS.md)

### Traceability Matrix

Complete traceability from requirements → acceptance tests → ADRs:

| Requirement | Test Cases | Architecture Decision |
|-------------|-----------|----------------------|
| FR-H001 | TEST-H001 | ADR-001 |
| FR-H002 | TEST-H002 | ADR-001 |
| FR-S001 | TEST-S001, TEST-S002 | ADR-005 |
| FR-D001 | TEST-D001 | ADR-003 |
| FR-D007 | TEST-D008 | ADR-004 |
| ... | ... | ... |

Full matrix available in ACCEPTANCE_TEST_SPECIFICATION.md Section 10.1

---

## Contact and Questions

For questions or clarifications about this requirements package:

- **Requirements Issues**: Create GitHub issue with label `requirements`
- **Technical Questions**: Tag `@architecture-team` in discussions
- **Process Questions**: Contact Product Owner or Engineering Manager

---

**Document Package Version**: 2.0.0
**Last Updated**: 2026-01-01
**Next Review**: 2026-03-01 (after Phase 2 completion)

---

## Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-01-01 | 2.0.0 | Initial requirements package creation | ATOLL Team |

---
