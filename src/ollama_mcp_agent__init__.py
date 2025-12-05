"""Ollama MCP Agent - LangChain-based agent integrating Ollama with MCP servers."""

__version__ = "1.0.0"

# Import main components - avoid circular imports by being selective
from .config.models import OllamaConfig, MCPConfig
from .config.manager import ConfigManager
from .mcp.client import MCPClient
from .mcp.server_manager import MCPServerManager

# Only import main and Application when explicitly needed
def get_main():
    """Lazy import of main function."""
    from .main import main
    return main

def get_application():
    """Lazy import of Application class."""
    from .main import Application
    return Application

__all__ = [
    "OllamaConfig",
    "MCPConfig",
    "ConfigManager",
    "MCPClient",
    "MCPServerManager",
    "get_main",
    "get_application",
]