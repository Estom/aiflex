"""
Agent Context Manager - Agent 上下文管理器

该模块负责管理 Agent 的对话状态，与无状态的 AgentRuntime 配合使用。
所有的会话状态都保存在 AgentContext 中，由 AgentContextManager 统一管理。
"""

import asyncio
import uuid
from collections import deque
from datetime import datetime
from typing import Any

from ..memory.compressor import ContextCompressor
from ..memory.memory import MemoryRecord, MemorySlotConfig
from .interfaces import (
    AgentContext,
    ChatHistoryMessage,
    ChatMessage,
    LLM,
)


class AgentContextManager:
    """
    Agent 上下文管理器

    负责：
    1. 管理多个会话的上下文状态
    2. 维护 session_id 到 AgentContext 的映射
    3. 管理 ChatHistoryMessage 类型的历史消息
    4. 管理记忆记录的存储和检索
    5. 支持上下文压缩功能，自动压缩过长的历史消息

    记忆更新规则：
    - 只会在本次 Turn 结束后，新增历史消息的时候，触发异步的更新记忆
    - 不阻塞用户感知到的最终结果展示

    上下文压缩规则：
    - 在本地的 Turn 对话开始之前，判断是否压缩历史上下文
    - 如果触发了压缩，则在被压缩的上下文后添加一条压缩类型的 ChatHistoryMessage
    - 在后续的上下文构建时，会舍弃掉该条历史记录之前的所有记录

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
        context = manager.get_context("session-123")

        # 添加用户消息到历史
        await manager.add_user_message("session-123", "你好", chat_id="chat-001")

        # 添加助手回复到历史
        await manager.add_assistant_message(
            "session-123",
            "你好！有什么可以帮助你的吗？",
            steps=[...],
            chat_messages=[...],
            chat_id="chat-001",
        )

        # 清除指定会话
        manager.clear_context("session-123")
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

        # 内置 InMemory 的历史记录和记忆存储
        self._sessions: dict[str, AgentContext] = {}

    def get_context(
        self,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentContext:
        """
        获取或创建上下文对象

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
                history_messages=[],  # 保留兼容性
                chat_history_messages=[],
                memory_records=[],
                workspace_root=None,
            )

        return self._sessions[session_id]

    async def add_user_message(
        self,
        session_id: str,
        content: str,
        chat_id: str | None = None,
    ) -> None:
        """
        添加用户消息到历史

        Args:
            session_id: 会话 ID
            content: 用户消息内容
            chat_id: 本次对话的 ID
        """
        context = self.get_context(session_id)

        history_message = ChatHistoryMessage(
            role="user",
            content=content,
            steps=None,
            timestamp=datetime.now().isoformat(),
            chat_id=chat_id,
            chat_messages=None,
        )

        context.chat_history_messages.append(history_message)

    async def add_assistant_message(
        self,
        session_id: str,
        content: str,
        steps: list[Any] | None = None,
        chat_messages: list[ChatMessage] | None = None,
        chat_id: str | None = None,
    ) -> None:
        """
        添加助手回复到历史

        添加后触发异步的记忆更新。

        Args:
            session_id: 会话 ID
            content: 助手回复内容
            steps: 执行步骤列表
            chat_messages: 对话过程中的消息列表
            chat_id: 本次对话的 ID
        """
        context = self.get_context(session_id)

        history_message = ChatHistoryMessage(
            role="assistant",
            content=content,
            steps=steps,
            timestamp=datetime.now().isoformat(),
            chat_id=chat_id,
            chat_messages=chat_messages,
        )

        context.chat_history_messages.append(history_message)

        # 限制历史轮次
        self._trim_history(session_id)

        # 触发异步的记忆更新（不阻塞）
        if self.memory_enabled:
            asyncio.create_task(self._generate_and_update_memory(session_id))

    async def check_and_compress_history(self, session_id: str) -> None:
        """
        检查并压缩历史上下文（公开方法）

        在 Turn 开始前判断是否压缩历史上下文。
        如果触发压缩，添加一条压缩标记的 ChatHistoryMessage。

        Args:
            session_id: 会话 ID
        """
        if not self.compression_enabled:
            return

        if self._should_compress_history(session_id):
            await self._compress_history(session_id)

    def _should_compress_history(self, session_id: str) -> bool:
        """
        判断是否需要压缩历史上下文

        Args:
            session_id: 会话 ID

        Returns:
            bool: 是否需要压缩
        """
        context = self.get_context(session_id)
        history_messages = context.chat_history_messages

        if not history_messages:
            return False

        # 估算当前历史消息的 token 数量
        estimated_tokens = self._estimate_tokens_from_history(history_messages)
        trigger_threshold = int(self.max_context_length * self.compression_trigger_ratio)

        return estimated_tokens >= trigger_threshold

    def _estimate_tokens_from_history(self, history_messages: list[ChatHistoryMessage]) -> int:
        """
        从历史消息列表估算 token 数量

        Args:
            history_messages: 历史消息列表

        Returns:
            int: 估算的 token 数量
        """
        import re

        total_chars = 0
        chinese_chars = 0
        ascii_chars = 0
        other_chars = 0

        for msg in history_messages:
            content = msg.content
            if not content:
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
        overhead = len(history_messages) * 10

        return tokens + overhead

    async def _compress_history(self, session_id: str) -> None:
        """
        压缩历史上下文

        添加一条压缩标记的 ChatHistoryMessage（role=assistant, is_compression=True），
        后续构建时会舍弃该消息之前的所有记录。

        Args:
            session_id: 会话 ID
        """
        if not self.llm:
            # 如果没有 LLM，回退到简单修剪
            self._trim_history(session_id)
            return

        context = self.get_context(session_id)
        history_messages = context.chat_history_messages

        if not history_messages:
            return

        # 创建压缩器
        compressor = ContextCompressor(
            llm=self.llm,
            compression_ratio=self.compression_ratio,
            min_messages=2,
        )

        try:
            # 将历史消息转换为 ChatMessage 格式进行压缩
            chat_messages = []
            for history_msg in history_messages:
                chat_messages.append(
                    ChatMessage(role=history_msg.role, content=history_msg.content)
                )

            # 压缩消息
            compressed = await compressor.compress(chat_messages)

            if compressed and len(compressed) > 0:
                # 获取压缩摘要
                summary = ""
                for msg in compressed:
                    if msg.get("content"):
                        summary = msg["content"]
                        break

                # 添加压缩类型的历史消息
                compression_message = ChatHistoryMessage(
                    role="assistant",
                    content=summary,
                    steps=None,
                    timestamp=datetime.now().isoformat(),
                    chat_id=None,
                    chat_messages=None,
                    is_compression=True,
                )

                # 添加到历史消息的开头（这样后续构建时会从这里开始）
                context.chat_history_messages.insert(0, compression_message)

        except Exception as e:
            # 如果压缩失败，回退到简单修剪
            print(f"History compression failed: {e}")
            self._trim_history(session_id)

    def _trim_history(self, session_id: str) -> None:
        """
        修剪历史消息，保留最近 N 轮对话

        Args:
            session_id: 会话 ID
        """
        max_messages = self.max_history_rounds * 2
        context = self.get_context(session_id)

        if len(context.chat_history_messages) > max_messages:
            # 使用 deque 保留最近的 max_messages 条消息
            trimmed = deque(
                context.chat_history_messages,
                maxlen=max_messages,
            )
            context.chat_history_messages = list(trimmed)

    async def _generate_and_update_memory(self, session_id: str) -> None:
        """
        异步生成并更新记忆

        不阻塞用户结果展示。

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
        current_records = context.memory_records or []

        # 将历史消息转换为 ChatMessage 格式
        history_messages = []
        for history_msg in context.chat_history_messages:
            history_messages.append(ChatMessage(role=history_msg.role, content=history_msg.content))

        # 创建记忆生成器
        generator = MemoryGenerator(
            llm=self.llm,
            slots=self.memory_slots,
            current_records=current_records,
        )

        # 生成新记忆
        new_records = await generator.generate(history_messages)

        # 更新记忆存储
        if new_records:
            # 合并新旧记忆
            records_map = {r.name: r for r in current_records}
            for new_record in new_records:
                records_map[new_record.name] = new_record
            context.memory_records = list(records_map.values())

    def clear_context(self, session_id: str) -> bool:
        """
        清除指定会话的上下文

        Args:
            session_id: 会话 ID

        Returns:
            bool: 如果会话存在并被清除返回 True，否则返回 False
        """
        existed = session_id in self._sessions

        if session_id in self._sessions:
            del self._sessions[session_id]

        return existed

    def clear_all(self) -> None:
        """清除所有会话的上下文"""
        self._sessions.clear()

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

    # ========== 兼容性方法（已废弃）==========

    async def get_messages(self, session_id: str) -> list[ChatMessage]:
        """
        获取指定会话的聊天消息列表（已废弃）

        Args:
            session_id: 会话 ID

        Returns:
            list[ChatMessage]: 聊天消息列表
        """
        context = self.get_context(session_id)
        messages: list[ChatMessage] = []

        for history_msg in context.chat_history_messages:
            messages.append(ChatMessage(role=history_msg.role, content=history_msg.content))

        return messages

    async def add_message(self, session_id: str, message: ChatMessage) -> None:
        """添加聊天消息（已废弃）"""
        role = message.get("role", "user")
        content = message.get("content", "")

        if role == "user":
            await self.add_user_message(session_id, content)
        elif role == "assistant":
            await self.add_assistant_message(session_id, content)

    async def add_messages(self, session_id: str, messages: list[ChatMessage]) -> None:
        """添加聊天消息列表（已废弃）"""
        for message in messages:
            await self.add_message(session_id, message)
