# ATOLL Development Instructions

## Table of Contents
1. [Quick Start](#quick-start)
2. [Installation & Setup](#installation--setup)
3. [Architecture Overview](#architecture-overview)
4. [Critical Patterns](#critical-patterns)
5. [Development Workflows](#development-workflows)
6. [Testing Patterns](#testing-patterns)
7. [Common Pitfalls](#common-pitfalls)
8. [Security Considerations](#security-considerations)
9. [Troubleshooting](#troubleshooting)
10. [Common Development Tasks](#common-development-tasks)
11. [Contribution Workflow](#contribution-workflow)
12. [Key Files Reference](#key-files-reference)
13. [Performance Requirements](#performance-requirements)

## Quick Start

**First Time Setup:**
```bash
# 1. Clone repository
git clone https://github.com/Buttje/ATOLL.git
cd ATOLL

# 2. Install dependencies (creates venv automatically)
python install.py

# 3. Verify Ollama is running (required)
ollama serve  # In separate terminal
ollama pull llama2  # Or your preferred model

# 4. Run ATOLL
atoll
```

**Development Workflow:**
```bash
# Run tests before making changes
pytest --cov=src --cov-report=html

# Make your changes, then run pre-commit checks
pre-commit run --all-files

# Run tests again to verify
pytest tests/unit/test_your_module.py -v

# Submit PR when ready
```

## Installation & Setup

### Prerequisites
- **Python 3.9+** (3.12 recommended)
- **Ollama** - [Install from ollama.ai](https://ollama.ai/)
- **8GB+ RAM** (16GB recommended for larger models)

### Development Environment Setup

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Verify installation
atoll --help
pytest --version
```

### Configuration Files

**Ollama Config** (`~/.ollama_server/.ollama_config.json`):
```json
{
  "base_url": "http://localhost",
  "port": 11434,
  "model": "llama2",
  "request_timeout": 30,
  "max_tokens": 2048
}
```

**MCP Config** (`mcp.json` in project root):
```json
{
  "mcpServers": {
    "example-server": {
      "command": "node",
      "args": ["/path/to/mcp-server/index.js"],
      "env": {},
      "transport": "stdio"
    }
  }
}
```

Configuration is auto-created with defaults on first run. Environment variables in MCP commands are expanded automatically.

## Architecture Overview

ATOLL is a LangChain-based AI agent that bridges Ollama LLMs with MCP (Model Context Protocol) servers. The architecture follows a layered design:

- **Application Layer** (`main.py`): Orchestrates startup, manages dual-mode UI (Command/Prompt), handles user interaction loop
- **Agent Layer** (`agent/`): LangChain integration, reasoning engine, tool wrappers for MCP
- **MCP Layer** (`mcp/`): Server manager, clients (stdio/SSE/HTTP), tool registry for cross-server tool discovery
- **Configuration** (`config/`): Pydantic dataclasses for type-safe configs (`~/.ollama_server/.ollama_config.json`, `mcp.json`)
- **UI Layer** (`ui/`): Terminal interface with mode toggling (ESC key), color schemes, input handling

**Key Data Flow**: User input → TerminalUI → Application.handle_prompt/command → RootAgent (extends ATOLLAgent) → MCPServerManager → MCPClient (stdio subprocess) → Tool execution → Response formatting → Display

**Architecture Note**: The legacy `OllamaMCPAgent` class has been removed. All agent functionality is now in the `ATOLLAgent` base class, with `RootAgent` as the primary implementation for user interaction.

## Critical Patterns

### Async/Await Throughout
- All I/O operations are async (MCP communication, Ollama calls)
- Use `asyncio.run_in_executor()` for sync LLM calls: `await loop.run_in_executor(None, self.llm.invoke, prompt)`
- Test async code with `pytest-asyncio` and `@pytest.mark.asyncio`

### MCP Tool Integration
Tools from MCP servers are wrapped in `MCPToolWrapper(BaseTool)` for LangChain compatibility:
```python
# Tools registered via tool_registry during server connection
wrapper = MCPToolWrapper(name, description, mcp_manager, server_name)
# Executed through: mcp_manager.execute_tool(server_name, tool_name, arguments)
```

### Dual-Mode UI (Critical)
- **Prompt Mode**: Natural language interaction with agent
- **Command Mode**: System commands (models, servers, tools, changemodel, help, quit)
- Toggle with ESC key (handled in `input_handler.py`)
- Commands are case-insensitive but preserve case in arguments: `parts[0].lower()` for command, preserve case for `parts[1:]`

### Configuration Management
- Ollama config stored in `~/.ollama_server/.ollama_config.json` (user home directory)
- MCP config in working directory (`mcp.json`)
- `ConfigManager` uses `Path` for file handling, validates with Pydantic dataclasses
- Directory `~/.ollama_server/` created automatically on first run
- Configuration changes via commands (`changemodel`, `setserver`) are persisted to disk automatically
- Environment variable expansion in MCP commands: `os.path.expandvars()`
- Default fallbacks when configs missing (see `OllamaConfig()` and `MCPConfig()`)

### Reasoning Engine
The `ReasoningEngine` applies rule-based analysis before LLM invocation:
- Detects patterns (e.g., "find implementation" → semantic matching hints)
- Identifies security-sensitive operations (password, credential keywords)
- Provides context-aware tool selection guidance
- Displayed as compact reasoning summary in UI (max 5 lines visible)

## Development Workflows

### Running Tests
```bash
# All tests with coverage
pytest --cov=src --cov-report=html

# Specific test pattern
pytest tests/unit/test_agent*.py -v

# Watch mode for TDD
pytest-watch
```

### Code Quality (Pre-commit)
- **Black** (line-length=100): Auto-formatting
- **Ruff**: Fast linting (replaces flake8/isort)
- **mypy**: Type checking (currently permissive: `disallow_untyped_defs = false`)

Run all checks: `pre-commit run --all-files`

### Adding New MCP Servers
1. Update `mcp.json` with server config (transport: stdio/sse/http)
2. Manually install the MCP server using its installation script or package manager
3. Server auto-discovered on startup via `MCPServerManager.connect_all()`
4. Tools registered in `ToolRegistry` (handles naming conflicts by server priority)
5. Test with `help server <name>` and `help tool <name>` commands

### Hot Model Switching
Use `changemodel <name>` command (no restart required):
- Updates `ollama_config.model` and recreates LLM instance
- Preserves conversation memory unless `clear` command used
- List available models with `models` command

## Testing Patterns

### Fixtures (conftest.py)
- `ollama_config`: Test OllamaConfig with test-model
- `mcp_config`: Test MCPConfig with stdio test-server
- `mock_mcp_client`: AsyncMock for MCPClient
- Use `pytest.mark.asyncio` for async tests

### Mocking Strategy
```python
# MCP operations
mock_manager = MagicMock(spec=MCPServerManager)
mock_manager.execute_tool = AsyncMock(return_value={"result": "success"})

# Platform-specific (UI tests)
@patch('platform.system', return_value='Windows')
@patch('os.system')
```

### Coverage Goals
- Maintain >80% coverage (current: 90%+)
- Focus on `unit/` for component tests, `integration/` for end-to-end flows
- Test both success and error paths (see `test_tools.py` exception handling)

## Common Pitfalls

### Subprocess Lifecycle
MCP stdio servers run as subprocesses (`asyncio.create_subprocess_exec`). Always:
- Capture stderr for debugging: `stderr=asyncio.subprocess.PIPE`
- Properly disconnect in Application.shutdown()
- Handle process termination errors gracefully

### JSON Parsing in Tools
Tool arguments may be JSON or plain strings:
```python
try:
    arguments = json.loads(input_str)
except json.JSONDecodeError:
    arguments = {"input": input_str}
```

### Windows vs Linux Paths
- Use `Path` from pathlib for cross-platform compatibility
- MCP commands use forward slashes even on Windows (handled by subprocess)
- Terminal clear: `'cls' if platform.system() == 'Windows' else 'clear'`

### LangChain Compatibility
- Use `langchain-ollama` package (not `langchain-community.llms.Ollama`)
- Prefer `HumanMessage`/`AIMessage` for conversation history
- Tool wrappers must extend `BaseTool` and implement `_arun()` for async

## Security Considerations

### Input Validation
- All user inputs are sanitized through Pydantic dataclasses
- MCP tool arguments validated against JSON schemas
- Configuration files validated on load with clear error messages

### Credential Management
- Never store API keys or secrets in configuration files
- Use environment variables for sensitive data: `os.environ.get("API_KEY")`
- MCP server commands support env var expansion: `"env": {"API_KEY": "$API_KEY"}`
- Reasoning engine flags security-sensitive operations (password, credential keywords)

### Subprocess Security
- MCP stdio servers run in isolated subprocesses with controlled environment
- stderr/stdout captured to prevent information leakage
- Process termination handled gracefully on shutdown
- No shell injection: use `asyncio.create_subprocess_exec()` with arg lists

### Dependency Security
- Keep dependencies updated (see `pyproject.toml`)
- Run `pip-audit` before adding new dependencies
- Review MCP server code before adding to `mcp.json`

## Troubleshooting

### Common Issues

**1. "Model not found" error**
```bash
# List available models
ollama list

# Pull missing model
ollama pull llama2

# Update config to use available model
atoll  # Then use: changemodel <name>
```

**2. MCP server fails to start**
```bash
# Check server installation
node /path/to/server/index.js  # Test directly

# Verify mcp.json paths are absolute
# Verify environment variables are set

# Check logs in terminal (stderr is captured)
```

**3. Async test failures**
```python
# Always use pytest.mark.asyncio for async tests
@pytest.mark.asyncio
async def test_my_async_function():
    result = await my_async_function()
    assert result == expected
```

**4. Import errors after installation**
```bash
# Reinstall in development mode
pip install -e ".[dev]"

# Verify PYTHONPATH includes src/
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

**5. Windows subprocess issues**
- Use forward slashes in MCP paths even on Windows
- Ensure `asyncio` is using ProactorEventLoop on Windows
- Check that MCP server scripts have proper line endings (LF not CRLF)

### Debug Mode

Enable verbose logging:
```python
# In code
import logging
logging.basicConfig(level=logging.DEBUG)

# Set in config
# See src/atoll/utils/logger.py for logger configuration
```

## Common Development Tasks

### Adding a New Command
```python
# 1. Add to Application.handle_command() in main.py
async def handle_command(self, command: str):
    parts = command.split()
    cmd = parts[0].lower()
    
    if cmd == "mynewcommand":
        # Your logic here
        return

# 2. Add to help text
# 3. Add unit test in tests/unit/test_main.py
```

### Adding a New MCP Tool Wrapper
```python
# 1. Create tool in src/atoll/mcp/tools.py
class MyMCPToolWrapper(MCPToolWrapper):
    def _arun(self, *args, **kwargs):
        # Async implementation
        pass

# 2. Register in ToolRegistry
# 3. Add tests in tests/unit/test_tools.py
```

### Running Specific Tests
```bash
# Single test file
pytest tests/unit/test_agent.py -v

# Single test function
pytest tests/unit/test_agent.py::test_function_name -v

# With coverage for one module
pytest tests/unit/test_agent.py --cov=src/atoll/agent --cov-report=term

# Watch mode for TDD
pytest-watch tests/unit/
```

### Debugging Agent Behavior
```python
# Add print statements in agent reasoning
# Check src/atoll/agent/reasoning.py for rule-based analysis

# Use langchain debug mode
from langchain.globals import set_debug
set_debug(True)

# Examine conversation memory
# Check RootAgent.memory in main.py
```

## Contribution Workflow

### Git Workflow
```bash
# 1. Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# 2. Make changes and commit
git add .
git commit -m "feat: add new feature"  # Use conventional commits

# 3. Run all checks before pushing
pre-commit run --all-files
pytest --cov=src --cov-report=html

# 4. Push and create PR
git push origin feature/your-feature-name
# Create PR on GitHub
```

### Commit Message Convention
Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions/changes
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

### Pull Request Guidelines
1. **Title**: Clear, concise description of changes
2. **Description**: Explain what, why, and how
3. **Tests**: Add tests for new functionality
4. **Coverage**: Maintain >80% code coverage
5. **Documentation**: Update docs if behavior changes
6. **Pre-commit**: All checks must pass
7. **Review**: Address feedback promptly

### Code Review Checklist
- [ ] Code follows existing patterns
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] No unnecessary changes
- [ ] Async/await used correctly
- [ ] Type hints added
- [ ] Error handling implemented
- [ ] Security considerations addressed

## Key Files Reference

- `src/atoll/main.py`: Application orchestration, command handling (lines 93-250)
- `src/atoll/agent/agent.py`: LangChain agent, tool creation, prompt processing
- `src/atoll/mcp/server_manager.py`: Server lifecycle, tool discovery
- `src/atoll/ui/terminal.py`: Dual-mode UI, input handling (UIMode enum)
- `tests/conftest.py`: Shared test fixtures and mocks

## Performance Requirements

- Local LLM responses: <2s target (depends on model/hardware)
- MCP server timeout: 30s default (configurable in `mcp.json`)
- Tool execution varies by MCP server implementation
