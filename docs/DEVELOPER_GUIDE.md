# Developer Guide

**Version:** 2.0.0  
**Last Updated:** January 2025

This guide helps developers extend ATOLL with custom agents, new LLM strategies, and deployment capabilities.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Creating a Custom Agent](#creating-a-custom-agent)
3. [Implementing a New LLM Strategy](#implementing-a-new-llm-strategy)
4. [Extending the Deployment Server](#extending-the-deployment-server)
5. [Adding New MCP Tools](#adding-new-mcp-tools)
6. [Testing Your Extensions](#testing-your-extensions)
7. [Contributing Back](#contributing-back)

---

## Getting Started

### Development Environment Setup

```bash
# Clone repository
git clone https://github.com/Buttje/ATOLL.git
cd ATOLL

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests to verify setup
pytest
```

### Project Structure

```
ATOLL/
├── src/atoll/              # Main source code
│   ├── agent/              # Agent implementations
│   │   ├── agent.py        # Base agent classes
│   │   ├── root_agent.py   # Root agent for user interaction
│   │   ├── agent_manager.py # Agent lifecycle management
│   │   └── reasoning.py    # Reasoning engine
│   ├── config/             # Configuration management
│   ├── deployment/         # Deployment server & API
│   │   ├── server.py       # Local deployment server
│   │   ├── api.py          # REST API endpoints
│   │   ├── client.py       # Deployment client
│   │   └── cli.py          # CLI entry point
│   ├── mcp/                # MCP protocol integration
│   ├── ui/                 # Terminal interface
│   ├── utils/              # Utility modules
│   │   ├── venv_utils.py   # Virtual environment helpers
│   │   ├── port_manager.py # Port allocation
│   │   └── logger.py       # Logging setup
│   └── main.py             # Main application entry
├── tests/                  # Test suite
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
└── docs/                   # Documentation
```

---

## Creating a Custom Agent

### Basic Agent Structure

Create a new agent by following this template:

**1. Create Agent Directory**

```bash
mkdir -p atoll_agents/my_custom_agent
cd atoll_agents/my_custom_agent
```

**2. Create `agent.toml` Configuration**

```toml
# agent.toml
[agent]
name = "my_custom_agent"
version = "1.0.0"
description = "My custom agent for specialized tasks"
author = "Your Name"
license = "MIT"

[agent.runtime]
python_version = ">=3.9"
entry_point = "main.py"

[agent.server]
host = "localhost"
# Port will be auto-assigned by deployment server

[agent.capabilities]
# List of capabilities your agent provides
tools = ["custom_tool_1", "custom_tool_2"]
```

**3. Create `requirements.txt`**

```txt
langchain>=0.2.0
langchain-ollama>=0.1.0
# Add your specific dependencies
requests>=2.28.0
pydantic>=2.0.0
```

**4. Create `main.py` Entry Point**

```python
"""Custom agent implementation."""

import asyncio
from atoll.agent.agent import ATOLLAgent
from atoll.config.models import OllamaConfig
from atoll.utils.logger import get_logger

logger = get_logger(__name__)


class MyCustomAgent(ATOLLAgent):
    """Custom agent with specialized capabilities."""

    def __init__(self, ollama_config: OllamaConfig, port: int = 8100):
        """Initialize custom agent.
        
        Args:
            ollama_config: Ollama LLM configuration
            port: Port for agent server (auto-assigned by deployment)
        """
        super().__init__(ollama_config)
        self.port = port
        self.server_running = False

    async def start_server(self) -> None:
        """Start the agent server."""
        logger.info(f"Starting custom agent on port {self.port}")
        self.server_running = True
        
        # Implement your server logic here
        # Example: HTTP server, WebSocket server, etc.
        
        print(f"Custom Agent listening on port {self.port}")
        
        # Keep server running
        while self.server_running:
            await asyncio.sleep(1)

    async def shutdown(self) -> None:
        """Shutdown the agent server."""
        logger.info("Shutting down custom agent")
        self.server_running = False


async def main():
    """Main entry point for custom agent."""
    # Load configuration
    from atoll.config.manager import ConfigManager
    
    config_manager = ConfigManager()
    ollama_config, _ = config_manager.load_configs()
    
    # Get port from environment (set by deployment server)
    import os
    port = int(os.getenv("AGENT_PORT", "8100"))
    
    # Create and start agent
    agent = MyCustomAgent(ollama_config, port=port)
    
    try:
        await agent.start_server()
    except KeyboardInterrupt:
        await agent.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

**5. Create `README.md`**

```markdown
# My Custom Agent

## Description
Detailed description of what your agent does.

## Installation
\```bash
pip install -r requirements.txt
\```

## Usage
\```bash
python main.py
\```

## Configuration
- `AGENT_PORT`: Port to listen on (default: 8100)
```

**6. Deploy Your Agent**

```bash
# Package your agent
cd atoll_agents
zip -r my_custom_agent.zip my_custom_agent/

# Deploy via REST API
curl -X POST http://localhost:8080/agents/upload \
  -F "file=@my_custom_agent.zip"

# Or use deployment client
from atoll.deployment.client import DeploymentClient

client = DeploymentClient("http://localhost:8080")
await client.deploy_agent("my_custom_agent.zip")
```

---

## Implementing a New LLM Strategy

ATOLL supports multiple LLM backends through a strategy pattern. Here's how to add a new provider:

### LLM Strategy Interface

```python
"""Example: Adding OpenAI as an LLM strategy."""

from typing import Any, Dict, List, Optional
from langchain_core.language_models import BaseLLM
from langchain_openai import ChatOpenAI


class OpenAIStrategy:
    """LLM strategy for OpenAI models."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ):
        """Initialize OpenAI strategy.
        
        Args:
            api_key: OpenAI API key
            model: Model name (e.g., 'gpt-4', 'gpt-3.5-turbo')
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional OpenAI parameters
        """
        self.model_name = model
        self.llm = ChatOpenAI(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

    def get_llm(self) -> BaseLLM:
        """Get the LangChain LLM instance."""
        return self.llm

    def generate(self, prompt: str) -> str:
        """Generate completion for prompt.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Generated text
        """
        response = self.llm.invoke(prompt)
        return response.content


class CustomHTTPStrategy:
    """Strategy for custom HTTP-based LLM endpoints."""

    def __init__(
        self,
        endpoint_url: str,
        api_key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        """Initialize custom HTTP strategy.
        
        Args:
            endpoint_url: URL of the LLM endpoint
            api_key: Optional API key for authentication
            headers: Additional HTTP headers
        """
        self.endpoint_url = endpoint_url
        self.headers = headers or {}
        
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    def generate(self, prompt: str) -> str:
        """Generate completion via HTTP endpoint."""
        import requests
        
        payload = {
            "prompt": prompt,
            "max_tokens": 2048,
        }
        
        response = requests.post(
            self.endpoint_url,
            json=payload,
            headers=self.headers,
            timeout=30
        )
        response.raise_for_status()
        
        return response.json().get("text", "")
```

### Using Custom Strategy

```python
# In your agent configuration
from my_strategies import OpenAIStrategy

# Initialize with OpenAI
strategy = OpenAIStrategy(
    api_key="sk-...",
    model="gpt-4",
    temperature=0.7
)

# Use in agent
agent = MyCustomAgent(llm_strategy=strategy)
```

### Configuration via agent.toml

```toml
[agent.llm]
strategy = "openai"  # or "ollama", "custom-http"

[agent.llm.openai]
api_key_env = "OPENAI_API_KEY"  # Environment variable name
model = "gpt-4"
temperature = 0.7
max_tokens = 2048

[agent.llm.custom-http]
endpoint_url = "http://localhost:8000/v1/completions"
api_key_env = "CUSTOM_LLM_API_KEY"
```

---

## Extending the Deployment Server

### Custom Deployment Logic

```python
"""Example: Adding custom deployment validation."""

from atoll.deployment.server import DeploymentServer
from pathlib import Path


class CustomDeploymentServer(DeploymentServer):
    """Extended deployment server with custom logic."""

    async def validate_agent_package(self, agent_path: Path) -> bool:
        """Custom validation before deploying agent.
        
        Args:
            agent_path: Path to extracted agent directory
            
        Returns:
            True if agent package is valid
        """
        # Call parent validation
        if not await super().validate_agent_package(agent_path):
            return False
        
        # Add custom checks
        # Example: Verify security requirements
        security_config = agent_path / "security.toml"
        if not security_config.exists():
            logger.warning(f"No security config found for {agent_path.name}")
            return False
        
        # Example: Check for required files
        required_files = ["main.py", "agent.toml", "requirements.txt"]
        for file in required_files:
            if not (agent_path / file).exists():
                logger.error(f"Missing required file: {file}")
                return False
        
        return True
```

---

## Adding New MCP Tools

### Creating MCP Tool Wrappers

```python
"""Example MCP tool wrapper."""

from langchain.tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel, Field


class CustomToolInput(BaseModel):
    """Input schema for custom tool."""
    query: str = Field(description="Query to process")
    options: Optional[dict] = Field(default=None, description="Optional parameters")


class CustomMCPTool(BaseTool):
    """Custom tool that integrates with MCP server."""

    name: str = "custom_tool"
    description: str = "Performs custom analysis on input"
    args_schema: Type[BaseModel] = CustomToolInput

    def __init__(self, mcp_manager):
        """Initialize tool with MCP manager."""
        super().__init__()
        self.mcp_manager = mcp_manager

    def _run(self, query: str, options: Optional[dict] = None) -> str:
        """Execute tool synchronously."""
        # Not used in async-only ATOLL
        raise NotImplementedError("Use async version")

    async def _arun(self, query: str, options: Optional[dict] = None) -> str:
        """Execute tool asynchronously via MCP.
        
        Args:
            query: Input query
            options: Optional parameters
            
        Returns:
            Tool execution result
        """
        result = await self.mcp_manager.execute_tool(
            server_name="custom_server",
            tool_name="custom_tool",
            arguments={"query": query, "options": options}
        )
        
        return result.get("output", "")
```

---

## Testing Your Extensions

### Unit Tests

```python
"""Test custom agent."""

import pytest
from my_custom_agent.main import MyCustomAgent


@pytest.mark.asyncio
async def test_agent_initialization():
    """Test agent initializes correctly."""
    from atoll.config.models import OllamaConfig
    
    config = OllamaConfig(
        base_url="http://localhost",
        port=11434,
        model="llama2"
    )
    
    agent = MyCustomAgent(config, port=9000)
    assert agent.port == 9000
    assert not agent.server_running


@pytest.mark.asyncio
async def test_agent_starts_and_stops():
    """Test agent lifecycle."""
    # ... implementation
```

### Integration Tests

```python
"""Integration test with deployment server."""

import pytest
from atoll.deployment.client import DeploymentClient


@pytest.mark.asyncio
async def test_deploy_custom_agent():
    """Test deploying custom agent via API."""
    client = DeploymentClient("http://localhost:8080")
    
    # Deploy agent package
    result = await client.deploy_agent("my_custom_agent.zip")
    assert result["status"] == "deployed"
    
    # Start agent
    await client.start_agent("my_custom_agent")
    
    # Check status
    status = await client.get_agent_status("my_custom_agent")
    assert status["status"] == "running"
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_custom_agent.py

# Run with coverage
pytest --cov=atoll --cov-report=html

# Run integration tests only
pytest tests/integration/
```

---

## Contributing Back

### Contribution Workflow

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/ATOLL.git
   cd ATOLL
   git remote add upstream https://github.com/Buttje/ATOLL.git
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/my-new-feature
   ```

3. **Make Changes**
   - Follow code style (Black, Ruff)
   - Add tests for new functionality
   - Update documentation

4. **Run Quality Checks**
   ```bash
   # Format code
   black src tests
   
   # Lint
   ruff check src tests
   
   # Type check
   mypy src
   
   # Run tests
   pytest --cov=src
   ```

5. **Commit and Push**
   ```bash
   git add .
   git commit -m "Add: Description of feature"
   git push origin feature/my-new-feature
   ```

6. **Create Pull Request**
   - Go to GitHub and create PR
   - Fill in PR template
   - Link related issues
   - Wait for review

### Code Style Guidelines

- **Formatting**: Use Black with line length 100
- **Linting**: Pass Ruff checks
- **Type Hints**: Add type hints to all functions
- **Docstrings**: Use Google-style docstrings
- **Tests**: Aim for >90% coverage

### Example Docstring

```python
def my_function(arg1: str, arg2: int = 10) -> bool:
    """Short one-line description.

    Longer description if needed, explaining the function's purpose
    and behavior in detail.

    Args:
        arg1: Description of first argument
        arg2: Description of second argument with default

    Returns:
        Description of return value

    Raises:
        ValueError: When arg2 is negative
        
    Examples:
        >>> my_function("test", 5)
        True
    """
    if arg2 < 0:
        raise ValueError("arg2 must be non-negative")
    return len(arg1) > arg2
```

---

## Additional Resources

- **Main README**: [../README.md](../README.md)
- **Installation Guide**: [INSTALLATION.md](INSTALLATION.md)
- **Deployment Server Guide**: [DEPLOYMENT_SERVER_V2_USAGE.md](DEPLOYMENT_SERVER_V2_USAGE.md)
- **API Reference**: [api/](api/)
- **Contributing Guidelines**: [../CONTRIBUTING.md](../CONTRIBUTING.md)

---

## Getting Help

- **Issues**: https://github.com/Buttje/ATOLL/issues
- **Discussions**: https://github.com/Buttje/ATOLL/discussions
- **Discord**: [Community Server] (coming soon)

---

**Document Version:** 2.0.0  
**Target Audience:** Developers extending ATOLL  
**Skill Level:** Intermediate to Advanced Python

---

*This developer guide fulfills Task 5.2 of the ATOLL v2.0 roadmap.*
