"""Unit tests for main application."""

import pytest
import asyncio
from unittest.mock import patch, Mock, AsyncMock, MagicMock
from ollama_mcp_agent.main import Application, main
from ollama_mcp_agent.config.models import OllamaConfig, MCPConfig


class TestApplication:
    """Test the Application class."""
    
    @pytest.mark.asyncio
    async def test_startup(self):
        """Test application startup."""
        with patch('ollama_mcp_agent.main.ConfigManager') as mock_config_manager:
            with patch('ollama_mcp_agent.main.TerminalUI') as mock_ui:
                with patch('ollama_mcp_agent.main.MCPServerManager') as mock_server_manager:
                    with patch('ollama_mcp_agent.main.OllamaMCPAgent') as mock_agent:
                        app = Application()
                        
                        # Set up mocks
                        mock_config_instance = mock_config_manager.return_value
                        mock_config_instance.ollama_config = OllamaConfig()
                        mock_config_instance.mcp_config = MCPConfig()
                        
                        mock_server_instance = mock_server_manager.return_value
                        mock_server_instance.connect_all = AsyncMock()
                        
                        await app.startup()
                        
                        assert app.agent is not None
                        mock_server_instance.connect_all.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_prompt(self):
        """Test handling user prompt."""
        with patch('ollama_mcp_agent.main.ConfigManager'):
            app = Application()
            
            # Set up mock agent
            app.agent = Mock()
            app.agent.process_prompt = AsyncMock(return_value="Test response")
            
            await app.handle_prompt("Test prompt")
            
            app.agent.process_prompt.assert_called_once_with("Test prompt")
    
    @pytest.mark.asyncio
    async def test_handle_command_models(self):
        """Test handling models command."""
        with patch('ollama_mcp_agent.main.ConfigManager'):
            app = Application()
            
            app.agent = Mock()
            app.agent.list_models = AsyncMock(return_value=["model1", "model2"])
            app.config_manager = Mock()
            app.config_manager.ollama_config = Mock()
            app.config_manager.ollama_config.model = "model1"
            app.ui = Mock()
            
            await app.handle_command("models")
            
            app.agent.list_models.assert_called_once()
            app.ui.display_models.assert_called_once_with(["model1", "model2"], "model1")
    
    @pytest.mark.asyncio
    async def test_handle_command_changemodel(self):
        """Test handling changemodel command."""
        with patch('ollama_mcp_agent.main.ConfigManager'):
            app = Application()
            
            app.agent = Mock()
            app.agent.change_model = Mock(return_value=True)
            app.ui = Mock()
            
            await app.handle_command("changemodel test-model")
            
            app.agent.change_model.assert_called_once_with("test-model")
    
    @pytest.mark.asyncio
    async def test_handle_command_quit(self):
        """Test handling quit command."""
        with patch('ollama_mcp_agent.main.ConfigManager'):
            app = Application()
            
            app.ui = Mock()
            app.ui.running = True
            
            await app.handle_command("quit")
            
            assert app.ui.running is False
    
    @pytest.mark.asyncio
    async def test_handle_command_unknown(self):
        """Test handling unknown command."""
        with patch('ollama_mcp_agent.main.ConfigManager'):
            app = Application()
            
            app.ui = Mock()
            
            await app.handle_command("unknown_command")
            
            # Should display error for unknown command
            app.ui.display_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_loop_keyboard_interrupt(self):
        """Test the main run loop with keyboard interrupt."""
        with patch('ollama_mcp_agent.main.ConfigManager'):
            with patch('ollama_mcp_agent.main.TerminalUI'):
                with patch('ollama_mcp_agent.main.MCPServerManager'):
                    with patch('ollama_mcp_agent.main.OllamaMCPAgent'):
                        app = Application()
                        
                        # Mock startup
                        app.startup = AsyncMock()
                        app.ui = Mock()
                        app.ui.running = True
                        app.ui.get_input = Mock(side_effect=KeyboardInterrupt)
                        
                        # Run should handle KeyboardInterrupt gracefully
                        await app.run()


def test_main_function():
    """Test the main entry point."""
    with patch('ollama_mcp_agent.main.asyncio.run') as mock_run:
        with patch('ollama_mcp_agent.main.Application') as mock_app_class:
            mock_app = Mock()
            mock_app.run = AsyncMock()
            mock_app_class.return_value = mock_app
            
            main()
            
            mock_run.assert_called_once()