"""ATOLL - Agentic Tools Orchestration on OLLama."""

# Note: OllamaMCPAgent is deprecated, use RootAgent or extend ATOLLAgent
from .agent import OllamaMCPAgent, RootAgent  # OllamaMCPAgent for legacy compatibility
from .config import ConfigManager, MCPConfig, OllamaConfig
from .main import Application, main
from .mcp import MCPClient, MCPServerManager

__version__ = "2.0.0"

__all__ = [
    "main",
    "Application",
    "RootAgent",
    "OllamaMCPAgent",  # Deprecated
    "ConfigManager",
    "OllamaConfig",
    "MCPConfig",
    "MCPClient",
    "MCPServerManager",
]
