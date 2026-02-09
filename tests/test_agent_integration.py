"""
Agent 集成测试

测试 pstock_sdk Agent 的完整功能，包括：
- ReAct 框架
- 工具调用
- 上下文管理（压缩、截断）
- 多会话、多轮对话
- 多智能体
- 记忆功能
- 对话终止
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
from typing import Any

from pstock_sdk.agent.core.agent import Agent, AgentBuilder, AgentOptions
from pstock_sdk.agent.core.agent_context import AgentContextManager
from pstock_sdk.agent.core.agent_runtime import AgentRuntime, AgentRuntimeConfig
from pstock_sdk.agent.core.interfaces import (
    AgentContext,
    AgentRunResult,
    AgentStep,
    ChatMessage,
    LLM,
    Tool,
    ToolDefinition,
)
from pstock_sdk.agent.memory.memory import MemoryRecord, MemorySlotConfig
from pstock_sdk.agent.memory.compressor import ContextCompressor


# =============================================================================
# Fixtures
# =============================================================================


class MockLLM:
    """Mock LLM for testing"""

    def __init__(
        self,
        responses: list[dict] | None = None,
        tool_call_response: list[dict] | None = None,
    ):
        """Initialize with predefined responses"""
        self.responses = responses or [
            {"message": {"role": "assistant", "content": "测试响应"}, "raw": None}
        ]
        self.tool_call_response = tool_call_response
        self.call_count = 0
        self._chat = AsyncMock()

    async def chat(self, messages: list[ChatMessage], tools: list[ToolDefinition] | None = None):
        """Return predefined response"""
        self.call_count += 1

        # If tool_call_response is set and tools are available, return tool call
        if self.tool_call_response and tools and len(tools) > 0:
            response = self.tool_call_response[min(self.call_count - 1, len(self.tool_call_response) - 1)]
            return response

        response = self.responses[min(self.call_count - 1, len(self.responses) - 1)]
        return response

    def reset(self):
        """Reset call count"""
        self.call_count = 0


class SimpleTool(Tool):
    """Simple test tool"""

    def __init__(self, name: str = "test_tool", result: str = "tool result"):
        self._name = name
        self._description = f"A simple test tool: {name}"
        self._result = result

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def display_name(self) -> str | None:
        return self._name

    @property
    def parameters(self) -> dict[str, Any] | None:
        return {"type": "object", "properties": {}}

    def get_definition(self) -> ToolDefinition:
        return {
            "type": "function",
            "function": {
                "name": self._name,
                "description": self._description,
                "parameters": self.parameters or {},
            },
        }

    async def execute(self, input: Any, context: AgentContext | None = None) -> str:
        return self._result


@pytest.fixture
def mock_llm():
    """Provide a mock LLM"""
    return MockLLM()


@pytest.fixture
def mock_llm_with_tools():
    """Provide a mock LLM that returns tool calls"""
    return MockLLM(
        tool_call_response=[
            {
                "message": {
                    "role": "assistant",
                    "content": "Let me call a tool",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "name": "test_tool",
                            "arguments": '{"query": "test"}',
                        }
                    ],
                },
                "raw": None,
            },
            {
                "message": {
                    "role": "assistant",
                    "content": "Final answer based on tool result",
                    "tool_calls": [],
                },
                "raw": None,
            },
        ]
    )


@pytest.fixture
def sample_tool():
    """Provide a sample tool"""
    return SimpleTool()


@pytest.fixture
def memory_slots():
    """Provide sample memory slots"""
    return [
        MemorySlotConfig(name="profile", description="用户画像"),
        MemorySlotConfig(name="preferences", description="用户偏好"),
    ]


# =============================================================================
# 1. ReAct Framework & Agent Configuration Tests
# =============================================================================


class TestReactFrameworkAndConfig:
    """测试 ReAct 框架和智能体配置"""

    @pytest.mark.asyncio
    async def test_agent_builder_basic(self, mock_llm):
        """测试 Agent 基础构建"""
        agent = (
            AgentBuilder()
            .with_name("test-agent")
            .with_description("测试 Agent")
            .with_llm(mock_llm)
            .with_max_steps(5)
            .build()
        )

        assert agent.name == "test-agent"
        assert agent.description == "测试 Agent"
        assert agent.config.max_steps == 5

    @pytest.mark.asyncio
    async def test_agent_with_instructions(self, mock_llm):
        """测试带自定义指令的 Agent"""
        custom_instructions = "You are a helpful assistant specializing in finance."

        agent = (
            AgentBuilder()
            .with_name("finance-agent")
            .with_description("金融分析助手")
            .with_llm(mock_llm)
            .with_instructions(custom_instructions)
            .build()
        )

        assert agent.config.instructions == custom_instructions

    @pytest.mark.asyncio
    async def test_agent_run_basic(self, mock_llm):
        """测试 Agent 基础运行"""
        agent = (
            AgentBuilder()
            .with_name("test-agent")
            .with_description("测试 Agent")
            .with_llm(mock_llm)
            .with_max_steps(3)
            .build()
        )

        result = await agent.run("你好")

        assert result.output == "测试响应"
        assert isinstance(result.steps, list)

    @pytest.mark.asyncio
    async def test_agent_max_steps(self, mock_llm):
        """测试最大步数限制"""
        # 设置一个不会返回最终答案的响应
        empty_responses = [
            {"message": {"role": "assistant", "content": None}, "raw": None}
        ] * 10

        mock_llm.responses = empty_responses

        agent = (
            AgentBuilder()
            .with_name("test-agent")
            .with_description("测试 Agent")
            .with_llm(mock_llm)
            .with_max_steps(3)
            .build()
        )

        result = await agent.run("测试任务")

        # 应该在达到最大步数后停止
        assert "Maximum steps reached" in result.output or "回答错误" in result.output


# =============================================================================
# 2. Tool Calling Tests
# =============================================================================


class TestToolCalling:
    """测试工具调用功能"""

    @pytest.mark.asyncio
    async def test_agent_with_tool(self, mock_llm_with_tools):
        """测试 Agent 调用工具"""
        tool = SimpleTool(name="test_tool", result="tool executed successfully")

        agent = (
            AgentBuilder()
            .with_name("tool-agent")
            .with_description("工具使用 Agent")
            .with_llm(mock_llm_with_tools)
            .with_tools([tool])
            .with_max_steps(5)
            .build()
        )

        result = await agent.run("使用工具完成任务")

        # 验证工具被调用
        assert any(step.type == "action" for step in result.steps)
        assert any(step.type == "observation" for step in result.steps)

    @pytest.mark.asyncio
    async def test_agent_multiple_tools(self, mock_llm):
        """测试 Agent 使用多个工具"""
        tools = [
            SimpleTool(name="search", result="Search results"),
            SimpleTool(name="calculate", result="42"),
        ]

        agent = (
            AgentBuilder()
            .with_name("multi-tool-agent")
            .with_description("多工具 Agent")
            .with_llm(mock_llm)
            .with_tools(tools)
            .build()
        )

        # 验证工具已注册
        assert agent.tool_registry.get("search") is not None
        assert agent.tool_registry.get("calculate") is not None
        assert len(agent.tool_registry.list()) == 2

    @pytest.mark.asyncio
    async def test_tool_execution_with_context(self):
        """测试工具执行时传递上下文"""
        context_received = []

        class ContextAwareTool(Tool):
            def __init__(self, context_collector: list):
                self._name = "context_tool"
                self._description = "A tool that receives context"
                self._collector = context_collector

            @property
            def name(self) -> str:
                return self._name

            @property
            def description(self) -> str:
                return self._description

            @property
            def display_name(self) -> str | None:
                return "Context Tool"

            @property
            def parameters(self) -> dict[str, Any] | None:
                return None

            def get_definition(self) -> ToolDefinition:
                return {
                    "type": "function",
                    "function": {
                        "name": self._name,
                        "description": self._description,
                        "parameters": {},
                    },
                }

            async def execute(self, input: Any, context: AgentContext | None = None) -> str:
                self._collector.append(context)
                return "executed with context"

        tool = ContextAwareTool(context_received)

        # 直接调用工具的 execute 方法，传入 context
        test_context = AgentContext(session_id="test")
        result = await tool.execute({}, test_context)

        # 验证上下文被传递
        assert len(context_received) == 1
        assert context_received[0] is test_context
        assert result == "executed with context"


# =============================================================================
# 3. Context Management Tests (Compression, Truncation)
# =============================================================================


class TestContextManagement:
    """测试上下文管理功能"""

    def test_context_truncation(self):
        """测试上下文截断"""
        manager = AgentContextManager(
            max_history_rounds=3,  # 最多保留3轮（6条消息）
        )

        context = manager.get_context("test-session")

        # 添加10轮对话（20条消息）
        for i in range(10):
            context.history_messages.append(ChatMessage(role="user", content=f"用户消息{i}"))
            context.history_messages.append(ChatMessage(role="assistant", content=f"助手回复{i}"))

        # 手动触发截断
        manager._trim_history(context)

        # 验证只保留最近3轮（6条消息）
        assert len(context.history_messages) == 6

    @pytest.mark.asyncio
    async def test_context_compression_disabled(self, mock_llm):
        """测试未启用压缩时的行为"""
        manager = AgentContextManager(
            max_history_rounds=10,
            compression_enabled=False,
            llm=mock_llm,
        )

        session_id = "test-session"
        context = manager.get_context(session_id)

        # 添加大量消息
        for i in range(20):
            await manager.update_context(
                session_id,
                f"用户消息{i}",
                f"助手回复{i}",
            )

        # 验证消息被截断但没有压缩
        assert len(context.history_messages) <= 20  # 被截断

    def test_should_compress(self):
        """测试压缩触发条件"""
        manager = AgentContextManager(
            max_history_rounds=10,
            compression_enabled=True,
            max_context_length=50,
            compression_trigger_ratio=0.8,
        )

        context = manager.get_context("test")

        # 添加40条消息（少于触发阈值 50 * 0.8 = 40）
        for i in range(39):
            context.history_messages.append(ChatMessage(role="user", content=f"msg{i}"))

        assert not manager._should_compress(context)

        # 添加更多消息达到阈值
        context.history_messages.append(ChatMessage(role="user", content="msg40"))

        assert manager._should_compress(context)


# =============================================================================
# 4. Multi-Session & Multi-Turn Conversation Tests
# =============================================================================


class TestSessionsAndConversations:
    """测试多会话和多轮对话"""

    @pytest.mark.asyncio
    async def test_multiple_sessions(self, mock_llm):
        """测试多个独立会话"""
        agent = (
            AgentBuilder()
            .with_name("session-agent")
            .with_description("多会话测试 Agent")
            .with_llm(mock_llm)
            .build()
        )

        # 创建三个不同的会话
        session1 = await agent.run_with_context("第一会话的问题", "session-1")
        session2 = await agent.run_with_context("第二会话的问题", "session-2")
        session3 = await agent.run_with_context("第三会话的问题", "session-3")

        # 验证会话独立
        sessions = agent.list_sessions()
        assert len(sessions) >= 3
        assert "session-1" in sessions
        assert "session-2" in sessions
        assert "session-3" in sessions

    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self, mock_llm):
        """测试多轮对话"""
        agent = (
            AgentBuilder()
            .with_name("conversation-agent")
            .with_description("多轮对话测试 Agent")
            .with_llm(mock_llm)
            .with_max_history_rounds(5)
            .build()
        )

        session_id = "multi-turn-session"

        # 第一轮
        result1 = await agent.run_with_context("我叫小明", session_id)
        context1 = agent.get_session_context(session_id)

        # 第二轮
        result2 = await agent.run_with_context("我多大了？", session_id)
        context2 = agent.get_session_context(session_id)

        # 第三轮
        result3 = await agent.run_with_context("我喜欢什么？", session_id)
        context3 = agent.get_session_context(session_id)

        # 验证上下文积累
        # 每轮添加用户+助手消息，所以应该有6条消息
        assert len(context3.history_messages) >= 6

    @pytest.mark.asyncio
    async def test_clear_session(self, mock_llm):
        """测试清除会话"""
        agent = (
            AgentBuilder()
            .with_name("session-agent")
            .with_description("会话清除测试 Agent")
            .with_llm(mock_llm)
            .build()
        )

        session_id = "temp-session"

        # 创建会话
        await agent.run_with_context("测试", session_id)
        assert agent.get_session_context(session_id) is not None

        # 清除会话
        result = agent.clear_session(session_id)
        assert result is True

        # 验证会话已清除
        assert agent.get_session_context(session_id) is None

    @pytest.mark.asyncio
    async def test_clear_all_sessions(self, mock_llm):
        """测试清除所有会话"""
        agent = (
            AgentBuilder()
            .with_name("session-agent")
            .with_description("会话清除测试 Agent")
            .with_llm(mock_llm)
            .build()
        )

        # 创建多个会话
        await agent.run_with_context("测试1", "session-1")
        await agent.run_with_context("测试2", "session-2")
        await agent.run_with_context("测试3", "session-3")

        # 获取上下文管理器并清除所有
        manager = agent.clear_session()


        # 验证所有会话已清除
        assert len(manager.list_sessions()) == 0


# =============================================================================
# 5. Multi-Agent Tests
# =============================================================================


class TestMultiAgent:
    """测试多智能体功能"""

    @pytest.mark.asyncio
    async def test_agent_with_children(self, mock_llm):
        """测试带有子 Agent 的 Agent"""
        # 创建子 Agent
        child_agent = (
            AgentBuilder()
            .with_name("child-agent")
            .with_description("子智能体")
            .with_llm(mock_llm)
            .build()
        )

        # 创建父 Agent
        parent_agent = (
            AgentBuilder()
            .with_name("parent-agent")
            .with_description("父智能体")
            .with_llm(mock_llm)
            .with_children([child_agent])
            .build()
        )

        # 验证子 Agent 已注册
        assert len(parent_agent.children) == 1
        assert parent_agent.children[0].name == "child-agent"

    @pytest.mark.asyncio
    async def test_multiple_children(self, mock_llm):
        """测试多个子 Agent"""
        children = [
            (
                AgentBuilder()
                .with_name(f"child-{i}")
                .with_description(f"子智能体{i}")
                .with_llm(mock_llm)
                .build()
            )
            for i in range(3)
        ]

        parent = (
            AgentBuilder()
            .with_name("parent")
            .with_description("父智能体")
            .with_llm(mock_llm)
            .with_children(children)
            .build()
        )

        assert len(parent.children) == 3

    @pytest.mark.asyncio
    async def test_child_agent_tool_registration(self, mock_llm):
        """测试子 Agent 被注册为工具"""
        child = (
            AgentBuilder()
            .with_name("child")
            .with_description("子智能体")
            .with_llm(mock_llm)
            .build()
        )

        parent = (
            AgentBuilder()
            .with_name("parent")
            .with_description("父智能体")
            .with_llm(mock_llm)
            .with_children([child])
            .build()
        )

        await parent._ensure_initialized()

        # 验证子 Agent 被注册为工具（工具名是 agent_child）
        child_tool = parent.tool_registry.get("agent_child")
        assert child_tool is not None
        assert child_tool.name == "agent_child"


# =============================================================================
# 6. Memory Feature Tests
# =============================================================================


class TestMemoryFeature:
    """测试记忆功能"""

    @pytest.mark.asyncio
    async def test_memory_slots_configuration(self, mock_llm, memory_slots):
        """测试记忆槽配置"""
        agent = (
            AgentBuilder()
            .with_name("memory-agent")
            .with_description("记忆功能测试 Agent")
            .with_llm(mock_llm)
            .with_memory_enabled(True)
            .with_memory_slots(memory_slots)
            .build()
        )

        manager = agent.get_context_manager()
        assert len(manager.memory_slots) == 2
        assert manager.memory_slots[0].name == "profile"
        assert manager.memory_slots[1].name == "preferences"

    @pytest.mark.asyncio
    async def test_memory_records_storage(self, mock_llm, memory_slots):
        """测试记忆记录存储"""
        manager = AgentContextManager(
            memory_enabled=True,
            memory_slots=memory_slots,
            llm=mock_llm,
        )

        # 手动添加记忆记录
        records = [
            MemoryRecord(name="profile", content="用户叫小明"),
            MemoryRecord(name="preferences", content="喜欢科技股"),
        ]
        manager._memory_records["session-1"] = records

        # 验证记忆可以加载
        loaded = manager._load_memories("session-1")
        assert len(loaded) == 2
        assert loaded[0]["content"] == "用户叫小明"

    @pytest.mark.asyncio
    async def test_memory_loaded_in_context(self, mock_llm, memory_slots):
        """测试记忆被加载到上下文"""
        manager = AgentContextManager(
            memory_enabled=True,
            memory_slots=memory_slots,
            llm=mock_llm,
        )

        # 预设记忆
        records = [
            MemoryRecord(name="profile", content="用户叫小明"),
        ]
        manager._memory_records["session-1"] = records

        # 获取上下文
        context = manager.get_context("session-1")

        # 验证记忆被添加到历史消息
        memory_messages = [msg for msg in context.history_messages if "[记忆:" in msg.get("content", "")]
        assert len(memory_messages) >= 1


# =============================================================================
# 7. Conversation Termination Tests
# =============================================================================


class TestConversationTermination:
    """测试对话终止功能"""

    @pytest.mark.asyncio
    async def test_terminate_during_run(self):
        """测试运行时终止"""
        class SlowLLM:
            def __init__(self):
                self.call_count = 0
                self.running = True

            async def chat(self, messages, tools=None):
                self.call_count += 1
                await asyncio.sleep(0.1)  # 模拟延迟

                if not self.running:
                    return {
                        "message": {"role": "assistant", "content": "stopped"},
                        "raw": None,
                    }

                return {
                    "message": {
                        "role": "assistant",
                        "content": None,  # 不返回最终答案，继续循环
                    },
                    "raw": None,
                }

        slow_llm = SlowLLM()
        agent = (
            AgentBuilder()
            .with_name("slow-agent")
            .with_description("慢速响应 Agent")
            .with_llm(slow_llm)
            .with_max_steps(100)  # 设置很大的最大步数
            .build()
        )

        # 在后台运行
        task = asyncio.create_task(agent.run("长时间任务"))

        # 等待一小段时间后终止
        await asyncio.sleep(0.15)
        agent.terminate()

        result = await task

        # 验证被终止
        assert "[会话已终止]" in result.output or "terminated" in result.output

    @pytest.mark.asyncio
    async def test_runtime_terminate_and_reset(self, mock_llm):
        """测试运行时终止和重置"""
        agent = (
            AgentBuilder()
            .with_name("test-agent")
            .with_description("终止测试 Agent")
            .with_llm(mock_llm)
            .build()
        )

        # 终止
        agent.runtime.terminate()
        assert agent.runtime._terminated is True

        # 重置
        agent.runtime.reset()
        assert agent.runtime._terminated is False

    @pytest.mark.asyncio
    async def test_terminate_step_type(self, mock_llm):
        """测试终止步骤类型"""
        # 创建一个可以被终止的 Agent
        agent = (
            AgentBuilder()
            .with_name("test-agent")
            .with_description("终止测试 Agent")
            .with_llm(mock_llm)
            .build()
        )

        # 直接终止
        agent.runtime.terminate()
        result = await agent.run("测试")

        # 验证步骤类型
        assert any(step.type == "terminated" for step in result.steps)


# =============================================================================
# 8. LLM Selection Tests
# =============================================================================


class TestLLMSelection:
    """测试模型选择和切换"""

    @pytest.mark.asyncio
    async def test_agent_with_different_llm(self):
        """测试使用不同的 LLM"""
        class CustomLLM:
            def __init__(self, response_text):
                self.response_text = response_text

            async def chat(self, messages, tools=None):
                return {
                    "message": {"role": "assistant", "content": self.response_text},
                    "raw": None,
                }

        llm1 = CustomLLM("Response from LLM 1")
        llm2 = CustomLLM("Response from LLM 2")

        agent1 = (
            AgentBuilder()
            .with_name("agent1")
            .with_description("Agent 1")
            .with_llm(llm1)
            .build()
        )
        agent2 = (
            AgentBuilder()
            .with_name("agent2")
            .with_description("Agent 2")
            .with_llm(llm2)
            .build()
        )

        result1 = await agent1.run("test")
        result2 = await agent2.run("test")

        assert result1.output == "Response from LLM 1"
        assert result2.output == "Response from LLM 2"


# =============================================================================
# 9. ContextManager Configuration Tests
# =============================================================================


class TestContextManagerConfiguration:
    """测试上下文管理器配置"""

    def test_compression_configuration(self):
        """测试压缩配置"""
        manager = AgentContextManager(
            compression_enabled=True,
            max_context_length=100,
            compression_trigger_ratio=0.7,
            compression_ratio=0.4,
        )

        assert manager.compression_enabled is True
        assert manager.max_context_length == 100
        assert manager.compression_trigger_ratio == 0.7
        assert manager.compression_ratio == 0.4

    def test_memory_configuration(self, memory_slots):
        """测试记忆配置"""
        manager = AgentContextManager(
            memory_enabled=True,
            memory_slots=memory_slots,
        )

        assert manager.memory_enabled is True
        assert len(manager.memory_slots) == 2

    @pytest.mark.asyncio
    async def test_full_configuration(self, mock_llm, memory_slots):
        """测试完整配置"""
        manager = AgentContextManager(
            max_history_rounds=20,
            memory_enabled=True,
            memory_slots=memory_slots,
            compression_enabled=True,
            max_context_length=100,
            compression_trigger_ratio=0.75,
            compression_ratio=0.3,
            llm=mock_llm,
        )

        # 验证所有配置
        assert manager.max_history_rounds == 20
        assert manager.memory_enabled is True
        assert manager.compression_enabled is True
        assert manager.max_context_length == 100


# =============================================================================
# 10. Stream Output Tests
# =============================================================================


class TestStreamOutput:
    """测试流式输出"""

    @pytest.mark.asyncio
    async def test_run_stream_with_steps(self, mock_llm):
        """测试流式运行并收集步骤"""
        agent = (
            AgentBuilder()
            .with_name("stream-agent")
            .with_description("流式输出测试 Agent")
            .with_llm(mock_llm)
            .build()
        )

        steps_collected = []

        def collect_steps(step: AgentStep) -> None:
            steps_collected.append(step)

        context = agent.context_manager.get_context("test-session")
        result = await agent.runtime.run_stream("测试任务", context, collect_steps)

        # 验证步骤被收集
        assert len(steps_collected) > 0
        assert result.output == "测试响应"


# =============================================================================
# 11. AgentBuilder Tests
# =============================================================================


class TestAgentBuilder:
    """测试 AgentBuilder 构建器模式"""

    @pytest.mark.asyncio
    async def test_builder_fluent_interface(self, mock_llm):
        """测试流式接口"""
        agent = (
            AgentBuilder()
            .with_name("test")
            .with_description("测试")
            .with_llm(mock_llm)
            .with_max_steps(10)
            .with_instructions("Custom instructions")
            .with_workspace_root("/tmp/workspace")
            .with_memory_enabled(True)
            .with_compression_enabled(True)
            .build()
        )

        assert agent.name == "test"
        assert agent.config.max_steps == 10
        assert agent.config.instructions == "Custom instructions"
        assert agent.config.workspace_root == "/tmp/workspace"

    @pytest.mark.asyncio
    async def test_builder_with_skills(self, mock_llm):
        """测试添加技能源"""
        agent = (
            AgentBuilder()
            .with_name("skill-agent")
            .with_description("技能测试 Agent")
            .with_llm(mock_llm)
            .with_skill_sources(["src/agents/test_agent/skills"])
            .build()
        )

        assert "src/agents/test_agent/skills" in agent.skill_sources


# =============================================================================
# 12. Edge Cases and Error Handling
# =============================================================================


class TestEdgeCases:
    """测试边界情况和错误处理"""

    @pytest.mark.asyncio
    async def test_empty_task(self, mock_llm):
        """测试空任务"""
        agent = (
            AgentBuilder()
            .with_name("test")
            .with_description("边界测试 Agent")
            .with_llm(mock_llm)
            .build()
        )
        result = await agent.run("")
        assert result.output is not None

    @pytest.mark.asyncio
    async def test_special_characters_in_task(self, mock_llm):
        """测试任务中的特殊字符"""
        agent = (
            AgentBuilder()
            .with_name("test")
            .with_description("边界测试 Agent")
            .with_llm(mock_llm)
            .build()
        )

        special_task = "测试中文 + English! @#$%^&*()_+"
        result = await agent.run(special_task)
        assert result.output is not None

    @pytest.mark.asyncio
    async def test_very_long_task(self, mock_llm):
        """测试超长任务"""
        agent = (
            AgentBuilder()
            .with_name("test")
            .with_description("边界测试 Agent")
            .with_llm(mock_llm)
            .build()
        )

        long_task = "分析" * 1000
        result = await agent.run(long_task)
        assert result.output is not None


# =============================================================================
# 13. Integration with Memory Generator
# =============================================================================


class TestMemoryGeneratorIntegration:
    """测试与记忆生成器的集成"""

    @pytest.mark.asyncio
    async def test_memory_generator_llm_required(self, memory_slots):
        """测试记忆生成器需要 LLM"""
        from pstock_sdk.agent.memory.memory import MemoryGenerator

        # 没有 LLM 时应该返回空列表
        generator = MemoryGenerator(
            llm=None,
            slots=memory_slots,
            current_records=[],
        )

        messages = [ChatMessage(role="user", content="测试")]
        result = await generator.generate(messages)

        assert result == []

    @pytest.mark.asyncio
    async def test_memory_generator_with_llm(self, memory_slots):
        """测试有 LLM 时的记忆生成"""
        from pstock_sdk.agent.memory.memory import MemoryGenerator

        class TestLLM:
            async def chat(self, messages, tools=None):
                return {
                    "message": {
                        "role": "assistant",
                        "content": '{"updates": [{"slot": "profile", "content": "用户信息"}]}',
                    },
                    "raw": None,
                }

        generator = MemoryGenerator(
            llm=TestLLM(),
            slots=memory_slots,
            current_records=[],
        )

        messages = [ChatMessage(role="user", content="我叫小明")]
        result = await generator.generate(messages)

        assert len(result) > 0
        assert result[0].name == "profile"


# =============================================================================
# 14. Integration with Context Compressor
# =============================================================================


class TestContextCompressorIntegration:
    """测试与上下文压缩器的集成"""

    @pytest.mark.asyncio
    async def test_compressor_creates_summary(self):
        """测试压缩器创建摘要"""
        class TestLLM:
            async def chat(self, messages, tools=None):
                return {
                    "message": {
                        "role": "assistant",
                        "content": "对话摘要：用户讨论了多个话题，最终达成了共识。",
                    },
                    "raw": None,
                }

        compressor = ContextCompressor(
            llm=TestLLM(),
            compression_ratio=0.5,
            min_messages=2,
        )

        # 创建测试消息
        messages = [
            ChatMessage(role="user", content=f"消息{i}")
            for i in range(10)
        ]

        result = await compressor.compress(messages)

        # 验证压缩结果
        assert len(result) < len(messages)
        assert any("[历史对话摘要]" in msg.get("content", "") for msg in result)

    def test_compressor_ratio_validation(self):
        """测试压缩比例验证"""
        with pytest.raises(ValueError):
            ContextCompressor(
                llm=MockLLM(),
                compression_ratio=1.5,  # 无效值
            )

    @pytest.mark.asyncio
    async def test_compressor_no_compression_needed(self):
        """测试不需要压缩的情况"""
        compressor = ContextCompressor(
            llm=MockLLM(),
            compression_ratio=0.5,
            min_messages=2,
        )

        messages = [
            ChatMessage(role="user", content=f"消息{i}")
            for i in range(3)
        ]

        result = await compressor.compress(messages)

        # 消息太少，不应该压缩
        assert len(result) == len(messages)
