"""MCP client implementation for connecting to MCP servers."""

import os
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from ..config.models import MCPServerConfig

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for connecting to MCP servers."""
    
    def __init__(self, name: str, config: MCPServerConfig):
        """Initialize MCP client."""
        self.name = name
        self.config = config
        self.connected = False
        self.process: Optional[asyncio.subprocess.Process] = None
        self.tools: Dict[str, Any] = {}
        self.prompts: Dict[str, Any] = {}
        self.resources: List[Any] = []
    
    async def connect(self) -> bool:
        """Connect to the MCP server."""
        try:
            if self.config.transport == "stdio":
                return await self._connect_stdio()
            elif self.config.transport == "sse":
                return await self._connect_sse()
            else:
                logger.error(f"Unsupported transport: {self.config.transport}")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to MCP server '{self.name}': {e}")
            return False
    
    async def _connect_stdio(self) -> bool:
        """Connect via stdio transport."""
        try:
            # Expand environment variables in command
            command = os.path.expandvars(self.config.command)
            args = [os.path.expandvars(arg) for arg in self.config.args] if self.config.args else []
            
            # Set up environment
            env = os.environ.copy()
            if self.config.env:
                for key, value in self.config.env.items():
                    env[key] = os.path.expandvars(value)
            
            # Create subprocess
            self.process = await asyncio.create_subprocess_exec(
                command,
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            
            self.connected = True
            logger.info(f"Connected to MCP server '{self.name}' via stdio")
            
            # Initialize communication
            await self._initialize()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server '{self.name}': {e}")
            return False
    
    async def _connect_sse(self) -> bool:
        """Connect via SSE transport."""
        # TODO: Implement SSE transport
        logger.warning("SSE transport not yet implemented")
        return False
    
    async def _initialize(self) -> None:
        """Initialize MCP protocol after connection."""
        # Send initialization request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "0.1.0",
                "capabilities": {}
            }
        }
        
        await self._send_message(init_request)
        
        # Wait for response
        response = await self._receive_message()
        
        if response and "result" in response:
            # Store server capabilities
            self.tools = response["result"].get("tools", {})
            self.prompts = response["result"].get("prompts", {})
            self.resources = response["result"].get("resources", [])
    
    async def _send_message(self, message: Dict[str, Any]) -> None:
        """Send a message to the MCP server."""
        if self.process and self.process.stdin:
            data = json.dumps(message) + "\n"
            self.process.stdin.write(data.encode())
            await self.process.stdin.drain()
    
    async def _receive_message(self) -> Optional[Dict[str, Any]]:
        """Receive a message from the MCP server."""
        if self.process and self.process.stdout:
            try:
                line = await asyncio.wait_for(
                    self.process.stdout.readline(),
                    timeout=self.config.timeoutSeconds
                )
                if line:
                    return json.loads(line.decode())
            except asyncio.TimeoutError:
                logger.warning(f"Timeout waiting for response from '{self.name}'")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse response from '{self.name}': {e}")
        return None
    
    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self.process = None
        self.connected = False
        logger.info(f"Disconnected from MCP server '{self.name}'")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server."""
        if not self.connected:
            raise RuntimeError(f"Not connected to MCP server '{self.name}'")
        
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        await self._send_message(request)
        response = await self._receive_message()
        
        if response and "result" in response:
            return response["result"]
        elif response and "error" in response:
            raise RuntimeError(f"Tool call error: {response['error']}")
        else:
            raise RuntimeError("No response from MCP server")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server.
        
        Returns:
            List of tool definitions
        """
        if not self.connected:
            return []
        
        # If we have cached tools from initialization, return those
        if self.tools:
            # Convert to list format expected by callers
            if isinstance(self.tools, dict):
                return [{"name": k, **v} for k, v in self.tools.items()]
            elif isinstance(self.tools, list):
                return self.tools
        
        # Otherwise, query the server for tools
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/list",
            "params": {}
        }
        
        await self._send_message(request)
        response = await self._receive_message()
        
        if response and "result" in response:
            tools = response["result"].get("tools", [])
            return tools
        
        return []