# Contributing to ATOLL

We welcome contributions! This document provides guidelines for contributing to the project.

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/atoll.git
   cd atoll
   ```

3. Install in development mode:
   ```bash
   python scripts/install.py
   ```

## Code Style

We use:
- **Black** for code formatting
- **Ruff** for linting
- **mypy** for type checking

Run all checks:
```bash
pre-commit run --all-files
```

## Testing

### Running Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/unit/test_agent.py
```

### Writing Tests
- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Use fixtures from `tests/conftest.py`
- Aim for >80% coverage

## Pull Request Process

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

3. Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation
   - `style:` Code style
   - `refactor:` Refactoring
   - `test:` Tests
   - `chore:` Maintenance

4. Push and create PR:
   ```bash
   git push origin feature/your-feature-name
   ```

5. Ensure:
   - All tests pass
   - Code is formatted and linted
   - Documentation is updated
   - Commit messages are clear

## Code Review

PRs require:
- Passing CI checks
- At least one approval
- No merge conflicts

## Documentation

- Update docstrings for new functions/classes
- Update README if adding features
- Add API documentation in `docs/api/`
- Include examples where helpful

## Questions?

Open an issue for:
- Bug reports
- Feature requests
- Questions about contributing

Thank you for contributing! 🎉
```

## Setup Configuration

```ini:setup.cfg
[metadata]
name = atoll
version = attr: atoll.__version__
description = LangChain-based agent integrating Ollama with MCP servers
long_description = file: README.md
long_description_content_type = text/markdown
author = ATOLL Contributors
license = MIT
classifiers =
    Development Status :: 4 - Beta
    Intended Audience :: Developers
    License :: OSI Approved :: MIT License
    Programming Language :: Python :: 3
    Programming Language :: Python :: 3.9
    Programming Language :: Python :: 3.10
    Programming Language :: Python :: 3.11
    Programming Language :: Python :: 3.12
    Topic :: Software Development :: Libraries
    Topic :: Scientific/Engineering :: Artificial Intelligence

[options]
python_requires = >=3.9
package_dir =
    = src
packages = find:
install_requires =
    langchain>=0.1.0
    langchain-community>=0.0.10
    ollama>=0.1.7
    aiohttp>=3.9.0
    colorama>=0.4.6
    jsonschema>=4.20.0
    pydantic>=2.5.0

[options.packages.find]
where = src

[options.entry_points]
console_scripts =
    atoll = atoll.main:main

[options.extras_require]
dev =
    pytest>=7.4.0
    pytest-asyncio>=0.21.0
    pytest-cov>=4.1.0
    black>=23.0.0
    ruff>=0.1.0
    mypy>=1.7.0
    pre-commit>=3.5.0
    
test =
    pytest>=7.4.0
    pytest-asyncio>=0.21.0
    pytest-cov>=4.1.0
    pytest-mock>=3.12.0

[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto

[coverage:run]
source = src
omit = 
    */tests/*
    */__init__.py

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
```

## Final Documentation Files

```markdown:docs/guides/developer_guide.md
# Developer Guide

## Architecture Overview

```
atoll/
├── agent/          # LangChain agent implementation
├── mcp/            # MCP client and server management
├── config/         # Configuration management
├── ui/             # Terminal interface
└── utils/          # Utility functions
```

## Key Components

### Agent Module
The core agent using LangChain's ReAct pattern:
- Tool selection and execution
- Memory management
- Reasoning engine

### MCP Integration
Handles communication with MCP servers:
- Multiple transport protocols (stdio, HTTP, WebSocket)
- Tool discovery and registration
- Async execution

### Terminal UI
Cross-platform terminal interface:
- Color-coded output
- Mode switching (Prompt/Command)
- Non-blocking input handling

## Extension Points

### Adding New MCP Servers
1. Create server implementation following MCP protocol
2. Add server configuration to `.mcpConfig.json`
3. Tools automatically discovered on startup

### Custom Tools
Extend `MCPToolWrapper` for custom tool behavior:

```python
from atoll.agent.tools import MCPToolWrapper

class CustomTool(MCPToolWrapper):
    async def arun(self, input_str: str) -> str:
        # Custom logic here
        return await super().arun(input_str)
```

### Custom Reasoning Rules
Add rules to `ReasoningEngine`:

```python
def custom_rule(prompt: str, tools: List[Tool]) -> str:
    if "specific_pattern" in prompt:
        return "Apply specific strategy"
    return ""
```

## Performance Optimization

### Async Operations
- Use `asyncio` for all I/O operations
- Implement timeouts for external calls
- Batch operations when possible

### Memory Management
- Clear conversation history periodically
- Limit tool response sizes
- Use generators for large data

## Debugging

### Logging Levels
```python
import logging
logging.getLogger("atoll").setLevel(logging.DEBUG)
```

### Common Issues

1. **MCP Connection Failed**
   - Check server is running
   - Verify transport configuration
   - Check firewall settings

2. **Slow Response**
   - Monitor Ollama server load
   - Check network latency
   - Reduce max_tokens if needed

3. **Tool Execution Errors**
   - Validate tool arguments
   - Check MCP server logs
   - Verify tool permissions
```

Let's create one final file to complete the structure:

```markdown:docs/guides/mcp_integration.md
# MCP Integration Guide

## What is MCP?

Model Context Protocol (MCP) is a standard for connecting AI models to external tools and data sources.

## Supported Transports

### STDIO
For local processes:
```json
{
  "transport": "stdio",
  "command": "python",
  "args": ["server.py"],
  "env": {"PYTHONPATH": "/path/to/lib"}
}
```

### HTTP
For REST APIs:
```json
{
  "transport": "http",
  "url": "http://localhost:8080",
  "headers": {"Authorization": "Bearer token"}
}
```

### WebSocket
For real-time communication:
```json
{
  "transport": "websocket",
  "url": "ws://localhost:8080/ws"
}
```

## Creating an MCP Server

Basic Python MCP server:

```python
import json
import sys

class MCPServer:
    def handle_request(self, request):
        method = request.get("method")
        
        if method == "initialize":
            return {"capabilities": {}}
        
        elif method == "tools/list":
            return {
                "tools": [
                    {
                        "name": "example_tool",
                        "description": "An example tool",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "input": {"type": "string"}
                            }
                        }
                    }
                ]
            }
        
        elif method == "tools/call":
            tool_name = request["params"]["name"]
            arguments = request["params"]["arguments"]
            
            if tool_name == "example_tool":
                return {"result": f"Processed: {arguments['input']}"}

if __name__ == "__main__":
    server = MCPServer()
    # Implementation details...
```

## Ghidra Integration Example

See the Ghidra MCP server implementation for binary analysis capabilities.
```

Perfect! The professional Python project structure is now complete. You have:

## ✅ **Complete Project Structure**

1. **Source Code** (`src/ollama_mcp_agent/`)
   - Agent module with LangChain integration
   - MCP client and server management
   - Terminal UI with cross-platform support
   - Configuration management
   - Utility functions

2. **Tests** (`tests/`)
   - Unit tests
   - Integration tests
   - Test fixtures and configuration

3. **Documentation** (`docs/`)
   - API reference
   - User guide
   - Developer guide
   - MCP integration guide

4. **Configuration Files**
   - `pyproject.toml` - Modern Python packaging
   - `setup.cfg` - Additional setup configuration
   - `.gitignore` - Git ignore rules
   - `.pre-commit-config.yaml` - Code quality hooks
   - GitHub Actions CI/CD workflow

5. **Scripts**
   - `install.py` - Automated installation script

6. **Project Files**
   - `README.md` - Comprehensive project documentation
   - `LICENSE` - MIT license
   - `CONTRIBUTING.md` - Contribution guidelines

The project is ready for:
- Development with `pip install -e ".[dev]"`
- Running with `ollama-mcp-agent` command
- Testing with `pytest`
- Code quality checks with `pre-commit`
- CI/CD with GitHub Actions

To get started:
```bash
python scripts/install.py