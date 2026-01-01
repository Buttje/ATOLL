# REST API Server Mode

ATOLL agents can run as REST API servers, enabling distributed deployment and integration with other services.

## Quick Start

Start an agent in server mode:

```bash
python -m atoll --server --port 8100
```

Or with a specific agent configuration:

```bash
python -m atoll --server --port 8100 --agent path/to/agent.toml
```

The server will start on `http://0.0.0.0:PORT` and provide Ollama-compatible endpoints.

## API Endpoints

### Health Check

```bash
GET /health
```

Returns server health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-01T12:00:00.000000"
}
```

### List Available Models

```bash
GET /api/tags
```

Ollama-compatible endpoint that lists available models (returns the configured agent).

**Response:**
```json
{
  "models": [
    {
      "name": "llama2",
      "modified_at": "2026-01-01T12:00:00.000000",
      "size": 0
    }
  ]
}
```

### Generate Response (Simple)

```bash
POST /api/generate
Content-Type: application/json

{
  "model": "llama2",
  "prompt": "What is the capital of France?",
  "stream": false
}
```

**Response:**
```json
{
  "model": "llama2",
  "created_at": "2026-01-01T12:00:00.000000",
  "response": "The capital of France is Paris.",
  "done": true,
  "context": null
}
```

### Chat (Conversation)

```bash
POST /api/chat
Content-Type: application/json

{
  "model": "llama2",
  "messages": [
    {"role": "user", "content": "What is the capital of France?"}
  ],
  "stream": false
}
```

**Response:**
```json
{
  "model": "llama2",
  "created_at": "2026-01-01T12:00:00.000000",
  "message": {
    "role": "assistant",
    "content": "The capital of France is Paris."
  },
  "done": true
}
```

### Session Management

```bash
GET /api/sessions
```

Returns active session statistics.

**Response:**
```json
{
  "active_sessions": 5,
  "timeout_minutes": 30
}
```

```bash
POST /api/sessions/cleanup
```

Manually trigger cleanup of expired sessions.

**Response:**
```json
{
  "cleaned_sessions": 3
}
```

## Deployment Server Integration

The deployment server automatically starts agents in REST API server mode:

1. Place agent configurations in the configured agents directory (default: `atoll_agents/`)
2. Start ATOLL with deployment server enabled
3. Agents are discovered and automatically started with allocated ports (starting from 8100)

Example agent directory structure:
```
atoll_agents/
├── ghidra_agent/
│   └── agent.toml  # or agent.json
└── custom_agent/
    └── agent.toml
```

When ATOLL starts, you'll see:
```
[OK] ATOLL deployment server started
  Local Server: localhost (running)
    Agents:
    ● GhidraAgent (Port: 8100) - running
    ● CustomAgent (Port: 8101) - running
```

## Client Examples

### Python (using requests)

```python
import requests

# Health check
response = requests.get("http://localhost:8100/health")
print(response.json())

# Generate response
response = requests.post(
    "http://localhost:8100/api/generate",
    json={
        "model": "llama2",
        "prompt": "Explain quantum computing",
        "stream": False
    }
)
print(response.json()["response"])

# Chat conversation
response = requests.post(
    "http://localhost:8100/api/chat",
    json={
        "model": "llama2",
        "messages": [
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi! How can I help you?"},
            {"role": "user", "content": "What's the weather?"}
        ],
        "stream": False
    }
)
print(response.json()["message"]["content"])
```

### cURL

```bash
# Health check
curl http://localhost:8100/health

# Generate
curl -X POST http://localhost:8100/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama2",
    "prompt": "Explain AI",
    "stream": false
  }'

# Chat
curl -X POST http://localhost:8100/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama2",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "stream": false
  }'
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│           Deployment Server                     │
│  ┌───────────────────────────────────────────┐  │
│  │  Agent Discovery & Lifecycle Management   │  │
│  └───────────────────────────────────────────┘  │
│                      ↓                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Agent 1  │  │ Agent 2  │  │ Agent N  │     │
│  │ :8100    │  │ :8101    │  │ :810N    │     │
│  └──────────┘  └──────────┘  └──────────┘     │
└─────────────────────────────────────────────────┘
         ↑                ↑                ↑
         │                │                │
    REST API         REST API         REST API
         │                │                │
    ┌─────────────────────────────────────────┐
    │       HTTP Clients / Parent Agent       │
    └─────────────────────────────────────────┘
```

## Features

- **Ollama API Compatibility**: Drop-in replacement for Ollama servers
- **Stateless Design**: Each request is independent
- **Session Management**: Optional session tracking for conversation context
- **Health Monitoring**: Built-in health checks for monitoring
- **Auto-Start**: Deployment server automatically starts agents
- **Port Management**: Automatic port allocation (8100+)
- **Graceful Shutdown**: Proper cleanup of connections and processes

## Configuration

Server mode respects ATOLL configuration files:
- Ollama configuration: `~/.ollama_server/.ollama_config.json`
- MCP servers: `mcp.json` in working directory
- Deployment config: `~/.atoll/deployment_servers.json`

## Error Handling

The server handles errors gracefully:

- **503 Service Unavailable**: Agent not initialized
- **500 Internal Server Error**: Generation/chat failed
- **400 Bad Request**: Invalid request format

Example error response:
```json
{
  "detail": "Agent not initialized"
}
```

## Performance

- Response times depend on:
  - LLM model size and complexity
  - Hardware (CPU/GPU)
  - Prompt length
  - MCP tool execution time
- Target: <5 seconds for typical prompts (95th percentile)
- Concurrent requests supported via FastAPI async handlers

## Limitations

- Streaming responses not yet implemented (stream=false only)
- Sessions auto-expire after 30 minutes of inactivity
- No authentication/authorization (intended for internal networks)
- Single agent per server instance

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
netstat -ano | findstr :8100  # Windows
lsof -i :8100                  # Linux/Mac

# Use a different port
python -m atoll --server --port 8200
```

### Agent Won't Start

Check logs for:
- Ollama server connectivity
- MCP server configuration errors
- Port conflicts

### Startup Timeout

MCP server connections have a 10-second timeout. If MCP servers are slow or unavailable, the agent will start without MCP support with a warning.

## Next Steps

- [Deployment Server Documentation](DEPLOYMENT_SERVER.md)
- [MCP Integration Guide](../README.md#mcp-integration)
- [Agent Configuration](../atoll_agents/README.md)
