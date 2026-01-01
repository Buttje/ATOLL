"""Tests for plugin system."""

import json
import tempfile
from pathlib import Path

import pytest

from atoll.plugins.base import ATOLLAgent
from atoll.plugins.manager import PluginManager


class MockAgent(ATOLLAgent):
    """Mock agent for testing."""

    async def process(self, prompt: str, context: dict) -> dict:
        return {"response": "Mock response", "reasoning": []}

    def get_capabilities(self) -> list[str]:
        return ["test_capability"]

    def get_supported_mcp_servers(self) -> list[str]:
        return ["test_server"]


class TestATOLLAgentBase:
    """Tests for ATOLLAgent base class."""

    def test_initialization(self):
        """Test agent initialization."""
        agent = MockAgent("TestAgent", "1.0.0")

        assert agent.name == "TestAgent"
        assert agent.version == "1.0.0"
        assert agent._metadata == {}

    def test_set_and_get_metadata(self):
        """Test metadata operations."""
        agent = MockAgent("TestAgent", "1.0.0")

        agent.set_metadata("key1", "value1")
        agent.set_metadata("key2", 42)

        assert agent.get_metadata("key1") == "value1"
        assert agent.get_metadata("key2") == 42
        assert agent.get_metadata("nonexistent", "default") == "default"

    def test_get_all_metadata(self):
        """Test getting all metadata."""
        agent = MockAgent("TestAgent", "1.0.0")

        agent.set_metadata("key1", "value1")
        agent.set_metadata("key2", "value2")

        metadata = agent.get_all_metadata()
        assert len(metadata) == 2
        assert metadata["key1"] == "value1"
        assert metadata["key2"] == "value2"

    def test_get_tools_default(self):
        """Test default get_tools returns empty list."""
        agent = MockAgent("TestAgent", "1.0.0")

        tools = agent.get_tools()
        assert tools == []

    def test_can_handle_default(self):
        """Test default can_handle returns 0.0."""
        agent = MockAgent("TestAgent", "1.0.0")

        score = agent.can_handle("test prompt", {})
        assert score == 0.0

    def test_string_representation(self):
        """Test string representations."""
        agent = MockAgent("TestAgent", "1.0.0")

        assert str(agent) == "TestAgent v1.0.0"
        assert "TestAgent" in repr(agent)
        assert "1.0.0" in repr(agent)


class TestPluginManager:
    """Tests for PluginManager."""

    def test_initialization_default(self):
        """Test initialization with default directory."""
        manager = PluginManager()

        assert manager.plugins_dir == Path.cwd() / "atoll_agents"
        assert manager.agents == {}
        assert manager.metadata == {}

    def test_initialization_custom_dir(self):
        """Test initialization with custom directory."""
        custom_dir = Path("/tmp/custom_plugins")
        manager = PluginManager(custom_dir)

        assert manager.plugins_dir == custom_dir

    def test_discover_plugins_no_directory(self):
        """Test plugin discovery when directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugins_dir = Path(tmpdir) / "nonexistent"
            manager = PluginManager(plugins_dir)

            count = manager.discover_plugins()
            assert count == 0

    def test_discover_plugins_empty_directory(self):
        """Test plugin discovery in empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PluginManager(Path(tmpdir))

            count = manager.discover_plugins()
            assert count == 0

    def test_load_plugin_missing_metadata(self):
        """Test loading plugin without agent.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugins_dir = Path(tmpdir)
            agent_dir = plugins_dir / "test_agent"
            agent_dir.mkdir()

            manager = PluginManager(plugins_dir)
            result = manager._load_plugin(agent_dir)

            assert result is False

    def test_load_plugin_invalid_metadata(self):
        """Test loading plugin with invalid metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugins_dir = Path(tmpdir)
            agent_dir = plugins_dir / "test_agent"
            agent_dir.mkdir()

            # Create invalid metadata (missing required fields)
            metadata_file = agent_dir / "agent.json"
            metadata_file.write_text('{"name": "TestAgent"}')

            manager = PluginManager(plugins_dir)
            result = manager._load_plugin(agent_dir)

            assert result is False

    def test_load_plugin_missing_module(self):
        """Test loading plugin with missing module file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugins_dir = Path(tmpdir)
            agent_dir = plugins_dir / "test_agent"
            agent_dir.mkdir()

            # Create valid metadata
            metadata = {
                "name": "TestAgent",
                "version": "1.0.0",
                "module": "test_module",
                "class": "TestAgentClass",
            }
            metadata_file = agent_dir / "agent.json"
            metadata_file.write_text(json.dumps(metadata))

            manager = PluginManager(plugins_dir)
            result = manager._load_plugin(agent_dir)

            assert result is False

    def test_get_agent(self):
        """Test getting agent by name."""
        manager = PluginManager()
        agent = MockAgent("TestAgent", "1.0.0")
        manager.agents["TestAgent"] = agent

        retrieved = manager.get_agent("TestAgent")
        assert retrieved == agent

        nonexistent = manager.get_agent("NonExistent")
        assert nonexistent is None

    def test_get_all_agents(self):
        """Test getting all agents."""
        manager = PluginManager()
        agent1 = MockAgent("Agent1", "1.0.0")
        agent2 = MockAgent("Agent2", "2.0.0")

        manager.agents["Agent1"] = agent1
        manager.agents["Agent2"] = agent2

        all_agents = manager.get_all_agents()
        assert len(all_agents) == 2
        assert "Agent1" in all_agents
        assert "Agent2" in all_agents

    def test_get_agent_metadata(self):
        """Test getting agent metadata."""
        manager = PluginManager()
        metadata = {"name": "TestAgent", "version": "1.0.0"}
        manager.metadata["TestAgent"] = metadata

        retrieved = manager.get_agent_metadata("TestAgent")
        assert retrieved == metadata

        nonexistent = manager.get_agent_metadata("NonExistent")
        assert nonexistent is None

    def test_get_agents_for_capability(self):
        """Test getting agents by capability."""
        manager = PluginManager()

        # Create agents with different capabilities
        class Agent1(MockAgent):
            def get_capabilities(self):
                return ["cap1", "cap2"]

        class Agent2(MockAgent):
            def get_capabilities(self):
                return ["cap2", "cap3"]

        agent1 = Agent1("Agent1", "1.0.0")
        agent2 = Agent2("Agent2", "1.0.0")

        manager.agents["Agent1"] = agent1
        manager.agents["Agent2"] = agent2

        # Test cap1 (only Agent1)
        agents = manager.get_agents_for_capability("cap1")
        assert len(agents) == 1
        assert agents[0].name == "Agent1"

        # Test cap2 (both agents)
        agents = manager.get_agents_for_capability("cap2")
        assert len(agents) == 2

        # Test nonexistent capability
        agents = manager.get_agents_for_capability("nonexistent")
        assert len(agents) == 0

    def test_get_agents_for_mcp_server(self):
        """Test getting agents by MCP server."""
        manager = PluginManager()

        class Agent1(MockAgent):
            def get_supported_mcp_servers(self):
                return ["server1", "server2"]

        class Agent2(MockAgent):
            def get_supported_mcp_servers(self):
                return ["server2", "server3"]

        agent1 = Agent1("Agent1", "1.0.0")
        agent2 = Agent2("Agent2", "1.0.0")

        manager.agents["Agent1"] = agent1
        manager.agents["Agent2"] = agent2

        # Test server1 (only Agent1)
        agents = manager.get_agents_for_mcp_server("server1")
        assert len(agents) == 1
        assert agents[0].name == "Agent1"

        # Test server2 (both agents)
        agents = manager.get_agents_for_mcp_server("server2")
        assert len(agents) == 2

    def test_select_agent_no_agents(self):
        """Test agent selection with no agents loaded."""
        manager = PluginManager()

        agent = manager.select_agent("test prompt", {})
        assert agent is None

    def test_select_agent_by_score(self):
        """Test agent selection by confidence score."""
        manager = PluginManager()

        class Agent1(MockAgent):
            def can_handle(self, prompt, context):
                return 0.3

        class Agent2(MockAgent):
            def can_handle(self, prompt, context):
                return 0.7

        agent1 = Agent1("Agent1", "1.0.0")
        agent2 = Agent2("Agent2", "1.0.0")

        manager.agents["Agent1"] = agent1
        manager.agents["Agent2"] = agent2

        # Agent2 should be selected (higher score)
        selected = manager.select_agent("test", {})
        assert selected.name == "Agent2"

    def test_select_agent_no_suitable(self):
        """Test agent selection when no agent can handle."""
        manager = PluginManager()

        class Agent1(MockAgent):
            def can_handle(self, prompt, context):
                return 0.0  # Can't handle

        agent1 = Agent1("Agent1", "1.0.0")
        manager.agents["Agent1"] = agent1

        selected = manager.select_agent("test", {})
        assert selected is None

    def test_list_plugins(self):
        """Test listing all plugins."""
        manager = PluginManager()

        agent = MockAgent("TestAgent", "1.0.0")
        manager.agents["TestAgent"] = agent
        manager.metadata["TestAgent"] = {
            "description": "Test agent description",
            "version": "1.0.0",
        }

        plugins = manager.list_plugins()

        assert len(plugins) == 1
        assert plugins[0]["name"] == "TestAgent"
        assert plugins[0]["version"] == "1.0.0"
        assert "description" in plugins[0]
        assert "capabilities" in plugins[0]
        assert "supported_servers" in plugins[0]


@pytest.mark.asyncio
async def test_mock_agent_process():
    """Test MockAgent process method."""
    agent = MockAgent("Test", "1.0.0")

    result = await agent.process("test prompt", {})

    assert "response" in result
    assert "reasoning" in result
