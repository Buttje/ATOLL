"""Plugin manager for discovering and managing ATOLL agent plugins."""

import importlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Optional

from .base import ATOLLAgent
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PluginManager:
    """Manages discovery and lifecycle of ATOLL agent plugins.

    Plugins are discovered from the atoll_agents/ directory.
    Each plugin must:
    1. Be in its own subdirectory (e.g., atoll_agents/ghidra_agent/)
    2. Have an agent.json metadata file
    3. Have a Python module that exports an ATOLLAgent subclass
    """

    def __init__(self, plugins_dir: Optional[Path] = None):
        """Initialize plugin manager.

        Args:
            plugins_dir: Directory to search for plugins (default: {package_root}/../../atoll_agents)
        """
        if plugins_dir is None:
            # Default to atoll_agents relative to package root
            # This works regardless of current working directory
            package_dir = Path(__file__).parent.parent.parent  # atoll/plugins -> atoll -> src -> project_root
            plugins_dir = package_dir.parent / "atoll_agents"

        self.plugins_dir = Path(plugins_dir)
        self.agents: dict[str, ATOLLAgent] = {}
        self.metadata: dict[str, dict] = {}

    def discover_plugins(self) -> int:
        """Discover and load all plugins from the plugins directory.

        Returns:
            Number of plugins successfully loaded
        """
        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory not found: {self.plugins_dir}")
            return 0

        loaded_count = 0

        for agent_dir in self.plugins_dir.iterdir():
            if not agent_dir.is_dir():
                continue

            # Skip hidden directories and __pycache__
            if agent_dir.name.startswith(".") or agent_dir.name == "__pycache__":
                continue

            try:
                if self._load_plugin(agent_dir):
                    loaded_count += 1
            except Exception as e:
                logger.error(f"Failed to load plugin from {agent_dir}: {e}")

        logger.info(f"Loaded {loaded_count} agent plugin(s)")
        return loaded_count

    def _load_plugin(self, agent_dir: Path) -> bool:
        """Load a single plugin from a directory.

        Args:
            agent_dir: Directory containing the plugin

        Returns:
            True if loaded successfully, False otherwise
        """
        # Check for agent.json metadata file
        metadata_file = agent_dir / "agent.json"
        if not metadata_file.exists():
            logger.warning(f"No agent.json found in {agent_dir}")
            return False

        # Load metadata
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load metadata from {metadata_file}: {e}")
            return False

        # Validate required metadata fields
        required_fields = ["name", "version", "module", "class"]
        if not all(field in metadata for field in required_fields):
            logger.error(f"Missing required fields in {metadata_file}")
            return False

        agent_name = metadata["name"]

        # Load the Python module
        module_path = agent_dir / f"{metadata['module']}.py"
        if not module_path.exists():
            logger.error(f"Module file not found: {module_path}")
            return False

        try:
            # Load module dynamically
            spec = importlib.util.spec_from_file_location(metadata["module"], module_path)
            if spec is None or spec.loader is None:
                logger.error(f"Failed to create module spec for {module_path}")
                return False

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get the agent class
            agent_class = getattr(module, metadata["class"])

            # Instantiate the agent
            agent = agent_class(metadata["name"], metadata["version"])

            # Verify it's an ATOLLAgent
            if not isinstance(agent, ATOLLAgent):
                logger.error(f"Plugin {agent_name} is not an ATOLLAgent subclass")
                return False

            # Store agent and metadata
            self.agents[agent_name] = agent
            self.metadata[agent_name] = metadata

            # Set additional metadata from file
            for key, value in metadata.items():
                if key not in required_fields:
                    agent.set_metadata(key, value)

            logger.info(f"Loaded plugin: {agent_name} v{metadata['version']}")
            return True

        except Exception as e:
            logger.error(f"Failed to load plugin {agent_name}: {e}")
            return False

    def get_agent(self, name: str) -> Optional[ATOLLAgent]:
        """Get an agent by name.

        Args:
            name: Name of the agent

        Returns:
            ATOLLAgent instance or None if not found
        """
        return self.agents.get(name)

    def get_all_agents(self) -> dict[str, ATOLLAgent]:
        """Get all loaded agents.

        Returns:
            Dictionary of agent name to ATOLLAgent instance
        """
        return self.agents.copy()

    def get_agent_metadata(self, name: str) -> Optional[dict]:
        """Get metadata for an agent.

        Args:
            name: Name of the agent

        Returns:
            Metadata dictionary or None if not found
        """
        return self.metadata.get(name)

    def get_agents_for_capability(self, capability: str) -> list[ATOLLAgent]:
        """Get all agents that provide a specific capability.

        Args:
            capability: Capability name (e.g., "binary_analysis")

        Returns:
            List of agents that provide this capability
        """
        result = []
        for agent in self.agents.values():
            if capability in agent.get_capabilities():
                result.append(agent)
        return result

    def get_agents_for_mcp_server(self, server_name: str) -> list[ATOLLAgent]:
        """Get all agents that work with a specific MCP server.

        Args:
            server_name: Name of the MCP server

        Returns:
            List of agents that support this server
        """
        result = []
        for agent in self.agents.values():
            if server_name in agent.get_supported_mcp_servers():
                result.append(agent)
        return result

    def select_agent(self, prompt: str, context: dict[str, Any]) -> Optional[ATOLLAgent]:
        """Select the most suitable agent for a given prompt.

        Args:
            prompt: User's prompt
            context: Current context

        Returns:
            Most suitable agent or None if no suitable agent found
        """
        if not self.agents:
            return None

        # Get confidence scores from all agents
        scores = []
        for name, agent in self.agents.items():
            try:
                score = agent.can_handle(prompt, context)
                scores.append((score, name, agent))
            except Exception as e:
                logger.error(f"Error getting score from {name}: {e}")

        if not scores:
            return None

        # Sort by score (highest first)
        scores.sort(reverse=True)

        # Return agent with highest score if score > 0
        if scores[0][0] > 0:
            return scores[0][2]

        return None

    def list_plugins(self) -> list[dict[str, Any]]:
        """List all loaded plugins with their metadata.

        Returns:
            List of plugin info dictionaries
        """
        result = []
        for name, agent in self.agents.items():
            metadata = self.metadata.get(name, {})
            result.append(
                {
                    "name": name,
                    "version": agent.version,
                    "capabilities": agent.get_capabilities(),
                    "supported_servers": agent.get_supported_mcp_servers(),
                    "description": metadata.get("description", "No description"),
                }
            )
        return result
