"""Ghidra specialized agent for binary analysis.

This agent is compliant with ATOLL v2.0 specification and integrates
with GhidraMCP server for binary reverse engineering tasks.

Author: ATOLL Contributors
Version: 2.0.0
License: MIT
"""

import re
from typing import Any, Optional

from atoll.plugins.base import ATOLLAgent


class GhidraAgent(ATOLLAgent):
    """Specialized agent for Ghidra-based binary analysis.

    This agent provides expertise in:
    - Binary decompilation and disassembly
    - Function analysis and signature identification
    - Symbol table and cross-reference analysis
    - Vulnerability detection in compiled binaries
    - Assembly code understanding
    - Binary format analysis (ELF, PE, Mach-O)

    The agent uses CodeLlama for optimized code analysis and integrates
    with GhidraMCP server for Ghidra tool access.
    """

    def __init__(
        self,
        name: str,
        version: str,
        llm_config: Optional[Any] = None,
        mcp_manager: Optional[Any] = None,
        ui: Optional[Any] = None,
    ):
        """Initialize Ghidra agent.

        Args:
            name: Agent name (typically "GhidraAgent")
            version: Agent version (e.g., "2.0.0")
            llm_config: Optional LLM configuration (uses agent.toml if not provided)
            mcp_manager: MCP server manager for tool access
            ui: Terminal UI for output
        """
        super().__init__(name, version, llm_config, mcp_manager, ui)

    async def process(self, prompt: str, context: dict[str, Any]) -> dict[str, Any]:
        """Process a prompt with Ghidra-specific reasoning.

        This method is called by the agent manager when this agent is selected
        to handle a prompt. It performs specialized analysis for binary reverse
        engineering tasks.

        Args:
            prompt: User's prompt/question
            context: Context dictionary with:
                - available_tools: List of available MCP tools
                - available_servers: List of connected MCP servers
                - conversation_history: Previous conversation

        Returns:
            Dictionary with:
                - response: Agent's response text
                - reasoning: List of reasoning steps taken
                - tool_calls: List of tools that should be invoked
                - agent: Name of this agent
        """
        reasoning = []

        # Analyze prompt for Ghidra-specific patterns
        prompt_lower = prompt.lower()

        # Decompilation requests
        if any(keyword in prompt_lower for keyword in ["decompile", "decompilation"]):
            reasoning.append("Detected decompilation request")
            reasoning.append("Will use Ghidra's decompiler to convert assembly to C-like code")
            reasoning.append("Analyzing function structure and control flow")

        # Function analysis
        if "function" in prompt_lower:
            reasoning.append("Function-level analysis requested")
            reasoning.append("Will retrieve function information, signature, and decompilation")
            reasoning.append("Checking for function calls and cross-references")

        # Security/vulnerability analysis
        if any(
            keyword in prompt_lower for keyword in ["vulnerability", "security", "exploit", "cve"]
        ):
            reasoning.append("Security analysis requested")
            reasoning.append("Will analyze for common vulnerability patterns:")
            reasoning.append("  - Buffer overflows")
            reasoning.append("  - Format string vulnerabilities")
            reasoning.append("  - Integer overflows")
            reasoning.append("  - Use-after-free conditions")

        # Symbol and cross-reference analysis
        if any(
            keyword in prompt_lower
            for keyword in ["symbol", "xref", "cross reference", "reference"]
        ):
            reasoning.append("Symbol/cross-reference analysis requested")
            reasoning.append("Will examine symbol table and reference relationships")

        # Binary format identification
        if any(keyword in prompt_lower for keyword in ["elf", "pe", "mach-o", "binary format"]):
            reasoning.append("Binary format analysis requested")
            reasoning.append("Will identify executable format and architecture")

        # Extract memory addresses if present
        addresses = re.findall(r"0x[0-9a-fA-F]+", prompt)
        if addresses:
            reasoning.append(f"Found memory address(es): {', '.join(addresses)}")
            reasoning.append("Will analyze code/data at specified addresses")

        # Extract function names if present (common patterns)
        function_names = re.findall(r"\b(main|start|_init|FUN_[0-9a-f]+)\b", prompt)
        if function_names:
            reasoning.append(f"Identified function name(s): {', '.join(set(function_names))}")

        # Build response
        response = {
            "response": "Analyzing binary with Ghidra capabilities...",
            "reasoning": reasoning,
            "tool_calls": [],  # Populated by LLM/tool execution system
            "agent": self.name,
            "confidence": self.can_handle(prompt, context),
        }

        return response

    def get_capabilities(self) -> list[str]:
        """Get Ghidra agent capabilities.

        Returns:
            List of capability identifiers that this agent provides.
            These match the capabilities listed in agent.toml.
        """
        return [
            "binary_analysis",
            "decompilation",
            "symbol_analysis",
            "reverse_engineering",
            "vulnerability_detection",
            "assembly_analysis",
            "function_analysis",
            "cross_reference_analysis",
        ]

    def get_supported_mcp_servers(self) -> list[str]:
        """Get MCP servers supported by this agent.

        Returns:
            List of MCP server names that this agent can work with.
        """
        return ["ghidramcp", "Ghidra"]  # Support both naming conventions

    def can_handle(self, prompt: str, context: dict[str, Any]) -> float:
        """Determine if this agent can handle the prompt.

        This method calculates a confidence score based on keywords, patterns,
        and available resources to determine if this agent is suitable for
        handling the given prompt.

        Args:
            prompt: User's prompt/question
            context: Current context with available tools and servers

        Returns:
            Confidence score from 0.0 (cannot handle) to 1.0 (perfect match)

        Scoring criteria:
            - 0.0-0.2: Low relevance, not recommended
            - 0.2-0.5: Some relevance, could assist
            - 0.5-0.8: Good match, recommended
            - 0.8-1.0: Excellent match, highly recommended
        """
        prompt_lower = prompt.lower()
        score = 0.0

        # Primary keywords (high value)
        primary_keywords = [
            "decompile",
            "disassemble",
            "reverse engineer",
            "ghidra",
            "binary analysis",
        ]

        # Secondary keywords (medium value)
        secondary_keywords = [
            "binary",
            "executable",
            "function analysis",
            "assembly",
            "elf",
            "pe file",
            "mach-o",
            "symbol",
            "cross reference",
            "xref",
            "vulnerability",
            "exploit",
        ]

        # Check for primary keywords (0.4 per match, max 0.8)
        primary_matches = sum(1 for keyword in primary_keywords if keyword in prompt_lower)
        if primary_matches > 0:
            score += min(0.4 * primary_matches, 0.8)

        # Check for secondary keywords (0.15 per match, max 0.4)
        secondary_matches = sum(1 for keyword in secondary_keywords if keyword in prompt_lower)
        if secondary_matches > 0:
            score += min(0.15 * secondary_matches, 0.4)

        # Boost score if GhidraMCP server is available
        available_servers = context.get("available_servers", [])
        if any(server.lower() in ["ghidramcp", "ghidra"] for server in available_servers):
            score += 0.2
        else:
            # Penalize if server not available (reduce confidence)
            score *= 0.5

        # Boost score for memory address patterns (indicates binary analysis)
        if re.search(r"0x[0-9a-fA-F]+", prompt):
            score += 0.15

        # Boost score for common function naming patterns
        if re.search(r"\b(main|start|_init|FUN_[0-9a-f]+|sub_[0-9a-f]+)\b", prompt):
            score += 0.1

        # Cap at 1.0
        return min(score, 1.0)
