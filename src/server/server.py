"""
PStock Server - Agent Server

This module provides the AgentServer class that supports multiple execution modes:
- Web mode: Start the FastAPI web server for the agent marketplace
- Interactive mode: Interactive CLI for chatting with agents
- Prompt mode: One-shot execution with a prompt

Example usage:
    agent = AgentBuilder().with_name("my-agent").with_llm(llm).build()
    registry.register(agent)

    server = AgentServer(registry)
    server.run()  # Parses CLI args and runs appropriate mode
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from sdk.agent.core.interfaces import AgentContext, ChatMessage

from .registry import AgentRegistry
from .routes import agents, chat


def format_step_output(step: Any) -> str:
    """
    Format agent step output for display

    Args:
        step: AgentStep containing type, content, and display_name

    Returns:
        Formatted string for the step
    """
    step_type = step.type
    display_name = step.display_name or step_type

    if step_type == "thought":
        return f"\n🤔 思考: {step.content}"
    elif step_type == "action":
        return f"\n🔧 行动: {display_name}"
    elif step_type == "observation":
        content_preview = step.content[:100] + "..." if len(step.content) > 100 else step.content
        return f"\n👁️  观察: {content_preview}"
    elif step_type == "answer":
        return f"\n💡 回答: {step.content}"
    else:
        return f"\n[{step_type}] {display_name}: {step.content[:50]}..."


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application

    Returns:
        FastAPI: The configured application
    """
    app = FastAPI(
        title="PStock Agent Marketplace",
        description="A web marketplace for discovering and interacting with PStock agents",
        version="0.1.0",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(agents.router)
    app.include_router(chat.router)

    # Mount static files (frontend)
    frontend_dist = Path(__file__).parent / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
        logger.info(f"Frontend static files mounted from {frontend_dist}")
    else:
        logger.warning(f"Frontend dist directory not found at {frontend_dist}")
        logger.warning("Run 'cd src/server/frontend && npm run build' to build the frontend")

    @app.get("/health")
    async def health_check() -> dict[str, Any]:
        """Health check endpoint"""
        return {"status": "healthy", "service": "pstock-server"}

    return app


class AgentServer:
    """
    Agent Server that supports multiple execution modes

    Modes:
    - Web: Start FastAPI web server for agent marketplace
    - Interactive: Interactive CLI for chatting with agents
    - Prompt: One-shot execution with a prompt
    """

    def __init__(self, registry: AgentRegistry):
        """
        Initialize the AgentServer

        Args:
            registry: AgentRegistry instance containing registered agents
        """
        self.registry = registry
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create CLI argument parser"""
        parser = argparse.ArgumentParser(
            description="PStock Agent Server - Run agents in different modes",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Start web server (default)
  python -m server --web

  # Interactive mode
  python -m server --interactive

  # One-shot prompt mode
  python -m server --prompt "What is the weather today?"

  # Specify agent by name
  python -m server --interactive --agent my-agent
            """,
        )

        # Mode selection (mutually exclusive)
        mode_group = parser.add_mutually_exclusive_group()
        mode_group.add_argument(
            "-w",
            "--web",
            action="store_true",
            help="Start web server mode (agent marketplace)",
        )
        mode_group.add_argument(
            "-i",
            "--interactive",
            action="store_true",
            help="Start interactive mode",
        )
        mode_group.add_argument(
            "-p",
            "--prompt",
            type=str,
            metavar="PROMPT",
            help="Run in one-shot prompt mode",
        )

        # Common options
        parser.add_argument(
            "--agent",
            type=str,
            metavar="NAME",
            help="Agent name to use (for interactive/prompt modes)",
        )
        parser.add_argument(
            "-s",
            "--stream",
            action="store_true",
            help="Use streaming output with intermediate thinking process (for interactive/prompt modes)",
        )
        parser.add_argument(
            "--host",
            type=str,
            default="0.0.0.0",
            help="Host to bind web server (default: 0.0.0.0)",
        )
        parser.add_argument(
            "--port",
            type=int,
            default=8000,
            help="Port to bind web server (default: 8000)",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="List all registered agents",
        )

        return parser

    def _list_agents(self) -> None:
        """List all registered agents"""
        agent_list = self.registry.list_all()
        if not agent_list:
            print("No agents registered.")
            return

        print(f"\nRegistered Agents ({len(agent_list)}):")
        print("-" * 60)
        for agent_info in agent_list:
            print(f"\nName: {agent_info.name}")
            print(f"ID: {agent_info.id}")
            print(f"Description: {agent_info.description}")
            print(f"Tools: {len(agent_info.tools)}")
            print(f"Skills: {len(agent_info.skills)}")
            print(f"Subagents: {len(agent_info.subagents)}")
        print()

    def _get_agent_by_name(self, name: str) -> Any | None:
        """Get agent by name"""
        agent_list = self.registry.list_all()
        for agent_info in agent_list:
            if agent_info.name == name:
                return self.registry.get(agent_info.id)
        return None

    async def _run_with_stream(self, agent, task: str, session_id: str | None = None) -> None:
        """
        Run agent task with streaming output

        Args:
            agent: The agent instance
            task: User task/prompt
            session_id: Session ID for context management
        """
        steps_collected = []

        async def emit_step(step: Any) -> None:
            """Callback for streaming step output"""
            steps_collected.append(step)
            output = format_step_output(step)
            print(output, end="", flush=True)

        result = await agent.run_stream(task, session_id, emit_step)

        # Output final result
        print(f"\n\n{'='*60}")
        print(f"最终答案:")
        print(f"{'='*60}")
        print(result.output)
        print(f"{'='*60}")
        print(f"总步骤数: {len(steps_collected)}")

    async def _run_interactive(self, agent_name: str | None = None, stream: bool = False) -> None:
        """Run interactive mode"""
        # Select agent
        agent = None
        if agent_name:
            agent = self._get_agent_by_name(agent_name)
            if not agent:
                print(f"Error: Agent '{agent_name}' not found.")
                print("Use --list to see available agents.")
                return
        else:
            agent_list = self.registry.list_all()
            if not agent_list:
                print("No agents registered.")
                return
            if len(agent_list) == 1:
                agent = self.registry.get(agent_list[0].id)
            else:
                print("\nSelect an agent:")
                for i, agent_info in enumerate(agent_list, 1):
                    print(f"  {i}. {agent_info.name} - {agent_info.description}")
                try:
                    choice = int(input("\nEnter agent number: ")) - 1
                    if 0 <= choice < len(agent_list):
                        agent = self.registry.get(agent_list[choice].id)
                    else:
                        print("Invalid choice.")
                        return
                except (ValueError, EOFError):
                    print("\nExiting.")
                    return

        print(f"\nStarting interactive session with: {agent.name}")
        print("Type 'quit' or 'exit' to end the session.")
        if stream:
            print("Streaming mode enabled - intermediate steps will be shown.")
        print("-" * 60)

        # Initialize context with empty history
        session_id = agent.create_session()

        while True:
            try:
                user_input = input("\nYou: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ("quit", "exit"):
                    print("Exiting session.")
                    break

                print(f"\n{agent.name}: ", end="", flush=True)

                if stream:
                    await self._run_with_stream(agent, user_input, session_id)
                else:
                    result = await agent.run(user_input, session_id)
                    print(result.output)

                    # Print steps if any
                    if result.steps:
                        print(f"\n[Executed {len(result.steps)} step(s)]")

            except (EOFError, KeyboardInterrupt):
                print("\n\nExiting session.")
                break
            except Exception as e:
                print(f"\nError: {e}")

    async def _run_prompt(self, prompt: str, agent_name: str | None = None, stream: bool = False) -> None:
        """Run one-shot prompt mode"""
        agent = None
        if agent_name:
            agent = self._get_agent_by_name(agent_name)
            if not agent:
                print(f"Error: Agent '{agent_name}' not found.", file=sys.stderr)
                print("Use --list to see available agents.", file=sys.stderr)
                return
        else:
            agent_list = self.registry.list_all()
            if not agent_list:
                print("No agents registered.", file=sys.stderr)
                return
            # Use the first agent as default
            agent_info = agent_list[0]
            agent = self.registry.get(agent_info.id)
            if len(agent_list) > 1:
                print(f"Using default agent: {agent_info.name}", file=sys.stderr)
                print(f"  (Use --agent {agent_info.name} to specify)", file=sys.stderr)

        if stream:
            await self._run_with_stream(agent, prompt, None)
        else:
            result = await agent.run(prompt, None)
            print(result.output)

            # Print steps if any
            if result.steps:
                print(f"\n[Executed {len(result.steps)} step(s)]", file=sys.stderr)

    def _run_web(self, host: str, port: int) -> None:
        """Run web server mode"""
        import uvicorn

        app = create_app()
        logger.info(f"Starting PStock Web Server on {host}:{port}")
        print(f"\n{'=' * 60}")
        print("PStock Agent Marketplace")
        print(f"{'=' * 60}")
        print(f"Web UI: http://localhost:{port}")
        print(f"API Docs: http://localhost:{port}/docs")
        print(f"{'=' * 60}\n")

        uvicorn.run(app, host=host, port=port, log_level="info")

    def run(self, args: list[str] | None = None) -> None:
        """
        Run the agent server

        Parses command line arguments and executes the appropriate mode.

        Args:
            args: Command line arguments (uses sys.argv if None)
        """
        parsed_args = self.parser.parse_args(args)

        # Handle --list
        if parsed_args.list:
            self._list_agents()
            return

        # Run appropriate mode
        if parsed_args.web:
            self._run_web(parsed_args.host, parsed_args.port)
        elif parsed_args.interactive:
            asyncio.run(self._run_interactive(parsed_args.agent, parsed_args.stream))
        elif parsed_args.prompt:
            asyncio.run(self._run_prompt(parsed_args.prompt, parsed_args.agent, parsed_args.stream))
        else:
            # Default to web mode if no mode specified
            print("No mode specified. Starting web server by default.")
            print("Use --help to see available modes.\n")
            self._run_web(parsed_args.host, parsed_args.port)


# Convenience functions for backward compatibility
def start_server(host: str = "0.0.0.0", port: int = 8000, log_level: str = "info") -> None:
    """
    Start the PStock web server (backward compatibility function)

    Args:
        host: Host to bind to
        port: Port to bind to
        log_level: Log level for uvicorn
    """
    import uvicorn

    app = create_app()
    logger.info(f"Starting PStock Server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level=log_level)


if __name__ == "__main__":
    from .registry import registry

    server = AgentServer(registry)
    server.run()
