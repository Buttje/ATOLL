"""FastAPI REST API server for ATOLL agents."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException

from ..agent.root_agent import RootAgent
from ..config.manager import ConfigManager
from ..mcp.server_manager import MCPServerManager
from ..ui.terminal import TerminalUI
from .models import (
    ChatRequest,
    ChatResponse,
    GenerateRequest,
    GenerateResponse,
    Message,
    ModelInfo,
    TagsResponse,
)
from .session import SessionManager

# Global instances
app = FastAPI(title="ATOLL Agent API", version="2.0.0")
session_manager = SessionManager()
agent: Optional[RootAgent] = None
config_manager: Optional[ConfigManager] = None


@app.on_event("startup")
async def startup_event():
    """Initialize agent on server startup."""
    global agent, config_manager

    try:
        # Load configurations
        config_manager = ConfigManager()
        config_manager.load_configs()

        # Create MCP manager
        ui = TerminalUI()
        mcp_manager = MCPServerManager(config_manager.mcp_config, ui=ui)

        # Create root agent
        agent = RootAgent(
            name="ServerAgent",
            version="2.0.0",
            llm_config=config_manager.ollama_config,
            mcp_manager=mcp_manager,
            ui=ui,
        )

        # Connect to MCP servers (with timeout)
        try:
            await asyncio.wait_for(mcp_manager.connect_all(), timeout=10.0)
            print(f"[OK] Connected to {len(mcp_manager.servers)} MCP server(s)")
        except asyncio.TimeoutError:
            print("[WARNING] MCP server connection timed out - continuing without MCP")
        except Exception as e:
            print(f"[WARNING] MCP connection failed: {e} - continuing without MCP")

        print("[OK] ATOLL Agent API started")
        print(f"  Model: {config_manager.ollama_config.model}")
    except Exception as e:
        print(f"[ERROR] Startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown."""
    if agent and agent.mcp_manager:
        await agent.mcp_manager.disconnect_all()
    print("[OK] ATOLL Agent API shutdown complete")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "ATOLL Agent API",
        "version": "2.0.0",
        "endpoints": ["/api/generate", "/api/chat", "/api/tags"],
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Ollama-compatible generate endpoint.

    Args:
        request: Generate request with prompt

    Returns:
        Generated response
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        # Process prompt through agent
        response_text = await agent.process_prompt(request.prompt)

        return GenerateResponse(
            model=request.model,
            created_at=datetime.now().isoformat(),
            response=response_text,
            done=True,
            context=request.context,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Ollama-compatible chat endpoint.

    Args:
        request: Chat request with message history

    Returns:
        Assistant response message
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        # Extract last user message
        if not request.messages:
            raise HTTPException(status_code=400, detail="No messages provided")

        last_message = request.messages[-1]
        if last_message.role != "user":
            raise HTTPException(status_code=400, detail="Last message must be from user")

        # Process through agent
        response_text = await agent.process_prompt(last_message.content)

        return ChatResponse(
            model=request.model,
            created_at=datetime.now().isoformat(),
            message=Message(role="assistant", content=response_text),
            done=True,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@app.get("/api/tags", response_model=TagsResponse)
async def list_tags():
    """Ollama-compatible tags endpoint - lists available models.

    Returns:
        List of available models (in this case, the configured agent)
    """
    if not config_manager:
        raise HTTPException(status_code=503, detail="Configuration not loaded")

    # Return the configured model as available
    return TagsResponse(
        models=[
            ModelInfo(
                name=config_manager.ollama_config.model,
                modified_at=datetime.now().isoformat(),
                size=0,  # Size not tracked for agents
            )
        ]
    )


@app.get("/api/sessions")
async def list_sessions():
    """List active conversation sessions.

    Returns:
        Session statistics
    """
    return {
        "active_sessions": session_manager.get_session_count(),
        "timeout_minutes": session_manager.timeout_minutes,
    }


@app.post("/api/sessions/cleanup")
async def cleanup_sessions():
    """Clean up expired sessions.

    Returns:
        Number of sessions cleaned up
    """
    cleaned = session_manager.cleanup_expired_sessions()
    return {"cleaned_sessions": cleaned}


async def run_server(port: int = 8000, agent_config_path: Optional[str] = None):
    """Run the FastAPI server.

    Args:
        port: Port to listen on
        agent_config_path: Path to agent configuration (optional)
    """
    # If agent_config_path provided, load that specific agent's configuration
    if agent_config_path:
        config_path = Path(agent_config_path)
        if not config_path.exists():
            print(f"Error: Agent configuration not found: {agent_config_path}")
            return

        print(f"Loading agent configuration: {agent_config_path}")
        # TODO: Load agent-specific configuration

    # Configure uvicorn
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(config)

    print(f"Starting ATOLL Agent API server on port {port}...")
    await server.serve()
