"""
Experience Update Tool - 经验更新工具

创建或更新 Agent 的经验记录
"""

from typing import Any

from ..core.interfaces import AgentContext, Tool, ToolDefinition
from ...stores.experience_store import ExperienceStore


class ExperienceUpdateTool(Tool):
    """
    经验更新工具

    创建或更新 Agent 的经验记录
    """

    def __init__(self, agent_name: str, experience_store: ExperienceStore):
        self._agent_name = agent_name
        self._experience_store = experience_store

    @property
    def name(self) -> str:
        return "experience_update"

    @property
    def description(self) -> str:
        return "Create or update a reusable experience for this agent. Use for lessons that improve future execution. Provide keywords and a concise experience content."

    @property
    def display_name(self) -> str:
        return "Experience Updater"

    def get_definition(self) -> ToolDefinition:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": "Optional experience id to update. If omitted, a new experience will be created.",
                        },
                        "keywords": {
                            "description": "Keywords for retrieval. Provide an array of strings (preferred) or a comma-separated string.",
                            "anyOf": [
                                {"type": "array", "items": {"type": "string"}},
                                {"type": "string"},
                            ],
                        },
                        "content": {
                            "type": "string",
                            "description": "The experience content. Should be durable and reusable, not tied to a single task.",
                        },
                    },
                    "required": ["keywords", "content"],
                },
            },
        }

    async def execute(self, input: Any, context: AgentContext | None = None) -> str:
        """执行更新"""
        payload = self._parse(input)
        record = self._experience_store.upsert(self._agent_name, payload)
        return f"Experience saved. id={record['id']}"

    def _parse(self, input: Any) -> dict:
        """解析输入"""
        if not input or not isinstance(input, dict):
            raise ValueError("Input must be an object with keywords/content fields.")

        payload = dict(input)  # type: ignore
        return {
            "id": payload.get("id") if isinstance(payload.get("id"), str) else None,
            "keywords": payload.get("keywords"),
            "content": payload.get("content"),
        }
