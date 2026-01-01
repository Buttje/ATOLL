"""Legacy module - OllamaMCPAgent has been removed.

All functionality has been migrated to the ATOLLAgent base class and RootAgent implementation.
Use RootAgent or create custom agents by extending ATOLLAgent.

This file is kept for backward compatibility with imports only.
"""

# For backward compatibility, re-export from new locations
from ..plugins.base import ATOLLAgent as OllamaMCPAgent  # noqa: F401
from .reasoning import ReasoningEngine  # noqa: F401
from .tools import MCPToolWrapper  # noqa: F401

__all__ = ["OllamaMCPAgent", "MCPToolWrapper", "ReasoningEngine"]
