# Reasoning Engine Architecture

## Overview

The Reasoning Engine has been refactored to use **LLM-based capability matching** instead of simple string pattern matching. This provides intelligent analysis of user requests against available MCP servers and ATOLL agents.

## Key Changes

### Before (Pattern Matching)
```python
# Simple string matching
if "find" in prompt.lower() and "implementation" in prompt.lower():
    reasoning_steps.append("Detected code search query")
```

### After (LLM-Based Analysis)
```python
# LLM analyzes capabilities and matches to user intent
analysis_prompt = self._build_analysis_prompt(
    prompt, mcp_capabilities, agent_capabilities, tools
)
analysis = await self.llm.invoke(analysis_prompt)
reasoning_steps = self._parse_analysis(analysis)
```

## Architecture

### ReasoningEngine Class

The `ReasoningEngine` now requires:
- **LLM instance**: For intelligent capability matching
- **MCPServerManager**: To discover MCP server capabilities
- **ATOLLAgentManager**: To discover ATOLL agent capabilities

### Initialization Flow

1. **Agent Creation** (`OllamaMCPAgent.__init__`):
   ```python
   self.reasoning_engine = ReasoningEngine(self.llm)
   self.reasoning_engine.set_mcp_manager(mcp_manager)
   ```

2. **After Agent Manager Load** (`main.py`):
   ```python
   self.agent_manager = ATOLLAgentManager(agents_dir)
   await self.agent_manager.load_all_agents()

   # Wire up agent manager to reasoning engine
   self.agent.agent_manager = self.agent_manager
   self.agent.reasoning_engine.set_agent_manager(self.agent_manager)
   ```

### Analysis Process

When a user submits a prompt:

1. **Gather MCP Capabilities** (`_gather_mcp_capabilities()`):
   - Queries all registered MCP servers
   - Collects tool names, descriptions, and schemas
   - Organizes by server name

2. **Gather Agent Capabilities** (`_gather_agent_capabilities()`):
   - Queries all loaded ATOLL agents
   - Collects agent capabilities via `get_capabilities()`
   - Collects supported MCP servers via `get_supported_mcp_servers()`
   - Collects agent-specific tools

3. **Build Analysis Prompt** (`_build_analysis_prompt()`):
   - Formats user request
   - Lists available MCP servers with sample tools
   - Lists available ATOLL agents with capabilities
   - Asks LLM to match capabilities to request

4. **LLM Analysis**:
   - LLM receives structured capability information
   - Determines which tools/agents are relevant
   - Explains reasoning
   - Provides confidence level

5. **Parse and Display** (`_parse_analysis()`):
   - Extracts reasoning steps from LLM response
   - Formats as bullet points
   - Limits to 5 most relevant steps
   - Displays in verbose output

## Example Analysis

### User Request
```
"Decompile the main function in this binary"
```

### Capabilities Provided to LLM
```
AVAILABLE MCP SERVERS:
ghidramcp: 28 tools
  - decompile_function: Decompile a function by name
  - list_functions: List all functions
  - get_current_function: Get currently selected function

AVAILABLE ATOLL AGENTS:
ghidra_agent v1.0.0:
  Capabilities: binary_analysis, decompilation, reverse_engineering
  MCP servers: ghidramcp
```

### LLM Analysis Output
```
→ MCP server 'ghidramcp' has decompile_function tool matching request
→ ATOLL agent 'ghidra_agent' specializes in decompilation tasks
→ Agent provides binary_analysis capability suitable for this operation
→ High confidence match
```

## Benefits

1. **Intelligent Matching**: LLM understands semantic similarity, not just keywords
2. **Context-Aware**: Considers full capability descriptions, not isolated terms
3. **Extensible**: Automatically adapts as new MCP servers/agents are added
4. **Explainable**: Provides clear reasoning for tool selection
5. **Confidence Levels**: LLM can indicate certainty in capability match

## Verbose Output

The reasoning is displayed in the verbose output section:

```
[1/5] Starting prompt analysis...
→ MCP server 'ghidramcp' has decompile_function tool matching request
→ ATOLL agent 'ghidra_agent' specializes in decompilation tasks
→ High confidence match
[2/5] Reasoning engine generated 3 insights
```

## Fallback Behavior

If LLM is not configured or fails:
```python
reasoning_steps.append("⚠ Reasoning engine: LLM not configured, using fallback analysis")
```

The agent will proceed with direct tool execution without reasoning analysis.

## Testing

New test file: `tests/unit/test_reasoning_new.py`

Tests cover:
- LLM-based analysis
- MCP capability gathering
- Agent capability gathering
- Prompt building
- Response parsing
- Fallback behavior

## Migration Notes

### Breaking Changes
- `ReasoningEngine.__init__()` now accepts optional `llm` parameter
- `analyze()` is now async (returns awaitable)
- Removed rule-based pattern matching methods

### Backward Compatibility
- If LLM not provided, falls back gracefully
- Existing code continues to work with fallback warnings

## Future Enhancements

1. **Agent Query Interface**: Allow agents to provide `can_handle()` scores for prompts
2. **Tool Ranking**: Use LLM to rank tools by relevance
3. **Multi-Step Planning**: LLM suggests tool execution sequence
4. **Learning**: Track successful capability matches for future reference
5. **Caching**: Cache capability analysis for repeated queries
