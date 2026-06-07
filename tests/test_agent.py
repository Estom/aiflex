"""
测试 Agent 核心功能
"""

import pytest

from sdk.agent.core.agent import AgentBuilder
from sdk.agent.tools.tool_registry import ToolRegistry
from sdk.utils.agent_step import build_agent_step


class MockLLM:
    """Mock LLM for testing"""

    async def chat(self, messages, tools=None):
        """返回固定响应"""
        return {
            "message": {
                "role": "assistant",
                "content": "测试响应",
            },
            "raw": None,
        }


@pytest.mark.asyncio
async def test_agent_builder():
    """测试 Agent Builder"""
    llm = MockLLM()

    agent = (
        AgentBuilder()
        .with_name("test-agent")
        .with_description("测试 Agent")
        .with_llm(llm)
        .build()
    )

    assert agent.name == "test-agent"
    assert agent.description == "测试 Agent"


@pytest.mark.asyncio
async def test_agent_run():
    """测试 Agent 运行"""
    llm = MockLLM()

    agent = (
        AgentBuilder()
        .with_name("test-agent")
        .with_description("测试 Agent")
        .with_llm(llm)
        .with_max_steps(5)
        .build()
    )

    result = await agent.run("测试任务")

    assert result.output == "测试响应"


def test_build_agent_step():
    """测试构建 Agent 步骤"""
    step = build_agent_step(
        "thought",
        "思考内容",
        "思考中",
    )

    assert step.type == "thought"
    assert step.content == "思考内容"
    assert step.display_name == "思考中"


def test_tool_registry():
    """测试工具注册表"""

    class MockTool:
        def __init__(self):
            self.name = "test_tool"
            self.description = "测试工具"

        def get_definition(self):
            return {
                "type": "function",
                "function": {
                    "name": self.name,
                    "description": self.description,
                },
            }

        async def execute(self, input, context=None):
            return "test result"

    registry = ToolRegistry()
    tool = MockTool()

    registry.register(tool)

    assert registry.get("test_tool") is tool
    assert len(registry.list()) == 1
    assert len(registry.definitions()) == 1
