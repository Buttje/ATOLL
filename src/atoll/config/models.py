"""Configuration data models."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


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
    def from_dict(cls, data: Dict[str, Any]) -> "OllamaConfig":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class MCPServerConfig:
    """MCP server configuration."""
    
    transport: str  # "stdio", "http", "websocket"
    command: Optional[str] = None
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    url: Optional[str] = None
    timeoutSeconds: int = 30
    cwd: Optional[str] = None  # Working directory for stdio
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPServerConfig":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {"transport": self.transport}
        if self.command is not None:
            result["command"] = self.command
        if self.args:
            result["args"] = self.args
        if self.env:
            result["env"] = self.env
        if self.url is not None:
            result["url"] = self.url
        if self.timeoutSeconds != 30:
            result["timeoutSeconds"] = self.timeoutSeconds
        if self.cwd is not None:
            result["cwd"] = self.cwd
        return result


@dataclass
class MCPConfig:
    """MCP configuration model."""
    
    servers: Dict[str, MCPServerConfig] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPConfig":
        """Create from dictionary."""
        servers = {}
        for name, server_data in data.get("servers", {}).items():
            servers[name] = MCPServerConfig.from_dict(server_data)
        return cls(servers=servers)