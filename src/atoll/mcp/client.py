"""MCP client implementation for connecting to MCP servers."""

import asyncio
import json
import logging
import os
from typing import Any, Optional

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
        self.capabilities: dict[str, Any] = {}
        self.server_info: dict[str, Any] = {}

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
                "capabilities": {},
                "clientInfo": {"name": "ATOLL", "version": "1.0.0"},
            },
        }

        logger.debug(f"Sending initialize request to '{self.name}': {init_request}")
        await self._send_message(init_request)

        # Wait for response
        response = await self._receive_message()
        logger.debug(f"Initialize response from '{self.name}': {response}")

        if response and "result" in response:
            # Store server capabilities (not the actual tools/prompts/resources)
            self.capabilities = response["result"].get("capabilities", {})
            self.server_info = response["result"].get("serverInfo", {})
            logger.info(
                f"Initialized '{self.name}' - Server: {self.server_info.get('name', 'unknown')}, Capabilities: {list(self.capabilities.keys())}"
            )

    async def _send_message(self, message: dict[str, Any]) -> None:
        """Send a message to the MCP server."""
        if self.process and self.process.stdin:
            data = json.dumps(message) + "\n"
            self.process.stdin.write(data.encode())
            await self.process.stdin.drain()

    async def _receive_message(self) -> Optional[dict[str, Any]]:
        """Receive a message from the MCP server."""
        if self.process and self.process.stdout:
            try:
                line = await asyncio.wait_for(
                    self.process.stdout.readline(), timeout=self.config.timeoutSeconds
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
            try:
                # Close pipes before terminating
                if self.process.stdin:
                    self.process.stdin.close()
                    await self.process.stdin.wait_closed()

                # Terminate the process
                self.process.terminate()

                # Wait for process to finish with timeout
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning(f"Process '{self.name}' did not terminate, killing it")
                    self.process.kill()
                    await self.process.wait()
            except Exception as e:
                logger.error(f"Error disconnecting from '{self.name}': {e}")
            finally:
                self.process = None

        self.connected = False
        logger.info(f"Disconnected from MCP server '{self.name}'")

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool on the MCP server."""
        if not self.connected:
            raise RuntimeError(f"Not connected to MCP server '{self.name}'")

        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }

        await self._send_message(request)
        response = await self._receive_message()

        if response and "result" in response:
            return response["result"]
        elif response and "error" in response:
            raise RuntimeError(f"Tool call error: {response['error']}")
        else:
            raise RuntimeError("No response from MCP server")

    async def list_resources(self, cursor: Optional[str] = None) -> dict[str, Any]:
        """List available resources from the MCP server.

        Args:
            cursor: Optional pagination cursor

        Returns:
            Dict with 'resources' list and optional 'nextCursor'
        """
        if not self.connected:
            return {"resources": []}

        request = {"jsonrpc": "2.0", "id": 4, "method": "resources/list", "params": {}}

        if cursor:
            request["params"]["cursor"] = cursor

        logger.debug(f"Sending resources/list request to '{self.name}'")
        await self._send_message(request)
        response = await self._receive_message()

        if response and "result" in response:
            return response["result"]
        elif response and "error" in response:
            logger.error(f"Error listing resources from '{self.name}': {response['error']}")

        return {"resources": []}

    async def read_resource(self, uri: str) -> dict[str, Any]:
        """Read a resource from the MCP server.

        Args:
            uri: Resource URI to read

        Returns:
            Dict with 'contents' list containing resource data
        """
        if not self.connected:
            raise RuntimeError(f"Not connected to MCP server '{self.name}'")

        request = {"jsonrpc": "2.0", "id": 5, "method": "resources/read", "params": {"uri": uri}}

        await self._send_message(request)
        response = await self._receive_message()

        if response and "result" in response:
            return response["result"]
        elif response and "error" in response:
            raise RuntimeError(f"Resource read error: {response['error']}")
        else:
            raise RuntimeError("No response from MCP server")

    async def subscribe_resource(self, uri: str) -> bool:
        """Subscribe to updates for a resource.

        Args:
            uri: Resource URI to subscribe to

        Returns:
            True if subscription successful
        """
        if not self.connected:
            return False

        if not self.capabilities.get("resources", {}).get("subscribe"):
            logger.warning(f"Server '{self.name}' does not support resource subscriptions")
            return False

        request = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "resources/subscribe",
            "params": {"uri": uri},
        }

        await self._send_message(request)
        response = await self._receive_message()

        if response and "result" in response:
            logger.info(f"Subscribed to resource '{uri}' on '{self.name}'")
            return True
        elif response and "error" in response:
            logger.error(f"Error subscribing to resource: {response['error']}")

        return False

    async def unsubscribe_resource(self, uri: str) -> bool:
        """Unsubscribe from updates for a resource.

        Args:
            uri: Resource URI to unsubscribe from

        Returns:
            True if unsubscription successful
        """
        if not self.connected:
            return False

        request = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "resources/unsubscribe",
            "params": {"uri": uri},
        }

        await self._send_message(request)
        response = await self._receive_message()

        if response and "result" in response:
            logger.info(f"Unsubscribed from resource '{uri}' on '{self.name}'")
            return True
        elif response and "error" in response:
            logger.error(f"Error unsubscribing from resource: {response['error']}")

        return False

    async def list_resource_templates(self) -> list[dict[str, Any]]:
        """List available resource templates from the MCP server.

        Returns:
            List of resource template definitions
        """
        if not self.connected:
            return []

        request = {"jsonrpc": "2.0", "id": 8, "method": "resources/templates/list", "params": {}}

        await self._send_message(request)
        response = await self._receive_message()

        if response and "result" in response:
            return response["result"].get("resourceTemplates", [])
        elif response and "error" in response:
            logger.error(
                f"Error listing resource templates from '{self.name}': {response['error']}"
            )

        return []

    async def list_prompts(self, cursor: Optional[str] = None) -> dict[str, Any]:
        """List available prompts from the MCP server.

        Args:
            cursor: Optional pagination cursor

        Returns:
            Dict with 'prompts' list and optional 'nextCursor'
        """
        if not self.connected:
            return {"prompts": []}

        request = {"jsonrpc": "2.0", "id": 9, "method": "prompts/list", "params": {}}

        if cursor:
            request["params"]["cursor"] = cursor

        logger.debug(f"Sending prompts/list request to '{self.name}'")
        await self._send_message(request)
        response = await self._receive_message()

        if response and "result" in response:
            return response["result"]
        elif response and "error" in response:
            logger.error(f"Error listing prompts from '{self.name}': {response['error']}")

        return {"prompts": []}

    async def get_prompt(
        self, name: str, arguments: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Get a specific prompt with arguments.

        Args:
            name: Prompt name
            arguments: Optional prompt arguments

        Returns:
            Dict with 'messages' list containing prompt content
        """
        if not self.connected:
            raise RuntimeError(f"Not connected to MCP server '{self.name}'")

        request = {"jsonrpc": "2.0", "id": 10, "method": "prompts/get", "params": {"name": name}}

        if arguments:
            request["params"]["arguments"] = arguments

        await self._send_message(request)
        response = await self._receive_message()

        if response and "result" in response:
            return response["result"]
        elif response and "error" in response:
            raise RuntimeError(f"Prompt get error: {response['error']}")
        else:
            raise RuntimeError("No response from MCP server")

    async def set_logging_level(self, level: str) -> bool:
        """Set the logging level for the MCP server.

        Args:
            level: Logging level ('debug', 'info', 'notice', 'warning', 'error', 'critical', 'alert', 'emergency')

        Returns:
            True if successful
        """
        if not self.connected:
            return False

        request = {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "logging/setLevel",
            "params": {"level": level},
        }

        await self._send_message(request)
        response = await self._receive_message()

        if response and "result" in response:
            logger.info(f"Set logging level to '{level}' for '{self.name}'")
            return True
        elif response and "error" in response:
            logger.error(f"Error setting logging level: {response['error']}")

        return False

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools from the MCP server.

        Returns:
            List of tool definitions per MCP spec
        """
        if not self.connected:
            return []

        # Query the server for tools per MCP spec
        request = {"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}}

        logger.debug(f"Sending tools/list request to '{self.name}': {request}")
        await self._send_message(request)
        response = await self._receive_message()
        logger.debug(f"Received response from '{self.name}': {response}")

        if response and "result" in response:
            tools = response["result"].get("tools", [])
            logger.info(f"Retrieved {len(tools)} tools from '{self.name}'")
            return tools
        elif response and "error" in response:
            logger.error(f"Error listing tools from '{self.name}': {response['error']}")
            # Log more details about the error
            if "data" in response["error"]:
                logger.debug(f"Error data: {response['error']['data']}")

        return []
