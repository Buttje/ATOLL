"""ATOLL Agent Manager - Discovers and manages specialized ATOLL agents."""

import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Optional

from ..config.models import MCPConfig
from ..mcp.server_manager import MCPServerManager
from ..plugins.base import ATOLLAgent
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AgentContext:
    """Context for an active ATOLL agent."""

    def __init__(
        self,
        agent: ATOLLAgent,
        name: str,
        mcp_manager: Optional[MCPServerManager] = None,
        parent_context: Optional["AgentContext"] = None,
    ):
        """Initialize agent context."""
        self.agent = agent
        self.name = name
        self.mcp_manager = mcp_manager
        self.parent_context = parent_context
        self.child_agents: dict[str, AgentContext] = {}


class ATOLLAgentManager:
    """Manages ATOLL agent discovery, loading, and hierarchy."""

    def __init__(self, agents_directory: Path):
        """Initialize agent manager.

        Args:
            agents_directory: Path to directory containing agent subdirectories
        """
        self.agents_directory = agents_directory
        self.discovered_agents: dict[str, dict] = {}
        self.loaded_agents: dict[str, AgentContext] = {}
        self.current_context: Optional[AgentContext] = None
        self.context_stack: list[AgentContext] = []

    async def discover_agents(self) -> dict[str, dict]:
        """Discover all ATOLL agents in the agents directory.

        Supports both:
        - New format: agent.toml (preferred)
        - Legacy format: agent.json + mcp.json

        Returns:
            Dict mapping agent names to their metadata
        """
        self.discovered_agents = {}

        if not self.agents_directory.exists():
            logger.info(f"Creating agents directory: {self.agents_directory}")
            self._create_agents_directory()
            logger.info(
                "No specialized agents installed yet. Add agents to the 'atoll_agents' directory."
            )
            return {}

        # Scan for agent subdirectories
        for agent_dir in self.agents_directory.iterdir():
            if not agent_dir.is_dir():
                continue

            # Check for agent.toml (new format, preferred)
            agent_toml_path = agent_dir / "agent.toml"
            agent_json_path = agent_dir / "agent.json"

            config_path = None
            config_type = None

            if agent_toml_path.exists():
                config_path = agent_toml_path
                config_type = "toml"
            elif agent_json_path.exists():
                config_path = agent_json_path
                config_type = "json"
            else:
                # No configuration file found
                continue

            try:
                if config_type == "toml":
                    # Load TOML configuration
                    from ..config.models import TOMLAgentConfig

                    toml_config = TOMLAgentConfig.from_toml_file(str(config_path))

                    agent_metadata = {
                        "name": toml_config.agent.name,
                        "version": toml_config.agent.version,
                        "description": toml_config.agent.description or "No description",
                        "capabilities": toml_config.agent.capabilities,
                        "directory": str(agent_dir),
                        "config_path": str(config_path),
                        "config_type": "toml",
                        "toml_config": toml_config,  # Store parsed config
                    }

                else:  # json (legacy)
                    with open(config_path, encoding="utf-8") as f:
                        agent_metadata = json.load(f)

                    agent_metadata["directory"] = str(agent_dir)
                    agent_metadata["mcp_config_path"] = str(agent_dir / "mcp.json")
                    agent_metadata["config_type"] = "json"

                agent_name = agent_metadata.get("name", agent_dir.name)
                self.discovered_agents[agent_name] = agent_metadata
                logger.info(f"Discovered agent: {agent_name} ({config_type} format)")

            except Exception as e:
                logger.error(f"Failed to load agent metadata from {config_path}: {e}")

        return self.discovered_agents

    async def load_agent(
        self,
        agent_name: str,
        parent_context: Optional[AgentContext] = None,
    ) -> Optional[AgentContext]:
        """Load and initialize a specific agent.

        Args:
            agent_name: Name of the agent to load
            parent_context: Parent agent context if loading a sub-agent

        Returns:
            AgentContext if successful, None otherwise
        """
        if agent_name not in self.discovered_agents:
            logger.error(f"Agent not found: {agent_name}")
            return None

        metadata = self.discovered_agents[agent_name]
        agent_dir = Path(metadata["directory"])

        try:
            # Load the agent module
            module_name = metadata.get("module", f"{agent_dir.name}")
            module_file = agent_dir / f"{module_name}.py"

            if not module_file.exists():
                logger.error(f"Agent module not found: {module_file}")
                return None

            # Import the module
            spec = importlib.util.spec_from_file_location(module_name, module_file)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Get the agent class
            class_name = metadata.get("class", "Agent")
            if not hasattr(module, class_name):
                logger.error(f"Agent class {class_name} not found in module {module_name}")
                return None

            agent_class = getattr(module, class_name)

            # Instantiate the agent
            agent_instance = agent_class(
                name=metadata.get("name", agent_name),
                version=metadata.get("version", "1.0.0"),
            )

            # Load agent-specific MCP servers if mcp.json exists
            mcp_manager = None
            mcp_config_path = Path(metadata["mcp_config_path"])
            if mcp_config_path.exists():
                try:
                    with open(mcp_config_path, encoding="utf-8") as f:
                        mcp_data = json.load(f)
                    # Use MCPConfig.from_dict() to properly parse standardized format
                    mcp_config = MCPConfig.from_dict(mcp_data)

                    # Create MCP manager for this agent
                    mcp_manager = MCPServerManager(mcp_config)
                    await mcp_manager.connect_all()

                    logger.info(
                        f"Loaded {len(mcp_manager.list_servers())} MCP servers for agent {agent_name}"
                    )
                except Exception as e:
                    logger.error(f"Failed to load MCP config for agent {agent_name}: {e}")

            # Create agent context
            context = AgentContext(
                agent=agent_instance,
                name=agent_name,
                mcp_manager=mcp_manager,
                parent_context=parent_context,
            )

            # Store in appropriate location
            if parent_context:
                parent_context.child_agents[agent_name] = context
            else:
                self.loaded_agents[agent_name] = context

            logger.info(f"Successfully loaded agent: {agent_name}")
            return context

        except Exception as e:
            logger.error(f"Failed to load agent {agent_name}: {e}")
            return None

    async def load_all_agents(self) -> None:
        """Discover and load all available agents."""
        await self.discover_agents()

        for agent_name in self.discovered_agents:
            await self.load_agent(agent_name)

    def switch_to_agent(self, agent_name: str) -> bool:
        """Switch command context to a specific agent.

        Args:
            agent_name: Name of the agent to switch to

        Returns:
            True if successful, False otherwise
        """
        # Check if agent exists in current context's children or top-level
        target_context = None

        if self.current_context and agent_name in self.current_context.child_agents:
            target_context = self.current_context.child_agents[agent_name]
        elif agent_name in self.loaded_agents:
            target_context = self.loaded_agents[agent_name]

        if not target_context:
            return False

        # Push current context onto stack if it exists
        if self.current_context:
            self.context_stack.append(self.current_context)

        self.current_context = target_context
        return True

    def go_back(self) -> bool:
        """Return to previous agent context.

        Returns:
            True if successful, False if already at top level
        """
        if not self.context_stack:
            return False

        self.current_context = self.context_stack.pop()
        return True

    def get_current_context(self) -> Optional[AgentContext]:
        """Get the current agent context."""
        return self.current_context

    def is_top_level(self) -> bool:
        """Check if currently at top level (no active agent context)."""
        return self.current_context is None

    def get_available_agents(self) -> list[str]:
        """Get list of available agent names in current context.

        Returns:
            List of agent names accessible from current context
        """
        if self.current_context:
            return list(self.current_context.child_agents.keys())
        return list(self.loaded_agents.keys())

    def get_agent_metadata(self, agent_name: str) -> Optional[dict]:
        """Get metadata for a specific agent."""
        return self.discovered_agents.get(agent_name)

    async def shutdown_all(self) -> None:
        """Shutdown all agents and their MCP connections."""
        logger.info("Shutting down all agents...")

        # Shutdown all loaded agents
        for context in self.loaded_agents.values():
            await self._shutdown_context(context)

        self.loaded_agents.clear()
        self.current_context = None
        self.context_stack.clear()

    async def _shutdown_context(self, context: AgentContext) -> None:
        """Recursively shutdown an agent context and its children."""
        # Shutdown child agents first
        for child_context in context.child_agents.values():
            await self._shutdown_context(child_context)

        # Disconnect MCP manager
        if context.mcp_manager:
            await context.mcp_manager.disconnect_all()

        logger.info(f"Shutdown agent: {context.name}")

    def _create_agents_directory(self) -> None:
        """Create the agents directory with README and optional example agents."""
        try:
            # Create the directory
            self.agents_directory.mkdir(parents=True, exist_ok=True)

            # Create README.md
            readme_path = self.agents_directory / "README.md"
            if not readme_path.exists():
                readme_content = """# ATOLL Agent Plugins

This directory contains specialized ATOLL agent plugins that extend the capabilities of the base ATOLL system.

## Quick Start

To add a specialized agent:

1. Copy an agent directory (e.g., from the ATOLL repository's `atoll_agents/` folder)
2. Each agent needs:
   - `agent.json` - Metadata file
   - `{module}.py` - Python implementation
   - Optional: `mcp.json` - MCP server configuration

## Example: Ghidra Agent

If you want to use the Ghidra reverse engineering agent:

```bash
# Copy the example from the ATOLL repository
cp -r <atoll-repo>/atoll_agents/ghidra_agent ./atoll_agents/
```

## Structure

```
atoll_agents/
├── README.md (this file)
└── my_agent/
    ├── agent.json
    ├── my_agent.py
    └── mcp.json (optional)
```

### agent.json Format

```json
{
  "name": "MyAgent",
  "version": "1.0.0",
  "module": "my_agent",
  "class": "MyAgent",
  "description": "Description of what this agent does",
  "capabilities": ["capability1", "capability2"],
  "supported_mcp_servers": ["server1", "server2"]
}
```

### Python Module Requirements

```python
from atoll.plugins.base import ATOLLAgent

class MyAgent(ATOLLAgent):
    def __init__(self, name: str, version: str):
        super().__init__(name, version)

    async def process(self, prompt: str, context: dict) -> dict:
        # Your agent logic here
        return {"response": "...", "reasoning": [...]}

    def get_capabilities(self) -> list[str]:
        return ["capability1", "capability2"]

    def get_supported_mcp_servers(self) -> list[str]:
        return ["server1", "server2"]
```

## Available Example Agents

Check the ATOLL repository for example agents:
- **ghidra_agent**: Binary analysis and decompilation using Ghidra MCP server

## More Information

See the ATOLL documentation for detailed information on creating custom agents:
https://github.com/Buttje/ATOLL/tree/main/docs
"""
                readme_path.write_text(readme_content, encoding="utf-8")
                logger.info(f"Created README at {readme_path}")

            # Try to copy example agents from installation if available
            try:
                # Find the source atoll_agents directory in the repository
                # This would be at the same level as the package installation
                source_agents_dir = self.agents_directory.parent / "atoll_agents_examples"

                # If we're in a development environment, look for the repo structure
                if not source_agents_dir.exists():
                    # Try finding it relative to package
                    import atoll

                    repo_root = Path(atoll.__file__).parent.parent.parent
                    source_agents_dir = repo_root / "atoll_agents"

                if source_agents_dir.exists():
                    # Copy ghidra_agent as example if it exists
                    ghidra_agent_src = source_agents_dir / "ghidra_agent"
                    ghidra_agent_dst = self.agents_directory / "ghidra_agent.example"

                    if ghidra_agent_src.exists() and not ghidra_agent_dst.exists():
                        shutil.copytree(ghidra_agent_src, ghidra_agent_dst)
                        logger.info(f"Copied example agent to {ghidra_agent_dst}")
                        logger.info(
                            "Rename 'ghidra_agent.example' to 'ghidra_agent' to activate it"
                        )
            except Exception as e:
                # Silently skip if we can't find/copy examples
                logger.debug(f"Could not copy example agents: {e}")

        except Exception as e:
            logger.error(f"Failed to create agents directory: {e}")
