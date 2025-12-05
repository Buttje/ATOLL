"""Comprehensive tests for config manager."""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, mock_open
from atoll.config.manager import ConfigManager
from atoll.config.models import OllamaConfig, MCPConfig


class TestConfigManagerComprehensive:
    """Comprehensive tests for config manager."""
    
    def test_save_ollama_config(self, tmp_path):
        """Test saving Ollama config."""
        config_path = tmp_path / "ollama.json"
        manager = ConfigManager(ollama_config_path=config_path)
        
        manager.ollama_config = OllamaConfig(
            base_url="http://localhost",
            port=11434,
            model="test-model"
        )
        
        manager.save_ollama_config()
        
        assert config_path.exists()
        with open(config_path) as f:
            data = json.load(f)
            assert data["model"] == "test-model"
    
    def test_load_ollama_config_json_error(self, tmp_path):
        """Test loading Ollama config with JSON error."""
        config_path = tmp_path / "ollama.json"
        config_path.write_text("invalid json")
        
        manager = ConfigManager(ollama_config_path=config_path)
        config = manager.load_ollama_config()
        
        # Should return default config on error
        assert isinstance(config, OllamaConfig)
    
    def test_load_mcp_config_json_error(self, tmp_path):
        """Test loading MCP config with JSON error."""
        config_path = tmp_path / "mcp.json"
        config_path.write_text("invalid json")
        
        manager = ConfigManager(mcp_config_path=config_path)
        config = manager.load_mcp_config()
        
        # Should return default config on error
        assert isinstance(config, MCPConfig)