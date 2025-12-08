"""MCP Server Installer for ATOLL."""

import asyncio
import json
import logging
import os
import platform
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List
from urllib.parse import urlparse

import aiohttp

from ..config.models import MCPConfig, MCPServerConfig
from ..ui.terminal import TerminalUI
from .client import MCPClient


class MCPInstaller:
    """Handles installation of MCP servers from various sources."""

    def __init__(self, ui: TerminalUI, config_manager, agent):
        """Initialize the MCP installer.

        Args:
            ui: Terminal UI for user feedback
            config_manager: Configuration manager for saving config
            agent: Ollama agent for LLM-based README interpretation
        """
        self.ui = ui
        self.config_manager = config_manager
        self.agent = agent

        # Detect host OS
        self.os_type = platform.system()  # 'Windows', 'Linux', 'Darwin' (macOS)
        self.logger = logging.getLogger("mcp_installer")
        self.logger.info(f"Host OS detected: {self.os_type}")

        # Set up logging
        self.log_dir = Path.home() / ".atoll" / "log"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "mcp_install.log"

        # Configure logging
        self.logger.setLevel(logging.INFO)

        # File handler
        file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Server installation directory
        self.servers_dir = Path.home() / ".atoll" / "mcp_servers"
        self.servers_dir.mkdir(parents=True, exist_ok=True)

        # Container runtime preference
        self.container_runtime: Optional[str] = None

    def _check_command_exists(self, command: str) -> bool:
        """Check if a command exists on the system.

        Args:
            command: Command name to check

        Returns:
            True if command exists, False otherwise
        """
        return shutil.which(command) is not None

    async def _detect_container_runtime(self) -> Optional[str]:
        """Detect available container runtime (Docker or Podman).

        Returns:
            'docker', 'podman', or None
        """
        if self.container_runtime:
            return self.container_runtime

        has_docker = self._check_command_exists("docker")
        has_podman = self._check_command_exists("podman")

        if has_podman and has_docker:
            self.ui.display_info("Both Docker and Podman detected")
            self.ui.display_info("Podman is recommended for better security and rootless operation")
            response = input("Choose container runtime (docker/podman) [podman]: ").strip().lower()
            self.container_runtime = "podman" if response in ["", "podman"] else "docker"
        elif has_podman:
            self.container_runtime = "podman"
            self.ui.display_verbose("Using Podman as container runtime")
        elif has_docker:
            self.container_runtime = "docker"
            self.ui.display_verbose("Using Docker as container runtime")
        else:
            self.container_runtime = None

        return self.container_runtime

    async def _install_container_runtime(self) -> bool:
        """Install container runtime (Podman preferred).

        Returns:
            True if installation succeeded, False otherwise
        """
        self.ui.display_info("No container runtime detected (Docker/Podman)")
        self.ui.display_info("Podman is recommended for better security and rootless operation")
        response = input("Install container runtime? (yes/no) [yes]: ").strip().lower()

        if response in ["", "yes", "y"]:
            runtime_choice = input("Choose runtime to install (docker/podman) [podman]: ").strip().lower()
            runtime = "podman" if runtime_choice in ["", "podman"] else "docker"

            self.ui.display_info(f"Installing {runtime}...")
            self.logger.info(f"Installing {runtime} on {self.os_type}")

            try:
                if self.os_type == "Windows":
                    return await self._install_container_runtime_windows(runtime)
                elif self.os_type == "Linux":
                    return await self._install_container_runtime_linux(runtime)
                elif self.os_type == "Darwin":
                    return await self._install_container_runtime_macos(runtime)
                else:
                    self.ui.display_error(f"Unsupported OS: {self.os_type}")
                    return False
            except Exception as e:
                self.ui.display_error(f"Failed to install {runtime}: {e}")
                self.logger.error(f"Container runtime installation failed: {e}", exc_info=True)
                return False
        else:
            self.ui.display_info("Container runtime installation cancelled")
            return False

    async def _install_container_runtime_windows(self, runtime: str) -> bool:
        """Install container runtime on Windows."""
        if runtime == "podman":
            self.ui.display_info("Please install Podman Desktop from: https://podman.io/getting-started/installation")
            self.ui.display_info("Or use winget: winget install RedHat.Podman-Desktop")
            response = input("Press Enter after installation completes...")
            return self._check_command_exists("podman")
        else:
            self.ui.display_info("Please install Docker Desktop from: https://www.docker.com/products/docker-desktop")
            response = input("Press Enter after installation completes...")
            return self._check_command_exists("docker")

    async def _install_container_runtime_linux(self, runtime: str) -> bool:
        """Install container runtime on Linux."""
        if runtime == "podman":
            self.ui.display_info("Installing Podman via package manager...")
            # Try different package managers
            if self._check_command_exists("apt"):
                cmd = "sudo apt update && sudo apt install -y podman"
            elif self._check_command_exists("dnf"):
                cmd = "sudo dnf install -y podman"
            elif self._check_command_exists("yum"):
                cmd = "sudo yum install -y podman"
            elif self._check_command_exists("pacman"):
                cmd = "sudo pacman -S --noconfirm podman"
            else:
                self.ui.display_error("No supported package manager found")
                return False

            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0
        else:
            self.ui.display_info("Installing Docker...")
            self.ui.display_info("Please follow instructions at: https://docs.docker.com/engine/install/")
            response = input("Press Enter after installation completes...")
            return self._check_command_exists("docker")

    async def _install_container_runtime_macos(self, runtime: str) -> bool:
        """Install container runtime on macOS."""
        if runtime == "podman":
            if self._check_command_exists("brew"):
                self.ui.display_info("Installing Podman via Homebrew...")
                result = subprocess.run(
                    "brew install podman && podman machine init && podman machine start",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0
            else:
                self.ui.display_info("Please install Podman Desktop from: https://podman.io/getting-started/installation")
                response = input("Press Enter after installation completes...")
                return self._check_command_exists("podman")
        else:
            self.ui.display_info("Please install Docker Desktop from: https://www.docker.com/products/docker-desktop")
            response = input("Press Enter after installation completes...")
            return self._check_command_exists("docker")

    async def install_server(
        self,
        source: str,
        server_type: Optional[str] = None,
        name: Optional[str] = None,
    ) -> bool:
        """Install an MCP server from a source.

        Args:
            source: Source path/URL/command for the server
            server_type: Type of installation (dir, repo, url, cmd)
            name: Optional unique name for the server

        Returns:
            True if installation succeeded, False otherwise
        """
        try:
            self.logger.info(f"Starting installation: source={source}, type={server_type}, name={name}")
            self.ui.display_info(f"Installing MCP server from: {source}")

            # Detect type if not specified
            if not server_type:
                server_type = self._detect_source_type(source)
                self.logger.info(f"Detected source type: {server_type}")
                self.ui.display_verbose(f"Detected source type: {server_type}")

            # Generate name if not provided
            if not name:
                name = self._generate_server_name(source, server_type)
                self.ui.display_info(f"Generated server name: {name}")
                self.logger.info(f"Generated server name: {name}")

            # Check for duplicate names
            if not self._validate_unique_name(name):
                self.ui.display_error(f"Server name '{name}' already exists")
                self.logger.error(f"Duplicate server name: {name}")
                return False

            # Route to appropriate installation method
            if server_type == "dir":
                return await self._install_from_directory(source, name)
            elif server_type == "repo":
                return await self._install_from_repository(source, name)
            elif server_type == "url":
                return await self._install_from_url(source, name)
            elif server_type == "cmd":
                return await self._install_from_command(source, name)
            else:
                self.ui.display_error(f"Unknown server type: {server_type}")
                self.logger.error(f"Unknown server type: {server_type}")
                return False

        except Exception as e:
            self.ui.display_error(f"Installation failed: {e}")
            self.logger.error(f"Installation failed: {e}", exc_info=True)
            self.ui.display_info(f"Check log file: {self.log_file}")
            return False

    def _detect_source_type(self, source: str) -> str:
        """Detect the type of installation source.

        Args:
            source: Source string to analyze

        Returns:
            Type string: 'dir', 'repo', 'url', or 'cmd'
        """
        # Check if it's a URL
        if source.startswith(("http://", "https://", "ws://", "wss://")):
            if "github.com" in source:
                return "repo"
            return "url"

        # Check if it's a local path
        path = Path(source)
        if path.exists():
            if path.is_dir():
                return "dir"
            elif path.is_file():
                return "cmd"

        # Default to command
        return "cmd"

    def _generate_server_name(self, source: str, server_type: str) -> str:
        """Generate a unique server name from the source.

        Args:
            source: Installation source
            server_type: Type of source

        Returns:
            Generated server name
        """
        if server_type == "dir":
            name = Path(source).name
        elif server_type == "repo":
            # Extract repository name from GitHub URL
            match = re.search(r"/([^/]+?)(?:\.git)?$", source)
            name = match.group(1) if match else "unknown-repo"
        elif server_type == "url":
            # Use hostname from URL
            parsed = urlparse(source)
            name = parsed.hostname or "unknown-url"
            name = name.replace(".", "-")
        else:
            name = "mcp-server"

        # Sanitize name
        name = re.sub(r"[^a-zA-Z0-9_-]", "-", name).lower()

        # Ensure uniqueness
        base_name = name
        counter = 1
        while not self._validate_unique_name(name):
            name = f"{base_name}-{counter}"
            counter += 1

        return name

    def _validate_unique_name(self, name: str) -> bool:
        """Check if a server name is unique.

        Args:
            name: Server name to check

        Returns:
            True if name is unique, False if it exists
        """
        if not self.config_manager.mcp_config:
            return True
        return name not in self.config_manager.mcp_config.servers

    async def _install_from_directory(self, dir_path: str, name: str) -> bool:
        """Install MCP server from a local directory.

        Args:
            dir_path: Path to directory containing the server
            name: Unique server name

        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Installing from directory: {dir_path}")
        self.ui.display_info(f"Installing from directory: {dir_path}")

        path = Path(dir_path)
        if not path.exists() or not path.is_dir():
            self.ui.display_error(f"Directory not found: {dir_path}")
            self.logger.error(f"Directory not found: {dir_path}")
            return False

        # Look for README
        readme = self._find_readme(path)
        if not readme:
            self.ui.display_error("No README found in directory")
            self.logger.error(f"No README found in {dir_path}")
            return False

        # Extract installation instructions using LLM
        install_command = await self._extract_install_command(readme, path)
        if not install_command:
            self.ui.display_error("Could not determine installation command")
            self.logger.error("Failed to extract installation command from README")
            return False

        # Execute installation
        if not await self._execute_install_command(install_command, path):
            return False

        # Find the server command
        server_command = await self._find_server_command(readme, path)
        if not server_command:
            self.ui.display_error("Could not determine server start command")
            self.logger.error("Failed to extract server command from README")
            return False

        # Validate server
        server_config = await self._create_server_config(name, "stdio", server_command, str(path))
        if not await self._validate_server(server_config):
            return False

        # Save configuration
        return self._save_server_config(name, server_config)

    async def _install_from_repository(self, repo_url: str, name: str) -> bool:
        """Install MCP server from a GitHub repository.

        Args:
            repo_url: GitHub repository URL
            name: Unique server name

        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Installing from repository: {repo_url}")
        self.ui.display_info(f"Cloning repository: {repo_url}")

        # Clone to servers directory
        target_dir = self.servers_dir / name

        if target_dir.exists():
            self.ui.display_error(f"Target directory already exists: {target_dir}")
            self.logger.error(f"Target directory exists: {target_dir}")
            return False

        # Clone repository
        try:
            subprocess.run(
                ["git", "clone", repo_url, str(target_dir)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.ui.display_info(f"Repository cloned to: {target_dir}")
            self.logger.info(f"Repository cloned successfully")
        except subprocess.CalledProcessError as e:
            self.ui.display_error(f"Failed to clone repository: {e.stderr}")
            self.logger.error(f"Git clone failed: {e.stderr}")
            return False
        except FileNotFoundError:
            self.ui.display_error("Git command not found. Please install git.")
            self.logger.error("Git command not available")
            return False

        # Continue with directory installation
        return await self._install_from_directory(str(target_dir), name)

    async def _install_from_url(self, url: str, name: str) -> bool:
        """Install MCP server from a URL (running server).

        Args:
            url: URL of running MCP server
            name: Unique server name

        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Installing from URL: {url}")
        self.ui.display_info(f"Connecting to server at: {url}")

        # Detect protocol
        parsed = urlparse(url)
        if parsed.scheme in ("http", "https"):
            transport = "http"
        elif parsed.scheme in ("ws", "wss"):
            self.ui.display_error("WebSocket transport not yet implemented")
            self.logger.error("WebSocket transport not supported")
            return False
        else:
            self.ui.display_error(f"Unsupported URL scheme: {parsed.scheme}")
            self.logger.error(f"Unsupported scheme: {parsed.scheme}")
            return False

        # Create server config
        server_config = await self._create_server_config(name, transport, "", url)

        # Validate server
        if not await self._validate_server(server_config):
            return False

        # Save configuration
        return self._save_server_config(name, server_config)

    async def _install_from_command(self, command: str, name: str) -> bool:
        """Install MCP server from a command.

        Args:
            command: Command to start the server
            name: Unique server name

        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Installing from command: {command}")
        self.ui.display_info(f"Configuring server command: {command}")

        # For now, assume it's a direct command
        # TODO: Add interactive prompts for args and env vars

        # Create server config
        server_config = await self._create_server_config(name, "stdio", command, "")

        # Validate server
        if not await self._validate_server(server_config):
            return False

        # Save configuration
        return self._save_server_config(name, server_config)

    def _find_readme(self, directory: Path) -> Optional[Path]:
        """Find README file in directory.

        Args:
            directory: Directory to search

        Returns:
            Path to README if found, None otherwise
        """
        for pattern in ["README.md", "README.txt", "README", "readme.md", "Readme.md"]:
            readme = directory / pattern
            if readme.exists():
                return readme
        return None

    async def _extract_install_command(self, readme: Path, directory: Path) -> Optional[str]:
        """Extract OS-specific installation command from README using LLM.

        Args:
            readme: Path to README file
            directory: Directory containing the README

        Returns:
            Installation command string or None
        """
        try:
            content = readme.read_text(encoding="utf-8", errors="ignore")
            self.logger.info(f"Analyzing README for {self.os_type} installation instructions")

            # Check if Docker/Podman container is an option
            has_docker_option = "docker" in content.lower() or "container" in content.lower()
            
            if has_docker_option:
                runtime = await self._detect_container_runtime()
                if not runtime:
                    if await self._install_container_runtime():
                        runtime = await self._detect_container_runtime()

                if runtime:
                    self.ui.display_info(f"Docker/Podman support detected, using {runtime}")
                    self.logger.info(f"Using container runtime: {runtime}")

            # Build OS-specific prompt
            os_name = {
                "Windows": "Windows",
                "Linux": "Linux",
                "Darwin": "macOS"
            }.get(self.os_type, self.os_type)

            prompt = f"""Analyze this README and extract the installation command(s) for {os_name}:

{content}

Host system: {os_name}
Container runtime available: {runtime if has_docker_option and runtime else "None"}

Provide ONLY the shell command needed to install this MCP server on {os_name}.
If Docker/Podman is available and the README supports it, prefer the container-based installation.
If multiple commands are needed, separate them with &&.
Do not include any explanation, just the command.
If no installation is needed, respond with: NONE"""

            try:
                response = await self.agent.process_prompt(prompt)
                command = response.strip()

                if command == "NONE" or not command:
                    return None

                # Resolve placeholders in the command
                command = await self._resolve_placeholders(command, directory)

                self.logger.info(f"Extracted install command: {command}")
                self.ui.display_verbose(f"Installation command: {command}")
                return command
            except Exception as llm_error:
                self.logger.error(f"LLM failed to process README: {llm_error}")
                self.ui.display_error(
                    "Failed to analyze README with LLM. Please ensure a valid Ollama model is configured."
                )
                self.ui.display_info(
                    "You can change the model with: changemodel <model-name>"
                )
                return None

        except Exception as e:
            self.logger.error(f"Failed to extract install command: {e}")
            return None

    async def _resolve_placeholders(self, command: str, directory: Path) -> str:
        """Resolve placeholders in installation/server commands.

        Args:
            command: Command with potential placeholders
            directory: Base directory for relative paths

        Returns:
            Command with resolved placeholders
        """
        self.logger.info("Resolving command placeholders")
        
        # Use forward slashes and escape backslashes for regex replacement
        dir_path = str(directory.absolute()).replace('\\', '/')
        
        # Common placeholder patterns
        placeholders = {
            r"{ABSOLUTE[_ ]PATH[_ ]TO[_ ]FILE[_ ]HERE}": dir_path,
            r"{ABSOLUTE[_ ]PATH}": dir_path,
            r"{PATH[_ ]TO[_ ]SERVER}": dir_path,
            r"{SERVER[_ ]PATH}": dir_path,
            r"{INSTALL[_ ]DIR}": dir_path,
            r"/path/to/(?:server|directory|file|install)": dir_path,
            r"<path[_ ]to[_ ](?:server|directory|file)>": dir_path,
        }

        original_command = command
        for pattern, replacement in placeholders.items():
            command = re.sub(pattern, replacement, command, flags=re.IGNORECASE)

        # Handle LLM/API endpoint placeholders - use ATOLL's Ollama server
        if "{LLM" in command.upper() or "{API" in command.upper() or "YOUR_API" in command.upper():
            ollama_url = f"{self.config_manager.ollama_config.base_url}:{self.config_manager.ollama_config.port}"
            llm_placeholders = {
                r"{LLM[_ ](?:SERVER|ENDPOINT|URL)}": ollama_url,
                r"{API[_ ](?:ENDPOINT|URL|KEY)}": ollama_url,
                r"YOUR_API_(?:ENDPOINT|URL)": ollama_url,
                r"<api[_ ]endpoint>": ollama_url,
            }
            for pattern, replacement in llm_placeholders.items():
                command = re.sub(pattern, replacement, command, flags=re.IGNORECASE)

        # If command changed, inform user
        if command != original_command:
            self.ui.display_verbose(f"Resolved placeholders in command")
            self.logger.info(f"Command before: {original_command}")
            self.logger.info(f"Command after: {command}")

        # Check for remaining unresolved placeholders
        remaining_placeholders = re.findall(r'{[^}]+}|<[^>]+>|\$\{[^}]+\}', command)
        if remaining_placeholders:
            self.ui.display_info(f"Command contains placeholders: {', '.join(remaining_placeholders)}")
            self.ui.display_info(f"Current command: {command}")
            response = input("Please provide the complete command or press Enter to use as-is: ").strip()
            if response:
                command = response

        return command

    async def _find_server_command(self, readme: Path, directory: Path) -> Optional[str]:
        """Extract OS-specific server start command from README using LLM.

        Args:
            readme: Path to README file
            directory: Directory containing the README

        Returns:
            Server start command or None
        """
        try:
            content = readme.read_text(encoding="utf-8", errors="ignore")
            self.logger.info(f"Analyzing README for {self.os_type} server start command")

            # Build OS-specific prompt
            os_name = {
                "Windows": "Windows",
                "Linux": "Linux",
                "Darwin": "macOS"
            }.get(self.os_type, self.os_type)

            prompt = f"""Analyze this README and extract the command to START the MCP server on {os_name}:

{content}

Host system: {os_name}

Provide ONLY the shell command needed to start/run this MCP server on {os_name}.
Do not include installation commands, just the command to run the server.
Do not include any explanation, just the command.
"""

            try:
                response = await self.agent.process_prompt(prompt)
                command = response.strip()

                if not command:
                    return None

                # Resolve placeholders in the command
                command = await self._resolve_placeholders(command, directory)

                self.logger.info(f"Extracted server command: {command}")
                self.ui.display_verbose(f"Server command: {command}")
                return command
            except Exception as llm_error:
                self.logger.error(f"LLM failed to process README: {llm_error}")
                self.ui.display_error(
                    "Failed to analyze README with LLM. Please ensure a valid Ollama model is configured."
                )
                return None

        except Exception as e:
            self.logger.error(f"Failed to extract server command: {e}")
            return None

    async def _execute_install_command(self, command: str, cwd: Path) -> bool:
        """Execute installation command.

        Args:
            command: Command to execute
            cwd: Working directory for command

        Returns:
            True if successful, False otherwise
        """
        self.ui.display_info(f"Executing: {command}")
        self.logger.info(f"Executing install command: {command}")

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd),
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                self.ui.display_info("Installation completed successfully")
                self.logger.info("Installation command succeeded")
                if stdout:
                    self.logger.info(f"stdout: {stdout.decode()}")
                return True
            else:
                self.ui.display_error(f"Installation failed with code {process.returncode}")
                self.logger.error(f"Installation failed: {stderr.decode()}")
                return False

        except Exception as e:
            self.ui.display_error(f"Failed to execute command: {e}")
            self.logger.error(f"Command execution failed: {e}")
            return False

    async def _create_server_config(
        self, name: str, transport: str, command: str, location: str
    ) -> MCPServerConfig:
        """Create server configuration object.

        Args:
            name: Server name
            transport: Transport type (stdio, http, sse)
            command: Command to start server (for stdio)
            location: URL or directory path

        Returns:
            MCPServerConfig object
        """
        config_dict = {"transport": transport}

        if transport == "stdio":
            # Parse command into parts
            parts = command.split()
            config_dict["command"] = parts[0] if parts else command
            config_dict["args"] = parts[1:] if len(parts) > 1 else []
            if location:
                config_dict["cwd"] = location
        elif transport == "http":
            config_dict["url"] = location
        elif transport == "sse":
            config_dict["url"] = location

        return MCPServerConfig.from_dict(config_dict)

    async def _validate_server(self, server_config: MCPServerConfig) -> bool:
        """Validate that an MCP server is functional.

        Args:
            server_config: Server configuration to validate

        Returns:
            True if server is valid, False otherwise
        """
        self.ui.display_info("Validating server...")
        self.logger.info("Starting server validation")

        try:
            # Create a temporary client
            client = MCPClient(server_config)

            # Connect
            await client.connect()
            self.logger.info("Server connection established")

            # List tools
            tools = await client.list_tools()
            if not tools:
                self.ui.display_error("Server has no tools")
                self.logger.error("Server validation failed: no tools")
                await client.disconnect()
                return False

            # Validate tool structure
            for tool in tools:
                if "name" not in tool or "description" not in tool:
                    self.ui.display_error(f"Invalid tool structure: {tool}")
                    self.logger.error(f"Tool missing required fields: {tool}")
                    await client.disconnect()
                    return False

            self.ui.display_info(f"✓ Server validated successfully ({len(tools)} tools)")
            self.logger.info(f"Server validation passed: {len(tools)} tools")

            await client.disconnect()
            return True

        except Exception as e:
            self.ui.display_error(f"Server validation failed: {e}")
            self.logger.error(f"Validation error: {e}", exc_info=True)
            return False

    def _save_server_config(self, name: str, server_config: MCPServerConfig) -> bool:
        """Save server configuration to MCP config file.

        Args:
            name: Server name
            server_config: Server configuration

        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Saving configuration for server: {name}")

            # Ensure MCP config exists
            if not self.config_manager.mcp_config:
                self.config_manager.mcp_config = MCPConfig()

            # Add server to configuration
            self.config_manager.mcp_config.servers[name] = server_config

            # Save to ~/.atoll/mcp_config.json
            config_dir = Path.home() / ".atoll"
            config_dir.mkdir(parents=True, exist_ok=True)
            config_file = config_dir / "mcp_config.json"

            config_dict = {"servers": {}}
            for srv_name, srv_config in self.config_manager.mcp_config.servers.items():
                config_dict["servers"][srv_name] = srv_config.to_dict()

            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2)

            self.ui.display_info(f"✓ Server '{name}' installed successfully")
            self.ui.display_info(f"Configuration saved to: {config_file}")
            self.logger.info(f"Configuration saved successfully to {config_file}")

            return True

        except Exception as e:
            self.ui.display_error(f"Failed to save configuration: {e}")
            self.logger.error(f"Configuration save failed: {e}", exc_info=True)
            return False
