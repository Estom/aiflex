import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from pstock_framework import AgentFrameworkLoader
from pstock_sdk import OpenAILLM, OpenAIModelOptions


def print_agent_config(agent) -> None:
    """打印 Agent 的 JSON 格式配置信息"""
    # 获取工具列表
    tools = agent.tool_registry.list()
    tools_list = [
        {"name": tool.name, "description": tool.description}
        for tool in tools
    ]

    # 获取技能列表
    skills = agent.skill_registry.list()
    skills_list = [
        {"name": skill["name"], "description": skill.get("description", "")}
        for skill in skills
    ]

    config = {
        "name": agent.name,
        "description": agent.description,
        "max_steps": agent.config.max_steps,
        "instructions": agent.config.instructions,
        "workspace_root": agent.config.workspace_root,
        "model": {
            "name": agent.llm.model,
            "temperature": agent.llm.temperature,
            "max_tokens": agent.llm.max_tokens,
        },
        "tools_count": len(tools_list),
        "tools": tools_list,
        "skills_count": len(skills_list),
        "skills": skills_list,
        "children_count": len(agent.children),
        "children": [
            {"name": child.name, "description": child.description}
            for child in agent.children
        ],
        "experience_enabled": agent.experience_enabled,
        "mcp_lazy_load": agent.mcp_lazy_load,
        "mcp_servers": agent.mcp_servers,
        "codespace_enabled": agent.codespace_enabled,
        "skill_sources": agent.skill_sources,
    }

    print(json.dumps(config, indent=2, ensure_ascii=False))


async def main():
    # 加载环境变量
    load_dotenv()

    # 从环境变量读取配置
    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # 初始化 LLM
    llm = OpenAILLM(
        api_key=api_key,
        options=OpenAIModelOptions(model=model, api_base=api_base)
    )

    # 获取当前目录作为 Agent 目录
    agent_dir = Path(__file__).parent.resolve()
    loader = AgentFrameworkLoader(agents_root=agent_dir, default_llm=llm)

    # 加载单个 Agent
    agent = await loader.load()
    print(f"Loaded agent: {agent.name}")

    # 打印 Agent 配置信息
    print("\n" + "=" * 60)
    print("Agent Configuration (JSON):")
    print("=" * 60)
    print_agent_config(agent)
    print("=" * 60 + "\n")

    # 运行任务
    result = await agent.run("Analyze AAPL stock")
    print(f"\nResult:\n{result.output}")


if __name__ == "__main__":
    asyncio.run(main())
