"""
MCP Client - Model Context Protocol Client

Python implementation of MCP client for communicating with MCP servers.
Supports both Streamable HTTP and SSE (Server-Sent Events) transports.
"""

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

import httpx
from loguru import logger

from .mcp_config import McpServerConfig

CLIENT_INFO = {"name": "pstock-mcp-client", "version": "0.1.0"}


@dataclass
class McpToolDefinition:
    """MCP 工具定义"""
    name: str
    display_name: str | None = None
    description: str | None = None
    parameters: dict[str, Any] | None = None


@dataclass
class _CallToolResult:
    """MCP 工具调用结果"""
    content: list[dict[str, Any]] | None = None
    structured_content: dict[str, Any] | None = None
    is_error: bool = False


class McpClient:
    """
    MCP 客户端

    使用官方 MCP 协议实现，支持 Streamable HTTP 和 SSE 传输
    """

    def __init__(self, config: McpServerConfig) -> None:
        """
        初始化 MCP 客户端

        Args:
            config: MCP 服务器配置
        """
        self._config = config
        self._base_url = config.baseUrl.rstrip("/")

    async def list_tools(self) -> list[McpToolDefinition]:
        """
        列出 MCP 服务器提供的所有工具

        Returns:
            工具定义列表
        """
        return await self._with_client(self._list_tools)

    async def call_tool(self, name: str, args: Any) -> str:
        """
        调用 MCP 工具

        Args:
            name: 工具名称
            args: 工具参数

        Returns:
            工具执行结果（字符串形式）
        """
        return await self._with_client(
            lambda client, headers: self._call_tool_and_stringify(client, name, args, headers)
        )

    async def _with_client(self, handler: Any) -> Any:
        """
        使用客户端执行操作

        先尝试 Streamable HTTP，失败后回退到 SSE

        Args:
            handler: 异步处理函数

        Returns:
            处理结果
        """
        headers = self._build_headers()

        # Try Streamable HTTP first, fall back to SSE if needed
        streamable_error = None
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                return await handler(client, headers)
        except Exception as e:
            streamable_error = e
            logger.debug(f"Streamable HTTP connection failed: {e}, trying SSE")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                return await handler(client, headers)
        except Exception as sse_error:
            raise ConnectionError(
                f"Failed to connect to MCP server. "
                f"Streamable HTTP error: {streamable_error}; SSE error: {sse_error}"
            ) from sse_error

    def _build_headers(self) -> dict[str, str]:
        """
        构建请求头

        Returns:
            请求头字典
        """
        headers: dict[str, str] = dict(self._config.headers or {})
        if self._config.apiKey and "Authorization" not in headers:
            headers["Authorization"] = f"Bearer {self._config.apiKey}"
        return headers

    async def _list_tools(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str],
    ) -> list[McpToolDefinition]:
        """
        获取工具列表

        Args:
            client: HTTP 客户端
            headers: 请求头

        Returns:
            工具定义列表
        """
        url = urljoin(self._base_url, "/v1/tools")

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        }

        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        tools = data.get("result", {}).get("tools", [])
        return [self._map_tool_definition(tool) for tool in tools]

    def _map_tool_definition(self, tool: dict[str, Any]) -> McpToolDefinition:
        """
        映射工具定义

        Args:
            tool: 原始工具定义

        Returns:
            McpToolDefinition: 标准化的工具定义
        """
        input_schema = tool.get("inputSchema", {})
        return McpToolDefinition(
            name=tool.get("name", ""),
            display_name=tool.get("annotations", {}).get("title"),
            description=tool.get("description"),
            parameters=input_schema.get("properties") if input_schema else None,
        )

    async def _call_tool_and_stringify(
        self,
        client: httpx.AsyncClient,
        name: str,
        args: Any,
        headers: dict[str, str],
    ) -> str:
        """
        调用工具并返回字符串结果

        Args:
            client: HTTP 客户端
            name: 工具名称
            args: 工具参数
            headers: 请求头

        Returns:
            工具执行结果（字符串形式）
        """
        result = await self._call_tool(client, name, args, headers)
        return self._stringify_tool_result(result)

    async def _call_tool(
        self,
        client: httpx.AsyncClient,
        name: str,
        args: Any,
        headers: dict[str, str],
    ) -> _CallToolResult:
        """
        调用工具

        Args:
            client: HTTP 客户端
            name: 工具名称
            args: 工具参数
            headers: 请求头

        Returns:
            CallToolResult: 工具调用结果
        """
        # Normalize args
        normalized_args = {}
        if args and isinstance(args, dict) and not isinstance(args, str):
            normalized_args = args

        url = urljoin(self._base_url, "/v1/tools")

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": normalized_args,
            },
        }

        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        result_data = data.get("result", {})
        return _CallToolResult(
            content=result_data.get("content"),
            structured_content=result_data.get("structuredContent"),
            is_error=result_data.get("isError", False),
        )

    def _stringify_tool_result(self, result: _CallToolResult) -> str:
        """
        将工具调用结果转换为字符串

        Args:
            result: 工具调用结果

        Returns:
            str: 字符串形式的结果
        """
        parts: list[str] = []

        for block in result.content or []:
            block_type = block.get("type", "")
            if block_type == "text":
                text = block.get("text", "")
                if text:
                    parts.append(text)
            elif block_type == "image":
                parts.append(f"[image:{block.get('mimeType', 'unknown')}]")
            elif block_type == "audio":
                parts.append(f"[audio:{block.get('mimeType', 'unknown')}]")
            elif block_type == "resource":
                parts.append(f"[resource:{block.get('uri', 'unknown')}]")
            else:
                parts.append(str(block))

        if parts:
            return "\n".join(parts)

        if result.structured_content:
            return json.dumps(result.structured_content, ensure_ascii=False)

        if result.is_error:
            return "MCP tool returned an error with no content."

        return ""
