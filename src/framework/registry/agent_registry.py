"""
AI Flex Framework - Agent 注册表

中央 Agent 注册表，用于存储和查找已加载的 Agent。
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sdk.agent.core.agent import Agent


class AgentFrameworkRegistry:
    """
    Agent 框架注册表

    存储已加载的 Agent 实例和配置，提供名称查找功能。
    """

    def __init__(self):
        """初始化注册表"""
        self._agents: dict[str, Agent] = {}
        self._configs: dict[str, Any] = {}

    def register(self, name: str, agent: "Agent", config: Any | None = None) -> None:
        """
        注册 Agent

        Args:
            name: Agent 名称
            agent: Agent 实例
            config: Agent 配置（可选）
        """
        self._agents[name] = agent
        if config:
            self._configs[name] = config

    def get(self, name: str) -> "Agent | None":
        """
        获取 Agent

        Args:
            name: Agent 名称

        Returns:
            Agent 实例，如果不存在则返回 None
        """
        return self._agents.get(name)

    def get_config(self, name: str) -> Any | None:
        """
        获取 Agent 配置

        Args:
            name: Agent 名称

        Returns:
            Agent 配置，如果不存在则返回 None
        """
        return self._configs.get(name)

    def list_agents(self) -> list[str]:
        """
        列出所有 Agent 名称

        Returns:
            Agent 名称列表
        """
        return list(self._agents.keys())

    def has_agent(self, name: str) -> bool:
        """
        检查 Agent 是否存在

        Args:
            name: Agent 名称

        Returns:
            是否存在
        """
        return name in self._agents

    def clear(self) -> None:
        """清空注册表"""
        self._agents.clear()
        self._configs.clear()
