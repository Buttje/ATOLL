"""Configuration manager."""

import json
from pathlib import Path
from typing import Optional
import os

from .models import OllamaConfig, MCPConfig
from ..utils.logger import get_logger
from ..utils.validators import validate_config

logger = get_logger(__name__)


class ConfigManager:
    """Manages application configurations."""
    
    DEFAULT_OLLAMA_CONFIG = ".ollamaConfig.json"
    DEFAULT_MCP_CONFIG = ".mcpConfig.json"
    
    def __init__(
        self,
        ollama_config_path: Optional[Path] = None,
        mcp_config_path: Optional[Path] = None,
    ):
        """Initialize configuration manager."""
        self.ollama_config_path = ollama_config_path or Path(self.DEFAULT_OLLAMA_CONFIG)
        self.mcp_config_path = mcp_config_path or Path(self.DEFAULT_MCP_CONFIG)
        
        self.ollama_config: Optional[OllamaConfig] = None
        self.mcp_config: Optional[MCPConfig] = None
    
    def load_configs(self) -> None:
        """Load all configuration files."""
        self.ollama_config = self.load_ollama_config()
        self.mcp_config = self.load_mcp_config()
    
    def load_ollama_config(self) -> OllamaConfig:
        """Load Ollama configuration."""
        if self.ollama_config_path.exists():
            try:
                with open(self.ollama_config_path, 'r') as f:
                    data = json.load(f)
                logger.info(f"Loaded Ollama config from {self.ollama_config_path}")
                return OllamaConfig.from_dict(data)
            except Exception as e:
                logger.error(f"Failed to load Ollama config: {e}")
        else:
            logger.warning(f"Ollama config not found at {self.ollama_config_path}, using defaults")
        
        return OllamaConfig()
    
    def load_mcp_config(self) -> MCPConfig:
        """Load MCP configuration."""
        if self.mcp_config_path.exists():
            try:
                with open(self.mcp_config_path, 'r') as f:
                    data = json.load(f)
                logger.info(f"Loaded MCP config from {self.mcp_config_path}")
                return MCPConfig.from_dict(data)
            except Exception as e:
                logger.error(f"Failed to load MCP config: {e}")
        else:
            logger.warning(f"MCP config not found at {self.mcp_config_path}, no servers configured")
        
        return MCPConfig()
    
    def save_ollama_config(self) -> None:
        """Save current Ollama configuration."""
        if self.ollama_config:
            data = {
                "base_url": self.ollama_config.base_url,
                "port": self.ollama_config.port,
                "model": self.ollama_config.model,
                "request_timeout": self.ollama_config.request_timeout,
                "max_tokens": self.ollama_config.max_tokens,
                "temperature": self.ollama_config.temperature,
                "top_p": self.ollama_config.top_p,
            }
            
            with open(self.ollama_config_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved Ollama config to {self.ollama_config_path}")