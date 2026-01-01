# ATOLL - Agentic Tools Orchestration on OLLama

<div align="center">

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Coverage](https://img.shields.io/badge/coverage-90%25-green.svg)](https://github.com/Buttje/ATOLL)
[![Version](https://img.shields.io/badge/version-2.0.0-brightgreen.svg)](https://github.com/Buttje/ATOLL/releases)

**A powerful LangChain-based AI agent that seamlessly integrates Ollama LLMs with MCP (Model Context Protocol) servers, enabling intelligent tool orchestration and extensible capabilities through MCP server integration.**

**✨ NEW in v2.0:** REST API for remote agent management, ZIP package deployment, MD5 checksum tracking, and virtual environment isolation!

[Features](#features) • [Quick Start](#quick-start) • [v2.0 Features](#v20-deployment-server) • [Documentation](#documentation) • [Contributing](#contributing)

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Usage](#usage)
- [Terminal Interface](#terminal-interface)
- [Architecture](#architecture)
- [Development](#development)
  - [Running Tests](#running-tests)
  - [Code Quality](#code-quality)
- [Documentation](#documentation)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Roadmap](#roadmap)
- [FAQ](#faq)
- [Support](#support)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## 🌟 Overview

ATOLL (Agentic Tools Orchestration on OLLama) is an intelligent AI agent framework that bridges the gap between local LLMs powered by Ollama and external tools through the Model Context Protocol (MCP). It provides a flexible, extensible platform for building AI applications that can interact with various tools and services.

**Key Capabilities:**
- Natural language interaction with AI agents
- Tool orchestration through MCP servers
- Support for multiple transport protocols (stdio, HTTP, SSE)
- Interactive terminal interface with dual modes
- Extensible architecture for custom tool integration

**Use Cases:**
- Automated system administration
- Data analysis and transformation
- Development workflow automation
- Research and experimentation with LLM agents

---

## ✨ Features

### Core Capabilities

- 🤖 **LangChain Agent Integration**: Intelligent decision-making and reasoning powered by Ollama LLM
- 🔧 **MCP Server Support**: Connect to multiple MCP servers with different transport protocols (stdio, HTTP, SSE)
- 🎨 **Interactive Terminal UI**: Color-coded interface with command and prompt modes for enhanced user experience
- ⚡ **Fast Local Operations**: Optimized for quick response times (<2s) with local LLM execution
- 📊 **Comprehensive Logging**: Detailed reasoning steps, error tracking, and debugging information
- 🔒 **Type-Safe Configuration**: Pydantic-based validation for configuration files
- 🧪 **Well-Tested**: Extensive test coverage (90%+) with unit and integration tests
- 🔄 **Hot Model Switching**: Change LLM models on-the-fly without restarting
- 💾 **Conversation Memory**: Maintains context across interactions with memory management

### 🚀 v2.0 Deployment Server

**NEW in v2.0 - Production-Ready Agent Management:**

- 🌐 **REST API**: Full-featured HTTP API for remote agent lifecycle management
- 📦 **ZIP Package Deployment**: Deploy agents as self-contained ZIP packages with automatic extraction
- 🔐 **MD5 Checksum Tracking**: Prevent duplicate deployments and ensure package integrity
- 🏠 **Virtual Environment Isolation**: Each agent runs in its own isolated Python environment
- 📡 **Deployment Client**: Python client library for programmatic server interaction (async & sync APIs)
- 🔄 **Auto-Restart**: Automatic agent restart on failure (configurable)
- 📊 **Status Monitoring**: Real-time agent status, port allocation, and health checks
- 🎯 **Multi-Agent Orchestration**: Deploy and manage multiple coordinated agents

**Perfect for:**
- CI/CD pipelines
- Production deployments
- Multi-agent systems
- Remote agent management
- Containerized deployments

See [Deployment Server v2.0 Usage Guide](docs/DEPLOYMENT_SERVER_V2_USAGE.md) for details.

---

## 📦 Prerequisites

Before installing ATOLL, ensure you have the following:

### Required
- **Python 3.9 or higher** - [Download Python](https://www.python.org/downloads/)
- **Ollama** - Local LLM runtime [Install Ollama](https://ollama.ai/)
- **pip** - Python package manager (usually included with Python)

### Optional
- **Git** - For cloning the repository
- **Virtual Environment** - Recommended for isolation (venv, conda, etc.)

### System Requirements
- **OS**: Linux, macOS, or Windows (with WSL recommended)
- **RAM**: Minimum 8GB (16GB recommended for larger models)
- **Disk**: ~2GB for installation + space for LLM models

---

## 🚀 Quick Start

### Installation

#### Option 1: Using the Installer (Recommended)

```bash
# Clone the repository
git clone https://github.com/Buttje/ATOLL.git
cd ATOLL

# Run the automated installer
python install.py
```

#### Option 2: Manual Installation

```bash
# Clone the repository
git clone https://github.com/Buttje/ATOLL.git
cd ATOLL

# Create and activate virtual environment
python -m venv venv

# Activate on Linux/macOS
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate

# Install the package with development dependencies
pip install -e ".[dev]"
```

#### Option 3: Install from PyPI

> **Note**: PyPI package is not yet available. This option will be enabled in a future release.

```bash
# Coming soon
# pip install atoll
```

### Configuration

ATOLL requires two configuration files in JSON format:

#### 1. Ollama Configuration (`~/.ollama_server/.ollama_config.json`)

Create this file in your home directory under `.ollama_server/`:

```json
{
  "base_url": "http://localhost",
  "port": 11434,
  "model": "llama2",
  "request_timeout": 30,
  "max_tokens": 2048
}
```

**Configuration Options:**
- `base_url`: Ollama server URL (default: `http://localhost`)
- `port`: Ollama server port (default: `11434`)
- `model`: LLM model name (e.g., `llama2`, `mistral`, `codellama`)
- `request_timeout`: Request timeout in seconds
- `max_tokens`: Maximum tokens for generation

> **Note**: Make sure Ollama is running with `ollama serve` and you have pulled the desired model with `ollama pull llama2`

#### 2. MCP Configuration (`mcp.json`)

Create this file to configure MCP servers following the [MCP Config Schema](https://json.schemastore.org/mcp-config-0.1.0.json):

```json
{
  "servers": {
    "my-stdio-server": {
      "type": "stdio",
      "command": "python",
      "args": ["path/to/server.py"],
      "cwd": "${workspaceFolder}",
      "env": {
        "API_KEY": "your-key-here"
      }
    },
    "my-http-server": {
      "type": "http",
      "url": "http://localhost:8080/mcp",
      "headers": {
        "Authorization": "Bearer token"
      }
    },
    "my-sse-server": {
      "type": "sse",
      "url": "http://localhost:8080/events"
    }
  }
}
```

**Server Types:**
- `stdio`: Standard input/output communication (for local scripts/executables)
  - Required: `command`
  - Optional: `args`, `env`, `cwd`, `envFile`
- `http`: HTTP-based communication
  - Required: `url`
  - Optional: `headers`
- `sse`: Server-Sent Events for streaming
  - Required: `url`
  - Optional: `headers`

> **Tip**: Start with an empty `servers` object if you don't have MCP servers configured yet

### Usage

#### Starting the Agent

```bash
# Using the installed command
atoll

# Or run as a module
python -m atoll
```

**Startup Indicators:**

When ATOLL starts, it checks and displays:
- ✓ **Ollama Server Status**: Whether the Ollama server is reachable at the configured URL and port
- ✓ **Model Availability**: Whether the configured model is available on the server

If the server is unreachable or the model is unavailable, you'll see warning messages with suggestions.

#### Basic Interaction

Once started, you'll see the interactive terminal interface:

```
============================================================
Ollama MCP Agent
Mode: Prompt (Press ESC to toggle)
============================================================

💬 Enter prompt: How can I analyze this binary file?
```

#### Command Mode

Press `ESC` to toggle to Command mode for system commands:

```bash
# List available models
Models

# Switch to a different model
ChangeModel mistral

# Configure Ollama server connection
SetServer http://localhost 11434

# List connected MCP servers
Servers

# List available tools
Tools

# Get help on a specific tool
help tool analyze_function

# Clear conversation memory
Clear

# Exit the application
Quit
```

#### Prompt Mode

In Prompt mode, ask questions in natural language:

```
💬 What functions are defined in this binary?
💬 Analyze the main function and explain what it does
💬 Find potential security vulnerabilities
```

---

## 🎨 Terminal Interface

ATOLL features a rich, color-coded terminal interface designed for clarity and ease of use:

### Color Scheme

- **🔵 Blue**: User input and prompts
- **🟡 Yellow**: Agent reasoning and thought process
- **🟢 Green**: Final responses and success messages
- **🔴 Red**: Error messages and warnings
- **🟣 Cyan**: System information and status

### Operating Modes

#### Prompt Mode (Default)
Natural language interaction with the AI agent:
```
💬 Enter prompt: Analyze this function for vulnerabilities
```

#### Command Mode
System commands and configuration:
```
⚡ Enter command: Models
```

Press `ESC` to toggle between modes at any time.

### Available Commands

| Command | Description |
|---------|-------------|
| `Models` | List all available Ollama models |
| `ChangeModel <model>` | Switch to a different model |
| `SetServer <url> [port]` | Configure Ollama server connection (e.g., `SetServer http://localhost 11434`) |
| `Servers` | List connected MCP servers |
| `Tools` | List available MCP tools |
| `help` | Display help information |
| `help server <name>` | Get details about a specific server |
| `help tool <name>` | Get details about a specific tool |
| `Clear` | Clear conversation memory |
| `Quit` / `Exit` | Exit the application |

### Keyboard Shortcuts

- `ESC` - Toggle between Prompt and Command modes
- `Ctrl+C` - Exit the application gracefully
- `Enter` - Submit input
- Arrow keys - Navigate command history (coming soon)

---

## 🏗️ Architecture

ATOLL is built with a modular, extensible architecture:

```
┌─────────────────────────────────────────────┐
│           Terminal UI (Prompt/Command)       │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         OllamaMCPAgent (LangChain)          │
│  ┌──────────────┐       ┌────────────────┐ │
│  │  Reasoning   │◄──────┤  Tool Calling  │ │
│  └──────────────┘       └────────────────┘ │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐   ┌────────▼──────────┐
│  Ollama LLM    │   │  MCP Server Mgr   │
│  (Local Model) │   │  ┌──────────────┐ │
└────────────────┘   │  │ Server Pool  │ │
                     │  │  - stdio     │ │
                     │  │  - HTTP      │ │
                     │  │  - SSE       │ │
                     │  └──────────────┘ │
                     └───────────────────┘
```

### Core Components

1. **Terminal UI** (`atoll/ui/`)
   - Input handling (prompt and command modes)
   - Color-coded output rendering
   - Mode switching and user interaction

2. **Agent** (`atoll/agent/`)
   - LangChain-based reasoning engine
   - Tool selection and orchestration
   - Conversation memory management

3. **MCP Integration** (`atoll/mcp/`)
   - Multi-protocol server connections
   - Tool registry and discovery
   - Request/response handling

4. **Configuration** (`atoll/config/`)
   - Pydantic-based validation
   - JSON schema validation
   - Runtime configuration management

5. **Utilities** (`atoll/utils/`)
   - Async helpers
   - Logging infrastructure
   - Validation utilities

### How It Works

1. **User Input**: User enters a prompt or command
2. **Parsing**: Input is parsed and validated
3. **Reasoning**: LangChain agent analyzes the request
4. **Tool Selection**: Agent decides which tools to use
5. **Execution**: Tools are called via MCP protocol
6. **Response**: Results are formatted and displayed

---

## 🔧 Development

We welcome contributions! Here's how to set up your development environment.

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/Buttje/ATOLL.git
cd ATOLL

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests with coverage
pytest

# Run specific test categories
pytest tests/unit              # Unit tests only
pytest tests/integration       # Integration tests only

# Run tests with verbose output
pytest -v

# Run tests matching a pattern
pytest -k "test_agent"

# Generate coverage report
pytest --cov=atoll --cov-report=html
open htmlcov/index.html        # View coverage report
```

### Code Quality

ATOLL maintains high code quality standards:

```bash
# Format code with black
black src tests

# Check code style with ruff
ruff check src tests

# Fix auto-fixable issues
ruff check --fix src tests

# Type checking with mypy
mypy src

# Run all checks (used in CI)
pre-commit run --all-files
```

### Project Structure

```
ATOLL/
├── src/atoll/              # Main source code
│   ├── agent/              # Agent implementation
│   ├── config/             # Configuration management
│   ├── mcp/                # MCP client and server management
│   ├── ui/                 # Terminal UI components
│   ├── utils/              # Utility functions
│   ├── __init__.py
│   ├── __main__.py
│   └── main.py             # Main entry point
├── tests/                  # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── fixtures/           # Test fixtures
├── docs/                   # Documentation
│   ├── api/                # API reference
│   └── guides/             # User and developer guides
├── scripts/                # Utility scripts
├── pyproject.toml          # Project configuration
├── .pre-commit-config.yaml # Pre-commit hooks
├── CONTRIBUTING.md         # Contribution guidelines
└── README.md               # This file
```

### Adding New Features

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Write tests for your feature
3. Implement your feature
4. Ensure all tests pass: `pytest`
5. Run code quality checks: `pre-commit run --all-files`
6. Commit your changes: `git commit -m "Add your feature"`
7. Push and create a pull request

---

## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory:

### Available Guides

- **[API Reference](docs/api/README.md)** - Detailed API documentation
- **[User Guide](docs/guides/user_guide.md)** - Complete user manual
- **[Developer Guide](docs/guides/developer_guide.md)** - Contributing and development
- **[MCP Integration Guide](docs/guides/mcp_integration.md)** - Setting up MCP servers
- **[Configuration Reference](docs/guides/configuration.md)** - Configuration options

### Quick Links

- [GitHub Issues](https://github.com/Buttje/ATOLL/issues) - Report bugs or request features
- [GitHub Discussions](https://github.com/Buttje/ATOLL/discussions) - Ask questions and share ideas
- [Changelog](https://github.com/Buttje/ATOLL/releases) - Version history and updates

---

## 🐛 Troubleshooting

### Common Issues

#### Issue: "Ollama config not found"
**Solution**: Create a `~/.ollama_server/.ollama_config.json` file with the required configuration. See [Configuration](#configuration) section. You can also let ATOLL create one with defaults on first run.

#### Issue: "Connection refused to Ollama"
**Solution**:
1. Ensure Ollama is running: `ollama serve`
2. Check the port in your config matches Ollama's port (default: 11434)
3. Verify with: `curl http://localhost:11434/api/tags`
4. Use the `SetServer` command to configure the correct URL and port

**Note**: ATOLL now displays connection status on startup. If you see "✗ Cannot reach Ollama server", follow the steps above or use `SetServer` to configure the correct connection.

#### Issue: "Model not found"
**Solution**: Pull the model first: `ollama pull llama2`

**Note**: ATOLL checks model availability on startup. If you see "⚠ Model 'xyz' is not available", either pull the model or use `ChangeModel` to switch to an available model (shown with `Models` command).

#### Issue: "MCP server failed to connect"
**Solution**:
1. Verify the server command/path is correct
2. Check if the server script is executable
3. Review server logs for errors
4. Test the server independently

#### Issue: "Import errors after installation"
**Solution**:
1. Ensure you're using Python 3.9+: `python --version`
2. Reinstall in a fresh virtual environment
3. Update pip: `pip install --upgrade pip`

#### Issue: "Tests failing"
**Solution**:
1. Install dev dependencies: `pip install -e ".[dev]"`
2. Check Python version compatibility
3. Clear pytest cache: `pytest --cache-clear`

### Getting Help

If you encounter issues not listed here:

1. **Check existing issues**: [GitHub Issues](https://github.com/Buttje/ATOLL/issues)
2. **Search discussions**: [GitHub Discussions](https://github.com/Buttje/ATOLL/discussions)
3. **Create a new issue**: Include:
   - Python version
   - Operating system
   - Installation method
   - Error messages and logs
   - Steps to reproduce

---

## 🤝 Contributing

We love contributions! ATOLL is an open-source project and we welcome contributions of all kinds:

- 🐛 Bug reports and fixes
- ✨ New features and enhancements
- 📝 Documentation improvements
- 🧪 Test coverage improvements
- 💡 Ideas and suggestions

### How to Contribute

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
4. **Make your changes** and commit them
5. **Write or update tests** as needed
6. **Ensure all tests pass** (`pytest`)
7. **Push to your fork** (`git push origin feature/amazing-feature`)
8. **Create a Pull Request** on GitHub

### Contribution Guidelines

Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for detailed information on:

- Code of conduct
- Development workflow
- Coding standards
- Testing requirements
- Pull request process
- Review process

### Development Principles

- **Write tests**: All new features should include tests
- **Document changes**: Update docs for user-facing changes
- **Follow style**: Use black, ruff, and mypy for code quality
- **Keep it simple**: Prefer clarity over cleverness
- **Be respectful**: Follow our code of conduct

### Areas We Need Help

- 🌐 Additional MCP server integrations
- 📱 UI/UX improvements
- 🌍 Internationalization (i18n)
- 📖 Documentation and examples
- 🧪 Test coverage expansion
- 🚀 Performance optimizations

---

## 🗺️ Roadmap

### Current Version (v1.0.0)
- ✅ Core LangChain agent integration
- ✅ MCP server support (stdio, HTTP, SSE)
- ✅ Interactive terminal UI
- ✅ Comprehensive test suite

### Upcoming Features

#### v1.1.0 (Q1 2026)
- [ ] Web-based UI interface
- [ ] Plugin system for custom tools
- [ ] Enhanced error recovery
- [ ] Performance optimizations
- [ ] Additional LLM provider support

#### v1.2.0 (Q2 2026)
- [ ] Multi-agent coordination
- [ ] Persistent conversation storage
- [ ] API server mode
- [ ] Docker container support
- [ ] Cloud deployment guides

#### v2.0.0 (Future)
- [ ] Distributed agent system
- [ ] Advanced reasoning capabilities
- [ ] Integration marketplace
- [ ] Enterprise features
- [ ] SaaS offering

Want to influence the roadmap? [Join the discussion](https://github.com/Buttje/ATOLL/discussions)!

---

## ❓ FAQ

### General Questions

**Q: What is ATOLL?**
A: ATOLL is an AI agent framework that connects Ollama LLMs with external tools via the Model Context Protocol (MCP).

**Q: Do I need an API key?**
A: No! ATOLL uses local Ollama models, so no API keys or cloud services are required.

**Q: What models are supported?**
A: Any model available in Ollama (llama2, mistral, codellama, etc.). See [Ollama's model library](https://ollama.ai/library).

**Q: Can I use this commercially?**
A: Yes! ATOLL is MIT licensed. Check individual model licenses for commercial use restrictions.

### Technical Questions

**Q: How do I add custom tools?**
A: Create an MCP server that implements your tools, then configure it in `mcp.json`. See the [MCP Integration Guide](docs/guides/mcp_integration.md).

**Q: Can I use multiple models simultaneously?**
A: Currently, one model at a time, but you can switch models without restarting using the `ChangeModel` command.

**Q: Does it support streaming responses?**
A: Not yet in the current version. Streaming support is planned for v1.1.0.

**Q: What's the performance like?**
A: Local operations are fast (<2s for most queries). Performance depends on your hardware and the model size.

**Q: Can I run this in a Docker container?**
A: Not officially packaged yet, but it's straightforward to containerize. Docker support is planned for v1.2.0.

### Deployment Questions

**Q: Can I deploy this to a server?**
A: Yes! The current version runs in terminal mode. API server mode is coming in v1.2.0.

**Q: What are the hardware requirements?**
A: Minimum 8GB RAM, 16GB recommended. Requirements scale with model size.

**Q: Can I use remote Ollama instances?**
A: Yes! Configure the `base_url` and `port` in `~/.ollama_server/.ollama_config.json` to point to a remote server. You can also use the `setserver` command at runtime to switch between different Ollama servers without restarting. Changes made via commands are automatically saved.

**Q: How do I know if my Ollama server is reachable?**
A: ATOLL automatically checks the server connection on startup and displays a clear status indicator. You'll see either "✓ Ollama server is reachable" or "✗ Cannot reach Ollama server" with helpful suggestions.

**Q: What if my model isn't available?**
A: ATOLL checks model availability on startup. If your configured model isn't found, you'll see a warning. Use the `Models` command to see available models and `ChangeModel` to switch, or pull the model using `ollama pull <model-name>`.

---

## 💬 Support

### Getting Help

- 📖 **Documentation**: Check the [docs](docs/) directory first
- 💬 **Discussions**: [GitHub Discussions](https://github.com/Buttje/ATOLL/discussions) for questions and ideas
- 🐛 **Issues**: [GitHub Issues](https://github.com/Buttje/ATOLL/issues) for bug reports
- 📧 **Email**: For sensitive matters, contact the maintainers

### Community

- 🌟 **Star the repo** to show support
- 👁️ **Watch** for updates and releases
- 🍴 **Fork** to create your own version
- 🗣️ **Share** your use cases and experiences

### Resources

- [Ollama Documentation](https://ollama.ai/docs)
- [LangChain Documentation](https://python.langchain.com/)
- [MCP Specification](https://github.com/modelcontextprotocol/specification)

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for full details.

### What This Means

✅ **You can**:
- Use commercially
- Modify and distribute
- Use privately
- Sublicense

❌ **You must**:
- Include the license and copyright notice
- State changes made to the code

❌ **Limitations**:
- No warranty provided
- No liability accepted

---

## 🙏 Acknowledgments

ATOLL stands on the shoulders of giants. We're grateful to:

### Core Technologies
- **[LangChain](https://github.com/langchain-ai/langchain)** - For the powerful agent framework
- **[Ollama](https://ollama.ai/)** - For making local LLMs accessible and practical
- **[Pydantic](https://github.com/pydantic/pydantic)** - For robust data validation

### Protocols & Standards
- **[MCP Protocol](https://github.com/modelcontextprotocol/specification)** - For the tool integration specification

### Development Tools
- **[pytest](https://pytest.org/)** - Testing framework
- **[black](https://github.com/psf/black)** - Code formatting
- **[ruff](https://github.com/astral-sh/ruff)** - Fast Python linter
- **[mypy](https://github.com/python/mypy)** - Static type checking

### Community
- All our **[contributors](https://github.com/Buttje/ATOLL/graphs/contributors)** who help improve ATOLL
- The **open source community** for inspiration and support
- **Early adopters** who provided valuable feedback

### Special Thanks
- The LangChain team for their excellent documentation
- The Ollama community for model optimization insights
- Everyone who filed issues, submitted PRs, and shared ideas

---

<div align="center">

**[⬆ Back to Top](#atoll---agentic-tools-orchestration-on-ollama)**

Made with ❤️ by the ATOLL community

[![GitHub stars](https://img.shields.io/github/stars/Buttje/ATOLL?style=social)](https://github.com/Buttje/ATOLL/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Buttje/ATOLL?style=social)](https://github.com/Buttje/ATOLL/network/members)
[![GitHub watchers](https://img.shields.io/github/watchers/Buttje/ATOLL?style=social)](https://github.com/Buttje/ATOLL/watchers)

</div>
