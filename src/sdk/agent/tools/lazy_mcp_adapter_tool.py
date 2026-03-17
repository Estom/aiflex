"""
Lazy MCP Adapter Tool - MCP 懒加载适配器工具

实现 MCP 服务器的懒加载，按需加载工具
"""

import asyncio
from typing import Any, ClassVar

from sdk.agent.core.interfaces import AgentContext
from sdk.agent.mcp.mcp_config import McpServerConfig
from sdk.agent.tools.base_tool import BaseTool
from sdk.utils.logger import logger

from .mcp_adapter_tool import McpToolFactory


class LazyMcpAdapterTool(BaseTool):
    """
    MCP 懒加载适配器工具

    在首次调用时加载 MCP 服务器的工具列表
    """

    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }

    def __init__(
        self,
        agent_name: str,
        mcp_name: str,
        mcp_server_config: McpServerConfig,
    ):
        self._agent_name = agent_name
        self._cfg = mcp_server_config
        self._registry: Any = None  # ToolRegistry

        self._loaded = False
        self._inflight: asyncio.Task[str] | None = None

        self._name = f"lazy_mcp_{mcp_server_config.name}"
        self._display_name = f"MCP: Lazy Loader ({mcp_server_config.name})"
        self._description = (
            f'Loads MCP tools from server "{mcp_server_config.name}" on demand. '
            f"Call this once before using tools from that MCP server; "
            f'this mcp is for "{mcp_server_config.description or ""}"; '
            "it will query the server's tool list and register those tools into the runtime."
        )

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

    def set_registry(self, registry: Any) -> None:
        """设置工具注册表"""
        self._registry = registry

    async def execute(self, input: Any, context: AgentContext | None = None) -> str:
        """执行工具（加载 MCP 工具）"""
        if self._loaded:
            return "MCP tools are already loaded for this agent."

        if self._inflight:
            return await self._inflight

        self._inflight = asyncio.create_task(self._load())
        return await self._inflight

    async def _load(self) -> str:
        """加载 MCP 工具"""
        if not self._registry:
            return f"Lazy MCP tool registry is not initialized for {self._cfg.name}."

        try:
            # 创建 MCP 工具工厂
            factory = McpToolFactory(self._cfg.name, self._cfg)

            # 获取所有 MCP 工具
            mcp_tools = await factory.create_tools()

            if not mcp_tools:
                return f"No tools found on MCP server {self._cfg.name}."

            # 注册工具到 registry
            for tool in mcp_tools:
                self._registry.register(tool)

            # 注销自己
            self._registry.unregister(self.name)

            self._loaded = True

            logger.info(f"Successfully loaded {len(mcp_tools)} tools from MCP server {self._cfg.name}")
            return f"Successfully loaded {len(mcp_tools)} MCP tools from {self._cfg.name}."

        except Exception as e:
            logger.error(f"Failed to load MCP tools from {self._cfg.name}: {e}")
            return f"Failed to load MCP tools from {self._cfg.name}: {e!s}"

