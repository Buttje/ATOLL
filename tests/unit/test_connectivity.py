"""Tests for Ollama server connectivity checks."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from aiohttp import ClientTimeout
from atoll.agent.agent import OllamaMCPAgent
from atoll.main import Application
from atoll.config.models import OllamaConfig


class TestServerConnectivity:
    """Test server connectivity checks."""
    
    @pytest.mark.asyncio
    async def test_check_server_connection_success(self):
        """Test successful server connection check."""
        config = OllamaConfig(base_url="http://localhost", port=11434)
        mcp_manager = Mock()
        mcp_manager.tool_registry = Mock(tools={})
        ui = Mock()
        
        agent = OllamaMCPAgent(
            ollama_config=config,
            mcp_manager=mcp_manager,
            ui=ui
        )
        
        # Mock the aiohttp request
        with patch('aiohttp.ClientSession') as mock_session_class:
            # Create a mock response
            mock_response = AsyncMock()
            mock_response.status = 200
            
            # Create a mock context manager for the response
            mock_response_cm = MagicMock()
            mock_response_cm.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response_cm.__aexit__ = AsyncMock(return_value=None)
            
            # Create a mock session
            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=mock_response_cm)
            
            # Create a mock context manager for the session
            mock_session_cm = MagicMock()
            mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.__aexit__ = AsyncMock(return_value=None)
            
            mock_session_class.return_value = mock_session_cm
            
            result = await agent.check_server_connection()
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_check_server_connection_failure(self):
        """Test server connection check failure."""
        config = OllamaConfig(base_url="http://localhost", port=11434)
        mcp_manager = Mock()
        mcp_manager.tool_registry = Mock(tools={})
        ui = Mock()
        
        agent = OllamaMCPAgent(
            ollama_config=config,
            mcp_manager=mcp_manager,
            ui=ui
        )
        
        # Mock the aiohttp request to raise an exception
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__ = AsyncMock(side_effect=Exception("Connection failed"))
            
            result = await agent.check_server_connection()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_model_available_success(self):
        """Test model availability check when model exists."""
        config = OllamaConfig(base_url="http://localhost", port=11434, model="llama2")
        mcp_manager = Mock()
        mcp_manager.tool_registry = Mock(tools={})
        ui = Mock()
        
        agent = OllamaMCPAgent(
            ollama_config=config,
            mcp_manager=mcp_manager,
            ui=ui
        )
        
        # Mock list_models to return the configured model
        with patch.object(agent, 'list_models', return_value=["llama2", "mistral"]):
            result = await agent.check_model_available()
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_check_model_available_not_found(self):
        """Test model availability check when model doesn't exist."""
        config = OllamaConfig(base_url="http://localhost", port=11434, model="nonexistent")
        mcp_manager = Mock()
        mcp_manager.tool_registry = Mock(tools={})
        ui = Mock()
        
        agent = OllamaMCPAgent(
            ollama_config=config,
            mcp_manager=mcp_manager,
            ui=ui
        )
        
        # Mock list_models to not include the configured model
        with patch.object(agent, 'list_models', return_value=["llama2", "mistral"]):
            result = await agent.check_model_available()
            
            assert result is False


class TestSetServerCommand:
    """Test the setserver command."""
    
    @pytest.mark.asyncio
    async def test_setserver_command_success(self):
        """Test successful setserver command."""
        app = Application()
        
        # Mock dependencies
        from atoll.config.models import OllamaConfig
        app.config_manager.ollama_config = OllamaConfig()
        app.config_manager.mcp_config = Mock(servers={})
        
        app.agent = Mock()
        app.agent.ollama_config = OllamaConfig()
        app.agent._create_llm = Mock(return_value=Mock())
        app.agent.check_server_connection = AsyncMock(return_value=True)
        app.agent.check_model_available = AsyncMock(return_value=True)
        app.agent.llm = Mock()
        
        app.config_manager.save_ollama_config = Mock()
        app.ui = Mock()
        app.ui.display_info = Mock()
        app.ui.display_warning = Mock()
        
        await app.set_ollama_server("http://newserver", 11435)
        
        assert app.config_manager.ollama_config.base_url == "http://newserver"
        assert app.config_manager.ollama_config.port == 11435
        app.config_manager.save_ollama_config.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_setserver_command_failure_reverts(self):
        """Test setserver command failure reverts changes."""
        app = Application()
        
        # Mock dependencies
        from atoll.config.models import OllamaConfig
        original_url = "http://localhost"
        original_port = 11434
        
        app.config_manager.ollama_config = OllamaConfig(
            base_url=original_url,
            port=original_port
        )
        app.config_manager.mcp_config = Mock(servers={})
        
        app.agent = Mock()
        app.agent.ollama_config = OllamaConfig(
            base_url=original_url,
            port=original_port
        )
        app.agent._create_llm = Mock(return_value=Mock())
        app.agent.check_server_connection = AsyncMock(return_value=False)
        app.agent.llm = Mock()
        
        app.config_manager.save_ollama_config = Mock()
        app.ui = Mock()
        app.ui.display_info = Mock()
        app.ui.display_error = Mock()
        
        await app.set_ollama_server("http://badserver", 12345)
        
        # Should revert to original values
        assert app.config_manager.ollama_config.base_url == original_url
        assert app.config_manager.ollama_config.port == original_port
        app.config_manager.save_ollama_config.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_command_setserver_with_port(self):
        """Test handling setserver command with port."""
        app = Application()
        app.agent = Mock()
        app.ui = Mock()
        
        with patch.object(app, 'set_ollama_server', new_callable=AsyncMock) as mock_set:
            await app.handle_command("setserver http://localhost 11434")
            
            mock_set.assert_called_once_with("http://localhost", 11434)
    
    @pytest.mark.asyncio
    async def test_handle_command_setserver_without_port(self):
        """Test handling setserver command without port."""
        app = Application()
        app.agent = Mock()
        app.ui = Mock()
        
        with patch.object(app, 'set_ollama_server', new_callable=AsyncMock) as mock_set:
            await app.handle_command("setserver http://localhost")
            
            mock_set.assert_called_once_with("http://localhost", None)
    
    @pytest.mark.asyncio
    async def test_handle_command_setserver_invalid_port(self):
        """Test handling setserver command with invalid port."""
        app = Application()
        app.agent = Mock()
        app.ui = Mock()
        app.ui.display_error = Mock()
        
        await app.handle_command("setserver http://localhost notaport")
        
        app.ui.display_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_command_setserver_no_args(self):
        """Test handling setserver command without arguments."""
        app = Application()
        app.agent = Mock()
        app.ui = Mock()
        app.ui.display_error = Mock()
        
        await app.handle_command("setserver")
        
        app.ui.display_error.assert_called_once()
