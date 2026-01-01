"""Configuration manager."""

import json
from pathlib import Path
from typing import Optional

from ..deployment.server import DeploymentServerConfig
from ..utils.logger import get_logger
from .models import ATOLLConfig, MCPConfig, OllamaConfig

logger = get_logger(__name__)


class ConfigManager:
    """Manages application configurations."""

    DEFAULT_OLLAMA_CONFIG_DIR = Path.home() / ".ollama_server"
    DEFAULT_OLLAMA_CONFIG_FILE = ".ollama_config.json"
    DEFAULT_ATOLL_CONFIG_DIR = Path.home() / ".atoll"
    DEFAULT_MCP_CONFIG_FILE = "mcp.json"
    DEFAULT_ATOLL_CONFIG_FILE = "atoll.json"
    DEFAULT_DEPLOYMENT_CONFIG_FILE = "deployment_servers.json"

    def __init__(
        self,
        ollama_config_path: Optional[Path] = None,
        mcp_config_path: Optional[Path] = None,
    ):
        """Initialize configuration manager."""
        if ollama_config_path is None:
            # Use ~/.ollama_server/.ollama_config.json
            self.ollama_config_path = (
                self.DEFAULT_OLLAMA_CONFIG_DIR / self.DEFAULT_OLLAMA_CONFIG_FILE
            )
            # Ensure the directory exists
            self.DEFAULT_OLLAMA_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        else:
            self.ollama_config_path = ollama_config_path

        if mcp_config_path is None:
            # Use ~/.atoll/mcp.json
            self.mcp_config_path = self.DEFAULT_ATOLL_CONFIG_DIR / self.DEFAULT_MCP_CONFIG_FILE
            # Ensure the directory exists
            self.DEFAULT_ATOLL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        else:
            self.mcp_config_path = mcp_config_path

        self.ollama_config: Optional[OllamaConfig] = None
        self.mcp_config: Optional[MCPConfig] = None
        self.atoll_config: Optional[ATOLLConfig] = None
        self.deployment_config: Optional[DeploymentServerConfig] = None
        self.atoll_config_path = self.DEFAULT_ATOLL_CONFIG_DIR / self.DEFAULT_ATOLL_CONFIG_FILE
        self.deployment_config_path = (
            self.DEFAULT_ATOLL_CONFIG_DIR / self.DEFAULT_DEPLOYMENT_CONFIG_FILE
        )

    def load_configs(self) -> None:
        """Load all configuration files."""
        self.ollama_config = self.load_ollama_config()
        self.mcp_config = self.load_mcp_config()
        self.atoll_config = self.load_atoll_config()
        self.deployment_config = self.load_deployment_config()

    def load_ollama_config(self) -> OllamaConfig:
        """Load Ollama configuration."""
        if self.ollama_config_path.exists():
            try:
                with open(self.ollama_config_path) as f:
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
                with open(self.mcp_config_path) as f:
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
            # Ensure directory exists
            self.ollama_config_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "base_url": self.ollama_config.base_url,
                "port": self.ollama_config.port,
                "model": self.ollama_config.model,
                "request_timeout": self.ollama_config.request_timeout,
                "max_tokens": self.ollama_config.max_tokens,
                "temperature": self.ollama_config.temperature,
                "top_p": self.ollama_config.top_p,
            }

            with open(self.ollama_config_path, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved Ollama config to {self.ollama_config_path}")

    def load_atoll_config(self) -> ATOLLConfig:
        """Load ATOLL configuration."""
        if self.atoll_config_path.exists():
            try:
                with open(self.atoll_config_path) as f:
                    data = json.load(f)
                logger.info(f"Loaded ATOLL config from {self.atoll_config_path}")
                return ATOLLConfig.from_dict(data)
            except Exception as e:
                logger.error(f"Failed to load ATOLL config: {e}")
        else:
            logger.info(f"ATOLL config not found at {self.atoll_config_path}, using defaults")

        return ATOLLConfig()

    def save_atoll_config(self) -> None:
        """Save current ATOLL configuration."""
        if self.atoll_config:
            # Ensure directory exists
            self.atoll_config_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "agents_directory": self.atoll_config.agents_directory,
            }

            with open(self.atoll_config_path, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved ATOLL config to {self.atoll_config_path}")

    def load_deployment_config(self) -> DeploymentServerConfig:
        """Load deployment server configuration."""
        if self.deployment_config_path.exists():
            try:
                with open(self.deployment_config_path) as f:
                    data = json.load(f)
                logger.info(f"Loaded deployment config from {self.deployment_config_path}")
                return DeploymentServerConfig.from_dict(data)
            except Exception as e:
                logger.error(f"Failed to load deployment config: {e}")
        else:
            logger.info(
                f"Deployment config not found at {self.deployment_config_path}, using defaults"
            )

        return DeploymentServerConfig()

    def save_deployment_config(self) -> None:
        """Save current deployment server configuration."""
        if self.deployment_config:
            # Ensure directory exists
            self.deployment_config_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "enabled": self.deployment_config.enabled,
                "host": self.deployment_config.host,
                "base_port": self.deployment_config.base_port,
                "max_agents": self.deployment_config.max_agents,
                "health_check_interval": self.deployment_config.health_check_interval,
                "restart_on_failure": self.deployment_config.restart_on_failure,
                "max_restarts": self.deployment_config.max_restarts,
                "auto_discover_port": self.deployment_config.auto_discover_port,
                "agents_directory": str(self.deployment_config.agents_directory)
                if self.deployment_config.agents_directory
                else None,
                "remote_servers": [
                    {
                        "name": rs.name,
                        "host": rs.host,
                        "port": rs.port,
                        "enabled": rs.enabled,
                        "description": rs.description,
                    }
                    for rs in self.deployment_config.remote_servers
                ],
            }

            with open(self.deployment_config_path, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved deployment config to {self.deployment_config_path}")
