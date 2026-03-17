"""
PStock Server - Agent Marketplace

This package provides a web-based marketplace for discovering and interacting
with PStock agents.

Example usage:
    from sdk.agent.core.agent import AgentBuilder
    from sdk.agent.llm.openai_llm import OpenAILLM, OpenAIModelOptions
    from server import registry, AgentServer

    # Create LLM
    llm = OpenAILLM(api_key="...", options=OpenAIModelOptions(model="gpt-4o-mini"))

    # Create and register agent
    agent = (AgentBuilder()
        .with_name("financial-analyst")
        .with_description("AI financial analyst")
        .with_llm(llm)
        .build())

    registry.register(agent)

    # Create and run server with different modes
    server = AgentServer(registry)

    # Web mode (agent marketplace)
    server.run(["--web"])

    # Interactive mode (CLI chat)
    server.run(["--interactive"])

    # Prompt mode (one-shot execution)
    server.run(["--prompt", "What is AAPL stock price?"])
"""

from .registry import AgentRegistry, registry
from .server import AgentServer, create_app, start_server

__all__ = ["AgentRegistry", "AgentServer", "create_app", "registry", "start_server"]
