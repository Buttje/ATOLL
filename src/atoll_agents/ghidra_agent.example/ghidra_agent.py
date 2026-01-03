"""Ghidra specialized agent for binary analysis."""

import re
from typing import Any

from atoll.plugins.base import ATOLLAgent


class GhidraAgent(ATOLLAgent):
    """Specialized agent for Ghidra-based binary analysis.

    This agent provides expertise in:
    - Binary decompilation
    - Function analysis
    - Symbol and cross-reference analysis
    - Vulnerability detection in binaries
    """

    def __init__(self, name: str, version: str):
        """Initialize Ghidra agent."""
        super().__init__(name, version)

    async def process(self, prompt: str, _context: dict[str, Any]) -> dict[str, Any]:
        """Process a prompt with Ghidra-specific reasoning.

        Args:
            prompt: User's prompt
            context: Context with available tools and history

        Returns:
            Dict with 'response', 'reasoning', and 'tool_calls'
        """
        reasoning = []

        # Analyze prompt for Ghidra-specific patterns
        if "decompile" in prompt.lower():
            reasoning.append("Detected decompilation request")
            reasoning.append("Will use Ghidra's decompiler for analysis")

        if "function" in prompt.lower():
            reasoning.append("Function-level analysis requested")
            reasoning.append("Will retrieve function information and decompilation")

        if "vulnerability" in prompt.lower() or "security" in prompt.lower():
            reasoning.append("Security analysis requested")
            reasoning.append("Will analyze for common vulnerability patterns")

        # Extract addresses if present
        addresses = re.findall(r"0x[0-9a-fA-F]+", prompt)
        if addresses:
            reasoning.append(f"Found address(es): {', '.join(addresses)}")

        # Build response
        response = {
            "response": "Analyzing with Ghidra capabilities...",
            "reasoning": reasoning,
            "tool_calls": [],  # Would be populated by actual tool execution
            "agent": self.name,
        }

        return response

    def get_capabilities(self) -> list[str]:
        """Get Ghidra agent capabilities."""
        return [
            "binary_analysis",
            "decompilation",
            "symbol_analysis",
            "reverse_engineering",
            "vulnerability_detection",
        ]

    def get_supported_mcp_servers(self) -> list[str]:
        """Get supported MCP servers."""
        return ["ghidramcp"]

    def can_handle(self, prompt: str, context: dict[str, Any]) -> float:
        """Determine if this agent can handle the prompt.

        Args:
            prompt: User's prompt
            context: Current context

        Returns:
            Confidence score 0.0-1.0
        """
        prompt_lower = prompt.lower()
        score = 0.0

        # Keywords that indicate Ghidra relevance
        ghidra_keywords = [
            "decompile",
            "disassemble",
            "binary",
            "executable",
            "reverse engineer",
            "function analysis",
            "ghidra",
            "assembly",
            "elf",
            "pe file",
            "cross reference",
            "xref",
        ]

        # Check for keywords
        matches = sum(1 for keyword in ghidra_keywords if keyword in prompt_lower)
        if matches > 0:
            score = min(0.3 + (matches * 0.2), 1.0)

        # Check if GhidraMCP server is available in context
        available_servers = context.get("available_servers", [])
        if "ghidramcp" in available_servers:
            score += 0.2

        # Check for address patterns
        if re.search(r"0x[0-9a-fA-F]+", prompt):
            score += 0.15

        return min(score, 1.0)
