"""
Base Tool - 工具基类

所有工具的基类，提供通用功能
"""

import os
from typing import Any

from ..core.interfaces import AgentContext, ToolDefinition


class BaseTool:
    """
    工具基类

    提供通用工具功能，包括：
    - 获取工作区根目录
    - 生成工具定义
    """

    @property
    def name(self) -> str:
        """工具名称（子类必须实现）"""
        raise NotImplementedError

    @property
    def description(self) -> str:
        """工具描述（子类必须实现）"""
        raise NotImplementedError

    @property
    def display_name(self) -> str | None:
        """工具显示名称"""
        return None

    @property
    def parameters(self) -> dict[str, Any] | None:
        """工具参数 schema"""
        return None

    def get_definition(self) -> ToolDefinition:
        """
        获取工具定义（OpenAI 格式）

        Returns:
            ToolDefinition: 工具定义
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                **({"parameters": self.parameters} if self.parameters else {}),
            },
        }

    async def execute(self, input: Any, context: AgentContext | None = None) -> str:
        """
        执行工具（子类必须实现）

        Args:
            input: 工具输入
            context: Agent 上下文

        Returns:
            str: 工具执行结果
        """
        raise NotImplementedError

    def _get_workspace_root(self, context: AgentContext | None) -> str:
        """
        获取有效的工作区根目录

        优先使用 context.workspace_root，其次使用 context.metadata.codespaceRoot，最后使用当前工作目录

        Args:
            context: Agent 上下文

        Returns:
            str: 工作区根目录路径
        """
        # 优先使用 context.workspace_root
        if context and context.workspace_root:
            return context.workspace_root
        # 其次使用 metadata.codespaceRoot（向后兼容）
        if context and context.metadata:
            candidate = context.metadata.get("codespaceRoot")
            if isinstance(candidate, str) and candidate.strip():
                return candidate
        # 最后使用当前工作目录
        return os.getcwd()

    def _resolve_path(self, workspace_root: str, user_path: str) -> str | None:
        """
        解析用户路径

        - 如果是绝对路径，直接使用
        - 如果是相对路径，相对于 workspace_root 解析

        Args:
            workspace_root: 工作区根目录
            user_path: 用户提供的路径

        Returns:
            str | None: 解析后的绝对路径，无效路径返回 None
        """
        cleaned = (user_path or "").strip()
        if not cleaned:
            return None

        workspace_abs = os.path.abspath(workspace_root)

        # 如果是绝对路径，直接使用
        if os.path.isabs(cleaned):
            return os.path.abspath(cleaned)

        # 相对路径，相对于 workspace_root 解析
        return os.path.abspath(os.path.join(workspace_abs, cleaned))
