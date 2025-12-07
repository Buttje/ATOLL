"""Extended tests for main application."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from atoll.main import Application


class TestApplicationExtended:
    """Extended tests for Application."""
    
    @pytest.mark.asyncio
    async def test_startup_with_mcp_servers(self):
        """Test startup with MCP servers configured."""
        with patch('atoll.main.ConfigManager') as mock_config_manager:
            app = Application()
            
            # Mock config manager
            mock_config_instance = mock_config_manager.return_value
            mock_config_instance.ollama_config = Mock(
                base_url="http://localhost",
                port=11434,
                model="test-model"
            )
            mock_config_instance.mcp_config = Mock(servers={})
            
            # Mock MCP server manager
            with patch('atoll.main.MCPServerManager') as mock_manager_class:
                mock_manager = mock_manager_class.return_value
                mock_manager.connect_all = AsyncMock()
                mock_manager.tool_registry = Mock(tools={})
                
                # Mock agent
                with patch('atoll.main.OllamaMCPAgent') as mock_agent_class:
                    mock_agent = mock_agent_class.return_value
                    mock_agent.check_server_connection = AsyncMock(return_value=True)
                    mock_agent.check_model_available = AsyncMock(return_value=True)
                    
                    await app.startup()
                    
                    assert app.agent is not None
                    assert app.mcp_manager is not None
                    mock_manager.connect_all.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_command_quit(self):
        """Test handling quit command."""
        app = Application()
        app.ui = Mock()
        app.ui.running = True
        
        await app.handle_command("quit")
        
        assert app.ui.running is False
    
    @pytest.mark.asyncio
    async def test_handle_command_models(self):
        """Test handling models command."""
        app = Application()
        app.ui = Mock()
        app.agent = Mock()
        app.agent.list_models = AsyncMock(return_value=["model1", "model2"])
        app.config_manager = Mock()
        app.config_manager.ollama_config = Mock(model="model1")
        
        await app.handle_command("models")
        
        app.agent.list_models.assert_called_once()
        app.ui.display_models.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_command_changemodel(self):
        """Test handling changemodel command."""
        app = Application()
        app.ui = Mock()
        app.agent = Mock()
        app.agent.change_model = Mock(return_value=True)
        
        await app.handle_command("changemodel llama2")
        
        app.agent.change_model.assert_called_once_with("llama2")
        app.ui.display_info.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_command_invalid(self):
        """Test handling invalid command."""
        app = Application()
        app.ui = Mock()
        
        await app.handle_command("invalid")
        
        app.ui.display_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_prompt_empty(self):
        """Test handling empty prompt."""
        app = Application()
        app.ui = Mock()
        app.agent = Mock()
        
        await app.handle_prompt("")
        
        # Should not call process_prompt for empty input
        app.agent.process_prompt.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_prompt_with_text(self):
        """Test handling prompt with text."""
        app = Application()
        app.ui = Mock()
        app.agent = Mock()
        app.agent.process_prompt = AsyncMock(return_value="response")
        
        await app.handle_prompt("test prompt")
        
        app.agent.process_prompt.assert_called_once_with("test prompt")