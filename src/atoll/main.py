"""Main entry point for ATOLL."""

import argparse
import asyncio
import sys
from typing import Optional

from .agent.agent import OllamaMCPAgent
from .config.manager import ConfigManager
from .mcp.server_manager import MCPServerManager
from .ui.colors import ColorScheme
from .ui.terminal import TerminalUI, UIMode


class Application:
    """Main application controller."""

    def __init__(self):
        """Initialize application."""
        self.config_manager = ConfigManager()
        self.ui = TerminalUI()
        self.colors = ColorScheme()
        self.agent: Optional[OllamaMCPAgent] = None
        self.mcp_manager: Optional[MCPServerManager] = None

    async def startup(self) -> None:
        """Perform startup sequence."""
        print(self.colors.header("Starting ATOLL..."))

        # Load configurations
        self.config_manager.load_configs()

        # Connect to Ollama
        print(self.colors.info("Connecting to Ollama..."))
        # Test connection will happen when agent is created

        # Connect to MCP servers
        self.mcp_manager = MCPServerManager(self.config_manager.mcp_config)
        await self.mcp_manager.connect_all()

        # Create agent
        self.agent = OllamaMCPAgent(
            ollama_config=self.config_manager.ollama_config,
            mcp_manager=self.mcp_manager,
            ui=self.ui,
        )

        # Check Ollama connectivity
        print(self.colors.info("Checking Ollama server connection..."))
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

        print(self.colors.final_response("✓ Startup complete!"))
        print()

    async def run(self) -> None:
        """Run the main application loop."""
        try:
            await self.startup()

            self.ui.display_header()

            while self.ui.running:
                try:
                    # Get user input
                    user_input = self.ui.get_input()

                    # Check for ESC key
                    if user_input == "ESC":
                        self.ui.toggle_mode()
                        continue

                    # Check for Ctrl+V key
                    if user_input == "CTRL_V":
                        self.ui.toggle_verbose()
                        continue

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
                else:
                    self.ui.display_error(
                        "Invalid help command. Use 'help', 'help server <name>', or 'help tool <name>'"
                    )
            else:
                self.display_help()

        elif cmd == "models":
            models = await self.agent.list_models()
            self.ui.display_models(models, self.config_manager.ollama_config.model)

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

        elif cmd == "servers":
            self.display_servers()

        elif cmd == "tools":
            self.display_tools()

        else:
            self.ui.display_error(f"Unknown command: '{cmd}'. Type 'help' for available commands.")

    def display_help(self) -> None:
        """Display help information for available commands."""
        help_text = """
ATOLL - Available Commands:
---------------------------
  help                    - Display this help message
  help server <name>      - Show details about a specific MCP server
  help tool <name>        - Show details about a specific tool
  models                  - List all available Ollama models
  changemodel <name>      - Switch to a different Ollama model
  setserver <url> [port]  - Configure Ollama server connection
  clear                   - Clear conversation memory
  servers                 - List connected MCP servers
  tools                   - List available MCP tools
  quit                    - Exit ATOLL

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
  > help server example-server
  > help tool example-tool
  > changemodel llama2
  > setserver http://localhost 11434
  > models
  > clear
  > tools
"""
        print(self.colors.info(help_text))

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
    parser.parse_args()

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
