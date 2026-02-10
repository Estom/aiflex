"""
Context Compressor - 上下文压缩器

该模块提供上下文压缩功能，通过 LLM 对历史消息进行摘要压缩，
减少上下文长度以适配模型的 token 限制。
"""

# ruff: noqa: E501

from typing import Any

from ..core.interfaces import ChatMessage, LLM


# 上下文压缩的内置提示词
CONTEXT_COMPRESSION_PROMPT = """你是一个专业的对话摘要助手。你的任务是将一段对话历史压缩成简洁的摘要。

原始对话（当前约 {current_tokens} tokens）:
{transcript}

目标：将上述对话压缩至约 {target_tokens} tokens。

请分析上述对话，生成一份简洁的摘要。摘要应该：
1. 包含对话的主要话题和关键信息
2. 保留用户的重要需求和偏好
3. 记录重要的结论或结果
4. 简洁明了，避免冗余
5. 控制在目标 token 数量附近（允许 ±20% 的误差）

返回格式（纯文本）：
直接返回摘要内容，不要包含任何其他说明或格式标记。
"""


class ContextCompressor:
    """
    上下文压缩器

    通过 LLM 对历史消息进行摘要压缩。

    Example:
        compressor = ContextCompressor(
            llm=llm,
            compression_ratio=0.3,  # 压缩后保留 30% 的消息
        )

        # 压缩历史消息
        compressed = await compressor.compress(history_messages)
    """

    def __init__(
        self,
        llm: LLM,
        compression_ratio: float = 0.5,
        min_messages: int = 2,
    ):
        """
        初始化上下文压缩器

        Args:
            llm: LLM 实例
            compression_ratio: 压缩比例，压缩后保留的消息数量比例 (0.0 - 1.0)
            min_messages: 最少保留的消息数量
        """
        if not 0.0 < compression_ratio <= 1.0:
            raise ValueError("compression_ratio must be between 0.0 and 1.0")

        self.llm = llm
        self.compression_ratio = compression_ratio
        self.min_messages = min_messages

    async def compress(
        self,
        messages: list[ChatMessage],
    ) -> list[ChatMessage]:
        """
        压缩历史消息

        Args:
            messages: 历史消息列表

        Returns:
            list[ChatMessage]: 压缩后的消息列表
        """
        if not messages:
            return []
        
        if messages[0].get("role") == "system":
            messages = messages[1:]

        # 如果目标数量大于等于原数量，不需要压缩
        if self.min_messages >= len(messages):
            return messages

        # 分离最近的消息和需要压缩的旧消息
        recent_messages = messages[-self.min_messages:]
        old_messages = messages[:-self.min_messages]

        if not old_messages:
            return messages

        # 压缩旧消息
        compressed_message = await self._compress_messages(old_messages)

        # 返回压缩消息 + 最近消息
        if not compressed_message:
            return messages
        return [compressed_message] + recent_messages

    def _estimate_tokens(self, text: str) -> int:
        """
        估算文本的 token 数量

        使用近似计算：
        - 中文字符（CJK Unified Ideographs）：约 1 token / 2 字符
        - ASCII 字符：约 1 token / 4 字符
        - 其他字符：约 1 token / 3 字符

        Args:
            text: 输入文本

        Returns:
            int: 估算的 token 数量
        """
        import re

        # 统计各类字符数量
        chinese_pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df\U0002a700-\U0002b73f\U0002b740-\U0002b81f\U0002b820-\U0002ceaf]')
        chinese = len(chinese_pattern.findall(text))
        ascii_count = len(re.findall(r'[\x00-\x7f]', text))
        other = len(text) - chinese - ascii_count

        # 近似计算 token 数量
        return (chinese // 2) + (ascii_count // 4) + (other // 3)

    async def _compress_messages(self, messages: list[ChatMessage]) -> ChatMessage:
        """
        压缩一组消息为单条摘要消息

        Args:
            messages: 需要压缩的消息列表

        Returns:
            ChatMessage | None: 压缩后的摘要消息，失败时返回 None
        """
        # 构建对话记录文本
        transcript = self._build_transcript(messages)

        # 估算当前 token 数量
        current_tokens = self._estimate_tokens(transcript)
        # 计算目标 token 数量
        target_tokens = max(50, int(current_tokens * self.compression_ratio))

        # 构建提示词
        prompt = CONTEXT_COMPRESSION_PROMPT.format(
            transcript=transcript,
            current_tokens=current_tokens,
            target_tokens=target_tokens,
        )

        # 调用 LLM 生成摘要
        try:
            llm_messages: list[ChatMessage] = [
                ChatMessage(role="system", content="你是一个专业的对话摘要助手。"),
                ChatMessage(role="user", content=prompt),
            ]

            response = await self.llm.chat(llm_messages)

            # 提取摘要内容
            summary = self._extract_summary(response)

            return ChatMessage(
                role="assistant",
                content=f"[历史对话摘要]\n{summary}",
            )

        except Exception:
            # 如果压缩失败，返回一个简单的标记消息
            return None

    def _build_transcript(self, messages: list[ChatMessage]) -> str:
        """
        从消息列表构建对话记录文本

        Args:
            messages: 消息列表

        Returns:
            str: 对话记录文本
        """
        lines = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            # 跳过空内容和记忆消息
            if not content:
                continue
            if isinstance(content, str) and content.startswith("[记忆:"):
                continue
            if content.startswith("[历史对话"):
                continue

            role_name = {
                "user": "用户",
                "assistant": "助手",
                "system": "系统",
            }.get(role, role)

            lines.append(f"{role_name}: {content}")

        return "\n".join(lines)

    def _extract_summary(self, response: Any) -> str:
        """
        从 LLM 响应中提取摘要内容

        Args:
            response: LLM 响应

        Returns:
            str: 摘要内容
        """
        # 获取响应内容
        if isinstance(response, dict):
            content = response.get("message", {}).get("content", "")
        elif hasattr(response, "content"):
            content = str(response.content)
        else:
            content = str(response)

        return content.strip()
