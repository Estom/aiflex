"""
Step Context Manager - 单次对话上下文管理器

该模块负责管理 Agent 单次对话(Turn)的上下文，与无状态的 AgentRuntime 配合使用。
"""

import uuid
from typing import Any

from ..memory.compressor import ContextCompressor
from ..memory.memory import MemoryRecord
from .interfaces import (
    AgentContext,
    ChatHistoryMessage,
    ChatMessage,
    LLM,
)


class StepContextManager:
    """
    单次对话上下文管理器

    负责：
    1. 创建 chat_id 用于标识本次对话
    2. 根据 AgentContext 和 task 构建初始 ChatMessage
    3. 管理消息列表的添加和获取
    4. 构建系统提示词和记忆消息
    5. 处理历史消息拼接（支持压缩类型消息的过滤）
    6. 支持单次模型调用前的消息压缩
    """

    def __init__(
        self,
        context: AgentContext,
        task: str,
        agent_name: str,
        agent_description: str,
        agent_instructions: str | None,
        workspace_root: str | None,
        skill_registry: Any = None,
        compression_enabled: bool = False,
        max_context_length: int = 50,
        compression_trigger_ratio: float = 0.8,
        compression_ratio: float = 0.3,
        llm: LLM | None = None,
    ):
        """
        初始化单次对话上下文管理器

        Args:
            context: Agent 上下文
            task: 用户任务
            agent_name: Agent 名称
            agent_description: Agent 描述
            agent_instructions: Agent 指令
            workspace_root: 工作区根目录
            skill_registry: 技能注册表
            compression_enabled: 是否启用上下文压缩
            max_context_length: 上下文最大长度
            compression_trigger_ratio: 压缩触发比例
            compression_ratio: 压缩后保留的比例
            llm: LLM 实例
        """
        self.context = context
        self.task = task
        self.agent_name = agent_name
        self.agent_description = agent_description
        self.agent_instructions = agent_instructions
        self.workspace_root = workspace_root
        self.skill_registry = skill_registry
        self.compression_enabled = compression_enabled
        self.max_context_length = max_context_length
        self.compression_trigger_ratio = 0.9
        self.compression_ratio = compression_ratio
        self.llm = llm

        # 创建 chat_id 用于标识本次对话
        self.chat_id = str(uuid.uuid4())

        # 存储本次对话的消息列表（不包括系统提示词和记忆消息）
        self._messages: list[ChatMessage] = []


    def add_user_message(self, content: str) -> ChatMessage:
        """
        添加用户消息到本次对话

        Args:
            content: 消息内容

        Returns:
            ChatMessage: 添加的消息
        """
        msg = ChatMessage(role="user", content=content)
        self._messages.append(msg)
        return msg


    def add_assistant_message(
        self,
        content: str | None,
        tool_calls: list[Any] | None = None,
    ) -> ChatMessage:
        """
        添加助手消息

        Args:
            content: 消息内容
            tool_calls: 工具调用列表

        Returns:
            ChatMessage: 添加的消息
        """
        msg = ChatMessage(
            role="assistant",
            content=content,
            tool_calls=tool_calls or [],
        )
        self._messages.append(msg)
        return msg

    def add_tool_message(
        self,
        tool_call_id: str,
        name: str,
        content: str,
    ) -> ChatMessage:
        """
        添加工具结果消息

        Args:
            tool_call_id: 工具调用 ID
            name: 工具名称
            content: 工具结果

        Returns:
            ChatMessage: 添加的消息
        """
        msg = ChatMessage(
            role="tool",
            tool_call_id=tool_call_id,
            name=name,
            content=content,
        )
        self._messages.append(msg)
        return msg

    def get_current_messages(self) -> list[ChatMessage]:
        """
        获取当前消息列表（用于模型调用）

        包括：系统提示词 -> 记忆消息 -> 历史消息 -> 本次对话的消息

        Returns:
            list[ChatMessage]: 消息列表
        """
        messages: list[ChatMessage] = []

        # 1. 添加系统提示词
        messages.append(self._build_system_message())

        # 2. 添加记忆消息（如果有）
        memory_message = self._build_memory_message()
        if memory_message:
            messages.append(memory_message)

        # 3. 添加历史消息
        messages.extend(self._get_history_messages())

        # 4. 添加本次对话的消息
        messages.extend(self._messages)

        return messages

    def _build_system_message(self) -> ChatMessage:
        """构建系统提示词"""
        return ChatMessage(role="system", content=self._build_system_prompt())

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        parts = [
            f"You are an agent named {self.agent_name}.",
            self.agent_description,
            self.agent_instructions
            or "Use ReAct style with OpenAI function calling. Call tools when helpful and provide a concise final answer when done.",
            "You can use the 'skill' tool to access specialized capabilities when needed.",
        ]

        if self.workspace_root:
            parts.append(f"Your workspace root is at: {self.workspace_root}")

        return "\n\n".join(parts)

    def _build_memory_message(self) -> ChatMessage | None:
        """
        构建记忆消息

        Returns:
            ChatMessage | None: 记忆消息，如果没有记忆则返回 None
        """
        memory_records = self.context.memory_records or []
        if not memory_records:
            return None

        memory_content_list = []
        for memory in memory_records:
            memory_content = f"[记忆: {memory.get('name', '')}]: {memory.get('content', '')}"
            memory_content_list.append(memory_content)

        content = "系统中当前存在以下记忆：\n\n" + "\n".join(memory_content_list)
        return ChatMessage(role="system", content=content)

    def _get_history_messages(self) -> list[ChatMessage]:
        """
        获取历史消息

        处理压缩类型的 ChatHistoryMessage：
        - 如果遇到压缩类型的历史消息，则舍弃该消息之前的所有记录
        - 只保留压缩类型消息及之后的记录

        Returns:
            list[ChatMessage]: 历史消息列表
        """
        
        chat_history: list[ChatHistoryMessage] = self.context.chat_history_messages or []

        # 倒序查找最近的压缩类型消息的索引
        compression_index = -1
        for i in range(len(chat_history) - 1, -1, -1):
            if chat_history[i].is_compression:
                compression_index = i
                break

        # 如果有压缩消息，从压缩消息开始获取
        if compression_index >= 0:
            chat_history = chat_history[compression_index:]

        # 展开历史消息为 ChatMessage 列表
        result: list[ChatMessage] = []
        for history_msg in chat_history:
            # 添加角色消息（user 或 assistant）
            result.append(ChatMessage(role=history_msg.role, content=history_msg.content))

            # 添加对话过程中的消息（如果有）
            # if history_msg.chat_messages:
            #     result.extend(history_msg.chat_messages)

        return result

    async def check_and_compress_messages(self) -> None:
        """
        检查并压缩消息（如果需要）

        判断是否需要在模型调用前压缩消息，如果需要则执行压缩。
        """
        if not self.compression_enabled:
            return

        if not self.llm:
            return

        # 估算当前消息的 token 数量
        messages = self.get_current_messages()
        estimated_tokens = self._estimate_tokens(messages)
        trigger_threshold = int(self.max_context_length * self.compression_trigger_ratio)

        if estimated_tokens < trigger_threshold:
            return

        # 需要压缩，执行压缩操作
        # 获取当前需要压缩的消息（不包括系统提示词和记忆消息）
        messages_to_compress = self._messages.copy()

        min_messages = 2
        if not messages_to_compress or len(messages_to_compress) <= min_messages:
            return
        

        # 创建压缩器
        compressor = ContextCompressor(
            llm=self.llm,
            compression_ratio=self.compression_ratio,
            min_messages=min_messages,
        )

        try:
            # 压缩消息
            compressed = await compressor.compress(messages_to_compress)

            if compressed and len(compressed) > 0:
                # 将压缩后的消息和压缩标记一起处理
                self._messages = compressed

        except Exception as e:
            # 如果压缩失败，保持原样
            print(f"Message compression failed: {e}")

    def _estimate_tokens(self, messages: list[ChatMessage]) -> int:
        """
        估算消息列表的 token 数量

        Args:
            messages: 消息列表

        Returns:
            int: 估算的 token 数量
        """
        import re

        total_chars = 0
        chinese_chars = 0
        ascii_chars = 0
        other_chars = 0

        for msg in messages:
            content = msg.get("content", "")
            if not content or not isinstance(content, str):
                continue

            # 统计各类字符数量
            chinese_pattern = re.compile(
                r"[\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df\U0002a700-\U0002b73f\U0002b740-\U0002b81f\U0002b820-\U0002ceaf]"
            )
            chinese = len(chinese_pattern.findall(content))
            ascii_count = len(re.findall(r"[\x00-\x7f]", content))
            other = len(content) - chinese - ascii_count

            chinese_chars += chinese
            ascii_chars += ascii_count
            other_chars += other
            total_chars += len(content)

        # 近似计算 token 数量
        tokens = (chinese_chars // 2) + (ascii_chars // 4) + (other_chars // 3)

        # 加上一些额外的开销
        overhead = len(messages) * 10

        return tokens + overhead

    def get_chat_id(self) -> str:
        """
        获取本次对话的 chat_id

        Returns:
            str: chat_id
        """
        return self.chat_id

    def get_messages(self) -> list[ChatMessage]:
        """
        获取本次对话的消息列表（不包括系统提示词和记忆消息）

        Returns:
            list[ChatMessage]: 消息列表
        """
        return self._messages.copy()
