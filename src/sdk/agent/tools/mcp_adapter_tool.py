"""
MCP Adapter Tool - MCP 适配器工具

将 MCP 服务器提供的工具包装为 Agent 可用的工具
"""

from typing import Any

from sdk.agent.core.interfaces import AgentContext
from sdk.agent.mcp.mcp_client import McpClient, McpToolDefinition
from sdk.agent.mcp.mcp_config import McpServerConfig
from sdk.agent.tools.base_tool import BaseTool
from sdk.utils.logger import logger


class McpAdapterTool(BaseTool):
    """
    MCP 适配器工具

    将 MCP 服务器的单个工具包装为 Agent 工具
    """

    def __init__(
        self,
        server_name: str,
        tool: McpToolDefinition,
        client: McpClient,
    ) -> None:
        """
        初始化 MCP 适配器工具

        Args:
            server_name: MCP 服务器名称
            tool: MCP 工具定义
            client: MCP 客户端
        """
        self._server_name = server_name
        self._tool = tool
        self._client = client

        self._name = f"mcp_{server_name}_{tool.name}"
        self._display_name = tool.display_name or f"MCP {server_name}: {tool.name}"
        self._description = tool.description or f"MCP tool {tool.name} from {server_name}"
        self._parameters = self._build_parameters(tool.parameters)

    @property
    def name(self) -> str:
        """工具名称"""
        return self._name

    @property
    def display_name(self) -> str:
        """工具显示名称"""
        return self._display_name

    @property
    def description(self) -> str:
        """工具描述"""
        return self._description

    @property
    def parameters(self) -> dict[str, Any] | None:
        """工具参数 schema"""
        return self._parameters

    async def execute(self, input: Any, context: AgentContext | None = None) -> str:
        """
        执行工具

        Args:
            input: 工具输入
            context: Agent 上下文（当前未使用）

        Returns:
            str: 工具执行结果
        """
        _ = context  # Reserved for future use
        try:
            result = await self._client.call_tool(self._tool.name, input)
        except Exception as e:
            logger.error(f"Error calling MCP tool {self._tool.name}: {e}")
            return f"Error calling MCP tool {self._tool.name}: {e!s}"
        return result

    def _build_parameters(self, tool_params: dict[str, Any] | None) -> dict[str, Any] | None:
        """
        构建工具参数 schema

        Args:
            tool_params: MCP 工具参数定义

        Returns:
            OpenAI 格式的参数 schema
        """
        if not tool_params:
            return None

        return {
            "type": "object",
            "properties": tool_params,
            "additionalProperties": False,
        }


class McpToolFactory:
    """
    MCP 工具工厂

    从 MCP 服务器创建所有工具
    """

    def __init__(self, server_name: str, config: McpServerConfig) -> None:
        """
        初始化 MCP 工具工厂

        Args:
            server_name: MCP 服务器名称
            config: MCP 服务器配置
        """
        self._server_name = server_name
        self._config = config
        self._client = McpClient(config)

    async def create_tools(self) -> list[McpAdapterTool]:
        """
        创建所有 MCP 工具

        Returns:
            MCP 适配器工具列表
        """
        try:
            tool_definitions = await self._client.list_tools()
            return [
                McpAdapterTool(self._server_name, tool_def, self._client)
                for tool_def in tool_definitions
            ]
        except Exception as e:
            logger.error(f"Failed to list tools from MCP server {self._server_name}: {e}")
            return []

