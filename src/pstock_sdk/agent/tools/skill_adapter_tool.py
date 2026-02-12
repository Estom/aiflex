"""
Skill Adapter Tool - Skill 适配器工具

将 Skill 包装为工具，使 Agent 可以通过工具调用动态加载 Skill
"""

from typing import Any

from ..core.interfaces import Tool, ToolDefinition
from ..skills.skill_registry import SkillRegistry
from .base_tool import BaseTool


class SkillAdapterTool(BaseTool):
    """
    Skill 适配器工具

    将 Skill 包装为工具，使 Agent 可以按名称调用 Skill
    """

    def __init__(self, skill_registry: SkillRegistry):
        self._skill_registry = skill_registry
        self._name = "get_skill"
        self._display_name = "Get Skill"
        self._description = self._build_description()
        self._parameters = {
            "type": "object",
            "properties": {
                "skill_name": {"type": "string", "description": "Name of the skill to execute"},
                "args": {
                    "type": "string",
                    "description": "Optional arguments to pass to the skill",
                },
            },
            "required": ["skill_name"],
        }

    @property
    def name(self) -> str:
        return self._name

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameters(self) -> dict[str, Any] | None:
        return self._parameters

    def _build_description(self) -> str:
        """
        构建工具描述，包含所有可用的 Skill 列表

        Returns:
            str: 工具描述
        """
        skills = self._skill_registry.list()
        skills_list = "\n".join(f"- {skill['name']}: {skill['description']}" for skill in skills)

        description = f"""Execute a skill within the main conversation.

When users ask you to perform tasks, check if any of the available skills below can help complete the task more effectively. Skills provide specialized capabilities and domain knowledge.

When users ask you to run a "slash command" or reference "/<something>" (e.g., "/commit", "/review-pr"), they are referring to a skill. Use this tool to invoke the corresponding skill.

Examples:
- User: "run /commit" → Assistant: [Calls Skill tool with skill: "commit"]
- User: "帮我分析这个 PDF" → Assistant: [Calls Skill tool with skill: "pdf"]

How to invoke:
- Use this tool with the skill name and optional arguments
- Examples:
  - `skill: "pdf"` - invoke pdf skill
  - `skill: "commit", args: "-m 'Fix bug'"` - invoke with arguments
  - `skill: "review-pr", args: "123"` - invoke with arguments

Important:
- When a skill is relevant, you must invoke this tool IMMEDIATELY as your first action
- NEVER just announce or mention a skill in your text response without actually calling this tool
- This is a BLOCKING REQUIREMENT: invoke relevant Skill tool BEFORE generating any other response about the task
- Only use skills listed in "Available skills" below
- Do not invoke a skill that is already running

Available skills:
{skills_list}
"""
        return description

    def get_definition(self) -> ToolDefinition:
        """
        获取工具定义（OpenAI 格式）

        每次调用时重新生成描述，以获取最新的 Skill 列表

        Returns:
            ToolDefinition: 工具定义
        """
        # 重新构建描述以获取最新的 Skill 列表
        self._description = self._build_description()

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                **({"parameters": self.parameters} if self.parameters else {}),
            },
        }

    async def execute(
        self, input: Any, _context: Any  # type: ignore
    ) -> str:
        """
        执行工具

        Args:
            input: 工具输入
            _context: 上下文（保留以符合 Tool 接口，未使用）

        Returns:
            str: Skill 文件内容
        """
        skill_name = self._extract_skill_name(input)
        if not skill_name:
            return 'Error: missing required argument "skill_name".'

        # 从 SkillRegistry 获取 Skill
        skill = self._skill_registry.get(skill_name)
        if not skill:
            available = [s["name"] for s in self._skill_registry.list()]
            return (
                f"Error: skill '{skill_name}' not found. Available skills: {', '.join(available)}"
            )

        # 读取 Skill 文件内容
        skill_path = skill.get("path")
        if not skill_path:
            return f"Error: skill '{skill_name}' has no path information."

        try:
            import asyncio
            from pathlib import Path

            content = await asyncio.to_thread(Path(skill_path).read_text, encoding="utf-8")

            # 返回 Skill 内容，格式类似 Claude Code
            # 添加 SKILL.md 文件位置，方便模型后续引用
            skill_dir = str(Path(skill_path).parent)
            return f"""Launching skill: {skill_name}

Skill file location: {skill_path}
Skill directory: {skill_dir}

{content}"""

        except Exception as e:
            return f"Error reading skill file '{skill_path}': {e!s}"

    def _extract_skill_name(self, input: Any) -> str | None:
        """
        提取 Skill 名称

        Args:
            input: 工具输入

        Returns:
            str | None: Skill 名称
        """
        if isinstance(input, str):
            # 解析类似 skill: "name" 或直接 "name" 的格式
            input = input.strip()
            if input.startswith('"') and input.endswith('"'):
                input = input[1:-1]
            return input.strip() or None
        if isinstance(input, dict) and "skill_name" in input:
            value = input["skill_name"]
            if isinstance(value, str):
                return value.strip()
        return None
