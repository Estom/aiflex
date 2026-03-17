"""
Skill Registry - 技能注册表

管理 Agent 可用的技能列表
"""

from ..core.interfaces import Skill


class SkillRegistry:
    """
    技能注册表

    管理技能的注册、注销和查询
    """

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        """
        注册技能

        Args:
            skill: 技能字典
        """
        self._skills[skill["name"]] = skill

    def unregister(self, name: str) -> None:
        """
        注销技能

        Args:
            name: 技能名称
        """
        self._skills.pop(name, None)

    def get(self, name: str) -> Skill | None:
        """
        获取技能

        Args:
            name: 技能名称

        Returns:
            Skill | None: 技能字典或 None
        """
        return self._skills.get(name)

    def list(self) -> list[Skill]:
        """
        列出所有技能

        Returns:
            list[Skill]: 技能列表
        """
        return list(self._skills.values())
