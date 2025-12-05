# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- Ghidra binary analysis integration support
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

[Unreleased]: https://github.com/Buttje/ATOLL/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Buttje/ATOLL/releases/tag/v1.0.0
