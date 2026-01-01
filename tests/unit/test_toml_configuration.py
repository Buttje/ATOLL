"""Acceptance tests for TOML Agent Configuration (FR-D007, FR-H003).

Test IDs: TEST-D008
Requirements: FR-D007 (TOML configuration), FR-H003 (per-agent LLM config)
"""

import tempfile
from pathlib import Path

import pytest

from atoll.config.models import (
    MCPServerConfig,
    OllamaConfig,
    TOMLAgentConfig,
    TOMLAgentDependencies,
    TOMLAgentLLMConfig,
    TOMLAgentMetadata,
    TOMLAgentResources,
    TOMLSubAgentConfig,
)


class TestTOMLAgentConfigStructure:
    """TEST-D008: TOML configuration file structure and validation."""

    def test_toml_agent_metadata_section(self):
        """Verify [agent] section structure."""
        # GIVEN: Agent metadata dictionary
        metadata_dict = {
            "name": "GhidraAgent",
            "version": "1.0.0",
            "description": "Binary analysis agent",
            "author": "ATOLL Team",
            "license": "MIT",
            "capabilities": ["decompilation", "analysis", "reverse_engineering"],
        }

        # WHEN: Metadata is created
        metadata = TOMLAgentMetadata.from_dict(metadata_dict)

        # THEN: All fields are correctly parsed
        assert metadata.name == "GhidraAgent"
        assert metadata.version == "1.0.0"
        assert metadata.description == "Binary analysis agent"
        assert metadata.author == "ATOLL Team"
        assert metadata.license == "MIT"
        assert len(metadata.capabilities) == 3
        assert "decompilation" in metadata.capabilities

    def test_toml_llm_config_section(self):
        """Verify [llm] section structure."""
        # GIVEN: LLM config dictionary
        llm_dict = {
            "model": "codellama:7b",
            "temperature": 0.3,
            "top_p": 0.95,
            "max_tokens": 4096,
            "request_timeout": 60,
            "system_prompt": "You are a specialized binary analysis agent.",
        }

        # WHEN: LLM config is created
        llm_config = TOMLAgentLLMConfig.from_dict(llm_dict)

        # THEN: All fields are correctly parsed
        assert llm_config.model == "codellama:7b"
        assert llm_config.temperature == 0.3
        assert llm_config.top_p == 0.95
        assert llm_config.max_tokens == 4096
        assert llm_config.request_timeout == 60
        assert "specialized binary analysis" in llm_config.system_prompt

    def test_toml_dependencies_section(self):
        """Verify [dependencies] section structure."""
        # GIVEN: Dependencies dictionary
        deps_dict = {
            "python": ">=3.9",
            "packages": ["pydantic>=2.0", "aiohttp>=3.9", "numpy>=1.24"],
        }

        # WHEN: Dependencies are created
        deps = TOMLAgentDependencies.from_dict(deps_dict)

        # THEN: All fields are correctly parsed
        assert deps.python == ">=3.9"
        assert len(deps.packages) == 3
        assert "pydantic>=2.0" in deps.packages

    def test_toml_resources_section(self):
        """Verify [resources] section structure."""
        # GIVEN: Resources dictionary
        resources_dict = {
            "cpu_limit": 2.0,
            "memory_limit": "4GB",
            "timeout": 300,
        }

        # WHEN: Resources are created
        resources = TOMLAgentResources.from_dict(resources_dict)

        # THEN: All fields are correctly parsed
        assert resources.cpu_limit == 2.0
        assert resources.memory_limit == "4GB"
        assert resources.timeout == 300

    def test_toml_mcp_servers_section(self):
        """Verify [mcp_servers.*] section structure."""
        # GIVEN: MCP server config dictionary
        server_dict = {
            "type": "stdio",
            "command": "python",
            "args": ["-m", "ghidra_mcp_server"],
            "env": {"GHIDRA_INSTALL_DIR": "/opt/ghidra"},
        }

        # WHEN: Server config is created
        server_config = MCPServerConfig.from_dict(server_dict)

        # THEN: All fields are correctly parsed
        assert server_config.type == "stdio"
        assert server_config.command == "python"
        assert len(server_config.args) == 2
        assert server_config.args[0] == "-m"
        assert server_config.env["GHIDRA_INSTALL_DIR"] == "/opt/ghidra"

    def test_toml_sub_agents_section(self):
        """Verify [sub_agents.*] section structure."""
        # GIVEN: Sub-agent config dictionary
        sub_agent_dict = {
            "url": "http://agent-server-1:8000",
            "auth_token": "secret-token",
            "health_check_interval": 30,
        }

        # WHEN: Sub-agent config is created
        sub_agent = TOMLSubAgentConfig.from_dict(sub_agent_dict)

        # THEN: All fields are correctly parsed
        assert sub_agent.url == "http://agent-server-1:8000"
        assert sub_agent.auth_token == "secret-token"
        assert sub_agent.health_check_interval == 30


class TestTOMLConfigParsing:
    """Test parsing of complete TOML configuration files."""

    def test_parse_complete_toml_config_from_dict(self):
        """Verify complete TOML config parses from dictionary."""
        # GIVEN: Complete TOML configuration dictionary
        config_dict = {
            "agent": {
                "name": "GhidraAgent",
                "version": "1.0.0",
                "description": "Binary analysis agent",
                "capabilities": ["decompilation"],
            },
            "llm": {
                "model": "codellama:7b",
                "temperature": 0.3,
            },
            "dependencies": {
                "python": ">=3.9",
                "packages": ["pydantic>=2.0"],
            },
            "resources": {
                "cpu_limit": 2.0,
                "memory_limit": "4GB",
            },
            "mcp_servers": {
                "ghidramcp": {
                    "type": "stdio",
                    "command": "python",
                    "args": ["-m", "ghidra_mcp_server"],
                }
            },
            "sub_agents": {
                "decompiler-1": {
                    "url": "http://agent-1:8000",
                    "health_check_interval": 30,
                }
            },
        }

        # WHEN: Config is parsed
        config = TOMLAgentConfig.from_dict(config_dict)

        # THEN: All sections are present and correct
        assert config.agent.name == "GhidraAgent"
        assert config.llm.model == "codellama:7b"
        assert config.dependencies.python == ">=3.9"
        assert config.resources.cpu_limit == 2.0
        assert "ghidramcp" in config.mcp_servers
        assert "decompiler-1" in config.sub_agents

    def test_parse_minimal_toml_config(self):
        """Verify minimal TOML config (only [agent] section)."""
        # GIVEN: Minimal config dictionary
        config_dict = {
            "agent": {
                "name": "SimpleAgent",
                "version": "1.0.0",
            }
        }

        # WHEN: Config is parsed
        config = TOMLAgentConfig.from_dict(config_dict)

        # THEN: Required fields are present, optional are None/empty
        assert config.agent.name == "SimpleAgent"
        assert config.llm is None
        assert config.dependencies is None
        assert config.resources is None
        assert len(config.mcp_servers) == 0
        assert len(config.sub_agents) == 0

    def test_parse_toml_file(self):
        """Verify loading TOML from actual file."""
        # GIVEN: TOML file content
        toml_content = """
[agent]
name = "TestAgent"
version = "1.0.0"
description = "Test agent"
capabilities = ["testing"]

[llm]
model = "llama2"
temperature = 0.5

[dependencies]
python = ">=3.9"
packages = ["pydantic>=2.0"]
"""

        # Create temporary TOML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            temp_path = f.name

        try:
            # WHEN: TOML file is loaded
            config = TOMLAgentConfig.from_toml_file(temp_path)

            # THEN: Config is correctly parsed
            assert config.agent.name == "TestAgent"
            assert config.agent.version == "1.0.0"
            assert config.llm.model == "llama2"
            assert config.llm.temperature == 0.5
            assert config.dependencies.python == ">=3.9"

        finally:
            # Cleanup
            Path(temp_path).unlink()

    def test_parse_toml_file_not_found(self):
        """Verify error handling for missing TOML file."""
        # GIVEN: Non-existent file path
        fake_path = "/nonexistent/agent.toml"

        # WHEN/THEN: Loading raises FileNotFoundError
        with pytest.raises(FileNotFoundError):
            TOMLAgentConfig.from_toml_file(fake_path)


class TestLLMConfigMerging:
    """Test LLM configuration inheritance and merging."""

    def test_merge_agent_config_overrides_parent(self):
        """Verify agent LLM config overrides parent values."""
        # GIVEN: Parent config and agent overrides
        parent = OllamaConfig(
            base_url="http://localhost",
            port=11434,
            model="llama2",
            temperature=0.7,
            top_p=0.9,
            max_tokens=2048,
        )

        agent_llm = TOMLAgentLLMConfig(
            model="codellama:7b",  # Override
            temperature=0.3,  # Override
            # top_p, max_tokens not specified - use parent
        )

        # WHEN: Configs are merged
        merged = agent_llm.merge_with_parent(parent)

        # THEN: Agent values override, parent fills gaps
        assert merged.model == "codellama:7b"  # From agent
        assert merged.temperature == 0.3  # From agent
        assert merged.top_p == 0.9  # From parent
        assert merged.max_tokens == 2048  # From parent
        assert merged.base_url == "http://localhost"  # Always parent
        assert merged.port == 11434  # Always parent

    def test_merge_preserves_parent_network_settings(self):
        """Verify base_url and port always come from parent."""
        # GIVEN: Parent and agent configs
        parent = OllamaConfig(
            base_url="http://production-server",
            port=8080,
            model="llama2",
        )

        agent_llm = TOMLAgentLLMConfig(
            model="codellama:7b",
            # No base_url/port in agent config (they shouldn't be)
        )

        # WHEN: Configs are merged
        merged = agent_llm.merge_with_parent(parent)

        # THEN: Network settings are from parent
        assert merged.base_url == "http://production-server"
        assert merged.port == 8080

    def test_merge_with_all_agent_overrides(self):
        """Verify merge when agent overrides all settings."""
        # GIVEN: Parent and comprehensive agent overrides
        parent = OllamaConfig(
            model="llama2",
            temperature=0.7,
            top_p=0.9,
            max_tokens=2048,
            request_timeout=30,
        )

        agent_llm = TOMLAgentLLMConfig(
            model="codellama:13b",
            temperature=0.2,
            top_p=0.95,
            max_tokens=4096,
            request_timeout=60,
        )

        # WHEN: Configs are merged
        merged = agent_llm.merge_with_parent(parent)

        # THEN: All agent values are used
        assert merged.model == "codellama:13b"
        assert merged.temperature == 0.2
        assert merged.top_p == 0.95
        assert merged.max_tokens == 4096
        assert merged.request_timeout == 60

    def test_merge_with_no_agent_overrides(self):
        """Verify merge when agent has no LLM overrides."""
        # GIVEN: Parent config and empty agent overrides
        parent = OllamaConfig(
            model="llama2",
            temperature=0.7,
            top_p=0.9,
            max_tokens=2048,
        )

        agent_llm = TOMLAgentLLMConfig()  # All None

        # WHEN: Configs are merged
        merged = agent_llm.merge_with_parent(parent)

        # THEN: All parent values are used
        assert merged.model == "llama2"
        assert merged.temperature == 0.7
        assert merged.top_p == 0.9
        assert merged.max_tokens == 2048


class TestTOMLConfigValidation:
    """Test TOML configuration validation and error handling."""

    def test_agent_section_required(self):
        """Verify [agent] section is required."""
        # GIVEN: Config without agent section
        config_dict = {
            "llm": {"model": "llama2"},
        }

        # WHEN/THEN: Parsing should handle missing agent section
        # (Implementation note: Currently from_dict expects agent.name which is required)
        with pytest.raises(TypeError):
            TOMLAgentConfig.from_dict(config_dict)

    def test_agent_name_required(self):
        """Verify agent.name is required field."""
        # GIVEN: Config with agent but no name
        config_dict = {
            "agent": {
                "version": "1.0.0",
                # name is missing
            }
        }

        # WHEN/THEN: Should raise error for missing name
        with pytest.raises(TypeError):
            TOMLAgentConfig.from_dict(config_dict)

    def test_multiple_mcp_servers(self):
        """Verify multiple MCP servers can be configured."""
        # GIVEN: Config with multiple MCP servers
        config_dict = {
            "agent": {"name": "MultiAgent", "version": "1.0.0"},
            "mcp_servers": {
                "server1": {
                    "type": "stdio",
                    "command": "python",
                    "args": ["-m", "server1"],
                },
                "server2": {
                    "type": "http",
                    "url": "http://localhost:9000",
                },
                "server3": {
                    "type": "sse",
                    "url": "http://localhost:9001/sse",
                },
            },
        }

        # WHEN: Config is parsed
        config = TOMLAgentConfig.from_dict(config_dict)

        # THEN: All servers are parsed
        assert len(config.mcp_servers) == 3
        assert "server1" in config.mcp_servers
        assert "server2" in config.mcp_servers
        assert "server3" in config.mcp_servers
        assert config.mcp_servers["server1"].type == "stdio"
        assert config.mcp_servers["server2"].type == "http"
        assert config.mcp_servers["server3"].type == "sse"

    def test_multiple_sub_agents(self):
        """Verify multiple sub-agents can be configured."""
        # GIVEN: Config with multiple sub-agents
        config_dict = {
            "agent": {"name": "ParentAgent", "version": "1.0.0"},
            "sub_agents": {
                "child1": {
                    "url": "http://agent1:8000",
                    "health_check_interval": 30,
                },
                "child2": {
                    "url": "http://agent2:8000",
                    "auth_token": "token2",
                    "health_check_interval": 60,
                },
            },
        }

        # WHEN: Config is parsed
        config = TOMLAgentConfig.from_dict(config_dict)

        # THEN: All sub-agents are parsed
        assert len(config.sub_agents) == 2
        assert "child1" in config.sub_agents
        assert "child2" in config.sub_agents
        assert config.sub_agents["child1"].url == "http://agent1:8000"
        assert config.sub_agents["child2"].auth_token == "token2"


class TestTOMLConfigExamples:
    """Test with realistic example configurations."""

    def test_ghidra_agent_config(self):
        """Test realistic Ghidra agent configuration."""
        # GIVEN: Ghidra agent TOML config
        config_dict = {
            "agent": {
                "name": "GhidraAgent",
                "version": "1.0.0",
                "description": "Specialized agent for binary analysis using Ghidra",
                "author": "ATOLL Team",
                "capabilities": ["binary_analysis", "decompilation", "reverse_engineering"],
            },
            "llm": {
                "model": "codellama:7b",
                "temperature": 0.3,
                "system_prompt": "You are a specialized binary analysis agent.",
            },
            "dependencies": {
                "python": ">=3.9",
                "packages": ["pydantic>=2.0", "aiohttp>=3.9"],
            },
            "resources": {
                "cpu_limit": 2.0,
                "memory_limit": "4GB",
                "timeout": 300,
            },
            "mcp_servers": {
                "ghidramcp": {
                    "type": "stdio",
                    "command": "python",
                    "args": ["-m", "ghidra_mcp_server"],
                }
            },
        }

        # WHEN: Config is parsed
        config = TOMLAgentConfig.from_dict(config_dict)

        # THEN: All sections are correct
        assert config.agent.name == "GhidraAgent"
        assert config.llm.model == "codellama:7b"
        assert config.resources.cpu_limit == 2.0
        assert "ghidramcp" in config.mcp_servers

    def test_distributed_agent_config(self):
        """Test agent configuration with sub-agents for distributed mode."""
        # GIVEN: Distributed agent config
        config_dict = {
            "agent": {
                "name": "DistributedCoordinator",
                "version": "1.0.0",
            },
            "sub_agents": {
                "worker-1": {
                    "url": "http://worker1.local:8000",
                    "auth_token": "token1",
                },
                "worker-2": {
                    "url": "http://worker2.local:8000",
                    "auth_token": "token2",
                },
                "worker-3": {
                    "url": "http://worker3.local:8000",
                    "auth_token": "token3",
                },
            },
        }

        # WHEN: Config is parsed
        config = TOMLAgentConfig.from_dict(config_dict)

        # THEN: Sub-agents are configured for load balancing
        assert len(config.sub_agents) == 3
        assert all(f"worker-{i}" in config.sub_agents for i in range(1, 4))


# Pytest fixtures
@pytest.fixture
def sample_toml_config_dict():
    """Fixture providing sample TOML config dictionary."""
    return {
        "agent": {
            "name": "SampleAgent",
            "version": "1.0.0",
            "description": "Sample test agent",
        },
        "llm": {
            "model": "llama2",
            "temperature": 0.5,
        },
    }


@pytest.fixture
def sample_parent_ollama_config():
    """Fixture providing sample parent Ollama config."""
    return OllamaConfig(
        base_url="http://localhost",
        port=11434,
        model="llama2",
        temperature=0.7,
        max_tokens=2048,
    )
