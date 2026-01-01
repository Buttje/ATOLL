"""Acceptance tests for Hierarchical Agent System (FR-H001 to FR-H012).

Test IDs: TEST-H001 through TEST-H012
Requirements: FR-H001 through FR-H012
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from atoll.agent.root_agent import RootAgent
from atoll.config.models import (
    MCPConfig,
    OllamaConfig,
    TOMLAgentConfig,
    TOMLAgentLLMConfig,
)
from atoll.mcp.server_manager import MCPServerManager
from atoll.plugins.base import ATOLLAgent
from atoll.ui.terminal import TerminalUI


class TestRootAgentInitialization:
    """TEST-H001: Root agent initialization with ATOLLAgent base class."""

    @pytest.mark.asyncio
    async def test_root_agent_inherits_from_atoll_agent(self):
        """Verify root agent inherits from ATOLLAgent base class."""
        # GIVEN: Configuration objects
        ollama_config = OllamaConfig(
            base_url="http://localhost",
            port=11434,
            model="llama2",
            temperature=0.7,
        )
        mcp_config = MCPConfig()
        mcp_manager = MCPServerManager(mcp_config)
        ui = TerminalUI()

        # WHEN: Root agent is created
        root_agent = RootAgent(
            name="Main",
            version="2.0.0",
            llm_config=ollama_config,
            mcp_manager=mcp_manager,
            ui=ui,
        )

        # THEN: Root agent is instance of ATOLLAgent
        assert isinstance(root_agent, ATOLLAgent)
        assert root_agent.name == "Main"
        assert root_agent.version == "2.0.0"
        assert root_agent.llm_config == ollama_config
        assert root_agent.mcp_manager == mcp_manager
        assert root_agent.ui == ui

    @pytest.mark.asyncio
    async def test_root_agent_has_llm_initialized(self):
        """Verify root agent has LLM properly initialized."""
        # GIVEN: Configuration
        ollama_config = OllamaConfig(
            base_url="http://localhost",
            port=11434,
            model="llama2",
        )
        ui = TerminalUI()

        # WHEN: Root agent is created with LLM config
        root_agent = RootAgent(
            name="Main",
            version="2.0.0",
            llm_config=ollama_config,
            mcp_manager=None,
            ui=ui,
        )

        # THEN: LLM is initialized
        assert root_agent.llm is not None
        assert hasattr(root_agent.llm, "model")

    @pytest.mark.asyncio
    async def test_root_agent_has_isolated_conversation_memory(self):
        """Verify root agent has its own conversation memory."""
        # GIVEN: Root agent
        ollama_config = OllamaConfig()
        root_agent = RootAgent(
            name="Main",
            version="2.0.0",
            llm_config=ollama_config,
        )

        # THEN: Conversation memory exists and is empty
        assert hasattr(root_agent, "conversation_memory")
        assert isinstance(root_agent.conversation_memory, list)
        assert len(root_agent.conversation_memory) == 0


class TestATOLLAgentBaseLLMIntegration:
    """TEST-H002: ATOLLAgent base class with LLM integration."""

    @pytest.mark.asyncio
    async def test_atoll_agent_has_llm_attributes(self):
        """Verify ATOLLAgent has LLM-related attributes."""

        # GIVEN: Mock agent class
        class TestAgent(ATOLLAgent):
            async def process(self, prompt, context):
                return {"response": "test"}

        ollama_config = OllamaConfig()

        # WHEN: Agent is instantiated with LLM config
        agent = TestAgent(
            name="TestAgent",
            version="1.0.0",
            llm_config=ollama_config,
        )

        # THEN: Agent has LLM attributes
        assert hasattr(agent, "llm")
        assert hasattr(agent, "llm_config")
        assert hasattr(agent, "mcp_manager")
        assert hasattr(agent, "ui")
        assert hasattr(agent, "conversation_memory")
        assert hasattr(agent, "tools")
        assert hasattr(agent, "reasoning_engine")

    @pytest.mark.asyncio
    async def test_atoll_agent_process_prompt_method(self):
        """Verify ATOLLAgent has process_prompt() method."""

        # GIVEN: Agent with LLM
        class TestAgent(ATOLLAgent):
            async def process(self, prompt, context):
                return {"response": "test"}

        ollama_config = OllamaConfig(model="llama2")
        agent = TestAgent(
            name="TestAgent",
            version="1.0.0",
            llm_config=ollama_config,
        )

        # THEN: process_prompt method exists
        assert hasattr(agent, "process_prompt")
        assert callable(agent.process_prompt)

    @pytest.mark.asyncio
    async def test_atoll_agent_can_change_model(self):
        """Verify ATOLLAgent can change LLM model dynamically."""

        # GIVEN: Agent with initial model
        class TestAgent(ATOLLAgent):
            async def process(self, prompt, context):
                return {"response": "test"}

        ollama_config = OllamaConfig(model="llama2")
        agent = TestAgent(
            name="TestAgent",
            version="1.0.0",
            llm_config=ollama_config,
        )
        initial_model = agent.llm_config.model

        # WHEN: Model is changed
        result = agent.change_model("codellama:7b")

        # THEN: Model is updated
        assert result is True
        assert agent.llm_config.model == "codellama:7b"
        assert agent.llm_config.model != initial_model


class TestPerAgentLLMConfiguration:
    """TEST-H003: Per-agent LLM configuration with TOML."""

    def test_toml_agent_llm_config_structure(self):
        """Verify TOMLAgentLLMConfig has required fields."""
        # GIVEN/WHEN: TOMLAgentLLMConfig is created
        llm_config = TOMLAgentLLMConfig(
            model="codellama:7b",
            temperature=0.3,
            system_prompt="Custom prompt",
        )

        # THEN: All fields are accessible
        assert llm_config.model == "codellama:7b"
        assert llm_config.temperature == 0.3
        assert llm_config.system_prompt == "Custom prompt"
        assert llm_config.top_p is None  # Optional field
        assert llm_config.max_tokens is None

    def test_toml_llm_config_merges_with_parent(self):
        """Verify agent LLM config merges with parent config."""
        # GIVEN: Parent and agent LLM configs
        parent_config = OllamaConfig(
            base_url="http://localhost",
            port=11434,
            model="llama2",
            temperature=0.7,
            max_tokens=2048,
        )
        agent_llm_config = TOMLAgentLLMConfig(
            model="codellama:7b",  # Override
            temperature=0.3,  # Override
            # max_tokens not specified - should use parent
        )

        # WHEN: Configs are merged
        merged = agent_llm_config.merge_with_parent(parent_config)

        # THEN: Agent overrides take precedence, parent fills gaps
        assert merged.model == "codellama:7b"  # From agent
        assert merged.temperature == 0.3  # From agent
        assert merged.max_tokens == 2048  # From parent
        assert merged.base_url == "http://localhost"  # Always from parent
        assert merged.port == 11434  # Always from parent

    def test_toml_agent_config_loads_from_dict(self):
        """Verify TOMLAgentConfig loads from dictionary."""
        # GIVEN: TOML-like dictionary
        config_dict = {
            "agent": {
                "name": "GhidraAgent",
                "version": "1.0.0",
                "description": "Binary analysis agent",
                "capabilities": ["decompilation", "analysis"],
            },
            "llm": {
                "model": "codellama:7b",
                "temperature": 0.3,
            },
            "dependencies": {
                "python": ">=3.9",
                "packages": ["pydantic>=2.0"],
            },
        }

        # WHEN: Config is loaded
        config = TOMLAgentConfig.from_dict(config_dict)

        # THEN: All sections are parsed correctly
        assert config.agent.name == "GhidraAgent"
        assert config.agent.version == "1.0.0"
        assert config.agent.capabilities == ["decompilation", "analysis"]
        assert config.llm is not None
        assert config.llm.model == "codellama:7b"
        assert config.llm.temperature == 0.3
        assert config.dependencies is not None
        assert config.dependencies.python == ">=3.9"


class TestAgentConversationMemoryIsolation:
    """TEST-H007: Agent conversation memory isolation."""

    @pytest.mark.asyncio
    async def test_each_agent_has_own_memory(self):
        """Verify each agent has isolated conversation memory."""

        # GIVEN: Two agents
        class TestAgent(ATOLLAgent):
            async def process(self, prompt, context):
                return {"response": "test"}

        ollama_config = OllamaConfig()

        agent1 = TestAgent(name="Agent1", version="1.0.0", llm_config=ollama_config)
        agent2 = TestAgent(name="Agent2", version="1.0.0", llm_config=ollama_config)

        # WHEN: Messages added to each agent
        from langchain_core.messages import HumanMessage

        agent1.conversation_memory.append(HumanMessage(content="Hello from agent1"))
        agent2.conversation_memory.append(HumanMessage(content="Hello from agent2"))

        # THEN: Memories are isolated
        assert len(agent1.conversation_memory) == 1
        assert len(agent2.conversation_memory) == 1
        assert agent1.conversation_memory[0].content == "Hello from agent1"
        assert agent2.conversation_memory[0].content == "Hello from agent2"

    @pytest.mark.asyncio
    async def test_clear_memory_only_affects_own_agent(self):
        """Verify clearing memory only affects the specific agent."""

        # GIVEN: Two agents with conversation history
        class TestAgent(ATOLLAgent):
            async def process(self, prompt, context):
                return {"response": "test"}

        ollama_config = OllamaConfig()

        agent1 = TestAgent(name="Agent1", version="1.0.0", llm_config=ollama_config)
        agent2 = TestAgent(name="Agent2", version="1.0.0", llm_config=ollama_config)

        from langchain_core.messages import HumanMessage

        agent1.conversation_memory.append(HumanMessage(content="Message 1"))
        agent2.conversation_memory.append(HumanMessage(content="Message 2"))

        # WHEN: Agent1 clears memory
        agent1.clear_conversation_memory()

        # THEN: Only agent1's memory is cleared
        assert len(agent1.conversation_memory) == 0
        assert len(agent2.conversation_memory) == 1
        assert agent2.conversation_memory[0].content == "Message 2"


class TestPromptRoutingToCurrentAgent:
    """TEST-H009: Prompt routing to current agent context."""

    @pytest.mark.asyncio
    async def test_prompt_routes_to_root_when_no_context(self, monkeypatch):
        """Verify prompts route to root agent when no context switch."""
        # GIVEN: Application with root agent, no agent manager context
        from atoll.main import Application

        app = Application()
        app.config_manager = MagicMock()
        app.ui = MagicMock()

        # Mock root agent
        app.agent = AsyncMock(spec=RootAgent)
        app.agent.process_prompt = AsyncMock(return_value="Root response")

        # Mock agent manager with no current context
        app.agent_manager = MagicMock()
        app.agent_manager.current_context = None

        # WHEN: Prompt is handled
        await app.handle_prompt("test prompt")

        # THEN: Root agent's process_prompt was called
        app.agent.process_prompt.assert_called_once_with("test prompt")

    @pytest.mark.asyncio
    async def test_prompt_routes_to_sub_agent_when_switched(self, monkeypatch):
        """Verify prompts route to sub-agent when context is switched."""
        # GIVEN: Application with sub-agent context
        from atoll.agent.agent_manager import AgentContext
        from atoll.main import Application

        app = Application()
        app.config_manager = MagicMock()
        app.ui = MagicMock()

        # Mock root agent
        app.agent = AsyncMock(spec=RootAgent)
        app.agent.process_prompt = AsyncMock(return_value="Root response")

        # Mock sub-agent with switched context
        sub_agent = AsyncMock(spec=ATOLLAgent)
        sub_agent.process_prompt = AsyncMock(return_value="Sub-agent response")

        context = AgentContext(
            agent=sub_agent, name="SubAgent", mcp_manager=None, parent_context=None
        )

        app.agent_manager = MagicMock()
        app.agent_manager.current_context = context

        # WHEN: Prompt is handled
        await app.handle_prompt("test prompt")

        # THEN: Sub-agent's process_prompt was called, NOT root agent
        sub_agent.process_prompt.assert_called_once_with("test prompt")
        app.agent.process_prompt.assert_not_called()


class TestAgentToolsIntegration:
    """TEST-H006: Context-aware tool listing."""

    @pytest.mark.asyncio
    async def test_agent_has_tools_list(self):
        """Verify agent has tools list attribute."""

        # GIVEN: Agent with MCP manager
        class TestAgent(ATOLLAgent):
            async def process(self, prompt, context):
                return {"response": "test"}

        ollama_config = OllamaConfig()
        mcp_config = MCPConfig()
        mcp_manager = MCPServerManager(mcp_config)

        agent = TestAgent(
            name="TestAgent",
            version="1.0.0",
            llm_config=ollama_config,
            mcp_manager=mcp_manager,
        )

        # THEN: Agent has tools list
        assert hasattr(agent, "tools")
        assert isinstance(agent.tools, list)

    @pytest.mark.asyncio
    async def test_agent_updates_tools_from_mcp_manager(self):
        """Verify agent can update tools from MCP manager."""

        # GIVEN: Agent
        class TestAgent(ATOLLAgent):
            async def process(self, prompt, context):
                return {"response": "test"}

        ollama_config = OllamaConfig()
        agent = TestAgent(
            name="TestAgent", version="1.0.0", llm_config=ollama_config, mcp_manager=None
        )

        # Mock MCP manager with tools
        mcp_manager = MagicMock(spec=MCPServerManager)
        mcp_manager.tool_registry = MagicMock()
        mcp_manager.tool_registry.tools = {
            "test_tool": {"description": "Test tool", "server": "test_server"}
        }

        # WHEN: MCP manager is set
        agent.set_mcp_manager(mcp_manager)

        # THEN: Tools are updated
        assert len(agent.tools) > 0


class TestAgentCapabilities:
    """TEST-H011: Agent capabilities and metadata."""

    def test_root_agent_has_capabilities(self):
        """Verify root agent declares capabilities."""
        # GIVEN/WHEN: Root agent is created
        ollama_config = OllamaConfig()
        root_agent = RootAgent(name="Main", version="2.0.0", llm_config=ollama_config)

        # THEN: Root agent has capabilities
        capabilities = root_agent.get_capabilities()
        assert isinstance(capabilities, list)
        assert len(capabilities) > 0
        assert "general_assistance" in capabilities

    def test_root_agent_can_handle_prompts(self):
        """Verify root agent can_handle returns confidence score."""
        # GIVEN: Root agent
        ollama_config = OllamaConfig()
        root_agent = RootAgent(name="Main", version="2.0.0", llm_config=ollama_config)

        # WHEN: can_handle is called
        confidence = root_agent.can_handle("test prompt", {})

        # THEN: Returns valid confidence score
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0


# Integration test combining multiple features
class TestHierarchicalSystemIntegration:
    """Integration tests for hierarchical agent system."""

    @pytest.mark.asyncio
    async def test_full_hierarchical_setup(self):
        """Test complete hierarchical agent setup."""
        # GIVEN: Ollama and MCP configs
        ollama_config = OllamaConfig(
            base_url="http://localhost",
            port=11434,
            model="llama2",
            temperature=0.7,
        )
        mcp_config = MCPConfig()
        mcp_manager = MCPServerManager(mcp_config)
        ui = TerminalUI()

        # WHEN: Root agent is created with full setup
        root_agent = RootAgent(
            name="Main",
            version="2.0.0",
            llm_config=ollama_config,
            mcp_manager=mcp_manager,
            ui=ui,
        )

        # THEN: All components are properly initialized
        assert isinstance(root_agent, ATOLLAgent)
        assert root_agent.llm is not None
        assert root_agent.conversation_memory is not None
        assert len(root_agent.conversation_memory) == 0
        assert root_agent.get_capabilities() is not None
        assert root_agent.can_handle("test", {}) > 0

    @pytest.mark.asyncio
    async def test_agent_to_agent_memory_isolation(self):
        """Test that multiple agents maintain isolated memories."""

        # GIVEN: Parent and child agents
        class TestAgent(ATOLLAgent):
            async def process(self, prompt, context):
                return {"response": "test"}

        ollama_config = OllamaConfig()
        parent = TestAgent(name="Parent", version="1.0.0", llm_config=ollama_config)
        child1 = TestAgent(name="Child1", version="1.0.0", llm_config=ollama_config)
        child2 = TestAgent(name="Child2", version="1.0.0", llm_config=ollama_config)

        # WHEN: Each adds messages
        from langchain_core.messages import HumanMessage

        parent.conversation_memory.append(HumanMessage(content="Parent message"))
        child1.conversation_memory.append(HumanMessage(content="Child1 message"))
        child2.conversation_memory.append(HumanMessage(content="Child2 message"))

        # THEN: All memories are isolated
        assert len(parent.conversation_memory) == 1
        assert len(child1.conversation_memory) == 1
        assert len(child2.conversation_memory) == 1
        assert parent.conversation_memory[0].content == "Parent message"
        assert child1.conversation_memory[0].content == "Child1 message"
        assert child2.conversation_memory[0].content == "Child2 message"


# Test fixtures and helpers
@pytest.fixture
def ollama_config():
    """Fixture for Ollama configuration."""
    return OllamaConfig(
        base_url="http://localhost",
        port=11434,
        model="llama2",
        temperature=0.7,
    )


@pytest.fixture
def mcp_config():
    """Fixture for MCP configuration."""
    return MCPConfig()


@pytest.fixture
def mock_ui():
    """Fixture for mock UI."""
    ui = MagicMock(spec=TerminalUI)
    ui.display_user_input = MagicMock()
    ui.display_response = MagicMock()
    ui.display_verbose = MagicMock()
    ui.display_error = MagicMock()
    return ui
