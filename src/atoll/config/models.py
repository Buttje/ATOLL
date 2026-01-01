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


@dataclass
class AgentConfig:
    """Agent behavior configuration."""

    # ReAct engine settings
    use_react_engine: bool = False
    max_react_iterations: int = 5
    max_observation_length: int = 1000
    tool_timeout: float = 30.0
    enable_parallel_actions: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentConfig":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ATOLLConfig:
    """ATOLL general configuration."""

    agents_directory: Optional[str] = None  # Path to ATOLL agents directory

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ATOLLConfig":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class TOMLAgentMetadata:
    """Agent metadata from TOML [agent] section."""

    name: str
    version: str = "1.0.0"
    description: Optional[str] = None
    author: Optional[str] = None
    license: Optional[str] = None
    capabilities: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TOMLAgentMetadata":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class TOMLAgentLLMConfig:
    """Agent LLM configuration from TOML [llm] section."""

    model: Optional[str] = None  # If None, use parent agent's model
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    request_timeout: Optional[int] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TOMLAgentLLMConfig":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def merge_with_parent(self, parent_config: OllamaConfig) -> OllamaConfig:
        """Merge this agent's LLM config with parent config.

        Args:
            parent_config: Parent agent's Ollama configuration

        Returns:
            New OllamaConfig with agent-specific overrides applied
        """
        return OllamaConfig(
            base_url=parent_config.base_url,  # Always from parent
            port=parent_config.port,  # Always from parent
            model=self.model if self.model is not None else parent_config.model,
            temperature=self.temperature
            if self.temperature is not None
            else parent_config.temperature,
            top_p=self.top_p if self.top_p is not None else parent_config.top_p,
            max_tokens=self.max_tokens if self.max_tokens is not None else parent_config.max_tokens,
            request_timeout=self.request_timeout
            if self.request_timeout is not None
            else parent_config.request_timeout,
        )


@dataclass
class TOMLAgentDependencies:
    """Agent dependencies from TOML [dependencies] section."""

    python: str = ">=3.9"
    packages: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TOMLAgentDependencies":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class TOMLAgentResources:
    """Agent resource limits from TOML [resources] section."""

    cpu_limit: Optional[float] = None  # CPU cores (e.g., 2.0 for 2 cores)
    memory_limit: Optional[str] = None  # Memory limit (e.g., "4GB")
    timeout: Optional[int] = None  # Request timeout in seconds

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TOMLAgentResources":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class TOMLSubAgentConfig:
    """Sub-agent connection configuration from TOML [sub_agents.*] section."""

    url: str  # HTTP URL of the sub-agent server
    auth_token: Optional[str] = None  # JWT token for authentication
    health_check_interval: int = 30  # Seconds between health checks

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TOMLSubAgentConfig":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class TOMLAgentConfig:
    """Complete agent configuration from agent.toml file.

    This replaces the JSON-based agent.json + mcp.json format with
    a unified TOML configuration as specified in FR-D007.
    """

    # Core agent metadata
    agent: TOMLAgentMetadata

    # LLM configuration (optional overrides)
    llm: Optional[TOMLAgentLLMConfig] = None

    # Python dependencies
    dependencies: Optional[TOMLAgentDependencies] = None

    # Resource limits
    resources: Optional[TOMLAgentResources] = None

    # MCP servers configuration
    mcp_servers: dict[str, MCPServerConfig] = field(default_factory=dict)

    # Sub-agents for hierarchical distributed mode
    sub_agents: dict[str, TOMLSubAgentConfig] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TOMLAgentConfig":
        """Create from dictionary parsed from TOML file.

        Args:
            data: Dictionary from tomli/tomllib parse

        Returns:
            TOMLAgentConfig instance
        """
        return cls(
            agent=TOMLAgentMetadata.from_dict(data.get("agent", {})),
            llm=TOMLAgentLLMConfig.from_dict(data["llm"]) if "llm" in data else None,
            dependencies=TOMLAgentDependencies.from_dict(data["dependencies"])
            if "dependencies" in data
            else None,
            resources=TOMLAgentResources.from_dict(data["resources"])
            if "resources" in data
            else None,
            mcp_servers={
                name: MCPServerConfig.from_dict(config)
                for name, config in data.get("mcp_servers", {}).items()
            },
            sub_agents={
                name: TOMLSubAgentConfig.from_dict(config)
                for name, config in data.get("sub_agents", {}).items()
            },
        )

    @classmethod
    def from_toml_file(cls, path: str) -> "TOMLAgentConfig":
        """Load configuration from TOML file.

        Args:
            path: Path to agent.toml file

        Returns:
            TOMLAgentConfig instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If TOML is invalid
        """
        import sys
        from pathlib import Path

        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Agent config file not found: {path}")

        # Python 3.11+ has tomllib built-in, otherwise use tomli
        if sys.version_info >= (3, 11):
            import tomllib

            with open(file_path, "rb") as f:
                data = tomllib.load(f)
        else:
            try:
                import tomli

                with open(file_path, "rb") as f:
                    data = tomli.load(f)
            except ImportError:
                raise ImportError(
                    "tomli package required for Python <3.11. Install with: pip install tomli"
                )

        return cls.from_dict(data)
