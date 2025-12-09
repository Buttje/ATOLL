# ATOLL Development Instructions

## Architecture Overview

ATOLL is a LangChain-based AI agent that bridges Ollama LLMs with MCP (Model Context Protocol) servers. The architecture follows a layered design:

- **Application Layer** (`main.py`): Orchestrates startup, manages dual-mode UI (Command/Prompt), handles user interaction loop
- **Agent Layer** (`agent/`): LangChain integration, reasoning engine, tool wrappers for MCP
- **MCP Layer** (`mcp/`): Server manager, clients (stdio/SSE/HTTP), tool registry for cross-server tool discovery
- **Configuration** (`config/`): Pydantic dataclasses for type-safe configs (`~/.ollama_server/.ollama_config.json`, `mcp.json`)
- **UI Layer** (`ui/`): Terminal interface with mode toggling (ESC key), color schemes, input handling

**Key Data Flow**: User input → TerminalUI → Application.handle_prompt/command → OllamaMCPAgent → MCPServerManager → MCPClient (stdio subprocess) → Tool execution → Response formatting → Display

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
