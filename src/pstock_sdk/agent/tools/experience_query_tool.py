"""
Experience Query Tool - 经验查询工具

查询 Agent 的长期经验
"""

from typing import Any

from ..core.interfaces import AgentContext, Tool, ToolDefinition
from ...stores.experience_store import ExperienceStore


class ExperienceQueryTool(Tool):
    """
    经验查询工具

    根据 keyword 查询 Agent 的经验记录
    """

    def __init__(self, agent_name: str, experience_store: ExperienceStore):
        self._agent_name = agent_name
        self._experience_store = experience_store

    @property
    def name(self) -> str:
        return "experience_query"

    @property
    def description(self) -> str:
        return "Query this agent's long-term experiences by keyword. Omit keyword to list all experiences."

    @property
    def display_name(self) -> str:
        return "Experience Query"

    def get_definition(self) -> ToolDefinition:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keyword": {
                            "type": "string",
                            "description": "Keyword to search in experience keywords/content. If omitted, returns all experiences.",
                        },
                    },
                },
            },
        }

    async def execute(self, input: Any, context: AgentContext | None = None) -> str:
        """执行查询"""
        payload = self._parse(input)
        records = self._experience_store.list(self._agent_name, payload.get("keyword"))

        if not records:
            keyword = payload.get("keyword", "")
            return f"No experiences found for keyword: {keyword}" if keyword else "No experiences found."

        lines = []
        for idx, r in enumerate(records):
            keys = ", ".join(r.get("keywords", []))
            lines.append(f"#{idx + 1} ({r['id']})\nkeywords: {keys}\n{r['content']}")

        return "\n\n".join(lines)

    def _parse(self, input: Any) -> dict:
        """解析输入"""
        if input is None:
            return {}
        if isinstance(input, str):
            keyword = input.strip()
            return {"keyword": keyword} if keyword else {}
        if isinstance(input, dict):
            keyword = input.get("keyword")
            if isinstance(keyword, str):
                return {"keyword": keyword.strip() or None}
        return {}
