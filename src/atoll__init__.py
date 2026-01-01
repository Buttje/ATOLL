"""ATOLL - Agentic Tools Orchestration on OLLama."""

__version__ = "1.1.0"

# Import main components - avoid circular imports by being selective
from atoll.config.manager import ConfigManager
from atoll.config.models import MCPConfig, OllamaConfig
from atoll.mcp.client import MCPClient
from atoll.mcp.server_manager import MCPServerManager


# Only import main and Application when explicitly needed
def get_main():
    """Lazy import of main function."""
    from atoll.main import main

    return main


def get_application():
    """Lazy import of Application class."""
    from atoll.main import Application

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
