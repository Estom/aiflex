"""
测试 Agent Runtime - ReAct 循环核心逻辑

测试覆盖:
- ReAct 循环的完整流程
- 最大步数限制
- 工具调用失败的处理
- 会话终止功能
- 流式输出模式
"""

from __future__ import annotations

import asyncio

import pytest

from sdk.agent.core.agent_runtime import AgentRuntime, AgentRuntimeConfig
from sdk.agent.core.interfaces import AgentContext, AgentStep, ChatMessage
from sdk.agent.skills.skill_registry import SkillRegistry
from sdk.agent.tools.tool_registry import ToolRegistry


class MockLLM:
    """Mock LLM for testing"""

    def __init__(
        self,
        responses: list[dict] | None = None,
        response_fn: callable | None = None,
    ):
        """
        初始化 Mock LLM

        Args:
            responses: 预定义的响应列表
            response_fn: 自定义响应函数
        """
        self.responses = responses or []
        self.response_fn = response_fn
        self.call_count = 0
        self.chat_calls = []

    async def chat(
        self, messages: list[ChatMessage], tools: list | None = None
    ) -> dict:
        """记录调用并返回响应"""
        self.chat_calls.append({"messages": messages, "tools": tools})
        self.call_count += 1

        if self.response_fn:
            return await self.response_fn(messages, tools)

        if self.responses:
            idx = min(self.call_count - 1, len(self.responses) - 1)
            return self.responses[idx]

        # 默认响应
        return {
            "message": {"role": "assistant", "content": "Final answer"},
            "raw": None,
        }


class MockTool:
    """Mock Tool for testing"""

    def __init__(
        self,
        name: str = "test_tool",
        description: str = "Test tool",
        execute_result: str = "Tool executed",
        should_fail: bool = False,
    ):
        self.name = name
        self._description = description
        self._execute_result = execute_result
        self._should_fail = should_fail
        self.execute_calls = []

    @property
    def description(self) -> str:
        return self._description

    @property
    def display_name(self) -> str | None:
        return self.name

    @property
    def parameters(self) -> dict | None:
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Input parameter"},
            },
            "required": ["input"],
        }

    def get_definition(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self._description,
                "parameters": self.parameters,
            },
        }

    async def execute(self, input: dict, context: AgentContext | None = None) -> str:
        """执行工具"""
        self.execute_calls.append({"input": input, "context": context})

        if self._should_fail:
            raise RuntimeError(f"Tool {self.name} failed")

        return self._execute_result


@pytest.fixture
def mock_llm():
    """创建 Mock LLM fixture"""
    return MockLLM()


@pytest.fixture
def tool_registry():
    """创建工具注册表 fixture"""
    return ToolRegistry()


@pytest.fixture
def skill_registry():
    """创建技能注册表 fixture"""
    return SkillRegistry()


@pytest.fixture
def agent_config():
    """创建 Agent 配置 fixture"""
    return AgentRuntimeConfig(
        name="test-agent",
        description="Test Agent",
        max_steps=5,
        instructions="Test instructions",
    )


@pytest.fixture
def agent_context():
    """创建 Agent 上下文 fixture"""
    return AgentContext(session_id="test-session")


@pytest.mark.asyncio
async def test_react_loop_with_final_answer(
    mock_llm, tool_registry, skill_registry, agent_config, agent_context
):
    """测试 ReAct 循环 - 直接返回最终答案"""
    # 设置 LLM 返回最终答案
    mock_llm.responses = [
        {
            "message": {
                "role": "assistant",
                "content": "This is the final answer",
            },
            "raw": None,
        }
    ]

    runtime = AgentRuntime(mock_llm, tool_registry, skill_registry, agent_config)
    result = await runtime.run("Test task", agent_context)

    assert result.output == "This is the final answer"
    # Should have thought and final steps
    assert len(result.steps) == 2
    assert result.steps[0].type == "thought"
    assert result.steps[-1].type == "final"
    assert mock_llm.call_count == 1


@pytest.mark.asyncio
async def test_react_loop_with_tool_call(
    mock_llm, tool_registry, skill_registry, agent_config, agent_context
):
    """测试 ReAct 循环 - 工具调用后返回最终答案"""
    # 设置工具
    tool = MockTool(name="search", execute_result="Search results")
    tool_registry.register(tool)

    # 第一次返回工具调用，第二次返回最终答案
    mock_llm.responses = [
        {
            "message": {
                "role": "assistant",
                "content": "I need to search",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "name": "search",
                        "arguments": '{"input": "test query"}',
                    }
                ],
            },
            "raw": None,
        },
        {
            "message": {
                "role": "assistant",
                "content": "Based on search results, here's the answer",
            },
            "raw": None,
        },
    ]

    runtime = AgentRuntime(mock_llm, tool_registry, skill_registry, agent_config)
    result = await runtime.run("Search for information", agent_context)

    assert "answer" in result.output.lower()
    # Should have: thought, action, observation, thought, final (5 steps)
    assert len(result.steps) == 5
    assert tool.execute_calls[0]["input"]["input"] == "test query"
    assert mock_llm.call_count == 2


@pytest.mark.asyncio
async def test_react_loop_max_steps(
    tool_registry, skill_registry, agent_config, agent_context
):
    """测试达到最大步数限制"""
    # 设置 LLM 持续返回工具调用
    responses = []
    for i in range(10):
        responses.append(
            {
                "message": {
                    "role": "assistant",
                    "content": f"Thinking step {i}",
                    "tool_calls": [
                        {
                            "id": f"call_{i}",
                            "name": "tool",
                            "arguments": '{"input": "test"}',
                        }
                    ],
                },
                "raw": None,
            }
        )

    mock_llm = MockLLM(responses=responses)

    # 注册工具
    tool = MockTool(name="tool", execute_result="Result")
    tool_registry.register(tool)

    runtime = AgentRuntime(mock_llm, tool_registry, skill_registry, agent_config)
    result = await runtime.run("Test task", agent_context)

    assert "Maximum steps reached" in result.output
    assert mock_llm.call_count == agent_config.max_steps


@pytest.mark.asyncio
async def test_tool_not_found(
    mock_llm, tool_registry, skill_registry, agent_config, agent_context
):
    """测试工具未找到的错误处理"""
    # LLM 返回不存在的工具调用
    mock_llm.responses = [
        {
            "message": {
                "role": "assistant",
                "content": "I'll use a tool",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "name": "nonexistent_tool",
                        "arguments": "{}",
                    }
                ],
            },
            "raw": None,
        },
        {
            "message": {
                "role": "assistant",
                "content": "Got error, final answer",
            },
            "raw": None,
        },
    ]

    runtime = AgentRuntime(mock_llm, tool_registry, skill_registry, agent_config)
    result = await runtime.run("Test task", agent_context)

    # Step 1: thought, Step 2: action, Step 3: observation (error)
    assert "not found" in result.steps[2].content.lower()
    assert mock_llm.call_count == 2


@pytest.mark.asyncio
async def test_tool_execution_error(
    mock_llm, tool_registry, skill_registry, agent_config, agent_context
):
    """测试工具执行错误的处理"""
    # 设置会失败的工具
    tool = MockTool(name="failing_tool", should_fail=True)
    tool_registry.register(tool)

    mock_llm.responses = [
        {
            "message": {
                "role": "assistant",
                "content": "I'll use the failing tool",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "name": "failing_tool",
                        "arguments": '{"input": "test"}',
                    }
                ],
            },
            "raw": None,
        },
        {
            "message": {
                "role": "assistant",
                "content": "Got error, providing final answer",
            },
            "raw": None,
        },
    ]

    runtime = AgentRuntime(mock_llm, tool_registry, skill_registry, agent_config)
    result = await runtime.run("Test task", agent_context)

    # 检查观察步骤包含错误信息
    observation_step = result.steps[2]
    assert observation_step.type == "observation"
    assert "failed" in observation_step.content.lower() or "error" in observation_step.content.lower()


@pytest.mark.asyncio
async def test_terminate_session(
    mock_llm, tool_registry, skill_registry, agent_config, agent_context
):
    """测试会话终止功能"""
    # 第一次调用后设置终止标志
    call_count = [0]

    async def response_with_terminate(messages, tools):
        call_count[0] += 1
        if call_count[0] == 1:
            # 第一次调用后终止
            asyncio.create_task(lambda: runtime.terminate())()
            return {
                "message": {
                    "role": "assistant",
                    "content": "First response",
                },
                "raw": None,
            }
        return {
            "message": {"role": "assistant", "content": "Should not reach here"},
            "raw": None,
        }

    mock_llm = MockLLM(response_fn=response_with_terminate)
    runtime = AgentRuntime(mock_llm, tool_registry, skill_registry, agent_config)

    # 先设置终止标志
    runtime.terminate()

    result = await runtime.run("Test task", agent_context)

    assert "会话已终止" in result.output
    assert runtime._terminated is False  # 应该重置


@pytest.mark.asyncio
async def test_reset_termination_flag(
    mock_llm, tool_registry, skill_registry, agent_config, agent_context
):
    """测试终止标志重置"""
    runtime = AgentRuntime(mock_llm, tool_registry, skill_registry, agent_config)

    # 终止会话
    runtime.terminate()
    assert runtime._terminated is True

    # 重置
    runtime.reset()
    assert runtime._terminated is False


@pytest.mark.asyncio
async def test_stream_mode(
    mock_llm, tool_registry, skill_registry, agent_config, agent_context
):
    """测试流式输出模式"""
    emitted_steps = []

    async def emit_step(step: AgentStep) -> None:
        emitted_steps.append(step)

    # 设置工具
    tool = MockTool(name="test_tool", execute_result="Tool result")
    tool_registry.register(tool)

    mock_llm.responses = [
        {
            "message": {
                "role": "assistant",
                "content": "Let me use a tool",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "name": "test_tool",
                        "arguments": '{"input": "test"}',
                    }
                ],
            },
            "raw": None,
        },
        {
            "message": {
                "role": "assistant",
                "content": "Final streaming answer",
            },
            "raw": None,
        },
    ]

    runtime = AgentRuntime(mock_llm, tool_registry, skill_registry, agent_config)
    result = await runtime.run_stream("Test task", agent_context, emit_step)

    assert result.output == "Final streaming answer"
    # Should have 5 steps: thought, action, observation, thought, final
    assert len(emitted_steps) == 5

    # 验证步骤类型
    assert emitted_steps[0].type == "thought"
    assert emitted_steps[1].type == "action"
    assert emitted_steps[2].type == "observation"


@pytest.mark.asyncio
async def test_multiple_tool_calls_in_one_step(
    mock_llm, tool_registry, skill_registry, agent_config, agent_context
):
    """测试单次调用多个工具"""
    tool1 = MockTool(name="tool1", execute_result="Result 1")
    tool2 = MockTool(name="tool2", execute_result="Result 2")
    tool_registry.register(tool1)
    tool_registry.register(tool2)

    mock_llm.responses = [
        {
            "message": {
                "role": "assistant",
                "content": "I'll use both tools",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "name": "tool1",
                        "arguments": '{"input": "test1"}',
                    },
                    {
                        "id": "call_2",
                        "name": "tool2",
                        "arguments": '{"input": "test2"}',
                    },
                ],
            },
            "raw": None,
        },
        {
            "message": {
                "role": "assistant",
                "content": "Combined answer",
            },
            "raw": None,
        },
    ]

    runtime = AgentRuntime(mock_llm, tool_registry, skill_registry, agent_config)
    result = await runtime.run("Test task", agent_context)

    assert len(tool1.execute_calls) == 1
    assert len(tool2.execute_calls) == 1
    assert result.output == "Combined answer"


@pytest.mark.asyncio
async def test_empty_response_handling(
    tool_registry, skill_registry, agent_config, agent_context
):
    """测试空响应的处理"""
    # 返回空内容
    mock_llm = MockLLM(
        responses=[
            {"message": {"role": "assistant", "content": None}, "raw": None},
            {"message": {"role": "assistant", "content": "Now I respond"}, "raw": None},
        ]
    )

    runtime = AgentRuntime(mock_llm, tool_registry, skill_registry, agent_config)
    result = await runtime.run("Test task", agent_context)

    # 应该继续到下一次迭代
    assert mock_llm.call_count == 2
    assert result.output == "Now I respond"


@pytest.mark.asyncio
async def test_custom_instructions(
    tool_registry, skill_registry, agent_context
):
    """测试自定义指令"""
    custom_instructions = "You are a helpful assistant specializing in math."

    config = AgentRuntimeConfig(
        name="math-agent",
        description="Math Agent",
        instructions=custom_instructions,
        max_steps=5,
    )

    mock_llm = MockLLM(
        responses=[
            {
                "message": {"role": "assistant", "content": "Math answer"},
                "raw": None,
            }
        ]
    )

    runtime = AgentRuntime(mock_llm, tool_registry, skill_registry, config)
    await runtime.run("Solve 2+2", agent_context)

    # 验证系统消息包含自定义指令
    messages = mock_llm.chat_calls[0]["messages"]
    system_msg = next((m for m in messages if m.get("role") == "system"), None)
    assert system_msg is not None
    assert custom_instructions in system_msg.get("content", "")


@pytest.mark.asyncio
async def test_workspace_root_in_context(
    mock_llm, tool_registry, skill_registry, agent_context
):
    """测试工作空间根目录配置"""
    workspace = "/tmp/workspace"

    config = AgentRuntimeConfig(
        name="test-agent",
        description="Test Agent",
        workspace_root=workspace,
        max_steps=5,
    )

    mock_llm.responses = [
        {
            "message": {"role": "assistant", "content": "Answer"},
            "raw": None,
        }
    ]

    runtime = AgentRuntime(mock_llm, tool_registry, skill_registry, config)
    await runtime.run("Test task", agent_context)

    assert runtime.config.workspace_root == workspace
