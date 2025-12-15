"""Base class for ATOLL agent plugins."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class ATOLLAgent(ABC):
    """Base class for ATOLL agent plugins.

    All specialized agents must inherit from this class and implement
    the required methods. Agents can provide specialized reasoning,
    tool handling, or domain-specific workflows.
    """

    def __init__(self, name: str, version: str):
        """Initialize the agent.

        Args:
            name: Name of the agent
            version: Version string (e.g., "1.0.0")
        """
        self.name = name
        self.version = version
        self._metadata: dict[str, Any] = {}

    @abstractmethod
    async def process(self, prompt: str, context: dict[str, Any]) -> dict[str, Any]:
        """Process a prompt with the agent's specialized capabilities.

        Args:
            prompt: User's prompt/question
            context: Context including available tools, history, etc.

        Returns:
            Dict with 'response', 'reasoning', and optionally 'tool_calls'
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> list[str]:
        """Get list of capabilities this agent provides.

        Returns:
            List of capability strings (e.g., ["binary_analysis", "decompilation"])
        """
        pass

    @abstractmethod
    def get_supported_mcp_servers(self) -> list[str]:
        """Get list of MCP server names this agent works with.

        Returns:
            List of MCP server names (e.g., ["ghidramcp", "binutils"])
        """
        pass

    def get_tools(self) -> list[dict[str, Any]]:
        """Get list of tools provided by this agent.

        Returns:
            List of tool dictionaries with 'name', 'description', 'schema'
        """
        return []

    def can_handle(self, prompt: str, context: dict[str, Any]) -> float:
        """Determine if this agent can handle the given prompt.

        Args:
            prompt: User's prompt
            context: Current context

        Returns:
            Confidence score 0.0-1.0, where higher means more suitable
        """
        return 0.0

    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata for the agent.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self._metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value.

        Args:
            key: Metadata key
            default: Default value if key not found

        Returns:
            Metadata value or default
        """
        return self._metadata.get(key, default)

    def get_all_metadata(self) -> dict[str, Any]:
        """Get all metadata.

        Returns:
            Dictionary of all metadata
        """
        return self._metadata.copy()

    def __str__(self) -> str:
        """String representation."""
        return f"{self.name} v{self.version}"

    def __repr__(self) -> str:
        """Detailed representation."""
        return f"ATOLLAgent(name='{self.name}', version='{self.version}')"
