"""
MCP Client - Model Context Protocol Client

使用官方 MCP Python SDK (pip install mcp) 连接 MCP 服务器。
支持 SSE 和 StreamableHTTP 两种传输方式。
"""

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, AsyncGenerator

import httpx
from loguru import logger
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamable_http_client

from .mcp_config import McpServerConfig

CLIENT_INFO = {"name": "aiflex-mcp-client", "version": "0.1.0"}


class TransportType(str, Enum):
    """MCP 传输类型"""
    SSE = "sse"
    STREAMABLE_HTTP = "streamable-http"


@dataclass
class McpToolDefinition:
    """MCP 工具定义"""
    name: str
    display_name: str | None = None
    description: str | None = None
    parameters: dict[str, Any] | None = None


class McpClient:
    """
    MCP 客户端

    使用官方 MCP Python SDK，支持 SSE 和 StreamableHTTP 传输
    """

    def __init__(self, config: McpServerConfig) -> None:
        """
        初始化 MCP 客户端

        Args:
            config: MCP 服务器配置
        """
        self._config = config
        self._transport_type = self._get_transport_type()

    def _get_transport_type(self) -> TransportType:
        """从配置获取传输类型"""
        transport = self._config.get("transportType", "sse")
        try:
            return TransportType(transport)
        except ValueError:
            logger.warning(
                f"Unknown transport type '{transport}', defaulting to 'sse'"
            )
            return TransportType.SSE

    @asynccontextmanager
    async def _session(self) -> AsyncGenerator[ClientSession, None]:
        """
        创建并初始化 ClientSession 上下文

        Yields:
            ClientSession: 已初始化的 MCP 客户端会话
        """
        base_url = self._config.baseUrl.rstrip("/")

        # 准备认证头
        headers = {}
        if self._config.apiKey:
            headers["Authorization"] = f"Bearer {self._config.apiKey}"
        if self._config.headers:
            headers.update(self._config.headers)

        if self._transport_type == TransportType.SSE:
            logger.info(f"Connecting to MCP server {self._config.name} using SSE transport")
            async with sse_client(url=base_url, headers=headers or None, timeout=60.0) as (
                read_stream,
                write_stream,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    yield session
        else:
            logger.info(f"Connecting to MCP server {self._config.name} using StreamableHTTP transport")
            # StreamableHTTP 也支持 headers
            async with streamable_http_client(url=base_url, headers=headers or None) as (
                read_stream,
                write_stream,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    yield session

    async def list_tools(self) -> list[McpToolDefinition]:
        """
        列出 MCP 服务器提供的所有工具

        Returns:
            工具定义列表
        """
        import traceback
        import anyio

        try:
            async with self._session() as session:
                tools_response = await session.list_tools()

                result = []
                for tool in tools_response.tools:
                    result.append(self._map_tool_definition(tool))

                return result
        except anyio.get_cancelled_exc_class():
            logger.warning(f"Connection to MCP server {self._config.name} was cancelled")
            return []
        except BaseException as e:
            logger.error(f"Failed to list tools from MCP server {self._config.name}: {e}")
            # 尝试获取 TaskGroup 的子异常
            if hasattr(e, "__cause__") and e.__cause__ is not None:
                logger.error(f"Caused by: {e.__cause__}")
            if hasattr(e, "__notes__"):
                for note in getattr(e, "__notes__", []):
                    logger.error(f"Error note: {note}")
            logger.debug(traceback.format_exc())
            return []

    def _map_tool_definition(self, tool: Any) -> McpToolDefinition:
        """
        映射工具定义

        Args:
            tool: 原始工具定义 (mcp.types.Tool)

        Returns:
            McpToolDefinition: 标准化的工具定义
        """
        # 获取 input_schema
        input_schema = tool.inputSchema if hasattr(tool, "inputSchema") else {}

        # 从 annotations 获取 display_name
        display_name = None
        if hasattr(tool, "annotations") and tool.annotations:
            display_name = tool.annotations.get("title")

        return McpToolDefinition(
            name=tool.name,
            display_name=display_name,
            description=tool.description if hasattr(tool, "description") else None,
            parameters=input_schema,
        )

    async def call_tool(self, name: str, args: Any) -> str:
        """
        调用 MCP 工具

        Args:
            name: 工具名称
            args: 工具参数

        Returns:
            工具执行结果（字符串形式）
        """
        try:
            # 规范化参数
            if args and isinstance(args, dict) and not isinstance(args, str):
                normalized_args = args
            else:
                normalized_args = {}

            async with self._session() as session:
                result = await session.call_tool(name=name, arguments=normalized_args)
                return self._stringify_tool_result(result)
        except Exception as e:
            logger.error(f"Failed to call MCP tool {name}: {e}")
            return f"Error calling MCP tool {name}: {e!s}"

    def _stringify_tool_result(self, result: Any) -> str:
        """
        将工具调用结果转换为字符串

        Args:
            result: 工具调用结果 (mcp.types.CallToolResult)

        Returns:
            str: 字符串形式的结果
        """
        parts: list[str] = []

        # 处理 content 列表
        if hasattr(result, "content") and result.content:
            for item in result.content:
                if hasattr(item, "text"):
                    text = item.text
                    if text:
                        parts.append(text)
                elif hasattr(item, "data"):
                    # 处理图片、资源等二进制数据
                    parts.append(f"[binary data: {type(item).__name__}]")
                else:
                    parts.append(str(item))

        if parts:
            return "\n".join(parts)

        return ""
