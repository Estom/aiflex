"""
OpenAI LLM - OpenAI 兼容的 LLM 实现

支持 OpenAI API 和兼容 OpenAI 格式的 API（如 Azure、通义千问等）
"""

import os
from typing import Any, AsyncIterable

from openai import AsyncOpenAI, Stream
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessageParam,
    ChatCompletionToolUnionParam,
)

from ..core.interfaces import ChatMessage, LLM, LLMResponse, ToolCall, ToolDefinition


DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_TEMPERATURE = 0.2


class OpenAIModelOptions:
    """OpenAI 模型配置选项"""

    def __init__(
        self,
        model: str | None = None,
        api_base: str | None = None,
        max_tokens: int | None = None,
        temperature: float = DEFAULT_TEMPERATURE,
        timeout: float | None = None,
    ):
        self.model = model
        self.api_base = api_base
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout


class OpenAILLM(LLM):
    """
    OpenAI LLM 实现

    支持 OpenAI API 和兼容的第三方 API
    """

    def __init__(self, api_key: str, options: OpenAIModelOptions | None = None):
        """
        初始化 OpenAI LLM

        Args:
            api_key: API 密钥
            options: 模型配置选项
        """
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required to initialize OpenAILLM")

        options = options or OpenAIModelOptions()
        self.model = options.model or DEFAULT_MODEL
        self.temperature = options.temperature
        self.max_tokens = options.max_tokens

        # 创建 OpenAI 客户端
        client_kwargs: dict[str, Any] = {"api_key": api_key}
        if options.api_base:
            client_kwargs["base_url"] = options.api_base
        if options.timeout:
            client_kwargs["timeout"] = options.timeout

        self.client = AsyncOpenAI(**client_kwargs)

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition] | None = None,
    ) -> LLMResponse:
        """
        聊天接口

        Args:
            messages: 聊天消息列表
            tools: 可用工具列表

        Returns:
            LLMResponse: LLM 响应
        """
        # 转换消息格式
        openai_messages = [self._map_message(msg) for msg in messages]

        # 转换工具格式
        openai_tools: list[ChatCompletionToolUnionParam] | None = None
        if tools:
            openai_tools = [self._map_tool(tool) for tool in tools]  # type: ignore

        # 调用 OpenAI API
        completion: ChatCompletion = await self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            messages=openai_messages,
            tools=openai_tools,
            tool_choice="auto" if openai_tools else None,
        )

        # 解析响应
        choice = completion.choices[0]
        message = choice.message

        # 提取工具调用
        tool_calls: list[ToolCall] = []
        if message.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                }
                for tc in message.tool_calls
            ]

        return {
            "message": {
                "role": "assistant",
                "content": message.content,
                "tool_calls": tool_calls if tool_calls else None,
            },
            "raw": completion,
        }

    async def stream(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition] | None = None,
    ) -> AsyncIterable[str]:
        """
        流式聊天接口

        Args:
            messages: 聊天消息列表
            tools: 可用工具列表

        Yields:
            str: 流式文本片段
        """
        openai_messages = [self._map_message(msg) for msg in messages]
        openai_tools: list[ChatCompletionToolUnionParam] | None = None
        if tools:
            openai_tools = [self._map_tool(tool) for tool in tools]  # type: ignore

        stream: Stream[ChatCompletion] = await self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
            messages=openai_messages,
            tools=openai_tools,
            tool_choice="auto" if openai_tools else None,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    def _map_message(self, message: ChatMessage) -> ChatCompletionMessageParam:
        """转换消息格式"""
        role = message["role"]

        if role == "tool":
            return {
                "role": "tool",
                "tool_call_id": message["tool_call_id"],
                "content": message["content"],
            }

        if role == "assistant":
            msg: ChatCompletionMessageParam = {
                "role": "assistant",
                "content": message.get("content"),
            }

            # 添加工具调用
            if message.get("tool_calls"):
                msg["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": tc["arguments"],
                        },
                    }
                    for tc in message["tool_calls"]
                ]

            return msg

        return {"role": role, "content": message["content"]}

    def _map_tool(self, tool: ToolDefinition) -> ChatCompletionToolUnionParam:
        """转换工具格式"""
        return {
            "type": tool["type"],
            "function": tool["function"],
        }
