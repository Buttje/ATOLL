"""MCP tool registry and management."""

from typing import Any, Dict, List


class MCPTool:
    """Represents an MCP tool."""
    
    def __init__(self, name: str, server: str, metadata: Dict[str, Any]):
        """Initialize MCP tool."""
        self.name = name
        self.server = server
        self.metadata = metadata
        self.description = metadata.get("description", f"Tool: {name}")
        self.parameters = metadata.get("inputSchema", {})


class MCPToolRegistry:
    """Registry for all discovered MCP tools."""
    
    def __init__(self):
        """Initialize tool registry."""
        self.tools: Dict[str, Dict[str, Any]] = {}
    
    def register_tool(self, server_name: str, tool_data: Dict[str, Any]) -> None:
        """Register a tool from an MCP server."""
        tool_name = tool_data.get("name")
        if not tool_name:
            return
        
        # Create unique tool identifier
        full_name = f"{server_name}_{tool_name}"
        
        self.tools[full_name] = {
            "name": tool_name,
            "server": server_name,
            "description": tool_data.get("description", ""),
            "inputSchema": tool_data.get("inputSchema", {}),
        }
    
    def get_tool(self, full_name: str) -> Dict[str, Any]:
        """Get tool information by full name."""
        return self.tools.get(full_name, {})
    
    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self.tools.keys())