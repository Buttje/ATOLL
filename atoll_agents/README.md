# ATOLL Agent Plugins

This directory contains specialized ATOLL agent plugins that extend the capabilities of the base ATOLL system.

## Structure

Each agent plugin must be in its own subdirectory and contain:

1. **agent.json** - Metadata file describing the agent
2. **{module}.py** - Python module implementing the agent class

### agent.json Format

```json
{
  "name": "AgentName",
  "version": "1.0.0",
  "module": "module_name",
  "class": "ClassName",
  "description": "Brief description of the agent",
  "author": "Author Name",
  "capabilities": [
    "capability1",
    "capability2"
  ],
  "supported_mcp_servers": [
    "server1",
    "server2"
  ]
}
```

### Python Module Requirements

The Python module must:
- Import `ATOLLAgent` from `atoll.plugins.base`
- Define a class that inherits from `ATOLLAgent`
- Implement all required abstract methods:
  - `async def process(prompt, context) -> dict`
  - `def get_capabilities() -> list[str]`
  - `def get_supported_mcp_servers() -> list[str]`

## Example: Creating a New Agent

```python
from atoll.plugins.base import ATOLLAgent
from typing import Any


class MyAgent(ATOLLAgent):
    """My specialized agent."""

    def __init__(self, name: str, version: str):
        super().__init__(name, version)

    async def process(self, prompt: str, context: dict[str, Any]) -> dict[str, Any]:
        """Process a prompt."""
        return {
            "response": "My response",
            "reasoning": ["Step 1", "Step 2"],
            "tool_calls": []
        }

    def get_capabilities(self) -> list[str]:
        """Get capabilities."""
        return ["my_capability"]

    def get_supported_mcp_servers(self) -> list[str]:
        """Get supported MCP servers."""
        return ["my_mcp_server"]

    def can_handle(self, prompt: str, context: dict[str, Any]) -> float:
        """Return confidence score 0.0-1.0."""
        if "keyword" in prompt.lower():
            return 0.8
        return 0.0
```

## Available Agents

### GhidraATOLL

Specialized agent for binary reverse engineering using Ghidra.

**Capabilities:**
- Binary analysis
- Decompilation
- Symbol analysis
- Reverse engineering
- Vulnerability detection

**Supported MCP Servers:**
- ghidramcp

## Agent Selection

Agents are automatically selected based on their `can_handle()` confidence score. The agent with the highest score (> 0) is used for processing the prompt.

## Testing

Test your agent by running:

```bash
python -c "
from atoll.plugins.manager import PluginManager
manager = PluginManager()
count = manager.discover_plugins()
print(f'Loaded {count} plugins')
"
```

## Best Practices

1. **Specificity**: Make your `can_handle()` method specific to avoid conflicts
2. **Error Handling**: Always handle errors gracefully in `process()`
3. **Documentation**: Document capabilities and requirements clearly
4. **Testing**: Create unit tests for your agent
5. **Dependencies**: Document any external dependencies in your README
