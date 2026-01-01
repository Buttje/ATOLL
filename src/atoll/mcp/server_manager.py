"""MCP server manager."""

import asyncio
from typing import TYPE_CHECKING, Any, Optional

from ..config.models import MCPConfig
from ..utils.logger import get_logger
from .client import MCPClient
from .tool_registry import ToolRegistry

if TYPE_CHECKING:
    from ..ui.terminal import TerminalUI

logger = get_logger(__name__)


class MCPServerManager:
    """Manages multiple MCP server connections."""

    def __init__(self, config: MCPConfig, ui: Optional["TerminalUI"] = None):
        """Initialize server manager."""
        self.config = config
        self.clients: dict[str, MCPClient] = {}
        self.tool_registry = ToolRegistry()
        self.ui = ui

    async def connect_all(self) -> None:
        """Connect to all configured MCP servers."""
        if not self.config.servers:
            if self.ui:
                self.ui.display_verbose("No MCP servers configured", prefix="[MCP]")
            logger.info("No MCP servers configured")
            return

        if self.ui:
            self.ui.display_verbose(
                f"Connecting to {len(self.config.servers)} MCP server(s)...", prefix="[MCP]"
            )

        tasks = []

        for name, server_config in self.config.servers.items():
            if self.ui:
                self.ui.display_verbose(f"Initializing connection to '{name}'", prefix="[MCP]")
            client = MCPClient(name, server_config)
            self.clients[name] = client
            tasks.append(self._connect_and_discover(client))

        if tasks:
            await asyncio.gather(*tasks)
            if self.ui:
                connected_count = sum(1 for c in self.clients.values() if c.connected)
                self.ui.display_verbose(
                    f"Connected to {connected_count}/{len(self.clients)} MCP server(s)",
                    prefix="[MCP]",
                )

    async def _connect_and_discover(self, client: MCPClient) -> None:
        """Connect to a server and discover its tools."""
        try:
            if self.ui:
                self.ui.display_verbose(
                    f"Connecting to MCP server '{client.name}'...", prefix="[MCP]"
                )

            if await client.connect():
                if self.ui:
                    self.ui.display_verbose(f"✓ Connected to '{client.name}'", prefix="[MCP]")

                # Discover available tools
                if self.ui:
                    self.ui.display_verbose(
                        f"Discovering tools from '{client.name}'...", prefix="[MCP]"
                    )

                tools = await client.list_tools()
                # Use register_tools (plural) instead of register_tool
                self.tool_registry.register_tools(client.name, tools)

                if self.ui:
                    self.ui.display_verbose(
                        f"✓ Discovered {len(tools)} tool(s) from '{client.name}'", prefix="[MCP]"
                    )
                logger.info(f"Discovered {len(tools)} tools from '{client.name}'")
            else:
                if self.ui:
                    self.ui.display_verbose(
                        f"✗ Failed to connect to '{client.name}'", prefix="[MCP]"
                    )

        except Exception as e:
            if self.ui:
                self.ui.display_verbose(
                    f"✗ Error connecting to '{client.name}': {str(e)}", prefix="[MCP]"
                )
            logger.error(f"Failed to connect to '{client.name}': {e}")

    async def disconnect_all(self) -> None:
        """Disconnect from all MCP servers."""
        tasks = [client.disconnect() for client in self.clients.values()]
        if tasks:
            await asyncio.gather(*tasks)

        self.clients.clear()
        self.tool_registry.clear()

    async def execute_tool(
        self, server_name: str, tool_name: str, arguments: dict[str, Any]
    ) -> Any:
        """Execute a tool on a specific server.

        Args:
            server_name: Name of the server that provides the tool
            tool_name: Name of the tool to execute
            arguments: Tool arguments

        Returns:
            Tool execution result

        Raises:
            ValueError: If server or tool not found
        """
        client = self.get_client(server_name)
        if not client:
            raise ValueError(f"Server '{server_name}' not found")

        return await client.call_tool(tool_name, arguments)

    def get_client(self, server_name: str) -> Optional[MCPClient]:
        """Get a specific MCP client."""
        return self.clients.get(server_name)

    def list_servers(self) -> list[str]:
        """List all connected server names."""
        return list(self.clients.keys())
