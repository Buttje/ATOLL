"""Tool registry for managing MCP tools."""

from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing tools from multiple MCP servers."""
    
    def __init__(self):
        """Initialize the tool registry."""
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._tool_to_server: Dict[str, str] = {}
    
    def register_tools(self, server_name: str, tools: List[Dict[str, Any]]) -> None:
        """Register tools from an MCP server.
        
        Args:
            server_name: Name of the MCP server
            tools: List of tool definitions from the server
        """
        for tool in tools:
            tool_name = tool.get("name")
            if not tool_name:
                logger.warning(f"Tool without name from server '{server_name}', skipping")
                continue
            
            # Add server info to tool
            tool_info = tool.copy()
            tool_info["server"] = server_name
            
            # Check for duplicates
            if tool_name in self.tools:
                logger.warning(
                    f"Tool '{tool_name}' already registered from server "
                    f"'{self._tool_to_server.get(tool_name)}', overwriting with "
                    f"version from '{server_name}'"
                )
            
            # Register the tool
            self.tools[tool_name] = tool_info
            self._tool_to_server[tool_name] = server_name
            
            logger.info(f"Registered tool '{tool_name}' from server '{server_name}'")
    
    def unregister_server_tools(self, server_name: str) -> None:
        """Unregister all tools from a specific server.
        
        Args:
            server_name: Name of the MCP server
        """
        tools_to_remove = [
            tool_name 
            for tool_name, server in self._tool_to_server.items() 
            if server == server_name
        ]
        
        for tool_name in tools_to_remove:
            del self.tools[tool_name]
            del self._tool_to_server[tool_name]
            logger.info(f"Unregistered tool '{tool_name}' from server '{server_name}'")
    
    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get a tool by name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool information or None if not found
        """
        return self.tools.get(tool_name)
    
    def get_server_for_tool(self, tool_name: str) -> Optional[str]:
        """Get the server name that provides a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Server name or None if tool not found
        """
        return self._tool_to_server.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """List all registered tool names.
        
        Returns:
            List of tool names
        """
        return list(self.tools.keys())
    
    def list_server_tools(self, server_name: str) -> List[str]:
        """List all tools from a specific server.
        
        Args:
            server_name: Name of the MCP server
            
        Returns:
            List of tool names from the server
        """
        return [
            tool_name 
            for tool_name, server in self._tool_to_server.items() 
            if server == server_name
        ]
    
    def clear(self) -> None:
        """Clear all registered tools."""
        self.tools.clear()
        self._tool_to_server.clear()
        logger.info("Cleared all registered tools")
        logger.info("Cleared all registered tools")