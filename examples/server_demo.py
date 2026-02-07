#!/usr/bin/env python
"""
PStock Server Demo Script

This script demonstrates how to:
1. Create agents using the PStock SDK
2. Register them to the marketplace
3. Start the AgentServer with different modes

Prerequisites:
- Set OPENAI_API_KEY in your environment or .env file

Usage:
    # Web mode (default)
    python examples/server_demo.py --web

    # Interactive mode
    python examples/server_demo.py --interactive

    # Prompt mode
    python examples/server_demo.py --prompt "Analyze AAPL stock"

    # List agents
    python examples/server_demo.py --list
"""

import os
from dotenv import load_dotenv

from pstock_sdk.agent.core.agent import AgentBuilder
from pstock_sdk.agent.llm.openai_llm import OpenAILLM, OpenAIModelOptions
from pstock_server import registry, AgentServer

load_dotenv()


def create_financial_analyst():
    """Create a financial analyst agent"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")

    # 从环境变量读取配置
    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # 初始化 LLM
    llm = OpenAILLM(
        api_key=api_key,
        options=OpenAIModelOptions(model=model, api_base=api_base)
    )

    agent = (
        AgentBuilder()
        .with_name("financial-analyst")
        .with_description(
            "AI-powered financial analyst that helps analyze stocks, "
            "financial statements, and market trends."
        )
        .with_llm(llm)
        .with_max_steps(10)
        .with_experience_enabled(False)
        .build()
    )

    return agent


def create_code_assistant():
    """Create a code assistant agent"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    # 从环境变量读取配置
    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # 初始化 LLM
    llm = OpenAILLM(
        api_key=api_key,
        options=OpenAIModelOptions(model=model, api_base=api_base)
    )

    agent = (
        AgentBuilder()
        .with_name("code-assistant")
        .with_description(
            "AI coding assistant that helps write, review, and debug code. "
            "Supports Python, JavaScript, TypeScript, and more."
        )
        .with_llm(llm)
        .with_max_steps(15)
        .with_experience_enabled(False)
        .build()
    )

    return agent


def main():
    """Main function to register agents and start the server"""
    print("Creating agents...")

    # Create agents
    financial_analyst = create_financial_analyst()
    code_assistant = create_code_assistant()

    # Register agents
    print("Registering agents to marketplace...")
    fa_id = registry.register(financial_analyst)
    ca_id = registry.register(code_assistant)

    print(f"\nRegistered agents:")
    print(f"  - Financial Analyst: {fa_id}")
    print(f"  - Code Assistant: {ca_id}")

    # Create server
    server = AgentServer(registry)

    # Run server with command line arguments
    server.run()


if __name__ == "__main__":
    main()
