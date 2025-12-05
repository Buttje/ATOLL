"""MCP tool wrapper for LangChain integration."""

from typing import Any, Dict, Optional, Union
from langchain_core.tools import BaseTool
from pydantic import Field, ConfigDict

from ..mcp.server_manager import MCPServerManager


class MCPToolWrapper(BaseTool):
    """Wrapper to expose MCP tools to LangChain."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description")
    mcp_manager: MCPServerManager = Field(exclude=True)
    server_name: Optional[str] = Field(default=None, description="Server name")
    
    def _run(self, input_str: str) -> str:
        """Synchronous execution (not recommended for MCP)."""
        import asyncio
        return asyncio.run(self._arun(input_str))
    
    async def _arun(self, input_str: str) -> str:
        """Asynchronous execution of the tool."""
        try:
            # Parse input as JSON if possible
            import json
            try:
                arguments = json.loads(input_str)
            except json.JSONDecodeError:
                # If not JSON, wrap string in an object
                arguments = {"input": input_str}
            
            # Execute tool through MCP manager
            result = await self.mcp_manager.execute_tool(
                server_name=self.server_name,
                tool_name=self.name,
                arguments=arguments,
            )
            
            # Return result as string
            if isinstance(result, dict):
                return json.dumps(result, indent=2)
            return str(result)
            
        except Exception as e:
            return f"Error executing tool {self.name}: {str(e)}"
            return f"Error executing tool {self.name}: {str(e)}"