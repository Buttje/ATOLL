# ATOLL - Agentic Tools Orchestration on OLLama

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Coverage](https://img.shields.io/badge/coverage-90%25-green.svg)](https://github.com/yourusername/atoll)

A LangChain-based agent integrating Ollama LLM with MCP (Model Context Protocol) servers for advanced tool usage, including specialized support for Ghidra integration.

## Features

- 🤖 **LangChain Agent**: Intelligent decision-making with Ollama LLM
- 🔧 **MCP Integration**: Connect to multiple MCP servers with different transport protocols
- 🎨 **Interactive Terminal UI**: Color-coded interface with command and prompt modes
- 🔍 **Ghidra Support**: Advanced binary analysis capabilities
- ⚡ **Fast Response**: Optimized for quick local operations (<2s)
- 📊 **Comprehensive Logging**: Detailed reasoning steps and error tracking

## Quick Start

### Installation

```bash
# Run the installer
python scripts/install.py

# Or install manually
python -m venv venv
venv\Scripts\activate
pip install -e ".[dev]"
```

### Configuration

1. Create `.ollamaConfig.json`:
```json
{
  "base_url": "http://localhost",
  "port": 11434,
  "model": "llama2",
  "request_timeout": 30,
  "max_tokens": 2048
}
```

2. Create `.mcpConfig.json`:
```json
{
  "servers": {
    "ghidra": {
      "transport": "stdio",
      "command": "python",
      "args": ["path/to/ghidra_mcp_server.py"],
      "timeoutSeconds": 30
    }
  }
}
```

### Usage

```bash
# Start the agent
atoll

# Or run directly
python -m atoll
```

## Terminal Interface

- **Blue**: User input
- **Yellow**: Agent reasoning
- **Green**: Final responses
- **Red**: Error messages

### Commands (Command Mode)

- `Models` - List available models
- `ChangeModel <model>` - Switch to a different model
- `Quit` - Exit the application
- Press `ESC` to toggle between Prompt and Command modes

## Development

### Running Tests

```bash
# Run all tests with coverage
pytest

# Run specific test categories
pytest tests/unit
pytest tests/integration

# Check coverage report
coverage html
open htmlcov/index.html
```

### Code Quality

```bash
# Format code
black src tests

# Lint code
ruff check src tests

# Type checking
mypy src

# Run all checks
pre-commit run --all-files
```

## Documentation

Full documentation is available in the `docs/` directory:
- [API Reference](docs/api/README.md)
- [User Guide](docs/guides/user_guide.md)
- [Developer Guide](docs/guides/developer_guide.md)
- [MCP Integration Guide](docs/guides/mcp_integration.md)

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- LangChain for the agent framework
- Ollama for local LLM support
- MCP protocol specification
- Ghidra for binary analysis capabilities
```

### 3. Source Code Structure

```python:atoll/src/atoll/__init__.py
"""ATOLL - Agentic Tools Orchestration on OLLama."""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from atoll.agent import OllamaMCPAgent
from atoll.config import ConfigManager

__all__ = ["OllamaMCPAgent", "ConfigManager"]
```

```python:atoll/src/atoll/py.typed
# Marker file for PEP 561
# This package supports type hints
```

### 4. Configuration Module

```python:atoll/src/atoll/config/__init__.py
"""Configuration management for ATOLL."""

from .manager import ConfigManager
from .models import OllamaConfig, MCPConfig, MCPServerConfig
from .validator import ConfigValidator

__all__ = ["ConfigManager", "OllamaConfig", "MCPConfig", "MCPServerConfig", "ConfigValidator"]
```

```python:atoll/src/atoll/config/models.py
"""Configuration data models."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl, validator


class TransportType(str, Enum):
    """MCP transport types."""
    
    STDIO = "stdio"
    STREAMABLE_HTTP = "streamable_http"
    SSE = "sse"


class OllamaConfig(BaseModel):
    """Ollama configuration model."""
    
    base_url: HttpUrl = Field(..., description="Base URL for Ollama server")
    port: int = Field(..., ge=1, le=65535, description="Port number")
    model: str = Field(..., min_length=1, description="Model name")
    request_timeout: int = Field(..., ge=1, description="Request timeout in seconds")
    max_tokens: int = Field(..., ge=1, description="Maximum tokens for generation")
    
    class Config:
        """Pydantic configuration."""
        
        json_schema_extra = {
            "example": {
                "base_url": "http://localhost",
                "port": 11434,
                "model": "llama2",
                "request_timeout": 30,
                "max_tokens": 2048,
            }
        }


class MCPServerConfig(BaseModel):
    """MCP server configuration model."""
    
    transport: TransportType = Field(..., description="Transport type")
    command: Optional[str] = Field(None, description="Command for stdio transport")
    args: Optional[List[str]] = Field(None, description="Command arguments")
    url: Optional[HttpUrl] = Field(None, description="URL for HTTP/SSE transport")
    headers: Optional[Dict[str, str]] = Field(None, description="HTTP headers")
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    timeout_seconds: Optional[int] = Field(None, ge=1, alias="timeoutSeconds")
    workdir: Optional[str] = Field(None, description="Working directory")
    
    @validator("command")
    def validate_stdio_fields(cls, v: Optional[str], values: Dict[str, Any]) -> Optional[str]:
        """Validate stdio-specific fields."""
        if values.get("transport") == TransportType.STDIO and not v:
            raise ValueError("command is required for stdio transport")
        return v
    
    @validator("url")
    def validate_http_fields(cls, v: Optional[HttpUrl], values: Dict[str, Any]) -> Optional[HttpUrl]:
        """Validate HTTP/SSE-specific fields."""
        if values.get("transport") in [TransportType.STREAMABLE_HTTP, TransportType.SSE] and not v:
            raise ValueError(f"url is required for {values.get('transport')} transport")
        return v


class MCPConfig(BaseModel):
    """MCP configuration model."""
    
    servers: Dict[str, MCPServerConfig] = Field(..., description="MCP server configurations")
    
    class Config:
        """Pydantic configuration."""
        
        json_schema_extra = {
            "example": {
                "servers": {
                    "ghidra": {
                        "transport": "stdio",
                        "command": "python",
                        "args": ["ghidra_mcp_server.py"],
                        "timeoutSeconds": 30,
                    }
                }
            }
        }
```

```python:atoll/src/atoll/config/validator.py
"""Configuration validation utilities."""

import json
from pathlib import Path
from typing import Any, Dict
import jsonschema
from jsonschema import Draft202012Validator, exceptions


class ConfigValidator:
    """Validates configuration files against JSON schemas."""
    
    OLLAMA_SCHEMA = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "OllamaConfig",
        "type": "object",
        "properties": {
            "base_url": {"type": "string", "format": "uri"},
            "port": {"type": "integer", "minimum": 1, "maximum": 65535},
            "model": {"type": "string", "minLength": 1},
            "request_timeout": {"type": "integer", "minimum": 1},
            "max_tokens": {"type": "integer", "minimum": 1},
        },
        "required": ["base_url", "port", "model", "request_timeout", "max_tokens"],
    }
    
    MCP_SCHEMA = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "MCPConfig",
        "type": "object",
        "properties": {
            "servers": {
                "type": "object",
                "patternProperties": {
                    "^[a-zA-Z0-9_-]+$": {
                        "type": "object",
                        "properties": {
                            "transport": {
                                "type": "string",
                                "enum": ["stdio", "streamable_http", "sse"],
                            },
                            "command": {"type": "string"},
                            "args": {"type": "array", "items": {"type": "string"}},
                            "url": {"type": "string", "format": "uri"},
                            "headers": {"type": "object"},
                            "env": {"type": "object"},
                            "timeoutSeconds": {"type": "integer", "minimum": 1},
                            "workdir": {"type": "string"},
                        },
                        "required": ["transport"],
                    }
                },
            }
        },
        "required": ["servers"],
    }
    
    @classmethod
    def validate_ollama_config(cls, config: Dict[str, Any]) -> None:
        """Validate Ollama configuration."""
        try:
            Draft202012Validator(cls.OLLAMA_SCHEMA).validate(config)
        except exceptions.ValidationError as e:
            raise ValueError(f"Invalid Ollama configuration: {e.message}") from e
    
    @classmethod
    def validate_mcp_config(cls, config: Dict[str, Any]) -> None:
        """Validate MCP configuration."""
        try:
            Draft202012Validator(cls.MCP_SCHEMA).validate(config)
        except exceptions.ValidationError as e:
            raise ValueError(f"Invalid MCP configuration: {e.message}") from e
    
    @classmethod
    def load_and_validate(cls, path: Path, schema_type: str) -> Dict[str, Any]:
        """Load and validate a configuration file."""
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        try:
            with open(path, "r") as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {path}: {e}") from e
        
        if schema_type == "ollama":
            cls.validate_ollama_config(config)
        elif schema_type == "mcp":
            cls.validate_mcp_config(config)
        else:
            raise ValueError(f"Unknown schema type: {schema_type}")
        
        return config
```

```python:atoll/src/atoll/config/manager.py
"""Configuration management implementation."""

import sys
from pathlib import Path
from typing import Optional
from colorama import Fore, Style, init

from .models import OllamaConfig, MCPConfig
from .validator import ConfigValidator


init(autoreset=True)


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(
        self,
        ollama_config_path: Optional[Path] = None,
        mcp_config_path: Optional[Path] = None,
    ):
        """Initialize configuration manager."""
        self.ollama_config_path = ollama_config_path or Path(".ollamaConfig.json")
        self.mcp_config_path = mcp_config_path or Path(".mcpConfig.json")
        self.ollama_config: Optional[OllamaConfig] = None
        self.mcp_config: Optional[MCPConfig] = None
    
    def load_configs(self) -> None:
        """Load and validate all configurations."""
        print(f"{Fore.CYAN}Loading configurations...{Style.RESET_ALL}")
        
        try:
            # Load Ollama configuration
            ollama_data = ConfigValidator.load_and_validate(
                self.ollama_config_path, "ollama"
            )
            self.ollama_config = OllamaConfig(**ollama_data)
            print(f"{Fore.GREEN}✓ Ollama configuration loaded{Style.RESET_ALL}")
            
            # Load MCP configuration
            mcp_data = ConfigValidator.load_and_validate(self.mcp_config_path, "mcp")
            self.mcp_config = MCPConfig(**mcp_data)
            print(f"{Fore.GREEN}✓ MCP configuration loaded{Style.RESET_ALL}")
            
        except (FileNotFoundError, ValueError) as e:
            print(f"{Fore.RED}Configuration error: {e}{Style.RESET_ALL}")
            sys.exit(1)
    
    def get_ollama_url(self) -> str:
        """Get full Ollama URL."""
        if not self.ollama_config:
            raise RuntimeError("Ollama configuration not loaded")
        return f"{self.ollama_config.base_url}:{self.ollama_config.port}"
```

### 5. MCP Client Module

```python:atoll/src/atoll/mcp/__init__.py
"""MCP client implementation."""

from .client import MCPClient
from .server_manager import MCPServerManager
from .tools import MCPTool, MCPToolRegistry

__all__ = ["MCPClient", "MCPServerManager", "MCPTool", "MCPToolRegistry"]
```

```python:atoll/src/atoll/mcp/client.py
"""MCP client for server communication."""

import asyncio
import json
import subprocess
from enum import Enum
from typing import Any, Dict, List, Optional
import aiohttp
from colorama import Fore, Style

from ..config.models import MCPServerConfig, TransportType


class MCPClient:
    """Client for communicating with MCP servers."""
    
    def __init__(self, name: str, config: MCPServerConfig):
        """Initialize MCP client."""
        self.name = name
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.tools: List[Dict[str, Any]] = []
    
    async def connect(self) -> None:
        """Connect to MCP server."""
        print(f"{Fore.CYAN}Connecting to MCP server '{self.name}'...{Style.RESET_ALL}")
        
        if self.config.transport == TransportType.STDIO:
            await self._connect_stdio()
        elif self.config.transport in [TransportType.STREAMABLE_HTTP, TransportType.SSE]:
            await self._connect_http()
        else:
            raise ValueError(f"Unsupported transport: {self.config.transport}")
        
        print(f"{Fore.GREEN}✓ Connected to '{self.name}'{Style.RESET_ALL}")
    
    async def _connect_stdio(self) -> None:
        """Connect via stdio transport."""
        if not self.config.command:
            raise ValueError("Command required for stdio transport")
        
        cmd = [self.config.command]
        if self.config.args:
            cmd.extend(self.config.args)
        
        env = None
        if self.config.env:
            import os
            env = os.environ.copy()
            env.update(self.config.env)
        
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=self.config.workdir,
            text=True,
        )
    
    async def _connect_http(self) -> None:
        """Connect via HTTP transport."""
        if not self.config.url:
            raise ValueError(f"URL required for {self.config.transport} transport")
        
        timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds or 30)
        self.session = aiohttp.ClientSession(
            headers=self.config.headers,
            timeout=timeout,
        )
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools from server."""
        if self.config.transport == TransportType.STDIO:
            return await self._list_tools_stdio()
        else:
            return await self._list_tools_http()
    
    async def _list_tools_stdio(self) -> List[Dict[str, Any]]:
        """List tools via stdio."""
        if not self.process or not self.process.stdin or not self.process.stdout:
            raise RuntimeError("Process not connected")
        
        request = json.dumps({"method": "tools/list"}) + "\n"
        self.process.stdin.write(request)
        self.process.stdin.flush()
        
        response = self.process.stdout.readline()
        result = json.loads(response)
        
        self.tools = result.get("tools", [])
        return self.tools
    
    async def _list_tools_http(self) -> List[Dict[str, Any]]:
        """List tools via HTTP."""
        if not self.session:
            raise RuntimeError("Session not connected")
        
        async with self.session.get(f"{self.config.url}/tools/list") as response:
            result = await response.json()
            self.tools = result.get("tools", [])
            return self.tools
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server."""
        if self.config.transport == TransportType.STDIO:
            return await self._call_tool_stdio(tool_name, arguments)
        else:
            return await self._call_tool_http(tool_name, arguments)
    
    async def _call_tool_stdio(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call tool via stdio."""
        if not self.process or not self.process.stdin or not self.process.stdout:
            raise RuntimeError("Process not connected")
        
        request = json.dumps({
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            }
        }) + "\n"
        
        self.process.stdin.write(request)
        self.process.stdin.flush()
        
        response = self.process.stdout.readline()
        result = json.loads(response)
        
        if "error" in result:
            raise RuntimeError(f"Tool error: {result['error']}")
        
        return result.get("result")
    
    async def _call_tool_http(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call tool via HTTP."""
        if not self.session:
            raise RuntimeError("Session not connected")
        
        async with self.session.post(
            f"{self.config.url}/tools/call",
            json={
                "name": tool_name,
                "arguments": arguments,
            }
        ) as response:
            result = await response.json()
            
            if "error" in result:
                raise RuntimeError(f"Tool error: {result['error']}")
            
            return result.get("result")
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
        
        if self.session:
            await self.session.close()
            self.session = None
```

```python:atoll/src/atoll/mcp/server_manager.py
"""MCP server connection manager."""

import asyncio
import sys
from typing import Dict, List, Optional
from colorama import Fore, Style

from ..config.models import MCPConfig
from .client import MCPClient
from .tools import MCPToolRegistry


class MCPServerManager:
    """Manages connections to multiple MCP servers."""
    
    def __init__(self, config: MCPConfig):
        """Initialize server manager."""
        self.config = config
        self.clients: Dict[str, MCPClient] = {}
        self.tool_registry = MCPToolRegistry()
    
    async def connect_all(self) -> None:
        """Connect to all configured MCP servers."""
        print(f"{Fore.CYAN}Connecting to MCP servers...{Style.RESET_ALL}")
        
        tasks = []
        for name, server_config in self.config.servers.items():
            client = MCPClient(name, server_config)
            self.clients[name] = client
            tasks.append(self._connect_and_discover(client))
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            print(f"{Fore.RED}Failed to connect to MCP servers: {e}{Style.RESET_ALL}")
            sys.exit(1)
        
        print(f"{Fore.GREEN}✓ All MCP servers connected{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Discovered {len(self.tool_registry.tools)} tools{Style.RESET_ALL}")
    
    async def _connect_and_discover(self, client: MCPClient) -> None:
        """Connect to server and discover tools."""
        await client.connect()
        tools = await client.list_tools()
        
        for tool_data in tools:
            self.tool_registry.register_tool(client.name, tool_data)
