#!/usr/bin/env python
"""Command-line interface for ATOLL Deployment Server.

This module provides a CLI entry point for running the deployment server
as a standalone application for managing remote agents.
"""

import argparse
import asyncio
import sys
from pathlib import Path

from atoll import __version__
from .server import DeploymentServer, DeploymentServerConfig


def main():
    """Main entry point for deployment server CLI."""
    parser = argparse.ArgumentParser(
        description="ATOLL Deployment Server - Manage remote agent instances",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start deployment server with default settings
  atoll-deploy

  # Start with custom port and agents directory
  atoll-deploy --port 8090 --agents-dir /opt/atoll/agents

  # Start with specific configuration
  atoll-deploy --config /etc/atoll/deployment.json

For more information, visit: https://github.com/Buttje/ATOLL
        """,
    )

    parser.add_argument(
        "--host",
        default="localhost",
        help="Host to bind the API server to (default: localhost)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for the REST API server (default: 8080)",
    )

    parser.add_argument(
        "--agents-dir",
        type=Path,
        help="Directory to discover agent configurations (default: ./atoll_agents)",
    )

    parser.add_argument(
        "--base-port",
        type=int,
        default=8100,
        help="Base port for agent instances (default: 8100)",
    )

    parser.add_argument(
        "--max-agents",
        type=int,
        default=10,
        help="Maximum number of agents to manage (default: 10)",
    )

    parser.add_argument(
        "--no-auto-restart",
        action="store_true",
        help="Disable automatic restart of failed agents",
    )

    parser.add_argument(
        "--config",
        type=Path,
        help="Path to deployment server configuration file (JSON)",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"ATOLL Deployment Server {__version__}",
    )

    args = parser.parse_args()

    # Load configuration
    if args.config:
        # Load from file
        import json

        try:
            with open(args.config) as f:
                config_data = json.load(f)
            config = DeploymentServerConfig(**config_data.get("deployment_server", {}))
        except Exception as e:
            print(f"Error loading configuration from {args.config}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Use command-line arguments
        agents_dir = args.agents_dir or Path.cwd() / "atoll_agents"
        config = DeploymentServerConfig(
            enabled=True,
            host=args.host,
            api_port=args.port,
            base_port=args.base_port,
            max_agents=args.max_agents,
            agents_directory=str(agents_dir),
            restart_on_failure=not args.no_auto_restart,
        )

    # Print startup banner
    print("=" * 70)
    print(f"ATOLL Deployment Server v{__version__}")
    print("=" * 70)
    print(f"API Server: http://{config.host}:{config.api_port}")
    print(f"Agents Directory: {config.agents_directory}")
    print(f"Agent Port Range: {config.base_port}-{config.base_port + config.max_agents - 1}")
    print(f"Auto-restart: {'Enabled' if config.restart_on_failure else 'Disabled'}")
    print("=" * 70)
    print()

    # Create and run deployment server
    server = DeploymentServer(config)

    try:
        asyncio.run(run_server(server))
    except KeyboardInterrupt:
        print("\n\nShutting down deployment server...")
        sys.exit(0)
    except Exception as e:
        print(f"\nError running deployment server: {e}", file=sys.stderr)
        sys.exit(1)


async def run_server(server: DeploymentServer):
    """Run the deployment server.

    Args:
        server: DeploymentServer instance
    """
    try:
        await server.start()

        # Keep server running
        print("\nDeployment server is running. Press Ctrl+C to stop.\n")
        while server.running:
            await asyncio.sleep(1)

    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        raise
    finally:
        await server.stop()


if __name__ == "__main__":
    main()
