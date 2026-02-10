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
        tool_registry: Any = None,
        skill_registry: Any = None,
        agent_name: str | None = None,
        agent_description: str | None = None,
        agent_instructions: str | None = None,
        workspace_root: str | None = None,
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
            tool_registry: 工具注册表
            skill_registry: 技能注册表
            agent_name: Agent 名称
            agent_description: Agent 描述
            agent_instructions: Agent 指令
            workspace_root: 工作区根目录
        """
        self.max_history_rounds = max_history_rounds
        self.memory_enabled = memory_enabled
        self.compression_enabled = compression_enabled
        self.max_context_length = max_context_length
        self.compression_trigger_ratio = compression_trigger_ratio
        self.compression_ratio = compression_ratio
        self.llm = llm
        self.memory_slots: list[MemorySlotConfig] = memory_slots or []
        self.tool_registry = tool_registry
        self.skill_registry = skill_registry
        self.agent_name = agent_name or "Agent"
        self.agent_description = agent_description or ""
        self.agent_instructions = agent_instructions
        self.workspace_root = workspace_root
        # 内置InMemory的历史记录和记忆存储
        self._sessions: dict[str, AgentContext] = {}
        self._memory_records: dict[str, list[MemoryRecord]] = {}

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
                workspace_root=self.workspace_root,
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

        包含系统提示词、记忆消息和历史消息。

        Args:
            session_id: 会话 ID

        Returns:
            list[ChatMessage]: 聊天消息列表
        """
        # 构建消息列表：系统提示词 -> 记忆消息 -> 历史消息
        messages: list[ChatMessage] = [
            self._get_system_message(),
        ]

        # 添加记忆消息
        memory = self._get_memory_message(session_id)
        if memory:
            messages.append(memory)

        # 添加历史消息
        messages.extend(self._get_history_messages(session_id))

        return messages

    def _get_system_message(self) -> ChatMessage:
        """获取系统提示词"""
        return ChatMessage(role="system", content=self._build_system_prompt())
    
    def _get_history_messages(self, session_id: str) -> list[ChatMessage]:
        """获取指定会话的历史消息列表"""
        context = self.get_context(session_id)
        return context.history_messages
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        # 技能列表
        skills_list = ""
        if self.skill_registry:
            skills_list = "\n".join(
                f"- {skill['name']} in path {skill.get('path', '')}: {skill['description']}"
                for skill in self.skill_registry.list()
            )

        parts = [
            f"You are an agent named {self.agent_name}.",
            self.agent_description,
            self.agent_instructions or "Use ReAct style with OpenAI function calling. Call tools when helpful and provide a concise final answer when done.",
            "You can use skills as follows and access them via read file tool:",
            f"Available skills:\n{skills_list}" if skills_list else "No skills are available.",
        ]

        if self.workspace_root:
            parts.append(f"Your workspace root is at: {self.workspace_root}")

        return "\n\n".join(parts)

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
            context = self.get_context(session_id)
            context.history_messages.append(message)
            
        self._after_update(session_id)

    async def _after_update(self, session_id: str) -> None:
        # 如果启用了压缩功能，判断是否需要压缩---只在用户输入后进行压缩
        history_messages = self._get_history_messages(session_id)
        if self._should_compress(session_id) and history_messages and history_messages[-1].get("role") == "user":
            await self._compress_context(session_id)
        else:
            # 限制历史轮次
            self._trim_history(session_id)

        # 如果启用了记忆功能，并且是LLM更新的消息---只在模型问答后进行记忆总结
        if self.memory_enabled and self.llm and self.memory_slots and history_messages and history_messages[-1].get("role") == "assistant":
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

    def _trim_history(self, session_id: str) -> None:
        """
        修剪历史消息，保留最近 N 轮对话

        每轮对话包含用户消息和助手回复，所以消息数量 = max_history_rounds * 2

        Args:
            context: 上下文对象
        """
        max_messages = self.max_history_rounds * 2
        context = self.get_context(session_id)
        if len(context.history_messages) > max_messages:
            # 使用 deque 保留最近的 max_messages 条消息
            trimmed = deque(
                context.history_messages,
                maxlen=max_messages,
            )
            context.history_messages = list(trimmed)

    def _estimate_tokens(self, messages: list[ChatMessage]) -> int:
        """
        估算消息列表的 token 数量

        使用近似计算：
        - 中文字符（CJK Unified Ideographs）：约 1 token / 2 字符
        - ASCII 字符：约 1 token / 4 字符
        - 其他字符：约 1 token / 3 字符

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
            if not content:
                continue

            # 统计各类字符数量
            # CJK 统一汉字范围（基本）
            chinese_pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df\U0002a700-\U0002b73f\U0002b740-\U0002b81f\U0002b820-\U0002ceaf]')
            chinese = len(chinese_pattern.findall(content))
            ascii_count = len(re.findall(r'[\x00-\x7f]', content))
            other = len(content) - chinese - ascii_count

            chinese_chars += chinese
            ascii_chars += ascii_count
            other_chars += other
            total_chars += len(content)

        # 近似计算 token 数量
        # 中文: ~2 字符/token, ASCII: ~4 字符/token, 其他: ~3 字符/token
        tokens = (chinese_chars // 2) + (ascii_chars // 4) + (other_chars // 3)

        # 加上一些额外的开销（role、tool_calls 等字段）
        overhead = len(messages) * 10  # 每条消息约 10 tokens 的结构开销

        return tokens + overhead

    def _should_compress(self, session_id: str) -> bool:
        """
        判断是否需要压缩上下文

        基于 token 长度而非消息数量来判定。

        Args:
            context: 上下文对象

        Returns:
            bool: 是否需要压缩
        """
        if not self.compression_enabled:
            return False

        # 估算当前历史消息的 token 数量
        history_messages = self._get_history_messages(session_id)
        estimated_tokens = self._estimate_tokens(history_messages)
        trigger_threshold = int(
            self.max_context_length * self.compression_trigger_ratio)

        return estimated_tokens >= trigger_threshold

    async def _compress_context(self, session_id: str) -> None:
        """
        压缩上下文

        Args:
            session_id: 会话 ID
            context: 上下文对象
        """
        if not self.llm:
            # 如果没有 LLM，回退到简单修剪
            self._trim_history(session_id)
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
            history_messages = self._get_history_messages(session_id)
            compressed_messages = await compressor.compress(history_messages)

            # 更新上下文使用压缩后的消息
            self.get_context(session_id).history_messages = compressed_messages

        except Exception as e:
            # 如果压缩失败，回退到简单修剪
            print(f"Context compression failed: {e}")
            self._trim_history(session_id)

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
            or session_id in self._memory_records
        )

        if session_id in self._sessions:
            del self._sessions[session_id]
        if session_id in self._memory_records:
            del self._memory_records[session_id]

        return existed

    def clear_all(self) -> None:
        """清除所有会话的上下文"""
        self._sessions.clear()
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