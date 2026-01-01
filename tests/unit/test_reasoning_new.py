"""Tests for the LLM-based reasoning engine."""

from unittest.mock import Mock

import pytest

from atoll.agent.reasoning import ReasoningEngine
from atoll.mcp.server_manager import MCPServerManager
from atoll.mcp.tool_registry import ToolRegistry


class TestReasoningEngine:
    """Test the ReasoningEngine class."""

    @pytest.mark.asyncio
    async def test_engine_initialization(self):
        """Test reasoning engine initialization."""
        mock_llm = Mock()
        engine = ReasoningEngine(llm=mock_llm)
        assert engine.llm == mock_llm
        assert engine._mcp_manager is None
        assert engine._agent_manager is None

    @pytest.mark.asyncio
    async def test_engine_without_llm(self):
        """Test reasoning engine without LLM uses fallback."""
        engine = ReasoningEngine()

        reasoning = await engine.analyze("test prompt", [])

        assert len(reasoning) == 1
        assert "LLM not configured" in reasoning[0]

    @pytest.mark.asyncio
    async def test_set_managers(self):
        """Test setting MCP and agent managers."""
        mock_llm = Mock()
        engine = ReasoningEngine(llm=mock_llm)

        mock_mcp_manager = Mock(spec=MCPServerManager)
        mock_agent_manager = Mock()

        engine.set_mcp_manager(mock_mcp_manager)
        engine.set_agent_manager(mock_agent_manager)

        assert engine._mcp_manager == mock_mcp_manager
        assert engine._agent_manager == mock_agent_manager

    @pytest.mark.asyncio
    async def test_gather_mcp_capabilities(self):
        """Test gathering MCP server capabilities."""
        mock_llm = Mock()
        engine = ReasoningEngine(llm=mock_llm)

        # Create mock MCP manager
        mock_mcp_manager = Mock(spec=MCPServerManager)
        mock_registry = Mock(spec=ToolRegistry)

        mock_registry.list_server_tools = Mock(return_value=["tool1", "tool2"])
        mock_registry.get_tool = Mock(
            return_value={"name": "tool1", "description": "Test tool", "inputSchema": {}}
        )
        mock_mcp_manager.list_servers = Mock(return_value=["test_server"])
        mock_mcp_manager.tool_registry = mock_registry

        engine.set_mcp_manager(mock_mcp_manager)

        capabilities = engine._gather_mcp_capabilities()

        assert "test_server" in capabilities
        assert capabilities["test_server"]["tool_count"] == 2

    @pytest.mark.asyncio
    async def test_gather_agent_capabilities(self):
        """Test gathering ATOLL agent capabilities."""
        mock_llm = Mock()
        engine = ReasoningEngine(llm=mock_llm)

        # Create mock agent manager
        mock_agent = Mock()
        mock_agent.get_capabilities = Mock(return_value=["binary_analysis"])
        mock_agent.get_supported_mcp_servers = Mock(return_value=["ghidra"])
        mock_agent.get_tools = Mock(return_value=[])
        mock_agent.version = "1.0.0"

        mock_context = Mock()
        mock_context.agent = mock_agent

        mock_agent_manager = Mock()
        mock_agent_manager.loaded_agents = {"test_agent": mock_context}

        engine.set_agent_manager(mock_agent_manager)

        capabilities = engine._gather_agent_capabilities()

        assert "test_agent" in capabilities
        assert "binary_analysis" in capabilities["test_agent"]["capabilities"]

    @pytest.mark.asyncio
    async def test_analyze_with_llm(self):
        """Test analysis with LLM."""
        # Mock LLM that returns structured response
        mock_llm = Mock()
        mock_llm.invoke = Mock(
            return_value="""
- MCP server 'filesystem' has relevant file tools
- Can handle file operations
- Confidence: high
        """
        )

        engine = ReasoningEngine(llm=mock_llm)

        # Mock MCP manager
        mock_mcp_manager = Mock(spec=MCPServerManager)
        mock_registry = Mock(spec=ToolRegistry)
        mock_registry.list_server_tools = Mock(return_value=[])
        mock_mcp_manager.list_servers = Mock(return_value=[])
        mock_mcp_manager.tool_registry = mock_registry

        engine.set_mcp_manager(mock_mcp_manager)

        reasoning = await engine.analyze("read a file", [])

        assert len(reasoning) > 0
        assert any("MCP server" in step for step in reasoning)

    @pytest.mark.asyncio
    async def test_parse_analysis(self):
        """Test parsing LLM analysis response."""
        engine = ReasoningEngine()

        llm_response = """
1. Tool matches requirement
- Secondary point
* Another format
• Unicode bullet
Plain text line
        """

        steps = engine._parse_analysis(llm_response)

        # Should extract and format properly
        assert len(steps) <= 5  # Max 5 steps
        assert all(step.startswith("→ ") for step in steps)

    @pytest.mark.asyncio
    async def test_build_analysis_prompt(self):
        """Test building analysis prompt for LLM."""
        engine = ReasoningEngine()

        mcp_caps = {
            "filesystem": {
                "tool_count": 3,
                "tools": [
                    {"name": "read_file", "description": "Read file contents"},
                    {"name": "write_file", "description": "Write to file"},
                ],
            }
        }

        agent_caps = {
            "ghidra_agent": {
                "capabilities": ["binary_analysis", "decompilation"],
                "supported_mcp_servers": ["ghidra"],
                "tools": [],
                "version": "1.0.0",
            }
        }

        prompt = engine._build_analysis_prompt("analyze a binary", mcp_caps, agent_caps, [])

        assert "analyze a binary" in prompt
        assert "filesystem" in prompt
        assert "ghidra_agent" in prompt
        assert "binary_analysis" in prompt
