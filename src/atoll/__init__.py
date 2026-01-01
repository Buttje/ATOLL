"""ATOLL - Agentic Tools Orchestration on OLLama."""

from .agent import OllamaMCPAgent
from .config import ConfigManager, MCPConfig, OllamaConfig
from .main import Application, main
from .mcp import MCPClient, MCPServerManager

__version__ = "1.1.0"

__all__ = [
    "main",
    "Application",
    "OllamaMCPAgent",
    "ConfigManager",
    "OllamaConfig",
    "MCPConfig",
    "MCPClient",
    "MCPServerManager",
]
