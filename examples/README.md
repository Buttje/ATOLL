# Configuration Examples

This directory contains example configuration files for ATOLL.

## Files

### .ollamaConfig.example.json

Example configuration for connecting to Ollama:

```json
{
  "base_url": "http://localhost",
  "port": 11434,
  "model": "llama2",
  "request_timeout": 30,
  "max_tokens": 2048,
  "temperature": 0.7,
  "top_p": 0.9
}
```

**Options:**
- `base_url`: Ollama server URL
- `port`: Ollama server port (default: 11434)
- `model`: LLM model name (e.g., llama2, mistral, codellama)
- `request_timeout`: Request timeout in seconds
- `max_tokens`: Maximum tokens for generation
- `temperature`: Sampling temperature (0.0-1.0)
- `top_p`: Nucleus sampling parameter

### .mcpConfig.example.json

Example configuration for MCP servers with different transports:

**Stdio Transport** (local Python scripts):
```json
{
  "servers": {
    "example-stdio": {
      "transport": "stdio",
      "command": "python",
      "args": ["path/to/your/mcp_server.py"],
      "timeoutSeconds": 30,
      "env": {
        "ENV_VAR": "value"
      }
    }
  }
}
```

**HTTP Transport**:
```json
{
  "servers": {
    "example-http": {
      "transport": "streamable_http",
      "url": "http://localhost:8080",
      "timeoutSeconds": 30
    }
  }
}
```

**Ghidra Integration**:
```json
{
  "servers": {
    "ghidra": {
      "transport": "stdio",
      "command": "python",
      "args": ["${HOME}/ghidra_scripts/ghidra_mcp_server.py"],
      "env": {
        "GHIDRA_HOME": "${HOME}/ghidra_10.4_PUBLIC",
        "PYTHONPATH": "${HOME}/ghidra_scripts"
      },
      "timeoutSeconds": 30
    }
  }
}
```

## Usage

1. Copy the example files to your project root:
   ```bash
   cp examples/.ollamaConfig.example.json .ollamaConfig.json
   cp examples/.mcpConfig.example.json .mcpConfig.json
   ```

2. Edit the files to match your environment:
   - Update paths to match your system
   - Change model names as needed
   - Configure MCP servers you want to use

3. Environment variables in paths are supported:
   - `${HOME}` - User home directory
   - `${USER}` - Username
   - Any other environment variable: `${VAR_NAME}`

## Notes

- Configuration files in the project root (`.ollamaConfig.json`, `.mcpConfig.json`) are ignored by git
- Start with an empty servers object in `.mcpConfig.json` if you don't have MCP servers yet
- Make sure Ollama is running: `ollama serve`
- Pull required models: `ollama pull llama2`
