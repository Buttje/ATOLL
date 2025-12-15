"""Tests for ReAct reasoning engine."""

import pytest
from unittest.mock import AsyncMock, Mock

from atoll.agent.react_engine import (
    ReActConfig,
    ReActEngine,
    ReActStep,
    StepType,
)


class TestReActEngine:
    """Test suite for ReActEngine."""

    def test_initialization_default(self):
        """Test initialization with default config."""
        engine = ReActEngine()

        assert engine.config is not None
        assert engine.config.max_iterations == 5
        assert engine.config.max_observation_length == 1000
        assert engine.config.tool_timeout == 30.0
        assert engine.steps == []

    def test_initialization_custom_config(self):
        """Test initialization with custom config."""
        config = ReActConfig(
            max_iterations=10, max_observation_length=500, tool_timeout=15.0, verbose=True
        )
        engine = ReActEngine(config=config)

        assert engine.config.max_iterations == 10
        assert engine.config.max_observation_length == 500
        assert engine.config.tool_timeout == 15.0
        assert engine.config.verbose is True

    def test_build_context(self):
        """Test context building with tools."""
        engine = ReActEngine()

        tools = [
            {"name": "search", "description": "Search the web"},
            {"name": "calculator", "description": "Perform calculations"},
        ]

        context = engine._build_context("test prompt", tools)

        assert "search" in context
        assert "calculator" in context
        assert "Search the web" in context
        assert "Perform calculations" in context
        assert "Thought:" in context
        assert "Action:" in context
        assert "Final Answer:" in context

    def test_parse_response_with_thought_and_action(self):
        """Test parsing response with thought and action."""
        engine = ReActEngine()

        response = """Thought: I need to search for information
Action: search
Action Input: Python programming"""

        parsed = engine._parse_response(response, 1)

        assert parsed is not None
        assert "thought" in parsed
        assert "action" in parsed
        assert parsed["thought"] == "I need to search for information"
        assert parsed["action"]["tool"] == "search"
        assert parsed["action"]["input"] == "Python programming"

    def test_parse_response_with_final_answer(self):
        """Test parsing response with final answer."""
        engine = ReActEngine()

        response = """Thought: I have all the information I need
Final Answer: Python is a high-level programming language"""

        parsed = engine._parse_response(response, 1)

        assert parsed is not None
        assert "thought" in parsed
        assert "final_answer" in parsed
        assert parsed["final_answer"] == "Python is a high-level programming language"

    def test_parse_response_malformed(self):
        """Test parsing malformed response."""
        engine = ReActEngine()

        response = "Just some random text without proper format"

        parsed = engine._parse_response(response, 1)

        # Should return None for malformed response
        assert parsed is None

    @pytest.mark.asyncio
    async def test_execute_action_success(self):
        """Test successful action execution."""
        mock_executor = AsyncMock(return_value="Search results here")
        engine = ReActEngine(tool_executor=mock_executor)

        result = await engine._execute_action("search", "Python")

        assert result == "Search results here"
        mock_executor.assert_called_once_with("search", "Python")

    @pytest.mark.asyncio
    async def test_execute_action_error(self):
        """Test action execution with error."""
        mock_executor = AsyncMock(side_effect=Exception("Tool failed"))
        engine = ReActEngine(tool_executor=mock_executor)

        result = await engine._execute_action("search", "Python")

        assert "Error executing tool" in result
        assert "Tool failed" in result

    @pytest.mark.asyncio
    async def test_execute_action_no_executor(self):
        """Test action execution without tool executor."""
        engine = ReActEngine()

        result = await engine._execute_action("search", "Python")

        assert "No tool executor configured" in result

    @pytest.mark.asyncio
    async def test_run_single_iteration(self):
        """Test ReAct run with single iteration to final answer."""
        # Mock LLM that returns final answer immediately
        async def mock_llm(prompt):
            return """Thought: I can answer this directly
Final Answer: The answer is 42"""

        mock_executor = AsyncMock(return_value="Tool result")
        engine = ReActEngine(tool_executor=mock_executor)

        tools = [{"name": "calculator", "description": "Do math"}]
        result = await engine.run("What is the answer?", tools, mock_llm)

        assert result["answer"] == "The answer is 42"
        assert result["iterations"] == 1
        assert len(result["steps"]) == 2  # Thought + Final Answer
        assert result["steps"][0].step_type == StepType.THOUGHT
        assert result["steps"][1].step_type == StepType.FINAL_ANSWER

    @pytest.mark.asyncio
    async def test_run_with_tool_execution(self):
        """Test ReAct run with tool execution."""
        call_count = [0]

        async def mock_llm(prompt):
            call_count[0] += 1
            if call_count[0] == 1:
                return """Thought: I need to use the calculator
Action: calculator
Action Input: 2 + 2"""
            else:
                return """Thought: I got the result
Final Answer: The result is 4"""

        mock_executor = AsyncMock(return_value="4")
        engine = ReActEngine(tool_executor=mock_executor)

        tools = [{"name": "calculator", "description": "Do math"}]
        result = await engine.run("What is 2 + 2?", tools, mock_llm)

        assert result["answer"] == "The result is 4"
        assert result["iterations"] == 2
        assert len(result["steps"]) >= 4  # Thought + Action + Observation + Thought + Final
        mock_executor.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_max_iterations(self):
        """Test ReAct run hitting max iterations."""

        async def mock_llm(prompt):
            # Never return final answer
            return """Thought: Let me think some more
Action: search
Action Input: more information"""

        mock_executor = AsyncMock(return_value="Some result")
        config = ReActConfig(max_iterations=3)
        engine = ReActEngine(config=config, tool_executor=mock_executor)

        tools = [{"name": "search", "description": "Search"}]
        result = await engine.run("Complex question", tools, mock_llm)

        assert "Unable to determine final answer" in result["answer"]
        assert result["iterations"] == 3

    @pytest.mark.asyncio
    async def test_run_llm_error(self):
        """Test ReAct run with LLM error."""

        async def mock_llm(prompt):
            raise Exception("LLM failed")

        engine = ReActEngine()

        tools = [{"name": "search", "description": "Search"}]
        result = await engine.run("Test question", tools, mock_llm)

        assert "Error" in result["answer"]
        assert "Failed to generate response" in result["answer"]
        assert result["iterations"] == 1

    @pytest.mark.asyncio
    async def test_observation_truncation(self):
        """Test that long observations are truncated."""

        async def mock_llm(prompt):
            return """Thought: Let me search
Action: search
Action Input: test"""

        # Return a very long result
        long_result = "x" * 2000
        mock_executor = AsyncMock(return_value=long_result)
        config = ReActConfig(max_observation_length=100)
        engine = ReActEngine(config=config, tool_executor=mock_executor)

        tools = [{"name": "search", "description": "Search"}]

        # Run one iteration then check observation
        result = await engine.run("Test", tools, mock_llm)

        # Find observation step
        obs_steps = [s for s in engine.steps if s.step_type == StepType.OBSERVATION]
        if obs_steps:
            obs = obs_steps[0]
            assert len(obs.content) <= 120  # 100 + " ... [truncated]"
            assert "[truncated]" in obs.content

    def test_get_steps_summary(self):
        """Test getting steps summary."""
        engine = ReActEngine()

        engine.steps = [
            ReActStep(StepType.THOUGHT, "Thinking about the problem", step_number=1),
            ReActStep(
                StepType.ACTION,
                "search: Python",
                tool_name="search",
                tool_args={"input": "Python"},
                step_number=1,
            ),
            ReActStep(StepType.OBSERVATION, "Found information", step_number=1),
        ]

        summary = engine.get_steps_summary()

        assert "[Step 1] Thought" in summary
        assert "[Step 1] Action" in summary
        assert "[Step 1] Observation" in summary

    def test_get_reasoning_trace(self):
        """Test getting reasoning trace."""
        engine = ReActEngine()

        engine.steps = [
            ReActStep(StepType.THOUGHT, "Thinking", step_number=1),
            ReActStep(
                StepType.ACTION,
                "search: test",
                tool_name="search",
                tool_args={"input": "test"},
                step_number=1,
            ),
        ]

        trace = engine.get_reasoning_trace()

        assert len(trace) == 2
        assert trace[0]["type"] == "Thought"
        assert trace[0]["step_number"] == 1
        assert trace[1]["type"] == "Action"
        assert trace[1]["tool_name"] == "search"


class TestReActConfig:
    """Test suite for ReActConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ReActConfig()

        assert config.max_iterations == 5
        assert config.max_observation_length == 1000
        assert config.tool_timeout == 30.0
        assert config.enable_parallel_actions is False
        assert config.verbose is False

    def test_custom_values(self):
        """Test custom configuration values."""
        config = ReActConfig(
            max_iterations=10,
            max_observation_length=500,
            tool_timeout=60.0,
            enable_parallel_actions=True,
            verbose=True,
        )

        assert config.max_iterations == 10
        assert config.max_observation_length == 500
        assert config.tool_timeout == 60.0
        assert config.enable_parallel_actions is True
        assert config.verbose is True
