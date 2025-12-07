"""ATOLL - Agentic Tools Orchestration on OLLama."""

from .main import main, Application
from .agent import OllamaMCPAgent
from .config import ConfigManager, OllamaConfig, MCPConfig
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