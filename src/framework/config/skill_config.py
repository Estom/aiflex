"""
AI Flex Framework - Skill 配置模型

定义 SKILL.md frontmatter 的 Pydantic 模型。
"""

from typing import Any

from pydantic import BaseModel, Field


class SkillMetadata(BaseModel):
    """
    Skill 元数据

    对应 SKILL.md 文件的 YAML frontmatter。
    """

    name: str = Field(description="Skill 名称")
    description: str = Field(default="", description="Skill 描述")
    allowed_tools: list[str] = Field(
        default_factory=list, description="允许使用的工具列表（Claude Skills 规范）"
    )
    version: str = Field(default="1.0.0", description="版本号")
    tags: list[str] = Field(default_factory=list, description="标签列表")
    author: str | None = Field(default=None, description="作者")
    examples: list[dict[str, Any]] = Field(
        default_factory=list, description="使用示例"
    )

    class Config:
        # 允许额外字段（为了兼容性）
        extra = "ignore"
