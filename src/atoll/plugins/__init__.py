"""Plugin system for ATOLL agents."""

from .base import ATOLLAgent
from .manager import PluginManager

__all__ = ["ATOLLAgent", "PluginManager"]
