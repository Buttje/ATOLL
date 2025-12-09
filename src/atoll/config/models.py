"""Configuration data models."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class OllamaConfig:
    """Ollama configuration model."""

    base_url: str = "http://localhost"
    port: int = 11434
    model: str = "llama2"
    request_timeout: int = 30
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OllamaConfig":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class MCPServerConfig:
    """MCP server configuration."""

    # Common fields
    type: str = "stdio"  # "stdio", "http", "sse"

    # STDIO-specific fields
    command: Optional[str] = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    envFile: Optional[str] = None
    cwd: Optional[str] = None  # Working directory for stdio

    # HTTP/SSE-specific fields
    url: Optional[str] = None
    headers: dict[str, str] = field(default_factory=dict)

    # Legacy/additional fields
    timeoutSeconds: int = 30
    transport: Optional[str] = None  # Legacy field, mapped from 'type'

    def __post_init__(self):
        """Post-initialization processing."""
        # Map 'type' to 'transport' for backward compatibility
        if self.transport is None and self.type:
            self.transport = self.type
        # Map 'transport' to 'type' if type not set
        if self.type == "stdio" and self.transport and self.transport != self.type:
            self.type = self.transport

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MCPServerConfig":
        """Create from dictionary, supporting both old and new schema formats."""
        # Handle both 'type' and 'transport' keys
        server_type = data.get("type", data.get("transport", "stdio"))

        # Build config dict
        config = {
            "type": server_type,
            "transport": server_type,
            "command": data.get("command"),
            "args": data.get("args", []),
            "env": data.get("env", {}),
            "envFile": data.get("envFile"),
            "cwd": data.get("cwd"),
            "url": data.get("url"),
            "headers": data.get("headers", {}),
            "timeoutSeconds": data.get("timeoutSeconds", 30),
        }

        return cls(**{k: v for k, v in config.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary in new schema format."""
        result = {"type": self.type}

        if self.type == "stdio":
            if self.command is not None:
                result["command"] = self.command
            if self.args:
                result["args"] = self.args
            if self.env:
                result["env"] = self.env
            if self.envFile is not None:
                result["envFile"] = self.envFile
            if self.cwd is not None:
                result["cwd"] = self.cwd
        elif self.type in ("http", "sse"):
            if self.url is not None:
                result["url"] = self.url
            if self.headers:
                result["headers"] = self.headers

        # Include timeoutSeconds if not default
        if self.timeoutSeconds != 30:
            result["timeoutSeconds"] = self.timeoutSeconds

        return result


@dataclass
class MCPConfig:
    """MCP configuration model."""

    servers: dict[str, MCPServerConfig] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MCPConfig":
        """Create from dictionary."""
        servers = {}
        for name, server_data in data.get("servers", {}).items():
            servers[name] = MCPServerConfig.from_dict(server_data)
        return cls(servers=servers)
