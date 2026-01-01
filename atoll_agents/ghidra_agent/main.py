#!/usr/bin/env python3
"""Main entry point for GhidraAgent.

This script initializes and runs the GhidraAgent as a standalone service,
compatible with ATOLL v2.0 deployment server.

Author: ATOLL Contributors
Version: 2.0.0
License: MIT
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path to import agent
sys.path.insert(0, str(Path(__file__).parent))

from ghidra_agent import GhidraAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point for GhidraAgent."""
    try:
        # Load configuration
        config_path = Path(__file__).parent / "agent.toml"

        if not config_path.exists():
            logger.error(f"Agent configuration not found: {config_path}")
            return 1

        logger.info("Starting GhidraAgent v2.0.0...")

        # Initialize agent (configuration loaded from agent.toml by deployment server)
        agent = GhidraAgent(name="GhidraAgent", version="2.0.0")

        logger.info("GhidraAgent initialized successfully")
        logger.info(f"Capabilities: {', '.join(agent.get_capabilities())}")
        logger.info(f"Supported MCP servers: {', '.join(agent.get_supported_mcp_servers())}")

        # Keep the agent running
        logger.info("GhidraAgent is ready and waiting for requests...")

        # In a real deployment, this would be managed by the deployment server
        # For now, we'll just demonstrate successful startup
        await asyncio.sleep(1)

        logger.info("GhidraAgent startup complete")
        return 0

    except Exception as e:
        logger.error(f"Failed to start GhidraAgent: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
