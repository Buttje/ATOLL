"""Pytest configuration and fixtures."""

import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock

from ollama_mcp_agent.config.models import OllamaConfig, MCPConfig, MCPServerConfig
from ollama_mcp_agent.mcp.client import MCPClient
from ollama_mcp_agent.ui.terminal import TerminalUI


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def ollama_config():
    """Create a test Ollama configuration."""
    return OllamaConfig(
        base_url="http://localhost",
        port=11434,
        model="test-model",
        request_timeout=10,
        max_tokens=1024,
    )


@pytest.fixture
def mcp_config():
    """Create a test MCP configuration."""
    return MCPConfig(
        servers={
            "test-server": MCPServerConfig(
                transport="stdio",
                command="python",
                args=["test_server.py"],
                timeoutSeconds=10,
            )
        }
    )


@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client."""
    client = Mock(spec=MCPClient)
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.call_tool = AsyncMock(return_value={"result": "success"})
    client.list_tools = AsyncMock(return_value=[
        {"name": "test_tool", "description": "A test tool"}
    ])
    return client


@pytest.fixture
def mock_ui():
    """Create a mock terminal UI."""
    ui = Mock(spec=TerminalUI)
    ui.display_user_input = Mock()
    ui.display_reasoning = Mock()
    ui.display_response = Mock()
    ui.display_error = Mock()
    ui.display_info = Mock()
    return ui


@pytest.fixture
def test_data_dir():
    """Get the test data directory."""
    return Path(__file__).parent / "fixtures"