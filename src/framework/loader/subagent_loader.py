"""
AI Flex Framework - 子 Agent 加载器

负责递归加载子 Agent。
"""

from pathlib import Path
from typing import Any

from loguru import logger

from ..config.agent_config import AgentConfig, SubagentConfig
from ..exceptions import CircularReferenceError
from ..utils.path_utils import find_agent_config, find_subagent_dirs


class SubagentLoader:
    """
    子 Agent 加载器

    递归加载子 Agent，防止循环引用。
    """

    def __init__(self, main_loader: "AgentLoader"):  # type: ignore[name-defined]
        """
        初始化子 Agent 加载器

        Args:
            main_loader: 主 Agent 加载器（用于递归加载）
        """
        self.main_loader = main_loader
        self.loading_stack: list[str] = []  # 用于检测循环引用

    async def load_subagents(
        self,
        agent_config: AgentConfig,
        parent_name: str,
    ) -> list[Any]:
        """
        加载子 Agent

        Args:
            agent_config: Agent 配置
            parent_name: 父 Agent 名称

        Returns:
            子 Agent 列表

        Raises:
            CircularReferenceError: 检测到循环引用
        """
        subagents = []

        # 1. 从配置中加载
        for sub_cfg in agent_config.subagents:
            if not sub_cfg.enabled:
                continue

            subagent = await self._load_subagent_from_config(
                sub_cfg, parent_name, agent_config.get_config_dir()
            )
            if subagent:
                subagents.append(subagent)

        # 2. 自动发现 subagents/ 目录
        subagent_dirs = find_subagent_dirs(agent_config.get_config_dir())
        for subagent_dir in subagent_dirs:
            subagent_name = subagent_dir.name

            # 检查是否已在配置中加载
            if any(cfg.name == subagent_name for cfg in agent_config.subagents):
                continue

            subagent = await self._load_subagent_from_directory(
                subagent_name, parent_name, agent_config.get_config_dir()
            )
            if subagent:
                subagents.append(subagent)

        return subagents

    async def _load_subagent_from_config(
        self,
        sub_cfg: SubagentConfig,
        parent_name: str,
        config_dir: Path,
    ) -> Any | None:
        """
        从配置加载子 Agent

        Args:
            sub_cfg: 子 Agent 配置
            parent_name: 父 Agent 名称
            config_dir: 配置目录

        Returns:
            子 Agent 实例，加载失败返回 None
        """
        # 检测循环引用
        full_name = f"{parent_name}/{sub_cfg.name}"
        if full_name in self.loading_stack:
            raise CircularReferenceError(
                f"Circular reference detected: {' -> '.join(self.loading_stack + [full_name])}"
            )

        # 查找子 Agent 目录
        subagent_dir = config_dir / "subagents" / sub_cfg.name
        if not subagent_dir.exists():
            logger.warning(f"Subagent directory not found: {subagent_dir}")
            return None

        # 递归加载
        self.loading_stack.append(full_name)
        try:
            subagent = await self.main_loader.load_agent_from_directory(subagent_dir)
            return subagent
        except Exception as e:
            logger.error(f"Failed to load subagent {sub_cfg.name}: {e}")
            return None
        finally:
            self.loading_stack.pop()

    async def _load_subagent_from_directory(
        self,
        subagent_name: str,
        parent_name: str,
        config_dir: Path,
    ) -> Any | None:
        """
        从目录加载子 Agent

        Args:
            subagent_name: 子 Agent 名称
            parent_name: 父 Agent 名称
            config_dir: 配置目录

        Returns:
            子 Agent 实例，加载失败返回 None
        """
        # 检测循环引用
        full_name = f"{parent_name}/{subagent_name}"
        if full_name in self.loading_stack:
            raise CircularReferenceError(
                f"Circular reference detected: {' -> '.join(self.loading_stack + [full_name])}"
            )

        subagent_dir = config_dir / "subagents" / subagent_name

        # 递归加载
        self.loading_stack.append(full_name)
        try:
            subagent = await self.main_loader.load_agent_from_directory(subagent_dir)
            return subagent
        except Exception as e:
            logger.error(f"Failed to load subagent {subagent_name}: {e}")
            return None
        finally:
            self.loading_stack.pop()
