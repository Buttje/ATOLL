"""Reasoning engine for agent decision-making."""

from typing import Any, Dict, List


class ReasoningEngine:
    """Implements reasoning and rule-based filtering for agent decisions."""
    
    def __init__(self):
        """Initialize reasoning engine."""
        self.rules = [
            self._check_ghidra_query,
            self._check_security_constraints,
            self._check_performance_requirements,
        ]
    
    def analyze(self, prompt: str, tools: List[Any]) -> List[str]:
        """Analyze prompt and return reasoning steps."""
        reasoning_steps = []
        
        # Check if prompt matches special patterns
        if "find" in prompt.lower() and "implementation" in prompt.lower():
            reasoning_steps.append("Detected code search query")
            
            if "inlined" in prompt.lower():
                reasoning_steps.append("Need to check for inlined functions")
                reasoning_steps.append("Will use semantic matching, not just name matching")
        
        # Apply rules
        for rule in self.rules:
            result = rule(prompt, tools)
            if result:
                reasoning_steps.append(result)
        
        # Determine tool selection strategy
        if tools:
            tool_names = [t.name for t in tools]
            if "ghidra" in prompt.lower() and any("ghidra" in name.lower() for name in tool_names):
                reasoning_steps.append("Selecting Ghidra-specific tools for binary analysis")
        
        return reasoning_steps
    
    def _check_ghidra_query(self, prompt: str, tools: List[Any]) -> str:
        """Check if this is a Ghidra-specific query."""
        ghidra_keywords = ["function", "implementation", "inlined", "address", "binary"]
        
        if any(keyword in prompt.lower() for keyword in ghidra_keywords):
            ghidra_tools = [t for t in tools if "ghidra" in t.name.lower()]
            if ghidra_tools:
                return f"Identified Ghidra query - {len(ghidra_tools)} relevant tools available"
        
        return ""
    
    def _check_security_constraints(self, prompt: str, tools: List[Any]) -> str:
        """Check for security-sensitive operations."""
        sensitive_keywords = ["password", "credential", "secret", "token", "key"]
        
        if any(keyword in prompt.lower() for keyword in sensitive_keywords):
            return "Security: Handling potentially sensitive data"
        
        return ""
    
    def _check_performance_requirements(self, prompt: str, tools: List[Any]) -> str:
        """Check performance requirements."""
        if "elf" in prompt.lower() or "binary" in prompt.lower():
            return "Performance: Response required within 10s for ELF <50MB"
        
        return ""