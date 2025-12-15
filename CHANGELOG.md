# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
