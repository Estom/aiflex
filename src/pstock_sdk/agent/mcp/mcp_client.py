"""
MCP Client - Model Context Protocol Client

使用官方 MCP Python SDK (pip install mcp) 连接 MCP 服务器。
支持 StreamableHTTP 远程服务器连接。
"""

import asyncio
from dataclasses import dataclass
from typing import Any

import httpx
from loguru import logger
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from .mcp_config import McpServerConfig

CLIENT_INFO = {"name": "pstock-mcp-client", "version": "0.1.0"}


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

    使用官方 MCP Python SDK，支持 StreamableHTTP 传输
    """

    def __init__(self, config: McpServerConfig) -> None:
        """
        初始化 MCP 客户端

        Args:
            config: MCP 服务器配置
        """
        self._config = config
        self._session: ClientSession | None = None
        self._http_client: httpx.AsyncClient | None = None
        self._client_context: Any | None = None
        self._initialized = False
        self._lock = asyncio.Lock()

    def _create_http_client(self) -> httpx.AsyncClient:
        """创建配置好认证信息的 HTTP 客户端"""
        headers = dict(self._config.headers or {})
        if self._config.apiKey and "Authorization" not in headers:
            headers["Authorization"] = f"Bearer {self._config.apiKey}"

        return httpx.AsyncClient(
            headers=headers,
            timeout=httpx.Timeout(60.0),
        )

    async def _get_session(self) -> ClientSession:
        """
        获取或创建 ClientSession

        Returns:
            ClientSession: MCP 客户端会话
        """
        async with self._lock:
            if self._session is None:
                await self._connect()

            if not self._initialized:
                await self._session.initialize()
                self._initialized = True

            return self._session

    async def _connect(self) -> None:
        """建立 MCP 连接"""
        # 创建 HTTP 客户端
        self._http_client = self._create_http_client()

        # 创建 streamable_http_client 上下文
        self._client_context = streamable_http_client(
            url=self._config.baseUrl.rstrip("/"),
            http_client=self._http_client,
        )

        # 进入上下文获取 streams
        read_stream, write_stream, _ = await self._client_context.__aenter__()

        # 创建 ClientSession
        self._session = ClientSession(
            read_stream=read_stream,
            write_stream=write_stream,
        )

    async def list_tools(self) -> list[McpToolDefinition]:
        """
        列出 MCP 服务器提供的所有工具

        Returns:
            工具定义列表
        """
        try:
            session = await self._get_session()
            tools_response = await session.list_tools()

            result = []
            for tool in tools_response.tools:
                result.append(self._map_tool_definition(tool))

            return result
        except Exception as e:
            logger.error(f"Failed to list tools from MCP server {self._config.name}: {e}")
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
        input_schema = tool.input_schema if hasattr(tool, "input_schema") else {}

        # 从 annotations 获取 display_name
        display_name = None
        if hasattr(tool, "annotations") and tool.annotations:
            display_name = tool.annotations.get("title")

        # 提取 properties 作为 parameters
        parameters = None
        if input_schema and isinstance(input_schema, dict):
            parameters = input_schema.get("properties")

        return McpToolDefinition(
            name=tool.name,
            display_name=display_name,
            description=tool.description if hasattr(tool, "description") else None,
            parameters=parameters,
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
            session = await self._get_session()

            # 规范化参数
            if args and isinstance(args, dict) and not isinstance(args, str):
                normalized_args = args
            else:
                normalized_args = {}

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

    async def close(self) -> None:
        """关闭客户端连接"""
        async with self._lock:
            if self._client_context:
                try:
                    await self._client_context.__aexit__(None, None, None)
                except Exception as e:
                    logger.warning(f"Error closing MCP client context: {e}")
                self._client_context = None

            if self._http_client:
                try:
                    await self._http_client.aclose()
                except Exception as e:
                    logger.warning(f"Error closing HTTP client: {e}")
                self._http_client = None

            self._session = None
            self._initialized = False

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._get_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()