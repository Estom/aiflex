"""
Agent Adapter Tool - 子 Agent 适配器工具

将子 Agent 包装为工具，实现多 Agent 协作
"""

from typing import Any, Callable

from ..core.interfaces import AgentContext, AgentRunResult, Tool, ToolDefinition
from ..tools.base_tool import BaseTool


type ChildAgentExecutor = Callable[[str, AgentContext | None], AgentRunResult]  # AgentRunResult


class AgentDescriptor:
    """Agent 描述符"""
    def __init__(self, name: str, description: str | None = None):
        self.name = name
        self.description = description


class AgentAdapterTool(BaseTool):
    """
    Agent 适配器工具

    将子 Agent 包装为工具，使父 Agent 可以调用子 Agent
    """

    parameters = {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "Task or question to delegate to the child agent.",
            },
        },
        "required": ["task"],
    }

    def __init__(
        self,
        agent_descriptor: AgentDescriptor,
        run_child_agent: ChildAgentExecutor,
    ):
        self._agent = agent_descriptor
        self._run_child_agent = run_child_agent
        self._name = f"agent_{agent_descriptor.name}"
        self._display_name = f"Agent: {agent_descriptor.name}"
        self._description = (
            agent_descriptor.description
            or f"Delegate task to child agent {agent_descriptor.name}."
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def description(self) -> str:
        return self._description

    async def execute(self, input: Any, context: AgentContext | None = None) -> str:
        """执行工具"""
        task = self._extract_task(input)
        if not task:
            return 'Error: missing required argument "task".'

        try:
            result = await self._run_child_agent(task, context)
            return result.output
        except Exception as e:
            return f"Child agent {self._agent.name} failed: {e!s}"

    def _extract_task(self, input: Any) -> str | None:
        """提取任务"""
        if isinstance(input, str):
            return input.strip()
        if isinstance(input, dict) and "task" in input:
            value = input["task"]
            if isinstance(value, str):
                return value.strip()
        return None
