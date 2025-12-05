# API Reference

## Core Modules

### Agent Module
- [OllamaMCPAgent](agent.md) - Main agent implementation
- [MCPToolWrapper](tools.md) - LangChain tool wrapper for MCP
- [ReasoningEngine](reasoning.md) - Reasoning and decision engine

### MCP Module
- [MCPClient](mcp_client.md) - MCP server client
- [MCPServerManager](mcp_manager.md) - Manages multiple MCP connections
- [MCPToolRegistry](mcp_registry.md) - Tool discovery and registration

### Config Module
- [ConfigManager](config_manager.md) - Configuration management
- [Models](config_models.md) - Configuration data models

### UI Module
- [TerminalUI](terminal_ui.md) - Terminal interface
- [ColorScheme](colors.md) - Color management
- [InputHandler](input.md) - Cross-platform input handling

### Utils Module
- [Logging](logging.md) - Logging utilities
- [Validators](validators.md) - Validation functions
- [AsyncHelpers](async.md) - Async utility functions
```

```markdown:docs/guides/user_guide.md
# User Guide

## Installation

### Requirements
- Python 3.9 or higher
- Ollama installed and running
- MCP servers (optional)

### Quick Install
```bash
python scripts/install.py
```

### Manual Installation
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install package
pip install -e ".[dev]"
```

## Configuration

### Ollama Configuration
Create `.ollamaConfig.json`:
```json
{
  "base_url": "http://localhost",
  "port": 11434,
  "model": "llama2",
  "request_timeout": 30,
  "max_tokens": 2048
}
```

### MCP Configuration
Create `.mcpConfig.json`:
```json
{
  "servers": {
    "example": {
      "transport": "stdio",
      "command": "python",
      "args": ["path/to/server.py"],
      "timeoutSeconds": 30
    }
  }
}
```

## Usage

### Starting the Agent
```bash
ollama-mcp-agent
```

### UI Modes

#### Prompt Mode
- Default mode for interacting with the agent
- Enter natural language prompts
- Agent will reason and use available tools

#### Command Mode
- Press ESC to toggle to Command Mode
- Available commands:
  - `Models` - List available Ollama models
  - `ChangeModel <name>` - Switch to a different model
  - `Quit` - Exit the application

### Example Prompts

1. **Binary Analysis**:
   ```
   Find all implementations of strcmp function, including inlined versions
   ```

2. **Code Search**:
   ```
   Search for security vulnerabilities in the authentication module
   ```

3. **General Query**:
   ```
   What is the purpose of function at address 0x401000?
   ```

## Tips

- Keep prompts clear and specific
- Use Command Mode to switch models for different tasks
- Check logs for detailed reasoning steps
- Ensure MCP servers are running before starting the agent
```

## GitHub Actions Workflow

```yaml:.github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: ['3.9', '3.10', '3.11', '3.12']

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[test]"
    
    - name: Run tests
      run: |
        pytest --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true

  lint:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Run linters
      run: |
        black --check src tests
        ruff check src tests
        mypy src
```

Let's verify everything is created properly:

```bash
dir /s /b