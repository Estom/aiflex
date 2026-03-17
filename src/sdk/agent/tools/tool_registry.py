"""
Tool Registry - 工具注册表

管理所有可用工具的注册、查询和定义生成
"""

from __future__ import annotations

from typing import Any

from ..core.interfaces import Tool, ToolDefinition


class ToolRegistry:
    """
    工具注册表

    负责管理工具的注册、注销、查询，
    并生成符合 OpenAI function calling 格式的工具定义
    """

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """
        注册工具

        Args:
            tool: 工具实例
        """
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        """
        注销工具

        Args:
            name: 工具名称
        """
        self._tools.pop(name, None)

    def get(self, name: str) -> Tool | None:
        """
        获取工具

        Args:
            name: 工具名称

        Returns:
            Tool | None: 工具实例或 None
        """
        return self._tools.get(name)

    def list(self) -> list[Tool]:
        """
        列出所有工具

        Returns:
            list[Tool]: 工具列表
        """
        return list(self._tools.values())

    def definitions(self) -> list[ToolDefinition]:
        """
        获取所有工具的定义（OpenAI 格式）

        Returns:
            list[ToolDefinition]: 工具定义列表
        """
        return [tool.get_definition() for tool in self.list()]
