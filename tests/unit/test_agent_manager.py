"""Tests for ATOLL agent manager."""

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from atoll.agent.agent_manager import AgentContext, ATOLLAgentManager
from atoll.plugins.base import ATOLLAgent


class MockAgent(ATOLLAgent):
    """Mock agent for testing."""

    async def process(self, prompt: str, context: dict):
        return {"response": "mock", "reasoning": []}

    def get_capabilities(self) -> list[str]:
        return ["test_capability"]

    def get_supported_mcp_servers(self) -> list[str]:
        return ["test_server"]


@pytest.fixture
def mock_agents_dir(tmp_path):
    """Create a mock agents directory structure."""
    agents_dir = tmp_path / "atoll_agents"
    agents_dir.mkdir()

    # Create test agent
    test_agent_dir = agents_dir / "test_agent"
    test_agent_dir.mkdir()

    # Create agent.json
    agent_metadata = {
        "name": "TestAgent",
        "version": "1.0.0",
        "module": "test_agent",
        "class": "MockAgent",
        "description": "Test agent",
    }
    with open(test_agent_dir / "agent.json", "w") as f:
        json.dump(agent_metadata, f)

    # Create agent module (placeholder)
    with open(test_agent_dir / "test_agent.py", "w") as f:
        f.write(
            """
from atoll.plugins.base import ATOLLAgent

class MockAgent(ATOLLAgent):
    async def process(self, prompt, context):
        return {"response": "test"}
    def get_capabilities(self):
        return ["test"]
    def get_supported_mcp_servers(self):
        return []
"""
        )

    return agents_dir


@pytest.mark.asyncio
async def test_agent_manager_init():
    """Test agent manager initialization."""
    agents_dir = Path("test_agents")
    manager = ATOLLAgentManager(agents_dir)

    assert manager.agents_directory == agents_dir
    assert manager.discovered_agents == {}
    assert manager.loaded_agents == {}
    assert manager.current_context is None
    assert manager.context_stack == []


@pytest.mark.asyncio
async def test_discover_agents_empty_dir(tmp_path):
    """Test discovering agents in empty directory."""
    agents_dir = tmp_path / "empty_agents"
    agents_dir.mkdir()

    manager = ATOLLAgentManager(agents_dir)
    discovered = await manager.discover_agents()

    assert discovered == {}
    assert manager.discovered_agents == {}


@pytest.mark.asyncio
async def test_discover_agents_nonexistent_dir():
    """Test discovering agents in nonexistent directory."""
    agents_dir = Path("nonexistent")

    manager = ATOLLAgentManager(agents_dir)
    discovered = await manager.discover_agents()

    assert discovered == {}


@pytest.mark.asyncio
async def test_discover_agents_with_valid_agent(mock_agents_dir):
    """Test discovering valid agents."""
    manager = ATOLLAgentManager(mock_agents_dir)
    discovered = await manager.discover_agents()

    assert "TestAgent" in discovered
    assert discovered["TestAgent"]["name"] == "TestAgent"
    assert discovered["TestAgent"]["version"] == "1.0.0"
    assert "directory" in discovered["TestAgent"]
    assert "mcp_config_path" in discovered["TestAgent"]


@pytest.mark.asyncio
async def test_switch_to_agent():
    """Test switching to agent context."""
    manager = ATOLLAgentManager(Path("test"))

    # Create mock agent context
    mock_agent = MockAgent("TestAgent", "1.0.0")
    context = AgentContext(mock_agent, "TestAgent")
    manager.loaded_agents["TestAgent"] = context

    # Switch to agent
    result = manager.switch_to_agent("TestAgent")

    assert result is True
    assert manager.current_context == context
    assert len(manager.context_stack) == 0  # No previous context


@pytest.mark.asyncio
async def test_switch_to_nonexistent_agent():
    """Test switching to nonexistent agent."""
    manager = ATOLLAgentManager(Path("test"))

    result = manager.switch_to_agent("NonexistentAgent")

    assert result is False
    assert manager.current_context is None


@pytest.mark.asyncio
async def test_go_back():
    """Test going back to previous context."""
    manager = ATOLLAgentManager(Path("test"))

    # Create mock contexts
    mock_agent1 = MockAgent("Agent1", "1.0.0")
    context1 = AgentContext(mock_agent1, "Agent1")

    mock_agent2 = MockAgent("Agent2", "1.0.0")
    context2 = AgentContext(mock_agent2, "Agent2")

    manager.loaded_agents["Agent1"] = context1
    manager.loaded_agents["Agent2"] = context2

    # Switch to agent1, then agent2
    manager.switch_to_agent("Agent1")
    manager.switch_to_agent("Agent2")

    assert manager.current_context == context2

    # Go back
    result = manager.go_back()

    assert result is True
    assert manager.current_context == context1


@pytest.mark.asyncio
async def test_go_back_at_top_level():
    """Test go back when already at top level."""
    manager = ATOLLAgentManager(Path("test"))

    result = manager.go_back()

    assert result is False
    assert manager.current_context is None


@pytest.mark.asyncio
async def test_is_top_level():
    """Test checking if at top level."""
    manager = ATOLLAgentManager(Path("test"))

    assert manager.is_top_level() is True

    # Switch to agent
    mock_agent = MockAgent("TestAgent", "1.0.0")
    context = AgentContext(mock_agent, "TestAgent")
    manager.loaded_agents["TestAgent"] = context
    manager.switch_to_agent("TestAgent")

    assert manager.is_top_level() is False


@pytest.mark.asyncio
async def test_get_available_agents_top_level():
    """Test getting available agents at top level."""
    manager = ATOLLAgentManager(Path("test"))

    # Add mock agents
    mock_agent1 = MockAgent("Agent1", "1.0.0")
    mock_agent2 = MockAgent("Agent2", "1.0.0")

    manager.loaded_agents["Agent1"] = AgentContext(mock_agent1, "Agent1")
    manager.loaded_agents["Agent2"] = AgentContext(mock_agent2, "Agent2")

    agents = manager.get_available_agents()

    assert "Agent1" in agents
    assert "Agent2" in agents
    assert len(agents) == 2


@pytest.mark.asyncio
async def test_get_available_agents_in_context():
    """Test getting available agents when in agent context."""
    manager = ATOLLAgentManager(Path("test"))

    # Create parent and child agents
    parent_agent = MockAgent("ParentAgent", "1.0.0")
    parent_context = AgentContext(parent_agent, "ParentAgent")

    child_agent = MockAgent("ChildAgent", "1.0.0")
    child_context = AgentContext(child_agent, "ChildAgent")

    parent_context.child_agents["ChildAgent"] = child_context
    manager.loaded_agents["ParentAgent"] = parent_context

    # Switch to parent
    manager.switch_to_agent("ParentAgent")

    agents = manager.get_available_agents()

    assert "ChildAgent" in agents
    assert len(agents) == 1


@pytest.mark.asyncio
async def test_get_agent_metadata():
    """Test getting agent metadata."""
    manager = ATOLLAgentManager(Path("test"))

    # Add mock metadata
    manager.discovered_agents["TestAgent"] = {
        "name": "TestAgent",
        "version": "1.0.0",
        "description": "Test agent",
    }

    metadata = manager.get_agent_metadata("TestAgent")

    assert metadata is not None
    assert metadata["name"] == "TestAgent"
    assert metadata["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_get_agent_metadata_nonexistent():
    """Test getting metadata for nonexistent agent."""
    manager = ATOLLAgentManager(Path("test"))

    metadata = manager.get_agent_metadata("NonexistentAgent")

    assert metadata is None


@pytest.mark.asyncio
async def test_shutdown_all():
    """Test shutting down all agents."""
    manager = ATOLLAgentManager(Path("test"))

    # Create mock contexts with MCP managers
    mock_agent = MockAgent("TestAgent", "1.0.0")
    mock_mcp_manager = AsyncMock()

    context = AgentContext(mock_agent, "TestAgent", mcp_manager=mock_mcp_manager)
    manager.loaded_agents["TestAgent"] = context

    await manager.shutdown_all()

    # Verify MCP manager disconnect was called
    mock_mcp_manager.disconnect_all.assert_called_once()

    # Verify cleanup
    assert len(manager.loaded_agents) == 0
    assert manager.current_context is None
    assert len(manager.context_stack) == 0
