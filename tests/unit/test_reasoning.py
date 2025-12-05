"""Unit tests for reasoning engine."""

import pytest
from unittest.mock import Mock
from ollama_mcp_agent.agent.reasoning import ReasoningEngine
from langchain_core.tools import BaseTool


class TestReasoningEngine:
    """Test the ReasoningEngine class."""
    
    def test_initialization(self):
        """Test reasoning engine initialization."""
        engine = ReasoningEngine()
        assert engine.rules is not None
        assert len(engine.rules) > 0
    
    def test_analyze_code_search_query(self):
        """Test analyzing code search queries."""
        engine = ReasoningEngine()
        
        steps = engine.analyze("find implementation of function", [])
        
        assert any("code search" in step.lower() for step in steps)
    
    def test_analyze_inlined_function_search(self):
        """Test analyzing inlined function searches."""
        engine = ReasoningEngine()
        
        steps = engine.analyze("find inlined implementation of memcpy", [])
        
        assert any("inlined" in step.lower() for step in steps)
        assert any("semantic matching" in step.lower() for step in steps)
    
    def test_ghidra_query_detection(self):
        """Test Ghidra query detection."""
        engine = ReasoningEngine()
        
        # Create mock Ghidra tool
        mock_tool = Mock(spec=BaseTool)
        mock_tool.name = "ghidra_analyze"
        
        steps = engine.analyze("analyze function in binary", [mock_tool])
        
        assert any("Ghidra query" in step for step in steps)
    
    def test_security_constraints(self):
        """Test security constraint detection."""
        engine = ReasoningEngine()
        
        steps = engine.analyze("retrieve password from database", [])
        
        assert any("Security" in step for step in steps)
        assert any("sensitive" in step.lower() for step in steps)
    
    def test_performance_requirements(self):
        """Test performance requirement detection."""
        engine = ReasoningEngine()
        
        steps = engine.analyze("analyze ELF binary", [])
        
        assert any("Performance" in step for step in steps)
        assert any("10s" in step for step in steps)
    
    def test_no_special_patterns(self):
        """Test when no special patterns are detected."""
        engine = ReasoningEngine()
        
        steps = engine.analyze("hello world", [])
        
        # Should return empty or minimal reasoning
        assert len(steps) == 0 or all(step == "" for step in steps)
    
    def test_multiple_rules_triggered(self):
        """Test when multiple rules are triggered."""
        engine = ReasoningEngine()
        
        mock_tool = Mock(spec=BaseTool)
        mock_tool.name = "ghidra_decrypt"
        
        steps = engine.analyze("find password function in binary ELF file", [mock_tool])
        
        # Should trigger multiple rules
        assert len(steps) >= 2
        assert any("Performance" in step for step in steps)
        assert any("Security" in step for step in steps)