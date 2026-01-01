"""Base class for ATOLL agent plugins."""

import asyncio
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

import aiohttp
from langchain_core.messages import AIMessage, HumanMessage

try:
    from langchain_ollama import OllamaLLM
except ImportError:
    from langchain_community.llms import Ollama as OllamaLLM

if TYPE_CHECKING:
    from ..agent.reasoning import ReasoningEngine
    from ..config.models import OllamaConfig
    from ..mcp.server_manager import MCPServerManager
    from ..ui.terminal import TerminalUI


class ATOLLAgent(ABC):
    """Base class for ATOLL agent plugins.

    All specialized agents must inherit from this class and implement
    the required methods. Agents can provide specialized reasoning,
    tool handling, or domain-specific workflows.

    This base class now includes LLM integration, providing each agent
    with its own conversation memory, LLM configuration, and tool access.
    """

    def __init__(
        self,
        name: str,
        version: str,
        llm_config: Optional["OllamaConfig"] = None,
        mcp_manager: Optional["MCPServerManager"] = None,
        ui: Optional["TerminalUI"] = None,
    ):
        """Initialize the agent.

        Args:
            name: Name of the agent
            version: Version string (e.g., "1.0.0")
            llm_config: Ollama LLM configuration (optional, will use parent's if None)
            mcp_manager: MCP server manager for tool access
            ui: Terminal UI instance for output
        """
        self.name = name
        self.version = version
        self._metadata: dict[str, Any] = {}

        # LLM integration components
        self.llm_config = llm_config
        self.mcp_manager = mcp_manager
        self.ui = ui
        self.llm: Optional[OllamaLLM] = None
        self.reasoning_engine: Optional["ReasoningEngine"] = None
        self.tools: list[Any] = []

        # Conversation memory (isolated per agent)
        self.conversation_memory: list[Any] = []

        # Initialize LLM if config provided
        if llm_config:
            self._initialize_llm(llm_config)

        # Initialize LLM if config provided
        if llm_config:
            self._initialize_llm(llm_config)

    def _initialize_llm(self, llm_config: "OllamaConfig") -> None:
        """Initialize the Ollama LLM with the given configuration.

        Args:
            llm_config: Ollama configuration for this agent
        """
        self.llm_config = llm_config
        self.llm = OllamaLLM(
            base_url=f"{llm_config.base_url}:{llm_config.port}",
            model=llm_config.model,
            temperature=llm_config.temperature,
            top_p=llm_config.top_p,
            num_predict=llm_config.max_tokens,
            timeout=llm_config.request_timeout,
        )

    def set_llm_config(self, llm_config: "OllamaConfig") -> None:
        """Set or update LLM configuration for this agent.

        Args:
            llm_config: New Ollama configuration
        """
        self._initialize_llm(llm_config)

    def set_mcp_manager(self, mcp_manager: "MCPServerManager") -> None:
        """Set the MCP server manager for tool access.

        Args:
            mcp_manager: MCP server manager instance
        """
        self.mcp_manager = mcp_manager
        self._update_tools()

    def set_ui(self, ui: "TerminalUI") -> None:
        """Set the terminal UI for output.

        Args:
            ui: Terminal UI instance
        """
        self.ui = ui

    def set_reasoning_engine(self, reasoning_engine: "ReasoningEngine") -> None:
        """Set the reasoning engine for this agent.

        Args:
            reasoning_engine: Reasoning engine instance
        """
        self.reasoning_engine = reasoning_engine

    def _update_tools(self) -> None:
        """Update tools list from MCP server manager."""
        if not self.mcp_manager:
            self.tools = []
            return

        from ..agent.tools import MCPToolWrapper

        tools = []
        for tool_name, tool_info in self.mcp_manager.tool_registry.tools.items():
            wrapper = MCPToolWrapper(
                name=tool_name,
                description=tool_info.get("description", "No description"),
                mcp_manager=self.mcp_manager,
                server_name=tool_info.get("server"),
            )
            tools.append(wrapper)

        self.tools = tools

    async def process_prompt(self, prompt: str) -> str:
        """Process a user prompt with LLM integration.

        This method provides the default LLM-based processing. Subclasses
        can override this to provide specialized behavior while still having
        access to the base LLM functionality.

        Args:
            prompt: User's prompt/question

        Returns:
            Agent's response string
        """
        if not self.llm:
            return "Error: LLM not initialized for this agent"

        if not self.ui:
            # Fallback if no UI available
            return await self._process_prompt_without_ui(prompt)

        try:
            # Display user input
            self.ui.display_user_input(prompt)

            # Apply reasoning if engine available
            if self.reasoning_engine:
                self.ui.display_verbose("Starting prompt analysis...", prefix="[1/5]")
                reasoning = await self.reasoning_engine.analyze(prompt, self.tools)
                if reasoning:
                    self.ui.display_reasoning("\n".join(reasoning))
                    self.ui.display_verbose(
                        f"Reasoning engine generated {len(reasoning)} insights", prefix="[2/5]"
                    )
                else:
                    self.ui.display_verbose(
                        "No specific reasoning patterns detected", prefix="[2/5]"
                    )

            # Add user message to conversation memory
            self.conversation_memory.append(HumanMessage(content=prompt))
            if self.ui:
                self.ui.display_verbose(
                    f"Added user message to conversation history (total: {len(self.conversation_memory)} messages)",
                    prefix="[3/5]",
                )

            # Build system prompt with available tools
            system_prompt = self._build_system_prompt()
            if self.ui:
                self.ui.display_verbose(
                    f"Built system prompt with {len(self.tools)} available tools", prefix="[4/5]"
                )

            # Get response from LLM
            full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:"

            if self.ui:
                self.ui.display_verbose(
                    f"Sending request to LLM (model: {self.llm_config.model})...", prefix="[5/5]"
                )
                self.ui.display_verbose(
                    "Waiting for LLM response (this may take a moment)...", prefix="[LLM]"
                )

            # Run LLM invoke in executor (since it's synchronous)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.llm.invoke, full_prompt)

            if self.ui:
                self.ui.display_verbose("Received response from LLM", prefix="[LLM]")

            # Add assistant response to conversation memory
            self.conversation_memory.append(AIMessage(content=response))
            if self.ui:
                self.ui.display_verbose(
                    f"Added assistant response to history (total: {len(self.conversation_memory)} messages)",
                    prefix="[Done]",
                )
                # Display response
                self.ui.display_response(response)

            return response

        except Exception as e:
            error_msg = f"Error processing prompt: {e}"
            if self.ui:
                self.ui.display_error(error_msg)
                self.ui.display_verbose(
                    f"Exception details: {type(e).__name__}: {str(e)}", prefix="[Error]"
                )
            return error_msg

    async def _process_prompt_without_ui(self, prompt: str) -> str:
        """Process prompt without UI (for headless operation).

        Args:
            prompt: User's prompt

        Returns:
            Agent's response
        """
        try:
            # Add to conversation memory
            self.conversation_memory.append(HumanMessage(content=prompt))

            # Build system prompt
            system_prompt = self._build_system_prompt()
            full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:"

            # Get response from LLM
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.llm.invoke, full_prompt)

            # Add to conversation memory
            self.conversation_memory.append(AIMessage(content=response))

            return response

        except Exception as e:
            return f"Error processing prompt: {e}"

    def _build_system_prompt(self) -> str:
        """Build system prompt with available tools.

        Subclasses can override this to customize the system prompt.

        Returns:
            System prompt string
        """
        prompt = f"""You are {self.name}, a helpful AI assistant with access to various tools.
Use the available tools to answer questions and complete tasks.
Think step-by-step and explain your reasoning."""

        if self.tools:
            prompt += "\n\nAvailable tools:"
            for tool in self.tools:
                prompt += f"\n- {tool.name}: {tool.description}"

        return prompt

    def clear_conversation_memory(self) -> None:
        """Clear this agent's conversation memory."""
        self.conversation_memory.clear()

    def change_model(self, model_name: str) -> bool:
        """Change the LLM model for this agent.

        Args:
            model_name: Name of the new model

        Returns:
            True if successful, False otherwise
        """
        if not self.llm_config:
            return False

        try:
            self.llm_config.model = model_name
            self._initialize_llm(self.llm_config)

            # Update reasoning engine if available
            if self.reasoning_engine:
                self.reasoning_engine.set_llm(self.llm)

            return True
        except Exception as e:
            if self.ui:
                self.ui.display_error(f"Failed to change model: {e}")
            return False

    async def check_server_connection(self) -> bool:
        """Check if Ollama server is reachable.

        Returns:
            True if server is reachable, False otherwise
        """
        if not self.llm_config:
            return False

        url = f"{self.llm_config.base_url}:{self.llm_config.port}/api/tags"

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response,
            ):
                return response.status == 200
        except Exception:
            return False

    async def check_model_available(self) -> bool:
        """Check if the configured model is available.

        Returns:
            True if model is available, False otherwise
        """
        if not self.llm_config:
            return False

        models = await self.list_models()
        return self.llm_config.model in models

    async def list_models(self) -> list[str]:
        """List available Ollama models.

        Returns:
            List of available model names
        """
        if not self.llm_config:
            return []

        url = f"{self.llm_config.base_url}:{self.llm_config.port}/api/tags"

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response,
            ):
                data = await response.json()
                models = [model["name"] for model in data.get("models", [])]
                return models
        except Exception as e:
            if self.ui:
                self.ui.display_error(f"Failed to list models: {e}")
            return []

    @abstractmethod
    async def process(self, prompt: str, context: dict[str, Any]) -> dict[str, Any]:
        """Process a prompt with the agent's specialized capabilities.

        This method is for backward compatibility and specialized processing.
        Most agents should use process_prompt() instead, which provides LLM integration.

        Args:
            prompt: User's prompt/question
            context: Context including available tools, history, etc.

        Returns:
            Dict with 'response', 'reasoning', and optionally 'tool_calls'
        """
        pass

    def get_capabilities(self) -> list[str]:
        """Get list of capabilities this agent provides.

        Returns:
            List of capability strings (e.g., ["binary_analysis", "decompilation"])
        """
        return []

    def get_supported_mcp_servers(self) -> list[str]:
        """Get list of MCP server names this agent works with.

        Returns:
            List of MCP server names (e.g., ["ghidramcp", "binutils"])
        """
        return []

    def get_tools(self) -> list[dict[str, Any]]:
        """Get list of tools provided by this agent.

        Returns:
            List of tool dictionaries with 'name', 'description', 'schema'
        """
        return []

    def can_handle(self, prompt: str, context: dict[str, Any]) -> float:
        """Determine if this agent can handle the given prompt.

        Args:
            prompt: User's prompt
            context: Current context

        Returns:
            Confidence score 0.0-1.0, where higher means more suitable
        """
        return 0.0

    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata for the agent.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self._metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value.

        Args:
            key: Metadata key
            default: Default value if key not found

        Returns:
            Metadata value or default
        """
        return self._metadata.get(key, default)

    def get_all_metadata(self) -> dict[str, Any]:
        """Get all metadata.

        Returns:
            Dictionary of all metadata
        """
        return self._metadata.copy()

    def __str__(self) -> str:
        """String representation."""
        return f"{self.name} v{self.version}"

    def __repr__(self) -> str:
        """Detailed representation."""
        return f"ATOLLAgent(name='{self.name}', version='{self.version}')"
