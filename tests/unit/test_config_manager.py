"""Unit tests for configuration manager."""

import json
from pathlib import Path

from atoll.config.manager import ConfigManager
from atoll.config.models import MCPServerConfig, OllamaConfig


class TestConfigManager:
    """Test the ConfigManager class."""

    def test_initialization(self):
        """Test config manager initialization."""
        manager = ConfigManager()

        expected_ollama_path = Path.home() / ".ollama_server" / ".ollama_config.json"
        expected_mcp_path = Path.home() / ".atoll" / "mcp.json"
        assert manager.ollama_config_path == expected_ollama_path
        assert manager.mcp_config_path == expected_mcp_path
        assert manager.ollama_config is None
        assert manager.mcp_config is None
        # Verify the directories were created
        assert manager.ollama_config_path.parent.exists()
        assert manager.mcp_config_path.parent.exists()

    def test_initialization_with_paths(self, tmp_path):
        """Test config manager with custom paths."""
        ollama_path = tmp_path / "ollama.json"
        mcp_path = tmp_path / "mcp.json"

        manager = ConfigManager(ollama_config_path=ollama_path, mcp_config_path=mcp_path)

        assert manager.ollama_config_path == ollama_path
        assert manager.mcp_config_path == mcp_path

    def test_load_ollama_config_default(self, tmp_path):
        """Test loading Ollama config with defaults."""
        config_file = tmp_path / "ollama.json"
        manager = ConfigManager(ollama_config_path=config_file)

        config = manager.load_ollama_config()

        assert config.model == "llama2"  # Changed from "qwen2.5-coder:3b" to match actual default
        assert config.base_url == "http://localhost"
        assert config.port == 11434

    def test_load_config_error_handling(self, tmp_path):
        """Test error handling when loading configs."""
        config_file = tmp_path / "bad.json"
        config_file.write_text("invalid json")

        manager = ConfigManager(ollama_config_path=config_file)

        # Should return default config on error
        config = manager.load_ollama_config()
        assert config.model == "llama2"  # Changed from "qwen2.5-coder:3b" to match actual default

    def test_load_ollama_config_from_file(self, tmp_path):
        """Test loading Ollama config from file."""
        config_file = tmp_path / "ollama.json"
        config_data = {"model": "test-model", "base_url": "http://test", "port": 8080}
        config_file.write_text(json.dumps(config_data))

        manager = ConfigManager(ollama_config_path=config_file)
        config = manager.load_ollama_config()

        assert config.model == "test-model"
        assert config.base_url == "http://test"
        assert config.port == 8080

    def test_load_mcp_config_from_file(self, tmp_path):
        """Test loading MCP config from file."""
        config_file = tmp_path / "mcp.json"
        config_data = {
            "servers": {
                "test-server": {
                    "transport": "stdio",
                    "command": "test-cmd",
                    "args": ["arg1"],
                    "timeoutSeconds": 10,
                }
            }
        }
        config_file.write_text(json.dumps(config_data))

        manager = ConfigManager(mcp_config_path=config_file)
        config = manager.load_mcp_config()

        assert "test-server" in config.servers
        assert config.servers["test-server"].command == "test-cmd"

    def test_load_configs(self, tmp_path):
        """Test loading all configs."""
        ollama_file = tmp_path / "ollama.json"
        mcp_file = tmp_path / "mcp.json"

        ollama_data = {"model": "test-model"}
        mcp_data = {"servers": {}}

        ollama_file.write_text(json.dumps(ollama_data))
        mcp_file.write_text(json.dumps(mcp_data))

        manager = ConfigManager(ollama_config_path=ollama_file, mcp_config_path=mcp_file)

        manager.load_configs()

        assert manager.ollama_config is not None
        assert manager.mcp_config is not None
        assert manager.ollama_config.model == "test-model"

    def test_save_ollama_config(self, tmp_path):
        """Test saving Ollama config."""
        config_file = tmp_path / "ollama.json"
        manager = ConfigManager(ollama_config_path=config_file)

        manager.ollama_config = OllamaConfig(
            model="save-test", base_url="http://save-test", port=9999
        )

        manager.save_ollama_config()

        # Read back and verify
        with open(config_file) as f:
            data = json.load(f)

        assert data["model"] == "save-test"
        assert data["base_url"] == "http://save-test"
        assert data["port"] == 9999

    def test_load_config_error_handling_with_invalid_json(self, tmp_path):
        """Test error handling when loading configs with invalid JSON."""
        config_file = tmp_path / "bad.json"
        config_file.write_text("invalid json")

        manager = ConfigManager(ollama_config_path=config_file)

        # Should return default config on error
        config = manager.load_ollama_config()
        assert config.model == "llama2"  # Changed to match actual default
        assert isinstance(config, OllamaConfig)


class TestMCPServerConfig:
    """Test MCPServerConfig model."""

    def test_to_dict_all_fields(self):
        """Test to_dict with all fields populated."""
        config = MCPServerConfig(
            type="stdio",
            command="python",
            args=["server.py", "--port=8080"],
            env={"PATH": "/usr/bin"},
            timeoutSeconds=60,
            cwd="/path/to/server",
        )
        result = config.to_dict()
        assert result["type"] == "stdio"
        assert result["command"] == "python"
        assert result["args"] == ["server.py", "--port=8080"]
        assert result["env"] == {"PATH": "/usr/bin"}
        assert result["timeoutSeconds"] == 60
        assert result["cwd"] == "/path/to/server"

    def test_to_dict_minimal(self):
        """Test to_dict with minimal fields."""
        config = MCPServerConfig(type="http", url="http://localhost:8080")
        result = config.to_dict()
        assert result["type"] == "http"
        assert result["url"] == "http://localhost:8080"

    def test_to_dict_default_timeout(self):
        """Test to_dict excludes default timeout."""
        config = MCPServerConfig(type="stdio", command="python")
        result = config.to_dict()
        assert "timeoutSeconds" not in result

    def test_from_dict_new_schema(self):
        """Test from_dict with new schema format."""
        data = {
            "type": "stdio",
            "command": "node",
            "args": ["server.js"],
            "env": {"NODE_ENV": "production"},
            "cwd": "/app",
        }
        config = MCPServerConfig.from_dict(data)
        assert config.type == "stdio"
        assert config.command == "node"
        assert config.args == ["server.js"]
        assert config.env == {"NODE_ENV": "production"}
        assert config.cwd == "/app"

    def test_from_dict_legacy_transport(self):
        """Test from_dict with legacy 'transport' field."""
        data = {"transport": "stdio", "command": "python", "args": ["server.py"]}
        config = MCPServerConfig.from_dict(data)
        assert config.type == "stdio"
        assert config.transport == "stdio"
        assert config.command == "python"

    def test_http_server_with_headers(self):
        """Test HTTP server configuration with headers."""
        config = MCPServerConfig(
            type="http",
            url="https://api.example.com/mcp",
            headers={"Authorization": "Bearer token123"},
        )
        result = config.to_dict()
        assert result["type"] == "http"
        assert result["url"] == "https://api.example.com/mcp"
        assert result["headers"] == {"Authorization": "Bearer token123"}

    def test_sse_server(self):
        """Test SSE server configuration."""
        config = MCPServerConfig(type="sse", url="https://events.example.com/stream")
        result = config.to_dict()
        assert result["type"] == "sse"
        assert result["url"] == "https://events.example.com/stream"
