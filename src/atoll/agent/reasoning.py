"""Reasoning engine for agent decision-making."""

import asyncio
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from langchain_ollama import OllamaLLM

    from ..mcp.server_manager import MCPServerManager
    from .agent_manager import ATOLLAgentManager


class ReasoningEngine:
    """Implements LLM-based reasoning for matching user queries to capabilities."""

    def __init__(self, llm: Optional["OllamaLLM"] = None):
        """Initialize reasoning engine.

        Args:
            llm: Optional LLM instance for capability matching
        """
        self.llm = llm
        self._mcp_manager: Optional[MCPServerManager] = None
        self._agent_manager: Optional[ATOLLAgentManager] = None

    def set_llm(self, llm: "OllamaLLM") -> None:
        """Set the LLM instance for reasoning.

        Args:
            llm: LLM instance to use
        """
        self.llm = llm

    def set_mcp_manager(self, mcp_manager: "MCPServerManager") -> None:
        """Set the MCP server manager for capability discovery.

        Args:
            mcp_manager: MCP server manager instance
        """
        self._mcp_manager = mcp_manager

    def set_agent_manager(self, agent_manager: "ATOLLAgentManager") -> None:
        """Set the ATOLL agent manager for agent capability discovery.

        Args:
            agent_manager: ATOLL agent manager instance
        """
        self._agent_manager = agent_manager

    async def analyze(self, prompt: str, tools: list[Any]) -> list[str]:
        """Analyze prompt using LLM-based capability matching.

        Args:
            prompt: User's prompt/request
            tools: Available tools from MCP servers

        Returns:
            List of reasoning steps explaining capability matches
        """
        reasoning_steps = []

        if not self.llm:
            reasoning_steps.append(
                "⚠ Reasoning engine: LLM not configured, using fallback analysis"
            )
            return reasoning_steps

        # Gather capabilities from MCP servers
        mcp_capabilities = self._gather_mcp_capabilities()

        # Gather capabilities from ATOLL agents
        atoll_agent_capabilities = self._gather_agent_capabilities()

        # Build analysis prompt for LLM
        analysis_prompt = self._build_analysis_prompt(
            prompt, mcp_capabilities, atoll_agent_capabilities, tools
        )

        # Get LLM analysis
        try:
            loop = asyncio.get_event_loop()
            analysis = await loop.run_in_executor(None, self.llm.invoke, analysis_prompt)

            # Parse LLM response into reasoning steps
            reasoning_steps = self._parse_analysis(analysis)

        except Exception as e:
            reasoning_steps.append(f"⚠ Reasoning analysis failed: {str(e)}")
            reasoning_steps.append("Proceeding with direct tool execution")

        return reasoning_steps

    def _gather_mcp_capabilities(self) -> dict[str, dict[str, Any]]:
        """Gather capabilities from registered MCP servers.

        Returns:
            Dict mapping server names to their capabilities
        """
        if not self._mcp_manager:
            return {}

        capabilities = {}

        for server_name in self._mcp_manager.list_servers():
            server_tools = self._mcp_manager.tool_registry.list_server_tools(server_name)

            tool_info = []
            for tool_name in server_tools:
                tool = self._mcp_manager.tool_registry.get_tool(tool_name)
                if tool:
                    tool_info.append(
                        {
                            "name": tool_name,
                            "description": tool.get("description", "No description"),
                            "schema": tool.get("inputSchema", {}),
                        }
                    )

            capabilities[server_name] = {"tools": tool_info, "tool_count": len(server_tools)}

        return capabilities

    def _gather_agent_capabilities(self) -> dict[str, dict[str, Any]]:
        """Gather capabilities from registered ATOLL agents.

        Returns:
            Dict mapping agent names to their capabilities
        """
        if not self._agent_manager:
            return {}

        capabilities = {}

        for agent_name, context in self._agent_manager.loaded_agents.items():
            agent = context.agent

            capabilities[agent_name] = {
                "capabilities": agent.get_capabilities(),
                "supported_mcp_servers": agent.get_supported_mcp_servers(),
                "tools": agent.get_tools(),
                "version": agent.version,
            }

        return capabilities

    def _build_analysis_prompt(
        self,
        user_prompt: str,
        mcp_capabilities: dict[str, dict[str, Any]],
        agent_capabilities: dict[str, dict[str, Any]],
        _tools: list[Any],
    ) -> str:
        """Build prompt for LLM capability analysis.

        Args:
            user_prompt: User's original prompt
            mcp_capabilities: Capabilities from MCP servers
            agent_capabilities: Capabilities from ATOLL agents
            tools: Available tool instances

        Returns:
            Formatted prompt for LLM analysis
        """
        prompt = f"""Analyze the following user request and determine which capabilities can address it.

USER REQUEST: {user_prompt}

AVAILABLE MCP SERVERS:
"""

        if mcp_capabilities:
            for server_name, info in mcp_capabilities.items():
                prompt += f"\n{server_name}: {info['tool_count']} tools\n"
                for tool in info["tools"][:3]:  # Show first 3 tools
                    prompt += f"  - {tool['name']}: {tool['description']}\n"
                if info["tool_count"] > 3:
                    prompt += f"  ... and {info['tool_count'] - 3} more tools\n"
        else:
            prompt += "  (No MCP servers configured)\n"

        prompt += "\nAVAILABLE ATOLL AGENTS:\n"

        if agent_capabilities:
            for agent_name, info in agent_capabilities.items():
                prompt += f"\n{agent_name} v{info['version']}:\n"
                prompt += f"  Capabilities: {', '.join(info['capabilities'])}\n"
                prompt += f"  MCP servers: {', '.join(info['supported_mcp_servers'])}\n"
        else:
            prompt += "  (No specialized agents loaded)\n"

        prompt += """
TASK: Analyze if and how the user request can be fulfilled. Provide:
1. Which MCP server(s) and tool(s) are relevant (be specific)
2. Which ATOLL agent(s) can handle this request (if any)
3. Why these capabilities match the request
4. Confidence level (high/medium/low)

Format your response as concise bullet points, max 5 lines total.
"""

        return prompt

    def _parse_analysis(self, llm_response: str) -> list[str]:
        """Parse LLM analysis into reasoning steps.

        Args:
            llm_response: Raw LLM response

        Returns:
            List of formatted reasoning steps
        """
        lines = llm_response.strip().split("\n")
        reasoning_steps = []

        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                # Clean up formatting
                if line.startswith("-") or line.startswith("*") or line.startswith("•"):
                    line = line[1:].strip()
                elif line[0].isdigit() and line[1:3] in [". ", ") "]:
                    line = line[3:].strip()

                if line:
                    reasoning_steps.append(f"→ {line}")

        # Limit to 5 most relevant steps
        return reasoning_steps[:5]
