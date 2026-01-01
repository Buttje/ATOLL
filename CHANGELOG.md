# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-01

### Breaking Changes
- **OllamaMCPAgent Removed**: Legacy `OllamaMCPAgent` class has been completely removed
  - All functionality migrated to `ATOLLAgent` base class (229 lines removed from `agent.py`)
  - `RootAgent` is now the primary agent implementation
  - Backward compatibility: `OllamaMCPAgent` re-exported as alias to `ATOLLAgent` for legacy imports
  - Update existing code to use `RootAgent` or extend `ATOLLAgent` directly
  - **Migration verified**: All 539 unit tests passing (100% success rate)

### Changed
- **Agent Architecture Modernization**
  - All agent methods now in `ATOLLAgent` base class (`src/atoll/plugins/base.py`)
  - Added to base class: `check_server_connection()`, `check_model_available()`, `list_models()`
  - `RootAgent` extends `ATOLLAgent` for user interaction
  - Improved plugin architecture for custom agents
  - Method name standardization: `clear_memory()` → `clear_conversation_memory()`
  - LLM initialization: `_create_llm()` → `_initialize_llm()` (consistent with base class)
  - Data flow updated: TerminalUI → Application → **RootAgent** → MCPServerManager
  - All test files updated: 36 agent tests converted and passing

- **Dynamic Port Allocation**
  - Deployment server REST API now automatically finds available ports
  - When `auto_discover_port: true` (default), API port dynamically allocated starting from 8080
  - Prevents port conflicts in multi-instance scenarios and testing
  - Logs port changes when default port is unavailable
  - Agent ports also dynamically allocated starting from configured base_port (default: 8100)

### Added
- **Deployment REST API (Always-On)**
  - REST API starts with deployment server (dynamic port allocation)
  - Automatic API server initialization alongside process manager
  - Full endpoint documentation in `/docs/DEPLOYMENT_REST_API.md`
  - Endpoints available:
    - `GET /health` - Health check
    - `GET /agents` - List all agents
    - `POST /agents/deploy` - Deploy agent package (ZIP)
    - `POST /agents/{name}/start` - Start specific agent
    - `POST /agents/{name}/stop` - Stop specific agent
    - `POST /agents/{name}/restart` - Restart specific agent
    - `GET /agents/{name}` - Get agent status
  - Command-line integration examples for PowerShell and curl
  - Startup output shows REST API URL: `http://localhost:8080`

- **Enhanced Deployment Architecture**
  - Clear separation between Deployment Server (port 8080) and Agent Servers (ports 8100+)
  - Deployment Server = Process Manager + REST API (management interface)
  - Agent Servers = Individual FastAPI instances (agent functionality)
  - Remote deployment servers configured via `deployment_servers.json`
  - Local server always auto-starts, remote servers optional
  - Structured startup report showing all server endpoints
  - Configuration includes `api_port` (8080) and `base_port` (8100)

- **Verbose Deployment Output**
  - Comprehensive startup banner showing host, port, and configuration
  - REST API startup confirmation with endpoint URL
  - Step-by-step progress indicators with emoji symbols for visual clarity
  - Real-time agent startup status (assigned port, PID, URL)
  - Detailed ZIP deployment logging:
    - MD5 checksum calculation and comparison
    - File extraction progress and count
    - Configuration file discovery and parsing
    - Virtual environment creation steps
    - Dependency installation progress
    - Agent registration confirmation
  - Clear success (✓) and failure (✗) indicators
  - All deployment operations now have verbose, user-friendly output

- **Verbose Error Diagnostics**
  - Comprehensive error capture for failed agent startups
  - Full stdout/stderr logging with exit codes
  - Intelligent pattern recognition for common issues:
    - Python 3.14+ Pydantic V1 compatibility warnings
    - Missing Python dependencies (ModuleNotFoundError)
    - Port conflicts (Address already in use)
    - Permission/access errors
    - Connection failures to required services
  - Configuration file analysis and validation
  - File structure validation (main.py, requirements.txt, .venv)
  - Actionable troubleshooting steps with platform-specific commands
  - Automatic diagnostics generation with emoji indicators (⚠️ 💡 📋)
  - Test coverage: 4 new diagnostic tests, all passing

### Changed
- **Port Structure Clarification**
  - Port 8080: Deployment Server REST API (management)
  - Ports 8100+: Individual Agent Servers (agent APIs)
  - Updated all documentation to reflect this structure
  - Remote servers in `deployment_servers.json` now use port 8080
  - Example configuration files updated with `api_port` field

### Fixed
- Agent startup path resolution (now uses relative path in working directory)
- Configuration file path issues in agent startup command

## [2.0.0] - 2026-01-01

### Added - Major Release: Deployment Server v2.0
- **REST API for Deployment Server**
  - FastAPI-based HTTP API for remote agent management
  - Endpoints: `/agents`, `/deploy`, `/start`, `/stop`, `/status`, `/health`
  - OpenAPI/Swagger documentation auto-generated
  - Async/await throughout for high performance
- **ZIP Package Deployment**
  - Upload agent packages as ZIP files
  - Automatic extraction and validation
  - Support for agent.toml configuration in packages
  - Package structure validation
- **MD5 Checksum Verification**
  - Track installed agents by MD5 checksum
  - Avoid redundant installations of identical packages
  - Checksum database persisted to disk
  - Fast lookup for existing agents
- **Virtual Environment Management**
  - Isolated venv for each agent
  - Automatic dependency installation from requirements.txt
  - Python version compatibility checking
  - Environment cleanup on agent removal
- **Deployment Client API**
  - Client class for connecting to deployment servers
  - Synchronous and asynchronous methods
  - Automatic package creation from agent directories
  - Remote agent lifecycle management
- **Standalone Deployment Server Mode**
  - Run deployment server as independent process
  - Command: `atoll-deploy-server --host 0.0.0.0 --port 8080`
  - Systemd service configuration example included
  - Multi-tenant support with agent isolation

### Changed
- Deployment server architecture completely redesigned
- Port allocation now properly checks availability
- Improved status reporting with detailed agent states
- Agent startup errors now captured and displayed
- Configuration path handling fixed (string to Path conversion)

### Fixed
- Bug: 'str' object has no attribute 'exists' in deployment server
- Bug: Port conflict between deployment server and agents
- Bug: Confusing status messages about port usage

### Documentation
- Added DEPLOYMENT_SERVER_ARCHITECTURE.md
- Added DEPLOYMENT_PORT_ALLOCATION_FIX.md
- Updated API documentation with OpenAPI spec
- Added deployment server setup guide

### Breaking Changes
- Deployment server now requires explicit REST API setup for remote access
- Agent configuration format extended (backward compatible)
- New required fields in deployment_servers.json

### Dependencies
- fastapi>=0.109.0 (already present, now actively used)
- uvicorn>=0.27.0 (already present, now actively used)
- Added python-multipart for file uploads

### Migration Guide
Version 1.x deployment configurations will continue to work for local agents.
For remote deployment, see docs/DEPLOYMENT_SERVER_ARCHITECTURE.md for setup instructions.

## [1.2.0] - 2025-12-15

### Added
- **Modern Terminal Input System** using prompt_toolkit for cross-platform support
  - Full readline-style editing (Ctrl+A, Ctrl+E, Ctrl+W, Ctrl+K, Ctrl+U)
  - History search with Ctrl+R
  - Persistent history saved to ~/.atoll_history
  - Insert/overtype mode toggle
  - Cross-platform support (Windows, Linux, macOS)
- **ReAct Reasoning Engine** implementing Thought→Action→Observation pattern
  - Iterative reasoning loop with configurable max iterations
  - LangChain-compatible response parsing
  - Tool execution with timeout and error handling
  - Observation truncation for performance
  - Full step tracking and reasoning trace for explainability
- **Plugin Architecture** for extensible agent system
  - ATOLLAgent base class for specialized agents
  - PluginManager for automatic discovery and lifecycle management
  - Agent metadata format (agent.json)
  - Capability-based agent selection with confidence scoring
  - Introspection capabilities (list plugins, get by capability/server)
- **GhidraATOLL Agent** for binary reverse engineering
  - Specialized for Ghidra and GhidraMCP integration
  - Binary analysis, decompilation, symbol analysis capabilities
  - Intelligent prompt scoring for relevance detection
  - Keyword and pattern matching for binary analysis tasks
- AgentConfig model for configurable agent behavior
- Comprehensive test suite: 59 new tests (all passing)
- Documentation for plugin creation and best practices

### Changed
- Terminal UI now uses AtollInput instead of InputHandler
- Startup confirmation uses AtollInput for consistent behavior
- Version bumped from 1.1.0 to 1.2.0

### Dependencies
- Added prompt-toolkit>=3.0.0 for terminal input handling

### Technical Details
- 378 tests passing (22 legacy tests superseded by new implementation)
- New modules: prompt_input.py, react_engine.py, plugins/
- Plugin directory: atoll_agents/ with automatic discovery
- Full backward compatibility maintained for existing functionality

## [1.1.0] - 2025-12-14

### Added
- Project organization improvements following Python best practices
- MANIFEST.in for proper package distribution
- .editorconfig for consistent code style across editors
- .gitattributes for consistent line endings
- py.typed marker for PEP 561 type hint support
- Enhanced .gitignore with project-specific patterns
- CODE_OF_CONDUCT.md for community guidelines
- Example configuration files in examples/
- Comprehensive pyproject.toml with ruff lint rules and coverage config

### Changed
- Updated LICENSE with full MIT license text
- Fixed pyproject.toml formatting and URLs
- Enhanced GitHub Copilot instructions for AI agents

## [1.0.0] - 2025-12-05

### Added
- Initial release of ATOLL (Agentic Tools Orchestration on OLLama)
- LangChain-based AI agent integrating Ollama with MCP servers
- Dual-mode terminal UI (Command/Prompt modes)
- MCP server support for stdio, HTTP, and SSE transports
- Tool registry for cross-server tool discovery
- Reasoning engine for intelligent tool selection
- Hot model switching without restart
- Comprehensive test suite with 90%+ coverage
- Configuration management with type-safe Pydantic models
- Interactive help system for servers and tools
- Conversation memory management

### Features
- Natural language interaction with AI agents
- Tool orchestration through MCP servers
- Color-coded terminal interface
- Async/await architecture throughout
- Cross-platform support (Windows, Linux, macOS)
- Type hints and mypy support
- Pre-commit hooks for code quality

[Unreleased]: https://github.com/Buttje/ATOLL/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/Buttje/ATOLL/releases/tag/v1.2.0
[1.1.0]: https://github.com/Buttje/ATOLL/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/Buttje/ATOLL/releases/tag/v1.0.0
