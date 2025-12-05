"""Integration tests for the application."""

import pytest
import asyncio
from unittest.mock import patch, Mock, AsyncMock

from ollama_mcp_agent.main import Application
from ollama_mcp_agent.config.models import OllamaConfig, MCPConfig


class TestIntegration:
    """Integration tests."""
    
    @pytest.mark.asyncio
    async def test_application_startup(self, tmp_path):
        """Test application startup sequence."""
        # Create temporary config files
        ollama_config_file = tmp_path / ".ollamaConfig.json"
        ollama_config_file.write_text('{"model": "test"}')
        
        mcp_config_file = tmp_path / ".mcpConfig.json"
        mcp_config_file.write_text('{"servers": {}}')
        
        with patch("ollama_mcp_agent.main.ConfigManager") as mock_config_manager:
            app = Application()
            
            # Create proper config objects
            mock_ollama_config = OllamaConfig(
                base_url="http://localhost",
                port=11434,
                model="test-model",
                request_timeout=10,
                max_tokens=1024,
                temperature=0.7,
                top_p=0.9
            )
            
            mock_mcp_config = MCPConfig(servers={})
            
            # Set up the mock config manager
            mock_config_instance = mock_config_manager.return_value
            mock_config_instance.ollama_config = mock_ollama_config
            mock_config_instance.mcp_config = mock_mcp_config
            mock_config_instance.load_configs.return_value = None
            
            # Mock the Ollama LLM to avoid actual connection
            with patch('ollama_mcp_agent.agent.agent.OllamaLLM') as mock_ollama:
                mock_llm = Mock()
                mock_ollama.return_value = mock_llm
                
                # Test startup doesn't crash
                try:
                    await asyncio.wait_for(app.startup(), timeout=5.0)
                except asyncio.TimeoutError:
                    pytest.fail("Application startup timed out")
                
                assert app.agent is not None
                assert app.mcp_manager is not None
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test a complete workflow from startup to prompt processing."""
        with patch("ollama_mcp_agent.main.ConfigManager") as mock_config_manager:
            app = Application()
            
            # Create proper config objects
            mock_ollama_config = OllamaConfig(
                base_url="http://localhost",
                port=11434,
                model="test-model",
                request_timeout=10,
                max_tokens=1024,
                temperature=0.7,
                top_p=0.9
            )
            
            mock_mcp_config = MCPConfig(servers={})
            
            # Set up the mock config manager
            mock_config_instance = mock_config_manager.return_value
            mock_config_instance.ollama_config = mock_ollama_config
            mock_config_instance.mcp_config = mock_mcp_config
            
            # Mock the necessary components
            with patch('ollama_mcp_agent.agent.agent.OllamaLLM') as mock_ollama:
                mock_llm = Mock()
                mock_llm.ainvoke = AsyncMock(return_value="Test response")
                mock_ollama.return_value = mock_llm
                
                # Start the application
                await app.startup()
                
                # Process a prompt
                with patch.object(app.ui, 'display_user_input'):
                    with patch.object(app.ui, 'display_response'):
                        result = await app.agent.process_prompt("Test prompt")
                        assert result is not None