"""
Agent Context Manager - Agent 上下文管理器

该模块负责管理 Agent 的对话状态，与无状态的 AgentRuntime 配合使用。
所有的会话状态都保存在 AgentContext 中，由 AgentContextManager 统一管理。
"""

import uuid
from collections import deque
from typing import Any

from ..memory.memory import MemoryRecord, MemorySlotConfig
from .interfaces import AgentContext, ChatMessage, LLM


class AgentContextManager:
    """
    Agent 上下文管理器

    负责：
    1. 管理多个会话的上下文状态
    2. 维护 session_id 到 AgentContext 的映射
    3. 控制历史消息保留的轮次
    4. 提供获取和更新上下文的接口
    5. 支持记忆功能，自动生成和更新记忆
    6. 支持上下文压缩功能，自动压缩过长的历史消息

    Example:
        from pstock_sdk.agent.llm.openai_llm import OpenAILLM, OpenAIModelOptions

        llm = OpenAILLM(api_key="sk-xxx", options=OpenAIModelOptions())
        manager = AgentContextManager(
            max_history_rounds=10,
            memory_enabled=True,
            memory_slots=[
                MemorySlotConfig(name="profile", description="用户画像信息"),
                MemorySlotConfig(name="preferences", description="用户偏好设置"),
            ],
            compression_enabled=True,
            max_context_length=50,
            compression_trigger_ratio=0.8,
            compression_ratio=0.3,
            llm=llm,
        )

        # 获取或创建上下文
        context = manager.get_or_create_context("session-123")
        context.history_messages.append(ChatMessage(role="user", content="你好"))

        # 更新上下文（添加新的对话轮次，并触发记忆生成）
        await manager.update_context(
            "session-123",
            user_message="你好",
            assistant_response="你好！有什么可以帮助你的吗？",
        )

        # 清除指定会话
        manager.clear_context("session-123")

        # 清除所有会话
        manager.clear_all()
    """

    def __init__(
        self,
        max_history_rounds: int = 10,
        memory_enabled: bool = False,
        memory_slots: list[MemorySlotConfig] | None = None,
        compression_enabled: bool = False,
        max_context_length: int = 50,
        compression_trigger_ratio: float = 0.8,
        compression_ratio: float = 0.3,
        llm: LLM | None = None,
    ):
        """
        初始化上下文管理器

        Args:
            max_history_rounds: 每个会话保留的最大历史轮次（每轮包含用户消息和助手回复）
            memory_enabled: 是否启用记忆功能
            memory_slots: 记忆槽配置列表
            compression_enabled: 是否启用上下文压缩功能
            max_context_length: 上下文最大长度（消息数量）
            compression_trigger_ratio: 压缩触发比例（达到此比例时触发压缩，0.0-1.0）
            compression_ratio: 压缩后保留的比例（0.0-1.0）
            llm: LLM 实例，用于记忆生成和上下文压缩
        """
        self.max_history_rounds = max_history_rounds
        self.memory_enabled = memory_enabled
        self.compression_enabled = compression_enabled
        self.max_context_length = max_context_length
        self.compression_trigger_ratio = compression_trigger_ratio
        self.compression_ratio = compression_ratio
        self.llm = llm
        self.memory_slots: list[MemorySlotConfig] = memory_slots or []
        # 内置InMemory的历史记录和记忆存储
        self._sessions: dict[str, AgentContext] = {}
        self._memory_records: dict[str, list[MemoryRecord]] = {}
        self._compressed_messages: dict[str, list[ChatMessage]] = {}

    def get_context(
        self,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentContext:
        """
        获取或创建上下文对象

        如果启用了记忆功能，会自动加载相关记忆并添加到历史消息中。
        如果有压缩后的消息，会使用压缩后的消息。

        Args:
            session_id: 会话 ID，如果为 None 则自动生成
            metadata: 额外的元数据

        Returns:
            AgentContext: 上下文对象
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        if session_id not in self._sessions:
            self._sessions[session_id] = AgentContext(
                session_id=session_id,
                metadata=metadata or {},
                history_messages=[],
            )

        return self._sessions[session_id]

    async def update_context(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        更新上下文，添加新的对话轮次

        如果启用了记忆功能，会触发记忆生成和更新。
        如果启用了压缩功能，会判断是否需要压缩并执行压缩。

        Args:
            session_id: 会话 ID
            user_message: 用户消息
            assistant_response: 助手回复
            metadata: 可选的元数据更新
        """
        context = self.get_context(session_id)
        if context is None:
            # 如果上下文不存在，创建新的
            context = self.get_context(session_id, metadata)

        # 添加对话到历史
        context.history_messages.append(
            ChatMessage(role="user", content=user_message))
        context.history_messages.append(
            ChatMessage(role="assistant", content=assistant_response)
        )

        # 更新元数据
        if metadata:
            context.metadata.update(metadata)

        self._after_update(session_id)

    async def get_messages(self, session_id: str) -> list[ChatMessage]:
        """
        获取指定会话的聊天消息列表

        Args:
            session_id: 会话 ID

        Returns:
            list[ChatMessage]: 聊天消息列表
        """
        context = self.get_context(session_id)
        history_messages = context.history_messages
        # 添加记忆消息
        memory = self._get_memory_message(session_id)
        return [memory, *history_messages]

    async def add_message(self, session_id: str, message: ChatMessage) -> None:
        """
        添加聊天消息列表到指定会话

        Args:
            session_id: 会话 ID
            messages: 聊天消息列表
        """
        context = self.get_context(session_id)
        context.history_messages.append(message)
        await self._after_update(session_id)

    async def add_messages(self, session_id: str, messages: list[ChatMessage]) -> None:
        """
        添加聊天消息列表到指定会话

        Args:
            session_id: 会话 ID
            messages: 聊天消息列表
        """
        for message in messages:
            self.add_message(session_id, message)

    async def _after_update(self, session_id: str) -> None:
        context = self.get_context(session_id)
        # 如果启用了压缩功能，判断是否需要压缩
        if self.compression_enabled and self._should_compress(context):
            await self._compress_context(session_id, context)
        else:
            # 限制历史轮次
            self._trim_history(context)

        # 如果启用了记忆功能，并且是LLM更新的消息
        if self.memory_enabled and self.llm and self.memory_slots and context.history_messages[-1].get("role") == "assistant":
            await self._generate_and_update_memory(session_id)

    def _get_memory_message(self, session_id: str) -> ChatMessage:
        """
        获取指定会话的记忆消息列表

        Args:
            session_id: 会话 ID

        Returns:
            ChatMessage: 记忆消息列表
        """
        # 如果启用了记忆功能，加载记忆并添加到历史
        chat_message = None
        if self.memory_enabled and self.memory_slots:
            memories = self._load_memories(session_id)
            memory_content_list = []
            for memory in memories:
                memory_content = (
                    f"[记忆: {memory.get('name', '')}]: {memory.get('content', '')}"
                )
                memory_content_list.append(memory_content)
            content = "系统中当前存在以下记忆：\n\n" + "\n".join(memory_content_list)
            chat_message = ChatMessage(role="assistant", content=content)

        return chat_message

    def _load_memories(self, session_id: str) -> list[MemoryRecord]:
        """
        加载指定会话的记忆

        Args:
            session_id: 会话 ID

        Returns:
            list: 记忆记录列表
        """
        return self._memory_records.get(session_id, [])

    async def _generate_and_update_memory(self, session_id: str) -> None:
        """
        生成并更新记忆

        Args:
            session_id: 会话 ID
        """
        if not self.llm or not self.memory_slots:
            return

        from ..memory.memory import MemoryGenerator

        context = self.get_context(session_id)
        if not context:
            return

        # 获取当前记忆记录
        current_records = self._load_memories(session_id)

        # 创建记忆生成器
        generator = MemoryGenerator(
            llm=self.llm,
            slots=self.memory_slots,
            current_records=current_records,
        )

        # 生成新记忆
        new_records = await generator.generate(context.history_messages)

        # 更新记忆存储
        if new_records:
            # 合并新旧记忆
            records_map = {r.name: r for r in current_records}
            for new_record in new_records:
                records_map[new_record.name] = new_record
            self._memory_records[session_id] = list(records_map.values())

    def _trim_history(self, context: AgentContext) -> None:
        """
        修剪历史消息，保留最近 N 轮对话

        每轮对话包含用户消息和助手回复，所以消息数量 = max_history_rounds * 2

        Args:
            context: 上下文对象
        """
        max_messages = self.max_history_rounds * 2
        if len(context.history_messages) > max_messages:
            # 使用 deque 保留最近的 max_messages 条消息
            trimmed = deque(
                context.history_messages,
                maxlen=max_messages,
            )
            context.history_messages = list(trimmed)

    def _should_compress(self, context: AgentContext) -> bool:
        """
        判断是否需要压缩上下文

        Args:
            context: 上下文对象

        Returns:
            bool: 是否需要压缩
        """
        if not self.compression_enabled:
            return False

        message_count = len(context.history_messages)
        trigger_threshold = int(
            self.max_context_length * self.compression_trigger_ratio)

        return message_count >= trigger_threshold

    async def _compress_context(self, session_id: str, context: AgentContext) -> None:
        """
        压缩上下文

        Args:
            session_id: 会话 ID
            context: 上下文对象
        """
        if not self.llm:
            # 如果没有 LLM，回退到简单修剪
            self._trim_history(context)
            return

        from ..memory.compressor import ContextCompressor

        # 创建压缩器
        compressor = ContextCompressor(
            llm=self.llm,
            compression_ratio=self.compression_ratio,
            min_messages=2,
        )

        try:
            # 压缩历史消息
            compressed_messages = await compressor.compress(context.history_messages)

            # 保存压缩后的消息
            self._compressed_messages[session_id] = compressed_messages

            # 更新上下文使用压缩后的消息
            context.history_messages = compressed_messages

        except Exception as e:
            # 如果压缩失败，回退到简单修剪
            print(f"Context compression failed: {e}")
            self._trim_history(context)

    def clear_context(self, session_id: str) -> bool:
        """
        清除指定会话的上下文

        Args:
            session_id: 会话 ID

        Returns:
            bool: 如果会话存在并被清除返回 True，否则返回 False
        """
        existed = (
            session_id in self._sessions
            or session_id in self._compressed_messages
            or session_id in self._memory_records
        )

        if session_id in self._sessions:
            del self._sessions[session_id]
        if session_id in self._compressed_messages:
            del self._compressed_messages[session_id]
        if session_id in self._memory_records:
            del self._memory_records[session_id]

        return existed

    def clear_all(self) -> None:
        """清除所有会话的上下文"""
        self._sessions.clear()
        self._compressed_messages.clear()
        self._memory_records.clear()

    def list_sessions(self) -> list[str]:
        """
        列出所有活跃的会话 ID

        Returns:
            list[str]: 会话 ID 列表
        """
        return list(self._sessions.keys())

    def get_session_count(self) -> int:
        """
        获取当前会话数量

        Returns:
            int: 会话数量
        """
        return len(self._sessions)

    def set_max_history_rounds(self, max_rounds: int) -> None:
        """
        设置最大历史轮次

        Args:
            max_rounds: 最大轮次
        """
        self.max_history_rounds = max_rounds
        # 对所有现有会话修剪历史
        for context in self._sessions.values():
            self._trim_history(context)
