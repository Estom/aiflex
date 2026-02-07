"""
PStock Framework - 自定义异常

定义框架中使用的异常层次。
"""

from typing import Any


class FrameworkError(Exception):
    """框架基础异常"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class AgentConfigError(FrameworkError):
    """Agent 配置错误"""

    pass


class PromptNotFoundError(FrameworkError):
    """Prompt 文件未找到错误"""

    pass


class CircularReferenceError(FrameworkError):
    """循环引用错误"""

    pass


class ToolImportError(FrameworkError):
    """工具导入错误（非致命）"""

    pass


class SkillParseError(FrameworkError):
    """Skill 解析错误（非致命）"""

    pass
