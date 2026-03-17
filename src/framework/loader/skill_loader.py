"""
PStock Framework - Skill 加载器

负责解析 SKILL.md 文件。
"""

import asyncio
from pathlib import Path
from typing import Any

import yaml
from loguru import logger

from ..config.skill_config import SkillMetadata
from ..exceptions import SkillParseError


class SkillLoader:
    """
    Skill 加载器

    从 SKILL.md 文件中解析元数据和内容。
    """

    async def load_skill_file(
        self, skill_md_path: Path, skill_name: str | None = None
    ) -> dict[str, Any] | None:
        """
        加载 SKILL.md 文件

        Args:
            skill_md_path: SKILL.md 文件路径
            skill_name: 技能名称（如果未在 frontmatter 中指定）

        Returns:
            Skill 字典，包含 name, description, path，解析失败返回 None
        """
        try:
            content = await asyncio.to_thread(skill_md_path.read_text, encoding="utf-8")

            # 解析 YAML frontmatter
            metadata = self._parse_frontmatter(content)
            if metadata:
                try:
                    skill_meta = SkillMetadata(**metadata)
                    name = skill_meta.name or skill_name or skill_md_path.parent.name
                    description = skill_meta.description
                except Exception as e:
                    logger.warning(
                        f"Invalid skill metadata in {skill_md_path}: {e}. Using fallback."
                    )
                    name = skill_name or skill_md_path.parent.name
                    description = metadata.get("description", "")
            else:
                name = skill_name or skill_md_path.parent.name
                description = ""

            return {
                "name": name,
                "description": description,
                "path": str(skill_md_path),
            }

        except Exception as e:
            # 非致命错误，记录警告并继续
            logger.warning(f"Failed to load SKILL.md: {skill_md_path}, error={e}")
            return None

    def _parse_frontmatter(self, content: str) -> dict[str, Any] | None:
        """
        解析 YAML frontmatter

        Args:
            content: 文件内容

        Returns:
            解析后的元数据字典，如果没有 frontmatter 则返回 None
        """
        # 检查是否以 --- 开头
        if not content.startswith("---"):
            return None

        # 找到第二个 ---
        end_idx = content.find("\n---", 3)
        if end_idx == -1:
            return None

        frontmatter_text = content[3:end_idx].strip()

        try:
            return yaml.safe_load(frontmatter_text)
        except Exception:
            return None

    async def load_skills_from_directory(
        self, skills_dir: Path
    ) -> list[dict[str, Any]]:
        """
        从目录加载所有 Skills

        Args:
            skills_dir: Skills 目录

        Returns:
            Skill 字典列表
        """
        if not skills_dir.exists() or not skills_dir.is_dir():
            return []

        skills = []
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists() and skill_md.is_file():
                skill = await self.load_skill_file(skill_md, skill_dir.name)
                if skill:
                    skills.append(skill)

        return skills

    async def load_skills_from_sources(
        self, sources: list[str], base_dir: Path
    ) -> list[dict[str, Any]]:
        """
        从多个源加载 Skills

        Args:
            sources: 技能源路径列表
            base_dir: 基础目录（用于解析相对路径）

        Returns:
            Skill 字典列表
        """
        all_skills = []

        for source in sources:
            source_path = (base_dir / source).resolve()

            if not source_path.exists():
                logger.debug(f"Skill source not found: {source_path}")
                continue

            if source_path.is_file() and source_path.name.upper() == "SKILL.md":
                skill = await self.load_skill_file(source_path, source_path.parent.name)
                if skill:
                    all_skills.append(skill)
            elif source_path.is_dir():
                # 检查直接 SKILL.md
                skill_md = source_path / "SKILL.md"
                if skill_md.exists():
                    skill = await self.load_skill_file(skill_md, source_path.name)
                    if skill:
                        all_skills.append(skill)
                else:
                    # 遍历子目录
                    skills = await self.load_skills_from_directory(source_path)
                    all_skills.extend(skills)

        return all_skills
