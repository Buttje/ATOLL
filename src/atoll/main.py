"""Main entry point for ATOLL."""

import argparse
import asyncio
import sys
import warnings
from pathlib import Path
from typing import Optional

from .agent.agent import OllamaMCPAgent
from .agent.agent_manager import ATOLLAgentManager
from .config.manager import ConfigManager
from .mcp.server_manager import MCPServerManager
from .ui.colors import ColorScheme
from .ui.terminal import TerminalUI, UIMode
from .utils.logger import setup_logging

# Suppress ResourceWarning for unclosed transports on Windows
# This is a known issue with ProactorEventLoop subprocess cleanup
warnings.filterwarnings("ignore", category=ResourceWarning, message=".*unclosed transport.*")


class Application:
    """Main application controller."""

    def __init__(self):
        """Initialize application."""
        self.config_manager = ConfigManager()
        self.ui = TerminalUI()
        self.colors = ColorScheme()
        self.agent: Optional[OllamaMCPAgent] = None
        self.mcp_manager: Optional[MCPServerManager] = None
        self.agent_manager: Optional[ATOLLAgentManager] = None
        self.command_history: list[str] = []

    async def startup(self) -> None:
        """Perform startup sequence."""
        print(self.colors.header("Starting ATOLL..."))

        # Load configurations
        self.config_manager.load_configs()

        # Connect to Ollama FIRST - before any other connections
        print(self.colors.info("Connecting to Ollama..."))

        # Create MCP manager (needed for agent initialization)
        self.mcp_manager = MCPServerManager(self.config_manager.mcp_config, ui=self.ui)

        # Create agent with MCP manager
        self.agent = OllamaMCPAgent(
            ollama_config=self.config_manager.ollama_config,
            mcp_manager=self.mcp_manager,
            ui=self.ui,
        )

        # Test Ollama server connection
        server_reachable = await self.agent.check_server_connection()
        if server_reachable:
            print(
                self.colors.answer_text(
                    f"✓ Ollama server is reachable at {self.config_manager.ollama_config.base_url}:{self.config_manager.ollama_config.port}"
                )
            )

            # Check model availability
            model_available = await self.agent.check_model_available()
            if model_available:
                print(
                    self.colors.answer_text(
                        f"✓ Model '{self.config_manager.ollama_config.model}' is available"
                    )
                )
            else:
                print(
                    self.colors.warning(
                        f"⚠ Model '{self.config_manager.ollama_config.model}' is not available"
                    )
                )
                print(self.colors.info("  Use 'models' command to see available models"))
        else:
            print(
                self.colors.error(
                    f"✗ Cannot reach Ollama server at {self.config_manager.ollama_config.base_url}:{self.config_manager.ollama_config.port}"
                )
            )
            print(
                self.colors.info(
                    "  Please check if Ollama is running and the configuration is correct"
                )
            )
            # Graceful exit - cannot continue without Ollama
            print(self.colors.error("\nExiting ATOLL due to Ollama connection failure."))
            sys.exit(1)

        # Now connect to MCP servers (after Ollama is verified)
        await self.mcp_manager.connect_all()

        # Recreate agent tools with connected MCP servers
        self.agent.tools = self.agent._create_tools()

        # Discover and load ATOLL agents
        print(self.colors.info("Discovering ATOLL agents..."))
        agents_dir = Path("atoll_agents")
        self.agent_manager = ATOLLAgentManager(agents_dir)
        await self.agent_manager.load_all_agents()

        # Display discovered agents
        if self.agent_manager.loaded_agents:
            print(
                self.colors.answer_text(
                    f"✓ Detected {len(self.agent_manager.loaded_agents)} ATOLL agent(s):"
                )
            )
            for agent_name, agent_context in self.agent_manager.loaded_agents.items():
                print(self.colors.user_input(f"  • {agent_name}"))
                metadata = self.agent_manager.get_agent_metadata(agent_name)
                if metadata:
                    desc = metadata.get("description", "No description")
                    print(self.colors.reasoning(f"    {desc}"))
                if agent_context.mcp_manager:
                    servers = agent_context.mcp_manager.list_servers()
                    if servers:
                        print(self.colors.reasoning(f"    MCP Servers: {', '.join(servers)}"))
        else:
            print(self.colors.reasoning("  No ATOLL agents detected"))

        print(self.colors.final_response("✓ Startup complete!"))
        print()

        # Wait for user confirmation to continue
        return await self._wait_for_startup_confirmation()

    async def _wait_for_startup_confirmation(self) -> bool:
        """Wait for user to press Enter to continue or Escape to exit.

        Returns:
            True if user wants to continue, False if user wants to exit
        """
        print(self.colors.info("Press [Enter] to continue or [Escape] to exit..."))

        # Use the prompt_toolkit input handler
        from .ui.prompt_input import AtollInput

        handler = AtollInput()

        try:
            result = await handler.read_line_async("")
            # If ESC was pressed, result will be "ESC"
            if result == "ESC":
                print()
                return False
            # Any other input (including empty) means continue
            print()
            return True
        except (KeyboardInterrupt, EOFError):
            print()
            return False

    async def run(self) -> None:
        """Run the main application loop."""
        try:
            # Run startup and check if user wants to continue
            should_continue = await self.startup()

            if not should_continue:
                print(self.colors.info("Exiting before starting main loop..."))
                return

            self.ui.display_header()

            while self.ui.running:
                try:
                    # Get user input
                    user_input = await self.ui.get_input_async(history=self.command_history)

                    # Check for ESC key
                    if user_input == "ESC":
                        self.ui.toggle_mode()
                        continue

                    # Check for Ctrl+V key
                    if user_input == "CTRL_V":
                        self.ui.toggle_verbose()
                        continue

                    # Add non-empty commands to history
                    if user_input.strip():
                        self.command_history.append(user_input)

                    # Handle based on mode
                    if self.ui.mode == UIMode.COMMAND:
                        await self.handle_command(user_input)
                    else:
                        await self.handle_prompt(user_input)

                except KeyboardInterrupt:
                    print("\n" + self.colors.info("Exiting..."))
                    break
                except Exception as e:
                    self.ui.display_error(f"Unexpected error: {e}")
        except KeyboardInterrupt:
            print("\n" + self.colors.info("Exiting..."))
        finally:
            # Cleanup
            await self.shutdown()

    async def shutdown(self) -> None:
        """Perform cleanup on shutdown."""
        try:
            if self.agent_manager:
                await self.agent_manager.shutdown_all()
            if self.mcp_manager:
                await self.mcp_manager.disconnect_all()
        except Exception:
            pass  # Ignore errors during shutdown

    async def handle_command(self, command: str) -> None:
        """Handle command mode input."""
        # Strip whitespace but preserve case for arguments
        command = command.strip()

        # Split command into parts
        parts = command.split(None, 2)  # Split on whitespace, max 3 parts
        if not parts:
            return

        # First part is the command (case-insensitive)
        cmd = parts[0].lower()

        # Handle commands
        if cmd == "quit" or cmd == "exit":
            self.ui.running = False

        elif cmd == "help":
            if len(parts) == 1:
                # Just "help"
                self.display_help()
            elif len(parts) >= 2:
                # "help <subcommand> [argument]"
                subcmd = parts[1].lower()
                if subcmd == "server" and len(parts) == 3:
                    server_name = parts[2]  # Preserve case
                    self.display_server_help(server_name)
                elif subcmd == "tool" and len(parts) == 3:
                    tool_name = parts[2]  # Preserve case
                    self.display_tool_help(tool_name)
                elif len(parts) == 2:
                    # "help <command>" - display help for specific command
                    self.display_command_help(subcmd)
                else:
                    self.ui.display_error(
                        "Usage: 'help', 'help <command>', 'help server <name>', or 'help tool <name>'"
                    )
            else:
                self.display_help()

        elif cmd == "list":
            if len(parts) >= 2:
                list_type = parts[1].lower()
                await self.handle_list_command(list_type)
            else:
                self.ui.display_error("Usage: list <server|models|agents|mcp|tools>")

        # Keep legacy 'models' command for compatibility
        elif cmd == "models":
            await self.handle_list_command("models")

        elif cmd == "changemodel":
            if len(parts) >= 2:
                model_name = parts[1]  # Preserve case
                if self.agent.change_model(model_name):
                    self.ui.display_info(f"Model changed to: {model_name}")
                    # Update config and persist to file
                    self.config_manager.ollama_config.model = model_name
                    self.config_manager.save_ollama_config()
            else:
                self.ui.display_error("Usage: changemodel <model-name>")

        elif cmd == "clear" or cmd == "clearmemory":
            self.agent.clear_memory()

        elif cmd == "setserver":
            if len(parts) >= 2:
                # Parse url and port from arguments
                # Expected format: setserver <url> [port]
                # e.g., setserver http://localhost 11434
                url = parts[1]
                port = None

                if len(parts) >= 3:
                    try:
                        port = int(parts[2])
                    except ValueError:
                        self.ui.display_error("Invalid port number. Port must be an integer.")
                        return

                await self.set_ollama_server(url, port)
            else:
                self.ui.display_error("Usage: setserver <url> [port]")

        # Keep legacy commands for compatibility
        elif cmd == "servers":
            await self.handle_list_command("mcp")

        elif cmd == "tools":
            await self.handle_list_command("tools")

        elif cmd == "switchto":
            if len(parts) >= 2:
                agent_name = parts[1]  # Preserve case
                await self.handle_switchto_command(agent_name)
            else:
                self.ui.display_error("Usage: switchto <agent-name>")

        elif cmd == "back":
            await self.handle_back_command()

        else:
            self.ui.display_error(f"Unknown command: '{cmd}'. Type 'help' for available commands.")

    def display_help(self) -> None:
        """Display help information for available commands."""
        # Check if we're in an agent context
        if self.agent_manager and not self.agent_manager.is_top_level():
            help_text = f"""
ATOLL - Agent Commands ({self.agent_manager.current_context.name}):
---------------------------------------------------------------------
  help                    - Display this help message
  help mcp <name>         - Show details about agent's MCP server
  help tool <name>        - Show details about agent's tool
  list models             - List all available Ollama models
  list agents             - List sub-agents of this agent
  list mcp                - List agent's MCP servers
  list tools              - List agent's MCP tools
  changemodel <name>      - Switch to a different Ollama model
  switchto <agent>        - Switch to a sub-agent context
  back                    - Return to previous context
  quit                    - Exit ATOLL

Navigation:
-----------
  ESC                     - Toggle between Prompt and Command mode
  Ctrl+V                  - Toggle verbose output mode
  Ctrl+C                  - Exit ATOLL

Prompt Mode:
------------
  Enter natural language prompts to interact with the AI agent.
  This agent specializes in its domain capabilities.
"""
        else:
            help_text = """
ATOLL - Available Commands:
---------------------------
  help                    - Display this help message
  help server <name>      - Show details about a specific MCP server
  help tool <name>        - Show details about a specific tool
  list server             - Show Ollama server information
  list models             - List all available Ollama models
  list agents             - List available ATOLL agents
  list mcp                - List connected MCP servers
  list tools              - List available MCP tools
  changemodel <name>      - Switch to a different Ollama model
  setserver <url> [port]  - Configure Ollama server connection
  switchto <agent>        - Switch to an ATOLL agent context
  clear                   - Clear conversation memory
  quit                    - Exit ATOLL

Legacy Commands (deprecated, use 'list' instead):
-------------------------------------------------
  models                  - Same as 'list models'
  servers                 - Same as 'list mcp'
  tools                   - Same as 'list tools'

Navigation:
-----------
  ESC                     - Toggle between Prompt and Command mode
  Ctrl+V                  - Toggle verbose output mode
  Ctrl+C                  - Exit ATOLL

Prompt Mode:
------------
  Enter natural language prompts to interact with the AI agent.
  The agent will use available tools to answer your questions.

Examples:
---------
  > list agents
  > switchto GhidraATOLL
  > list mcp
  > help server ghidramcp
  > help tool decompile_function
  > changemodel llama2
  > setserver http://localhost 11434
  > back
  > quit
"""
        print(self.colors.info(help_text))

    def display_command_help(self, command: str) -> None:
        """Display detailed help for a specific command."""
        command_helps = {
            "help": """
Command: help
Usage: help [command|server <name>|tool <name>]

Display help information about ATOLL commands, MCP servers, or tools.

Examples:
  help                  - Show all available commands
  help models           - Show help for the 'models' command
  help server myserver  - Show details about 'myserver' MCP server
  help tool mytool      - Show details about 'mytool' tool
""",
            "list": """
Command: list
Usage: list <type>

Unified command to list various ATOLL resources and components.

Types:
  server  - Show Ollama server information (URL, port, active model)
  models  - List all available Ollama models (currently active highlighted)
  agents  - List available ATOLL agents in current context
  mcp     - List MCP servers in current context (top-level or agent-specific)
  tools   - List available MCP tools in current context

Examples:
  list server
  list models
  list agents
  list mcp
  list tools
""",
            "models": """
Command: models (deprecated - use 'list models')
Usage: models

List all available Ollama models on the configured server.
The currently active model is highlighted.

Example:
  models
""",
            "changemodel": """
Command: changemodel
Usage: changemodel <model-name>

Switch to a different Ollama model. The change is persisted
to the configuration file and will be used for all subsequent
prompts until changed again.

Arguments:
  <model-name>  - Name of the model (e.g., llama2, mistral, codellama)

Examples:
  changemodel llama2
  changemodel mistral:7b-instruct
""",
            "setserver": """
Command: setserver
Usage: setserver <url> [port]

Configure the Ollama server connection. Updates the base URL
and optionally the port. The change is persisted to the
configuration file. ATOLL will verify connectivity and model
availability before applying the change.

Arguments:
  <url>   - Base URL of the Ollama server (e.g., http://localhost)
  [port]  - Optional port number (default: 11434)

Examples:
  setserver http://localhost 11434
  setserver http://192.168.1.100
""",
            "clear": """
Command: clear
Usage: clear

Clear the conversation memory. This removes all previous messages
from the agent's memory, starting fresh. Useful when you want to
begin a new conversation context without the agent remembering
previous interactions.

Aliases: clearmemory

Example:
  clear
""",
            "switchto": """
Command: switchto
Usage: switchto <agent-name>

Switch the command context to a specific ATOLL agent. When in an agent
context, you can access agent-specific MCP servers and tools, and switch
to sub-agents if they exist.

Arguments:
  <agent-name>  - Name of the ATOLL agent to switch to

Examples:
  switchto GhidraATOLL
  list mcp           # Shows agent's MCP servers
  back               # Return to previous context
""",
            "back": """
Command: back
Usage: back

Return to the previous agent context. Works hierarchically - if you are
in a sub-agent, returns to its parent agent. If in a top-level agent,
returns to the main ATOLL context. Not available in main context.

Example:
  switchto GhidraATOLL
  # ... work in agent context ...
  back               # Return to main ATOLL
""",
            "servers": """
Command: servers (deprecated - use 'list mcp')
Usage: servers

List all connected MCP (Model Context Protocol) servers.
Shows server names and connection status.

Example:
  servers
""",
            "tools": """
Command: tools (deprecated - use 'list tools')
Usage: tools

List all available tools from connected MCP servers.
Tools are functions that the AI agent can invoke to perform
specific tasks or access external resources.

Example:
  tools
""",
            "quit": """
Command: quit
Usage: quit

Exit ATOLL and disconnect from all MCP servers.

Aliases: exit

Example:
  quit
""",
        }

        help_text = command_helps.get(command)
        if help_text:
            print(self.colors.info(help_text))
        else:
            self.ui.display_error(
                f"No help available for '{command}'. Use 'help' to see all available commands."
            )

    def display_server_help(self, server_name: str) -> None:
        """Display detailed help for a specific MCP server."""
        client = self.mcp_manager.get_client(server_name)

        if not client:
            self.ui.display_error(
                f"Server '{server_name}' not found. Use 'servers' to list available servers."
            )
            return

        # Get server configuration
        server_config = self.config_manager.mcp_config.servers.get(server_name)

        print()
        print(self.colors.header(f"{'=' * 60}"))
        print(self.colors.header(f"Server: {server_name}"))
        print(self.colors.header(f"{'=' * 60}"))
        print()

        # Connection status
        status = "✓ Connected" if client.connected else "✗ Disconnected"
        status_color = self.colors.answer_text if client.connected else self.colors.error
        print(status_color(f"Status: {status}"))
        print()

        # Server properties
        if server_config:
            print(self.colors.info("Configuration:"))
            print(self.colors.user_input(f"  Transport:  {server_config.transport}"))
            if server_config.command:
                print(self.colors.user_input(f"  Command:    {server_config.command}"))
            if server_config.args:
                print(self.colors.user_input(f"  Arguments:  {' '.join(server_config.args)}"))
            if server_config.url:
                print(self.colors.user_input(f"  URL:        {server_config.url}"))
            print(self.colors.user_input(f"  Timeout:    {server_config.timeoutSeconds}s"))
            if server_config.env:
                print(self.colors.user_input("  Environment:"))
                for key, value in server_config.env.items():
                    print(self.colors.user_input(f"    {key} = {value}"))
            print()

        # List tools provided by this server
        server_tools = self.mcp_manager.tool_registry.list_server_tools(server_name)
        if server_tools:
            print(self.colors.info(f"Tools provided ({len(server_tools)}):"))
            for tool_name in server_tools:
                tool_info = self.mcp_manager.tool_registry.get_tool(tool_name)
                description = tool_info.get("description", "No description")
                print(self.colors.answer_text(f"  • {tool_name}"))
                print(self.colors.reasoning(f"    {description}"))
            print()
            print(self.colors.info("Use 'help tool <name>' for detailed tool information."))
        else:
            print(self.colors.warning("No tools available from this server."))

        print()

    def display_tool_help(self, tool_name: str) -> None:
        """Display detailed help for a specific tool."""
        tool_info = self.mcp_manager.tool_registry.get_tool(tool_name)

        if not tool_info:
            self.ui.display_error(
                f"Tool '{tool_name}' not found. Use 'tools' to list available tools."
            )
            return

        print()
        print(self.colors.header(f"{'=' * 60}"))
        print(self.colors.header(f"Tool: {tool_name}"))
        print(self.colors.header(f"{'=' * 60}"))
        print()

        # Server information
        server = tool_info.get("server", "unknown")
        print(self.colors.info(f"Server: {server}"))
        print()

        # Description
        description = tool_info.get("description", "No description available")
        print(self.colors.answer_text("Description:"))
        print(self.colors.user_input(f"  {description}"))
        print()

        # Input schema / parameters
        input_schema = tool_info.get("inputSchema", {})
        if input_schema:
            print(self.colors.answer_text("Parameters:"))

            schema_type = input_schema.get("type", "object")
            properties = input_schema.get("properties", {})
            required = input_schema.get("required", [])

            if properties:
                for param_name, param_info in properties.items():
                    is_required = param_name in required
                    required_marker = " (required)" if is_required else " (optional)"

                    param_type = param_info.get("type", "any")
                    param_desc = param_info.get("description", "No description")

                    print(self.colors.user_input(f"  • {param_name}{required_marker}"))
                    print(self.colors.reasoning(f"    Type: {param_type}"))
                    print(self.colors.reasoning(f"    Description: {param_desc}"))

                    # Show enum values if available
                    if "enum" in param_info:
                        enum_values = ", ".join(str(v) for v in param_info["enum"])
                        print(self.colors.reasoning(f"    Allowed values: {enum_values}"))

                    # Show default value if available
                    if "default" in param_info:
                        print(self.colors.reasoning(f"    Default: {param_info['default']}"))

                    print()
            else:
                print(self.colors.reasoning(f"  Schema type: {schema_type}"))
                print(self.colors.reasoning("  No specific parameters defined"))
                print()
        else:
            print(self.colors.warning("No parameter information available"))
            print()

        # Usage example
        print(self.colors.answer_text("Usage:"))
        print(
            self.colors.reasoning(
                "  This tool can be invoked by the AI agent when processing prompts."
            )
        )
        print(
            self.colors.reasoning("  You can ask questions that require this tool's functionality.")
        )
        print()

    def display_servers(self) -> None:
        """Display connected MCP servers."""
        servers = self.mcp_manager.list_servers()
        if servers:
            print(self.colors.info("\nConnected MCP Servers:"))
            for server in servers:
                client = self.mcp_manager.get_client(server)
                status = "✓ Connected" if client and client.connected else "✗ Disconnected"
                status_color = (
                    self.colors.answer_text if client and client.connected else self.colors.error
                )
                print(self.colors.user_input(f"  • {server}"))
                print(status_color(f"    {status}"))
            print()
            print(self.colors.info("Use 'help server <name>' for detailed information."))
        else:
            print(self.colors.warning("\nNo MCP servers configured."))
        print()

    def display_tools(self) -> None:
        """Display available MCP tools."""
        tools = self.mcp_manager.tool_registry.list_tools()
        if tools:
            print(self.colors.info(f"\nAvailable Tools ({len(tools)}):"))
            for tool_name in tools:
                tool_info = self.mcp_manager.tool_registry.get_tool(tool_name)
                server = tool_info.get("server", "unknown")
                description = tool_info.get("description", "No description")
                print(self.colors.answer_text(f"  • {tool_name}"))
                print(self.colors.reasoning(f"    Server: {server}"))
                print(self.colors.reasoning(f"    Description: {description}"))
            print()
            print(self.colors.info("Use 'help tool <name>' for detailed information."))
        else:
            print(self.colors.warning("\nNo tools available."))
        print()

    async def handle_list_command(self, list_type: str) -> None:
        """Handle unified list command.

        Args:
            list_type: Type to list (server, models, agents, mcp, tools)
        """
        if list_type == "server":
            # List Ollama server info
            print(self.colors.info("\nOllama Server:"))
            print(self.colors.user_input(f"  URL: {self.config_manager.ollama_config.base_url}"))
            print(self.colors.user_input(f"  Port: {self.config_manager.ollama_config.port}"))
            print(self.colors.user_input(f"  Model: {self.config_manager.ollama_config.model}"))
            print()

        elif list_type == "models":
            models = await self.agent.list_models()
            self.ui.display_models(models, self.config_manager.ollama_config.model)

        elif list_type == "agents":
            # List available agents in current context
            agents = self.agent_manager.get_available_agents()
            if agents:
                context_name = (
                    "Main ATOLL"
                    if self.agent_manager.is_top_level()
                    else self.agent_manager.current_context.name
                )
                print(self.colors.info(f"\nATOLL Agents ({context_name}):"))
                for agent_name in agents:
                    metadata = self.agent_manager.get_agent_metadata(agent_name)
                    print(self.colors.answer_text(f"  • {agent_name}"))
                    if metadata:
                        desc = metadata.get("description", "No description")
                        print(self.colors.reasoning(f"    {desc}"))
                print()
                print(self.colors.info("Use 'switchto <agent-name>' to enter agent context"))
            else:
                print(self.colors.warning("\nNo ATOLL agents available"))
            print()

        elif list_type == "mcp":
            # List MCP servers for current context
            if self.agent_manager.current_context:
                # In agent context - show agent's MCP servers
                if self.agent_manager.current_context.mcp_manager:
                    servers = self.agent_manager.current_context.mcp_manager.list_servers()
                    print(
                        self.colors.info(
                            f"\nMCP Servers ({self.agent_manager.current_context.name}):"
                        )
                    )
                else:
                    servers = []
                    print(
                        self.colors.warning(
                            f"\n{self.agent_manager.current_context.name} has no MCP servers"
                        )
                    )
            else:
                # Top-level - show main MCP servers
                servers = self.mcp_manager.list_servers()
                print(self.colors.info("\nMCP Servers (Main):"))

            if servers:
                for server in servers:
                    if (
                        self.agent_manager.current_context
                        and self.agent_manager.current_context.mcp_manager
                    ):
                        client = self.agent_manager.current_context.mcp_manager.get_client(server)
                    else:
                        client = self.mcp_manager.get_client(server)

                    status = "✓ Connected" if client and client.connected else "✗ Disconnected"
                    status_color = (
                        self.colors.answer_text
                        if client and client.connected
                        else self.colors.error
                    )
                    print(self.colors.user_input(f"  • {server}"))
                    print(status_color(f"    {status}"))
                print()
                print(self.colors.info("Use 'help server <name>' for detailed information"))
            print()

        elif list_type == "tools":
            # List tools for current context
            if self.agent_manager.current_context:
                # In agent context - show agent's tools
                if self.agent_manager.current_context.mcp_manager:
                    tools = (
                        self.agent_manager.current_context.mcp_manager.tool_registry.list_tools()
                    )
                    context_name = self.agent_manager.current_context.name
                else:
                    tools = []
                    context_name = self.agent_manager.current_context.name
            else:
                # Top-level - show main tools
                tools = self.mcp_manager.tool_registry.list_tools()
                context_name = "Main"

            if tools:
                print(self.colors.info(f"\nAvailable Tools ({context_name}, {len(tools)} total):"))
                for tool_name in tools:
                    if (
                        self.agent_manager.current_context
                        and self.agent_manager.current_context.mcp_manager
                    ):
                        tool_info = (
                            self.agent_manager.current_context.mcp_manager.tool_registry.get_tool(
                                tool_name
                            )
                        )
                    else:
                        tool_info = self.mcp_manager.tool_registry.get_tool(tool_name)

                    server = tool_info.get("server", "unknown")
                    description = tool_info.get("description", "No description")
                    print(self.colors.answer_text(f"  • {tool_name}"))
                    print(self.colors.reasoning(f"    Server: {server}"))
                    print(self.colors.reasoning(f"    Description: {description}"))
                print()
                print(self.colors.info("Use 'help tool <name>' for detailed information"))
            else:
                print(self.colors.warning(f"\nNo tools available in {context_name} context"))
            print()

        else:
            self.ui.display_error(f"Unknown list type: '{list_type}'")
            self.ui.display_info("Usage: list <server|models|agents|mcp|tools>")

    async def handle_switchto_command(self, agent_name: str) -> None:
        """Handle switchto command to enter agent context."""
        if self.agent_manager.switch_to_agent(agent_name):
            self.ui.display_info(f"✓ Switched to agent: {agent_name}")
            self.ui.display_info(
                "Available commands: help, list models, list agents, list mcp, list tools, changemodel, switchto, back"
            )

            # Update UI to show agent context
            context_info = f"[{agent_name}]"
            self.ui.display_info(f"Context: {context_info}")
        else:
            self.ui.display_error(f"Agent '{agent_name}' not found")
            self.ui.display_info("Use 'list agents' to see available agents")

    async def handle_back_command(self) -> None:
        """Handle back command to return to previous context."""
        if self.agent_manager.is_top_level():
            self.ui.display_warning("Already at top level")
        elif self.agent_manager.go_back():
            if self.agent_manager.current_context:
                self.ui.display_info(
                    f"✓ Returned to agent: {self.agent_manager.current_context.name}"
                )
            else:
                self.ui.display_info("✓ Returned to Main ATOLL")
        else:
            self.ui.display_error("Cannot go back")

    async def set_ollama_server(self, url: str, port: Optional[int] = None) -> None:
        """Set Ollama server connection properties."""
        # Update config
        old_url = self.config_manager.ollama_config.base_url
        old_port = self.config_manager.ollama_config.port

        self.config_manager.ollama_config.base_url = url
        if port is not None:
            self.config_manager.ollama_config.port = port

        # Test connection with new settings
        self.ui.display_info(
            f"Testing connection to {url}:{self.config_manager.ollama_config.port}..."
        )

        # Recreate the agent's LLM with new settings
        self.agent.ollama_config.base_url = url
        if port is not None:
            self.agent.ollama_config.port = port
        self.agent.llm = self.agent._create_llm()

        # Check if server is reachable
        server_reachable = await self.agent.check_server_connection()

        if server_reachable:
            self.ui.display_info(
                f"✓ Successfully connected to {url}:{self.config_manager.ollama_config.port}"
            )

            # Save to config file
            self.config_manager.save_ollama_config()
            self.ui.display_info("Configuration saved")

            # Check model availability
            model_available = await self.agent.check_model_available()
            if model_available:
                self.ui.display_info(
                    f"✓ Model '{self.config_manager.ollama_config.model}' is available"
                )
            else:
                self.ui.display_warning(
                    f"⚠ Model '{self.config_manager.ollama_config.model}' is not available on this server"
                )
        else:
            # Revert changes
            self.config_manager.ollama_config.base_url = old_url
            self.config_manager.ollama_config.port = old_port
            self.agent.ollama_config.base_url = old_url
            self.agent.ollama_config.port = old_port
            self.agent.llm = self.agent._create_llm()

            self.ui.display_error(
                f"✗ Failed to connect to {url}:{port if port else self.config_manager.ollama_config.port}"
            )
            self.ui.display_info(
                "Configuration not saved. Server connection restored to previous settings."
            )

    async def handle_prompt(self, prompt: str) -> None:
        """Handle prompt mode input."""
        if prompt.strip():
            await self.agent.process_prompt(prompt)


def get_version() -> str:
    """Get the ATOLL version."""
    # Import here to avoid circular import
    from . import __version__

    return __version__


def main():
    """Main entry point."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        prog="atoll",
        description="ATOLL - Agentic Tools Orchestration on OLLama",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"ATOLL {get_version()}",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    # Setup logging
    log_level = "DEBUG" if args.debug else "WARNING"
    setup_logging(level=log_level)

    try:
        app = Application()
        asyncio.run(app.run())
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully without showing traceback
        print("\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
