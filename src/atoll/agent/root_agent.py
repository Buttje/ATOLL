"""Root ATOLL Agent - Main agent for user interaction."""

from typing import Any

from ..plugins.base import ATOLLAgent


class RootAgent(ATOLLAgent):
    """Root agent that serves as the main entry point for ATOLL.

    This agent provides general-purpose AI assistance and can delegate
    to specialized sub-agents when needed.
    """

    async def process(self, prompt: str, context: dict[str, Any]) -> dict[str, Any]:
        """Process a prompt with general AI capabilities.

        This method is for backward compatibility. The root agent primarily
        uses process_prompt() for LLM-integrated processing.

        Args:
            prompt: User's prompt
            context: Context with available tools and history

        Returns:
            Dict with 'response' and 'reasoning'
        """
        # Use the integrated process_prompt for actual processing
        response = await self.process_prompt(prompt)

        return {
            "response": response,
            "reasoning": ["Processed with general AI capabilities"],
            "tool_calls": [],
            "agent": self.name,
        }

    def get_capabilities(self) -> list[str]:
        """Get root agent capabilities."""
        return [
            "general_assistance",
            "task_delegation",
            "tool_coordination",
            "mcp_integration",
        ]

    def get_supported_mcp_servers(self) -> list[str]:
        """Get supported MCP servers.

        The root agent supports all available MCP servers.
        """
        if self.mcp_manager:
            return self.mcp_manager.list_servers()
        return []

    def can_handle(self, prompt: str, context: dict[str, Any]) -> float:
        """Determine if root agent can handle the prompt.

        The root agent can handle any prompt as a fallback,
        but gives lower priority to allow specialized agents first.

        Args:
            prompt: User's prompt
            context: Current context

        Returns:
            Confidence score 0.5 (medium, fallback priority)
        """
        return 0.5

    def _build_system_prompt(self) -> str:
        """Build system prompt for the root agent.

        Returns:
            Customized system prompt for root agent
        """
        prompt = """You are ATOLL (Agentic Tools with Ollama and LangChain), a powerful AI assistant
designed to help users with various tasks through specialized tools and capabilities.

You have access to Model Context Protocol (MCP) servers that provide tools for:
- File system operations
- Web search and data retrieval
- Code analysis and development
- Database operations
- And more depending on configured servers

When users ask questions:
1. Analyze what tools might be helpful
2. Break down complex tasks into steps
3. Use available tools to gather information
4. Provide clear, helpful responses

Think step-by-step and explain your reasoning."""

        if self.tools:
            prompt += "\n\nAvailable tools:"
            for tool in self.tools:
                prompt += f"\n- {tool.name}: {tool.description}"

        return prompt
