"""MCP server manager."""

import asyncio
from typing import Dict, List, Optional, Any

from ..config.models import MCPConfig
from .client import MCPClient
from .tool_registry import ToolRegistry
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MCPServerManager:
    """Manages multiple MCP server connections."""
    
    def __init__(self, config: MCPConfig):
        """Initialize server manager."""
        self.config = config
        self.clients: Dict[str, MCPClient] = {}
        self.tool_registry = ToolRegistry()
    
    async def connect_all(self) -> None:
        """Connect to all configured MCP servers."""
        tasks = []
        
        for name, server_config in self.config.servers.items():
            client = MCPClient(name, server_config)
            self.clients[name] = client
            tasks.append(self._connect_and_discover(client))
        
        if tasks:
            await asyncio.gather(*tasks)
    
    async def _connect_and_discover(self, client: MCPClient) -> None:
        """Connect to a server and discover its tools."""
        try:
            if await client.connect():
                # Discover available tools
                tools = await client.list_tools()
                # Use register_tools (plural) instead of register_tool
                self.tool_registry.register_tools(client.name, tools)
                
                logger.info(f"Discovered {len(tools)} tools from '{client.name}'")
        
        except Exception as e:
            logger.error(f"Failed to connect to '{client.name}': {e}")
    
    async def disconnect_all(self) -> None:
        """Disconnect from all MCP servers."""
        tasks = [client.disconnect() for client in self.clients.values()]
        if tasks:
            await asyncio.gather(*tasks)
        
        self.clients.clear()
        self.tool_registry.clear()
    
    async def execute_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any]
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
    
    def list_servers(self) -> List[str]:
        """List all connected server names."""
        return list(self.clients.keys())