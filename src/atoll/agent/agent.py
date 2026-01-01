"""Main agent implementation using LangChain and Ollama."""

import asyncio
from typing import TYPE_CHECKING, Any, Optional

import aiohttp

# Use the new langchain-ollama package
try:
    from langchain_ollama import OllamaLLM
except ImportError:
    from langchain_community.llms import Ollama as OllamaLLM

from langchain_core.messages import AIMessage, HumanMessage

from ..config.models import OllamaConfig
from ..mcp.server_manager import MCPServerManager
from ..ui.terminal import TerminalUI
from .reasoning import ReasoningEngine
from .tools import MCPToolWrapper

if TYPE_CHECKING:
    from .agent_manager import ATOLLAgentManager


class OllamaMCPAgent:
    """Ollama-powered agent with MCP tool integration."""

    def __init__(
        self,
        ollama_config: OllamaConfig,
        mcp_manager: MCPServerManager,
        ui: TerminalUI,
        agent_manager: Optional["ATOLLAgentManager"] = None,
    ):
        """Initialize the agent.

        Args:
            ollama_config: Ollama configuration
            mcp_manager: MCP server manager
            ui: Terminal UI instance
            agent_manager: Optional ATOLL agent manager
        """
        self.ollama_config = ollama_config
        self.mcp_manager = mcp_manager
        self.ui = ui
        self.agent_manager = agent_manager

        # Initialize Ollama LLM
        self.llm = self._create_llm()

        # Initialize reasoning engine with LLM and managers
        self.reasoning_engine = ReasoningEngine(self.llm)
        self.reasoning_engine.set_mcp_manager(mcp_manager)
        if agent_manager:
            self.reasoning_engine.set_agent_manager(agent_manager)

        # Initialize tools
        self.tools = self._create_tools()

        # Conversation history
        self.messages: list[Any] = []

    def _create_llm(self) -> OllamaLLM:
        """Create Ollama LLM instance."""
        return OllamaLLM(
            base_url=f"{self.ollama_config.base_url}:{self.ollama_config.port}",
            model=self.ollama_config.model,
            temperature=self.ollama_config.temperature,
            top_p=self.ollama_config.top_p,
            num_predict=self.ollama_config.max_tokens,
            timeout=self.ollama_config.request_timeout,
        )

    def _create_tools(self) -> list[Any]:
        """Create LangChain tools from MCP tools."""
        tools = []

        for tool_name, tool_info in self.mcp_manager.tool_registry.tools.items():
            wrapper = MCPToolWrapper(
                name=tool_name,
                description=tool_info.get("description", "No description"),
                mcp_manager=self.mcp_manager,
                server_name=tool_info.get("server"),
            )
            tools.append(wrapper)

        return tools

    async def process_prompt(self, prompt: str) -> str:
        """Process a user prompt and return the response."""
        try:
            # Display user input
            self.ui.display_user_input(prompt)

            # Verbose: Show analysis start
            self.ui.display_verbose("Starting prompt analysis...", prefix="[1/5]")

            # Apply reasoning (async call)
            reasoning = await self.reasoning_engine.analyze(prompt, self.tools)
            if reasoning:
                self.ui.display_reasoning("\n".join(reasoning))
                self.ui.display_verbose(
                    f"Reasoning engine generated {len(reasoning)} insights", prefix="[2/5]"
                )
            else:
                self.ui.display_verbose("No specific reasoning patterns detected", prefix="[2/5]")

            # Add user message to history
            self.messages.append(HumanMessage(content=prompt))
            self.ui.display_verbose(
                f"Added user message to conversation history (total: {len(self.messages)} messages)",
                prefix="[3/5]",
            )

            # Build system prompt with available tools
            system_prompt = self._build_system_prompt()
            self.ui.display_verbose(
                f"Built system prompt with {len(self.tools)} available tools", prefix="[4/5]"
            )

            # Add user message to history
            self.messages.append(HumanMessage(content=prompt))

            # Build system prompt with available tools
            system_prompt = self._build_system_prompt()

            # Get response from LLM
            full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:"

            self.ui.display_verbose(
                f"Sending request to LLM (model: {self.ollama_config.model})...", prefix="[5/5]"
            )
            self.ui.display_verbose(
                "Waiting for LLM response (this may take a moment)...", prefix="[LLM]"
            )

            # Ollama LLM doesn't have ainvoke, so we run invoke in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.llm.invoke, full_prompt)

            self.ui.display_verbose("Received response from LLM", prefix="[LLM]")

            # Add assistant response to history
            self.messages.append(AIMessage(content=response))
            self.ui.display_verbose(
                f"Added assistant response to history (total: {len(self.messages)} messages)",
                prefix="[Done]",
            )
            # Add assistant response to history
            self.messages.append(AIMessage(content=response))

            # Display response
            self.ui.display_response(response)

            return response

        except Exception as e:
            error_msg = f"Error processing prompt: {e}"
            self.ui.display_error(error_msg)
            self.ui.display_verbose(
                f"Exception details: {type(e).__name__}: {str(e)}", prefix="[Error]"
            )
            return error_msg

    def _build_system_prompt(self) -> str:
        """Build system prompt with available tools."""
        prompt = """You are a helpful AI assistant with access to various tools.
Use the available tools to answer questions and complete tasks.
Think step-by-step and explain your reasoning."""

        if self.tools:
            prompt += "\n\nAvailable tools:"
            for tool in self.tools:
                prompt += f"\n- {tool.name}: {tool.description}"

        return prompt

    def change_model(self, model_name: str) -> bool:
        """Change the Ollama model."""
        try:
            self.ollama_config.model = model_name
            self.llm = self._create_llm()
            # Update reasoning engine with new LLM
            self.reasoning_engine.set_llm(self.llm)
            return True
        except Exception as e:
            self.ui.display_error(f"Failed to change model: {e}")
            return False

    def clear_memory(self) -> None:
        """Clear conversation memory."""
        self.messages.clear()
        self.ui.display_info("Conversation memory cleared")

    async def check_server_connection(self) -> bool:
        """Check if Ollama server is reachable."""
        url = f"{self.ollama_config.base_url}:{self.ollama_config.port}/api/tags"

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response,
            ):
                return response.status == 200
        except Exception:
            return False

    async def check_model_available(self) -> bool:
        """Check if the configured model is available."""
        models = await self.list_models()
        return self.ollama_config.model in models

    async def list_models(self) -> list[str]:
        """List available Ollama models."""
        url = f"{self.ollama_config.base_url}:{self.ollama_config.port}/api/tags"

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response,
            ):
                data = await response.json()
                models = [model["name"] for model in data.get("models", [])]
                return models
        except Exception as e:
            self.ui.display_error(f"Failed to list models: {e}")
            return []
