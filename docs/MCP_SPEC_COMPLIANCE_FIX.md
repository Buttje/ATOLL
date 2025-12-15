# MCP Specification Compliance Fix

## Issue
Ghidra MCP server was connecting successfully but tools were not appearing in ATOLL. The server was reporting as "connected" but the `tools` command showed no tools available.

## Root Cause
The MCP client implementation incorrectly attempted to extract tools from the `initialize` response. According to the [MCP specification](https://modelcontextprotocol.io/specification/2025-03-26/server/tools), the `initialize` response contains:
- `protocolVersion`: The protocol version (e.g., "0.1.0")
- `capabilities`: Server capabilities (e.g., `{"tools": {"listChanged": true}}`)
- `serverInfo`: Server metadata (name, version)

The initialize response does **NOT** contain the actual tools list.

### Incorrect Behavior (Before Fix)
```python
# In _initialize() method
if response and "result" in response:
    # BUG: Trying to extract tools from initialize response
    self.tools = response["result"].get("tools", {})
    self.prompts = response["result"].get("prompts", {})
    self.resources = response["result"].get("resources", [])
```

This code expected tools in the initialize response, which is not per MCP spec.

## Solution
Per MCP specification, tools must be fetched via a separate `tools/list` JSON-RPC request:

### Request Format
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/list",
  "params": {}
}
```

### Expected Response Format
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "tools": [
      {
        "name": "tool_name",
        "description": "Tool description",
        "inputSchema": {
          "type": "object",
          "properties": { ... },
          "required": [ ... ]
        }
      }
    ]
  }
}
```

## Changes Made

### 1. Updated `MCPClient.__init__()` ([src/atoll/mcp/client.py](../src/atoll/mcp/client.py))
Removed incorrect attributes and added proper ones:
```python
# Before
self.tools: Dict[str, Any] = {}
self.prompts: Dict[str, Any] = {}
self.resources: List[Any] = []

# After
self.capabilities: Dict[str, Any] = {}
self.server_info: Dict[str, Any] = {}
```

### 2. Fixed `_initialize()` Method
Changed to extract capabilities instead of tools:
```python
# Before
if response and "result" in response:
    self.tools = response["result"].get("tools", {})
    self.prompts = response["result"].get("prompts", {})
    self.resources = response["result"].get("resources", [])

# After
if response and "result" in response:
    self.capabilities = response["result"].get("capabilities", {})
    self.server_info = response["result"].get("serverInfo", {})
```

### 3. Updated `list_tools()` Method
Removed incorrect caching logic that relied on tools from initialize:
```python
async def list_tools(self) -> List[Dict[str, Any]]:
    """List available tools from the MCP server.

    Returns:
        List of tool definitions per MCP spec
    """
    if not self.connected:
        return []

    # Query the server for tools per MCP spec
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
        logger.info(f"Retrieved {len(tools)} tools from '{self.name}'")
        return tools
    elif response and "error" in response:
        logger.error(f"Error listing tools from '{self.name}': {response['error']}")

    return []
```

## Testing
Created comprehensive tests in [test_mcp_spec_compliance.py](../tests/unit/test_mcp_spec_compliance.py):

1. **test_initialize_returns_capabilities_not_tools**: Verifies initialize response contains capabilities, not tools
2. **test_list_tools_sends_correct_request**: Verifies tools/list request follows MCP spec format
3. **test_tools_not_cached_from_initialize**: Ensures tools are never cached from initialize response

All 343 unit tests pass, including 3 new spec compliance tests.

## Impact
- Ghidra MCP server tools now appear correctly after connection
- All MCP servers following the specification will work properly
- Tool discovery happens via proper `tools/list` method
- Better logging shows when tools are retrieved

## Verification
To verify the fix works with Ghidra MCP server:

1. Ensure Ghidra MCP server is configured in `~/.atoll/mcp.json`:
   ```json
   {
     "servers": {
       "Ghidra": {
         "type": "stdio",
         "command": "python",
         "args": ["path/to/bridge_mcp_ghidra.py", "--ghidra-server", "http://127.0.0.1:8080"]
       }
     }
   }
   ```

2. Start ATOLL and check server status:
   ```
   ATOLL> servers
   ```

3. List available tools:
   ```
   ATOLL> tools
   ```

You should now see all Ghidra tools listed, including:
- decompile_function
- decompile_function_by_address
- disassemble_function
- get_function_xrefs
- list_functions
- search_functions_by_name
- And many more...

## References
- [MCP Specification - Tools](https://modelcontextprotocol.io/specification/2025-03-26/server/tools)
- [MCP Specification - Initialization](https://modelcontextprotocol.io/specification/2025-03-26/protocol/initialization)
- [Ghidra MCP Server](https://github.com/LaurieWired/GhidraMCP)
