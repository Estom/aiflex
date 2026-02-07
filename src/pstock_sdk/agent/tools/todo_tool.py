"""
Todo Tool - Todo 列表管理工具

管理复杂任务的待办事项列表
"""

import json
from enum import StrEnum
from typing import Any, ClassVar

from pstock_sdk.agent.core.interfaces import AgentContext
from pstock_sdk.agent.tools.base_tool import BaseTool


class TodoStatus(StrEnum):
    """Todo 状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TodoItem(dict):
    """Todo 项"""

    def __init__(
        self,
        description: str,
        status: TodoStatus,
        **kwargs: Any,
    ):
        super().__init__(
            description=description,
            status=status,
            **kwargs,
        )

    @property
    def description(self) -> str:
        return self["description"]

    @property
    def status(self) -> TodoStatus:
        return TodoStatus(self["status"])


class TodoPayload(dict):
    """Todo 载荷"""

    def __init__(
        self,
        todos: list[TodoItem] | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            todos=todos or [],
            **kwargs,
        )

    @property
    def todos(self) -> list[TodoItem]:
        return self.get("todos", [])


class TodoTool(BaseTool):
    """
    Todo 工具

    管理复杂任务的待办事项列表
    """

    DESCRIPTION = (
        "This tool manages a todo list for complex tasks. "
        "Provide the complete list of todos with their statuses; it will replace the existing list. "
        "Only one item can be in_progress at a time."
    )

    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "todos": {
                "type": "array",
                "description": "Complete todo list; this overwrites the previous list.",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string", "description": "Task description"},
                        "status": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "completed", "cancelled"],
                            "description": "Status of the task",
                        },
                    },
                    "required": ["description", "status"],
                },
            },
        },
        "required": ["todos"],
    }

    def __init__(self) -> None:
        self._name = "write_todos_list"
        self._display_name = "Todo List"
        self._description = self.DESCRIPTION

    @property
    def name(self) -> str:
        """工具名称"""
        return self._name

    @property
    def display_name(self) -> str:
        """工具显示名称"""
        return self._display_name

    @property
    def description(self) -> str:
        """工具描述"""
        return self._description

    async def execute(self, input: Any, context: AgentContext | None = None) -> str:
        """
        执行工具

        Args:
            input: 工具输入
            context: Agent 上下文（未使用）

        Returns:
            str: 工具执行结果
        """
        _ = context  # Reserved for future use
        todos = self._normalize_todos(input)
        if todos is None:
            return "Error: invalid payload. Expected { todos: Todo[] }."

        validation_error = self._validate_todos(todos)
        if validation_error:
            return f"Error: {validation_error}"

        if len(todos) == 0:
            return "Successfully cleared the todo list."

        body = "\n".join(
            f"{index + 1}. [{todo.status}] {todo.description}"
            for index, todo in enumerate(todos)
        )

        return f"Successfully updated the todo list. Current list:\n{body}"

    def _normalize_todos(self, input: Any) -> list[TodoItem] | None:
        """
        规范化 todo 输入

        Args:
            input: 原始输入

        Returns:
            规范化后的 todo 列表，如果无效则返回 None
        """
        if not input:
            return None

        # If the model sends a stringified JSON, try parsing it
        if isinstance(input, str):
            try:
                parsed = json.loads(input)
                if isinstance(parsed, dict) and "todos" in parsed:
                    todos = parsed["todos"]
                    if isinstance(todos, list):
                        return [TodoItem(**item) for item in todos]
            except (json.JSONDecodeError, TypeError, KeyError):
                return None

        # If the model sends an object with todos field
        if isinstance(input, dict) and "todos" in input:
            todos = input["todos"]
            if isinstance(todos, list):
                try:
                    return [TodoItem(**item) for item in todos]
                except (TypeError, KeyError):
                    return None

        return None

    def _validate_todos(self, todos: list[TodoItem]) -> str | None:
        """
        验证 todo 列表

        Args:
            todos: Todo 列表

        Returns:
            错误信息，如果验证通过则返回 None
        """
        allowed = {TodoStatus.PENDING, TodoStatus.IN_PROGRESS, TodoStatus.COMPLETED, TodoStatus.CANCELLED}

        for todo in todos:
            if not todo or not isinstance(todo, dict):
                return "Each todo must be an object."

            description = todo.get("description")
            if not isinstance(description, str) or not description.strip():
                return "Each todo must have a non-empty description."

            status = todo.get("status")
            if status not in allowed:
                return "Todo status must be one of pending, in_progress, completed, or cancelled."

        in_progress_count = sum(1 for t in todos if t.get("status") == TodoStatus.IN_PROGRESS)
        if in_progress_count > 1:
            return "Only one todo can be in_progress at a time."

        return None
