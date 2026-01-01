# Ghidra ATOLL Agent

## Overview

The Ghidra ATOLL Agent is a specialized AI agent for binary reverse engineering and analysis. It integrates with the GhidraMCP server to provide Ghidra's powerful binary analysis capabilities through natural language interaction.

## Version

**2.0.0** - Compliant with ATOLL v2.0 Specification

## Capabilities

- **Binary Analysis**: Analyze compiled executables and libraries
- **Decompilation**: Convert assembly code to high-level C-like pseudocode
- **Symbol Analysis**: Examine symbol tables and naming information
- **Reverse Engineering**: Understand program behavior and structure
- **Vulnerability Detection**: Identify potential security issues in binaries
- **Assembly Analysis**: Understand low-level assembly instructions
- **Function Analysis**: Analyze function signatures, calls, and behavior
- **Cross-Reference Analysis**: Track data and code references

## Requirements

### Prerequisites

1. **ATOLL v2.0+**: This agent requires ATOLL version 2.0 or higher
2. **Ghidra**: Installed and configured (tested with Ghidra 10.x+)
3. **GhidraMCP Server**: The MCP bridge for Ghidra must be installed and accessible
4. **Python 3.9-3.13**: Compatible Python version
5. **Ollama**: With CodeLlama model installed (`ollama pull codellama:7b`)

### Python Dependencies

See `requirements.txt` for full list:
- pydantic>=2.0.0
- aiohttp>=3.9.0
- langchain>=0.2.0
- langchain-core>=0.2.0
- langchain-ollama>=0.1.0

## Installation

### Option 1: Deploy via ATOLL Deployment Server (Recommended)

```bash
# Create ZIP package
cd /path/to/ATOLL/atoll_agents/ghidra_agent
zip -r GhidraAgent-2.0.0.zip agent.toml ghidra_agent.py requirements.txt README.md

# Deploy to server
curl -X POST http://deployment-server:8080/deploy \
  -F "file=@GhidraAgent-2.0.0.zip"

# Start agent
curl -X POST http://deployment-server:8080/start \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "GhidraAgent"}'
```

### Option 2: Manual Installation

```bash
# Copy to ATOLL agents directory
cp -r ghidra_agent ~/.atoll/agents/

# Install dependencies
cd ~/.atoll/agents/ghidra_agent
pip install -r requirements.txt

# Start ATOLL with agent discovery
atoll --agents-dir ~/.atoll/agents
```

## Configuration

### GhidraMCP Server Setup

Update the `agent.toml` file with your GhidraMCP server location:

```toml
[mcp_servers.ghidramcp]
type = "stdio"
command = "python"
args = [
    "/path/to/GhidraMCP/bridge_mcp_ghidra.py",
    "--ghidra-server",
    "http://127.0.0.1:8080"
]
```

### LLM Configuration

The agent uses CodeLlama by default for optimized code analysis:

```toml
[llm]
model = "codellama:7b"
temperature = 0.3
```

You can customize this in `agent.toml` or override at runtime.

## Usage Examples

### Example 1: Decompile a Function

```
User: Decompile the main function at address 0x401000
```

The agent will:
1. Identify the decompilation request
2. Use GhidraMCP to access Ghidra
3. Decompile the function at the specified address
4. Explain the function's behavior

### Example 2: Security Analysis

```
User: Are there any buffer overflow vulnerabilities in function FUN_00401234?
```

The agent will:
1. Analyze the function for security issues
2. Check for unsafe string operations
3. Identify potential vulnerabilities
4. Provide recommendations

### Example 3: Symbol Analysis

```
User: Show me all cross-references to the strcmp function
```

The agent will:
1. Search for strcmp in the symbol table
2. Find all call sites
3. Display cross-references
4. Explain usage patterns

## Integration with ATOLL

### Agent Selection

The agent is automatically selected when prompts contain keywords like:
- decompile, disassemble, reverse engineer
- binary, executable, assembly
- function names, memory addresses (0x...)
- vulnerability, security, exploit

### Confidence Scoring

The agent calculates a confidence score (0.0-1.0) based on:
- **Primary keywords**: decompile, ghidra, binary analysis (high weight)
- **Secondary keywords**: symbol, xref, vulnerability (medium weight)
- **GhidraMCP availability**: Boosts score if server connected
- **Address patterns**: Presence of hex addresses
- **Function patterns**: Common function naming conventions

Score ranges:
- 0.8-1.0: Excellent match (highly recommended)
- 0.5-0.8: Good match (recommended)
- 0.2-0.5: Moderate relevance
- 0.0-0.2: Low relevance

## Architecture

```
┌──────────────────────────────────────┐
│         ATOLL Main System            │
│  ┌────────────────────────────────┐  │
│  │    Agent Manager               │  │
│  │  - Agent Discovery             │  │
│  │  - Agent Selection (scoring)   │  │
│  │  - Routing                     │  │
│  └────────────┬───────────────────┘  │
│               │                       │
│  ┌────────────▼───────────────────┐  │
│  │    GhidraAgent                 │  │
│  │  - Specialized reasoning       │  │
│  │  - CodeLlama LLM               │  │
│  │  - Binary analysis expertise   │  │
│  └────────────┬───────────────────┘  │
│               │                       │
│  ┌────────────▼───────────────────┐  │
│  │    MCP Server Manager          │  │
│  │  - Tool registry               │  │
│  │  - Execution                   │  │
│  └────────────┬───────────────────┘  │
└───────────────┼───────────────────────┘
                │
┌───────────────▼───────────────────────┐
│         GhidraMCP Server              │
│  - Ghidra Bridge                      │
│  - Tool implementations               │
│  - Binary analysis functions          │
└───────────────┬───────────────────────┘
                │
┌───────────────▼───────────────────────┐
│            Ghidra                     │
│  - Decompiler                         │
│  - Disassembler                       │
│  - Analysis engines                   │
└───────────────────────────────────────┘
```

## Troubleshooting

### Agent Not Selected

**Problem**: Prompt doesn't trigger the Ghidra agent

**Solution**:
- Use explicit keywords: "decompile", "ghidra", "binary analysis"
- Include memory addresses: "analyze function at 0x401000"
- Check agent is discovered: `atoll agents list`

### GhidraMCP Connection Failed

**Problem**: Cannot connect to GhidraMCP server

**Solution**:
1. Verify Ghidra is running in headless mode
2. Check GhidraMCP server is accessible
3. Update `agent.toml` with correct path and URL
4. Test connection: `python bridge_mcp_ghidra.py --test`

### Low Confidence Score

**Problem**: Agent selected but has low confidence

**Solution**:
- Make prompts more specific to binary analysis
- Include function names or addresses
- Mention "Ghidra" or "decompile" explicitly

### Memory Issues

**Problem**: Agent crashes or runs out of memory

**Solution**:
- Increase memory limit in `agent.toml`:
  ```toml
  [resources]
  memory_limit = "8GB"
  ```
- Reduce concurrent requests:
  ```toml
  max_concurrent_requests = 2
  ```

## Development

### Running Tests

```bash
pytest tests/test_ghidra_agent.py -v
```

### Code Structure

```
ghidra_agent/
├── agent.toml           # TOML configuration
├── ghidra_agent.py      # Agent implementation
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── __pycache__/        # Python cache (excluded from ZIP)
```

### Extending the Agent

To add custom capabilities:

1. Update `agent.toml` capabilities list
2. Modify `can_handle()` to recognize new patterns
3. Update `process()` to handle new request types
4. Add corresponding GhidraMCP tools if needed

## Support

- **Documentation**: [ATOLL v2.0 Docs](https://github.com/Buttje/ATOLL)
- **Issues**: [GitHub Issues](https://github.com/Buttje/ATOLL/issues)
- **MCP Protocol**: [Model Context Protocol](https://spec.modelcontextprotocol.io/)
- **Ghidra**: [Ghidra Documentation](https://ghidra-sre.org/)

## License

MIT License - See LICENSE file

## Changelog

### v2.0.0 (2026-01-01)
- Updated to ATOLL v2.0 specification
- Migrated from agent.json to agent.toml format
- Enhanced confidence scoring algorithm
- Added comprehensive reasoning steps
- Improved security analysis capabilities
- Added function pattern recognition
- Updated to use CodeLlama for code analysis
- Added deployment server support

### v1.0.0 (2025-12-15)
- Initial release
- Basic binary analysis capabilities
- GhidraMCP integration
- Function decompilation support
