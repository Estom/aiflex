"""
PStock SDK - 核心接口定义

本模块定义了 Agent、Tool、LLM 等核心接口。
"""

from dataclasses import dataclass, field
from typing import Any, Protocol
from typing import TypedDict


class ToolDefinition(TypedDict):
    """工具定义，符合 OpenAI function calling 格式"""
    type: str
    function: "FunctionDefinition"


class FunctionDefinition(TypedDict, total=False):
    """函数定义"""
    name: str
    description: str
    parameters: dict[str, Any]


class ToolCall(TypedDict):
    """工具调用"""
    id: str
    name: str
    arguments: str


class Tool(Protocol):
    """工具接口协议"""

    @property
    def name(self) -> str:
        """工具名称"""
        ...

    @property
    def description(self) -> str:
        """工具描述"""
        ...

    @property
    def display_name(self) -> str | None:
        """工具显示名称"""
        ...

    @property
    def parameters(self) -> dict[str, Any] | None:
        """工具参数 schema"""
        ...

    def get_definition(self) -> ToolDefinition:
        """获取工具定义"""
        ...

    async def execute(self, input: Any, context: "AgentContext | None" = None) -> str:
        """执行工具"""
        ...


class Skill(TypedDict):
    """技能定义"""
    name: str
    description: str
    path: str | None


class ChatMessage(TypedDict, total=False):
    """聊天消息"""
    role: str  # 'system' | 'user' | 'assistant' | 'tool'
    content: str | None
    tool_calls: list[ToolCall]
    tool_call_id: str
    name: str


class LLMResponse(TypedDict, total=False):
    """LLM 响应"""
    message: ChatMessage
    raw: Any


class LLM(Protocol):
    """LLM 接口协议"""

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition] | None = None,
    ) -> LLMResponse:
        """聊天接口"""
        ...


@dataclass
class AgentStep:
    """Agent 执行步骤"""
    type: str
    content: str
    display_name: str | None = None
    raw: str | None = None
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentContext:
    """Agent 运行时上下文"""
    session_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    history_messages: list[ChatMessage] = field(default_factory=list)


@dataclass
class AgentRunResult:
    """Agent 运行结果"""
    output: str
    steps: list[AgentStep] = field(default_factory=list)


@dataclass
class ChatHistoryMessage:
    """聊天历史消息"""
    role: str  # 'user' | 'assistant'
    content: str
    steps: list[AgentStep] | None = None
    timestamp: str | None = None
    chat_id: str | None = None
