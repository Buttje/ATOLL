"""ReAct (Reasoning + Action) reasoning engine implementation."""

import asyncio
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class StepType(Enum):
    """Types of steps in the ReAct loop."""

    THOUGHT = "Thought"
    ACTION = "Action"
    OBSERVATION = "Observation"
    FINAL_ANSWER = "Final Answer"


@dataclass
class ReActStep:
    """Represents a single step in the ReAct loop."""

    step_type: StepType
    content: str
    tool_name: Optional[str] = None
    tool_args: Optional[dict] = None
    step_number: int = 0


@dataclass
class ReActConfig:
    """Configuration for ReAct engine."""

    max_iterations: int = 5
    max_observation_length: int = 1000
    tool_timeout: float = 30.0
    enable_parallel_actions: bool = False
    verbose: bool = False


class ReActEngine:
    """ReAct (Reasoning + Action) engine for agentic workflows.

    Implements the ReAct pattern that interleaves:
    - Thought: Chain-of-thought reasoning
    - Action: Tool execution
    - Observation: Tool result processing

    The loop continues until a final answer is reached or max iterations exceeded.
    """

    # Regex patterns for parsing LLM responses
    _THOUGHT_PATTERN = r"Thought:\s*(.+?)(?=\n(?:Action:|Final Answer:)|$)"
    _FINAL_ANSWER_PATTERN = r"Final Answer:\s*(.+)"
    _ACTION_PATTERN = r"Action:\s*(.+?)(?=\n|$)"
    _ACTION_INPUT_PATTERN = r"Action Input:\s*(.+?)(?=\n|$)"

    def __init__(
        self,
        config: Optional[ReActConfig] = None,
        tool_executor: Optional[Callable] = None,
    ):
        """Initialize ReAct engine.

        Args:
            config: Configuration for the engine
            tool_executor: Async function to execute tools
        """
        self.config = config or ReActConfig()
        self.tool_executor = tool_executor
        self.steps: list[ReActStep] = []

    async def run(
        self,
        initial_prompt: str,
        available_tools: list[dict],
        llm_generate: Callable,
    ) -> dict:
        """Run the ReAct loop.

        Args:
            initial_prompt: The user's initial question/request
            available_tools: List of available tools with their schemas
            llm_generate: Async function to call LLM

        Returns:
            Dict with 'answer', 'steps', and 'iterations'
        """
        self.steps = []
        scratchpad = []

        # Build initial context
        context = self._build_context(initial_prompt, available_tools)
        scratchpad.append(f"Question: {initial_prompt}")

        for iteration in range(self.config.max_iterations):
            if self.config.verbose:
                logger.info(f"ReAct iteration {iteration + 1}/{self.config.max_iterations}")

            # Generate thought and action
            scratchpad_text = "\n".join(scratchpad)
            prompt = f"{context}\n\n{scratchpad_text}\n\nThought:"

            try:
                response = await llm_generate(prompt)
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
                return {
                    "answer": f"Error: Failed to generate response: {e}",
                    "steps": self.steps,
                    "iterations": iteration + 1,
                }

            # Parse response for thought, action, and final answer
            parsed = self._parse_response(response, iteration + 1)

            if not parsed:
                # Malformed response
                logger.warning(f"Failed to parse LLM response at iteration {iteration + 1}")
                scratchpad.append(
                    f"Thought {iteration + 1}: Unable to parse response, trying again..."
                )
                continue

            # Add thought
            if parsed.get("thought"):
                thought_step = ReActStep(
                    step_type=StepType.THOUGHT,
                    content=parsed["thought"],
                    step_number=iteration + 1,
                )
                self.steps.append(thought_step)
                scratchpad.append(f"Thought {iteration + 1}: {parsed['thought']}")

            # Check for final answer
            if parsed.get("final_answer"):
                final_step = ReActStep(
                    step_type=StepType.FINAL_ANSWER,
                    content=parsed["final_answer"],
                    step_number=iteration + 1,
                )
                self.steps.append(final_step)

                return {
                    "answer": parsed["final_answer"],
                    "steps": self.steps,
                    "iterations": iteration + 1,
                }

            # Execute action if present
            if parsed.get("action"):
                action_step = ReActStep(
                    step_type=StepType.ACTION,
                    content=f"{parsed['action']['tool']}: {parsed['action']['input']}",
                    tool_name=parsed["action"]["tool"],
                    tool_args={"input": parsed["action"]["input"]},
                    step_number=iteration + 1,
                )
                self.steps.append(action_step)
                scratchpad.append(
                    f"Action {iteration + 1}: {parsed['action']['tool']}({parsed['action']['input']})"
                )

                # Execute tool
                observation = await self._execute_action(
                    parsed["action"]["tool"], parsed["action"]["input"]
                )

                # Truncate observation if needed
                if len(observation) > self.config.max_observation_length:
                    observation = (
                        observation[: self.config.max_observation_length]
                        + "... [truncated]"
                    )

                obs_step = ReActStep(
                    step_type=StepType.OBSERVATION,
                    content=observation,
                    step_number=iteration + 1,
                )
                self.steps.append(obs_step)
                scratchpad.append(f"Observation {iteration + 1}: {observation}")

        # Max iterations reached
        return {
            "answer": "Unable to determine final answer within iteration limit",
            "steps": self.steps,
            "iterations": self.config.max_iterations,
        }

    def _build_context(self, prompt: str, tools: list[dict]) -> str:
        """Build context prompt with tool descriptions."""
        context = """You are an AI assistant that can reason and take actions to answer questions.

You have access to the following tools:"""

        for tool in tools:
            context += f"\n- {tool.get('name', 'unknown')}: {tool.get('description', 'No description')}"

        context += """

Use the following format for your response:

Thought: [Your reasoning about what to do next]
Action: [The tool to use, must be one of the tool names above]
Action Input: [The input to the tool]

After you receive an Observation, you can either:
1. Continue with another Thought/Action/Action Input if you need more information
2. Give your Final Answer if you have enough information

When you have the final answer, respond with:
Final Answer: [Your complete answer to the user's question]

Remember:
- Always think step by step
- Only use tools that are available
- Provide clear and concise answers"""

        return context

    # Regex patterns for parsing LLM responses
    _THOUGHT_PATTERN = r"Thought:\s*(.+?)(?=\n(?:Action:|Final Answer:)|$)"
    _FINAL_ANSWER_PATTERN = r"Final Answer:\s*(.+)"
    _ACTION_PATTERN = r"Action:\s*(.+?)(?=\n|$)"
    _ACTION_INPUT_PATTERN = r"Action Input:\s*(.+?)(?=\n|$)"

    def _parse_response(self, response: str, step_number: int) -> Optional[dict]:
        """Parse LLM response into structured format.

        Expected formats:
        - Thought: <text>
        - Action: <tool_name>
        - Action Input: <input>
        - Final Answer: <answer>
        """
        result = {}

        # Extract thought
        thought_match = re.search(self._THOUGHT_PATTERN, response, re.DOTALL)
        if thought_match:
            result["thought"] = thought_match.group(1).strip()

        # Extract final answer
        final_match = re.search(self._FINAL_ANSWER_PATTERN, response, re.DOTALL)
        if final_match:
            result["final_answer"] = final_match.group(1).strip()
            return result

        # Extract action and action input
        action_match = re.search(self._ACTION_PATTERN, response)
        action_input_match = re.search(self._ACTION_INPUT_PATTERN, response, re.DOTALL)

        if action_match and action_input_match:
            result["action"] = {
                "tool": action_match.group(1).strip(),
                "input": action_input_match.group(1).strip(),
            }

        # Return None if we couldn't extract anything useful
        if not result or (not result.get("thought") and not result.get("action")):
            return None

        return result

    async def _execute_action(self, tool_name: str, tool_input: str) -> str:
        """Execute a tool action."""
        if not self.tool_executor:
            return f"Error: No tool executor configured"

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                self.tool_executor(tool_name, tool_input), timeout=self.config.tool_timeout
            )
            return str(result)
        except asyncio.TimeoutError:
            return f"Error: Tool '{tool_name}' timed out after {self.config.tool_timeout}s"
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"

    def get_steps_summary(self) -> str:
        """Get a formatted summary of all steps."""
        if not self.steps:
            return "No steps recorded"

        summary = []
        for step in self.steps:
            prefix = f"[Step {step.step_number}] {step.step_type.value}"
            summary.append(f"{prefix}: {step.content[:100]}...")

        return "\n".join(summary)

    def get_reasoning_trace(self) -> list[dict]:
        """Get the full reasoning trace as structured data."""
        return [
            {
                "step_number": step.step_number,
                "type": step.step_type.value,
                "content": step.content,
                "tool_name": step.tool_name,
                "tool_args": step.tool_args,
            }
            for step in self.steps
        ]
