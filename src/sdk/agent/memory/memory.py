"""
Memory Store - 记忆存储

该模块提供记忆存储、记录生成等功能，用于管理 Agent 的长期和短期记忆。
"""

# ruff: noqa: E501

from typing import Any

from ..core.interfaces import ChatMessage, LLM


class MemorySlotConfig(dict):
    """记忆槽配置"""

    def __init__(
        self,
        name: str,
        description: str | None = None,
        type: str = "short_term",  # 'short_term' | 'long_term'
        **kwargs: Any,
    ):
        super().__init__(
            name=name,
            description=description,
            type=type,
            **kwargs,
        )

    @property
    def name(self) -> str:
        return self["name"]

    @property
    def description(self) -> str | None:
        return self.get("description")

    @property
    def type(self) -> str:
        return self.get("type", "short_term")


class MemoryRecord(dict):
    """记忆记录"""

    def __init__(
        self,
        name: str,
        content: str,
        **kwargs: Any,
    ):
        super().__init__(
            name=name,
            content=content,
            **kwargs,
        )

    @property
    def name(self) -> str:
        return self["name"]

    @property
    def content(self) -> str:
        return self["content"]

    @property
    def type(self) -> str:
        return self.get("type", "short_term")


# 记忆生成器的内置提示词
MEMORY_GENERATION_PROMPT = """\
你是一个专业的记忆生成助手。你的任务是从对话记录中提取和总结关键信息，并将其存储到指定的记忆槽中。

记忆槽配置:
{slot_config}

当前记忆值:
{current_memories}

对话记录:
{transcript}

请分析上述对话记录，并为每个需要更新的记忆槽生成新的记忆内容。

返回格式（JSON）:
{{
  "updates": [
    {{
      "slot": "槽位名称",
      "content": "新的记忆内容（如果需要清空，返回空字符串）"
    }}
  ]
}}

注意：
1. 只更新有新信息或需要变更的槽位
2. 保持记忆简洁、准确、客观
3. 避免添加推测性或不确定的信息
4. 如果某个槽位没有相关新信息，不要包含在更新列表中
"""


class MemoryGenerator:
    """
    记忆生成器

    根据 LLM 和对话历史生成记忆记录。

    Example:
        generator = MemoryGenerator(
            llm=llm,
            slots=[
                MemorySlotConfig(name="profile", description="用户画像"),
                MemorySlotConfig(name="preferences", description="用户偏好"),
            ],
            current_records=[
                MemoryRecord(name="profile", content="已知信息"),
            ],
        )

        # 生成记忆
        messages = [
            ChatMessage(role="user", content="我叫小明"),
            ChatMessage(role="assistant", content="你好小明！"),
        ]
        records = await generator.generate(messages)
    """

    def __init__(
        self,
        llm: LLM,
        slots: list[MemorySlotConfig],
        current_records: list[MemoryRecord] | None = None,
    ):
        """
        初始化记忆生成器

        Args:
            llm: LLM 实例（用于生成记忆）
            slots: 记忆槽配置列表
            current_records: 已有的记忆记录列表
        """
        self.llm = llm
        self.slots = slots
        self.current_records = current_records or []

    async def generate(
        self,
        history_messages: list[ChatMessage],
    ) -> list[MemoryRecord]:
        """
        根据历史消息生成记忆记录

        Args:
            history_messages: 历史消息列表（ChatMessage 对象）

        Returns:
            list[MemoryRecord]: 生成的记忆记录列表
        """
        if not self.llm or not self.slots:
            return []

        # 构建对话记录文本
        transcript = self._build_transcript(history_messages)

        # 构建提示词
        prompt = self._build_prompt(transcript)

        # 调用 LLM 生成记忆
        try:
            messages: list[ChatMessage] = [
                ChatMessage(role="system", content="你是一个专业的记忆生成助手。"),
                ChatMessage(role="user", content=prompt),
            ]

            response = await self.llm.chat(messages)

            # 解析响应
            return self._parse_response(response)

        except Exception as e:
            # 如果调用失败，返回空列表
            print(f"Memory generation failed: {e}")
            return []

    def _build_prompt(self, transcript: str) -> str:
        """
        构建记忆生成提示词

        Args:
            transcript: 对话记录文本

        Returns:
            str: 完整的提示词
        """
        slot_config = self._format_slot_config()
        current_memories = self._format_current_memories()

        return MEMORY_GENERATION_PROMPT.format(
            slot_config=slot_config,
            current_memories=current_memories,
            transcript=transcript,
        )

    def _format_slot_config(self) -> str:
        """
        格式化记忆槽配置

        Returns:
            str: 格式化后的槽配置文本
        """
        lines = []
        for slot in self.slots:
            lines.append(f"- {slot.name}: {slot.description or 'No description'}")
        return "\n".join(lines)

    def _format_current_memories(self) -> str:
        """
        格式化当前记忆内容

        Returns:
            str: 格式化后的当前记忆文本
        """
        if not self.current_records:
            return "No memories stored yet."

        lines = []
        for record in self.current_records:
            name = record.get("name", "")
            content = record.get("content", "")
            lines.append(f"- {name}: {content if content else '(empty)'}")
        return "\n".join(lines)

    def _build_transcript(self, history_messages: list[ChatMessage]) -> str:
        """
        从历史消息构建对话记录文本

        Args:
            history_messages: 历史消息列表

        Returns:
            str: 对话记录文本
        """
        lines = []
        for msg in history_messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            # 跳过记忆消息
            if isinstance(content, str) and content.startswith("[记忆:"):
                continue

            role_name = "用户" if role == "user" else "助手"
            lines.append(f"{role_name}: {content}")

        return "\n".join(lines)

    def _parse_response(self, response: Any) -> list[MemoryRecord]:
        """
        解析 LLM 响应，生成 MemoryRecord 对象

        Args:
            response: LLM 响应

        Returns:
            list[MemoryRecord]: 记忆记录列表
        """
        try:
            # 获取响应内容
            if isinstance(response, dict):
                content = response.get("message", {}).get("content", "")
            elif hasattr(response, "content"):
                content = str(response.content)
            else:
                content = str(response)

            # 解析 JSON
            import json
            result = json.loads(content)

            records = []
            for update in result.get("updates", []):
                slot_name = update.get("slot")
                slot_content = update.get("content", "")

                # 找到对应的槽配置
                slot_config = None
                for slot in self.slots:
                    if slot.name == slot_name:
                        slot_config = slot
                        break

                if slot_config:
                    record = MemoryRecord(
                        name=slot_name,
                        content=slot_content,
                        type=slot_config.type,
                        description=slot_config.description,
                    )
                    records.append(record)

            return records

        except Exception as e:
            print(f"Failed to parse memory response: {e}")
            return []
