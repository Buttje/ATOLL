"""Configuration management for Ollama MCP Agent."""

from .manager import ConfigManager
from .models import MCPConfig, MCPServerConfig, OllamaConfig

__all__ = ["OllamaConfig", "MCPConfig", "MCPServerConfig", "ConfigManager"]
