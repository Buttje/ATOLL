# ATOLL Agent Plugins

This directory contains specialized ATOLL agent plugins that extend the capabilities of the base ATOLL system.

## Quick Start

To add a specialized agent:

1. Copy an agent directory (e.g., from the ATOLL repository's `atoll_agents/` folder)
2. Each agent needs:
   - `agent.json` - Metadata file
   - `{module}.py` - Python implementation
   - Optional: `mcp.json` - MCP server configuration

## Example: Ghidra Agent

If you want to use the Ghidra reverse engineering agent:

```bash
# Copy the example from the ATOLL repository
cp -r <atoll-repo>/atoll_agents/ghidra_agent ./atoll_agents/
```

## Structure

```
atoll_agents/
├── README.md (this file)
└── my_agent/
    ├── agent.json
    ├── my_agent.py
    └── mcp.json (optional)
```

### agent.json Format

```json
{
  "name": "MyAgent",
  "version": "1.0.0",
  "module": "my_agent",
  "class": "MyAgent",
  "description": "Description of what this agent does",
  "capabilities": ["capability1", "capability2"],
  "supported_mcp_servers": ["server1", "server2"]
}
```

### Python Module Requirements

```python
from atoll.plugins.base import ATOLLAgent

class MyAgent(ATOLLAgent):
    def __init__(self, name: str, version: str):
        super().__init__(name, version)

    async def process(self, prompt: str, context: dict) -> dict:
        # Your agent logic here
        return {"response": "...", "reasoning": [...]}

    def get_capabilities(self) -> list[str]:
        return ["capability1", "capability2"]

    def get_supported_mcp_servers(self) -> list[str]:
        return ["server1", "server2"]
```

## Available Example Agents

Check the ATOLL repository for example agents:
- **ghidra_agent**: Binary analysis and decompilation using Ghidra MCP server

## More Information

See the ATOLL documentation for detailed information on creating custom agents:
https://github.com/Buttje/ATOLL/tree/main/docs
