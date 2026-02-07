"""
PStock Framework - Tool 加载器

负责自动发现和加载工具模块。
"""

import asyncio
import importlib.util
import inspect
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import validate_call

from ..exceptions import ToolImportError
from ..utils.path_utils import find_tool_files


class ToolLoader:
    """
    Tool 加载器

    从 tools/*.py 文件中自动发现并加载工具。
    """

    def __init__(self, base_dir: Path):
        """
        初始化 Tool 加载器

        Args:
            base_dir: Agent 目录
        """
        self.base_dir = base_dir
        self.tools_dir = base_dir / "tools"

    async def load_tools(
        self,
        auto_discover: bool = True,
        enabled: list[str] | None = None,
        disabled: list[str] | None = None,
    ) -> list[Any]:
        """
        加载工具

        Args:
            auto_discover: 是否自动发现 tools/*.py
            enabled: 启用的工具名称列表（白名单）
            disabled: 禁用的工具名称列表（黑名单）

        Returns:
            工具实例列表
        """
        enabled = enabled or []
        disabled = disabled or []

        if not auto_discover:
            return []

        if not self.tools_dir.exists() or not self.tools_dir.is_dir():
            return []

        tool_files = find_tool_files(self.base_dir)
        tools = []

        for tool_file in tool_files:
            try:
                tool = await self._load_tool_file(tool_file)

                if not tool:
                    continue

                # 检查白名单
                if enabled and tool.name not in enabled:
                    logger.debug(f"Tool {tool.name} not in enabled list, skipping")
                    continue

                # 检查黑名单
                if disabled and tool.name in disabled:
                    logger.debug(f"Tool {tool.name} in disabled list, skipping")
                    continue

                tools.append(tool)

            except Exception as e:
                # 非致命错误，记录警告并继续
                logger.warning(
                    f"Failed to load tool file: {tool_file}, error={e}",
                )

        return tools

    async def _load_tool_file(self, tool_file: Path) -> Any | None:
        """
        加载单个工具文件

        Args:
            tool_file: 工具文件路径

        Returns:
            工具实例，如果加载失败则返回 None
        """
        try:
            # 动态导入模块
            spec = importlib.util.spec_from_file_location(
                tool_file.stem, tool_file
            )
            if spec is None or spec.loader is None:
                raise ToolImportError(
                    f"Failed to load module spec: {tool_file}",
                    details={"file": str(tool_file)},
                )

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 查找工具类或函数
            tool = self._find_tool_in_module(module, tool_file.stem)
            if tool:
                logger.info(f"Loaded tool: {tool.name} from {tool_file}")
                return tool

            return None

        except Exception as e:
            raise ToolImportError(
                f"Failed to import tool module: {e}",
                details={"file": str(tool_file), "error": str(e)},
            )

    def _find_tool_in_module(self, module: Any, module_name: str) -> Any | None:
        """
        在模块中查找工具

        工具可以是：
        1. 实现 Tool Protocol 的类的实例
        2. 使用 @validate_call 装饰器的函数
        3. 名称为 "create_tool" 或 "get_tool" 的函数

        Args:
            module: Python 模块
            module_name: 模块名称

        Returns:
            工具实例，如果未找到则返回 None
        """
        # 1. 检查是否有 create_tool 或 get_tool 函数
        for func_name in ["create_tool", "get_tool"]:
            if hasattr(module, func_name):
                func = getattr(module, func_name)
                if callable(func):
                    try:
                        tool = func()
                        if tool and self._is_tool(tool):
                            return tool
                    except Exception as e:
                        logger.warning(
                            f"Failed to call {func_name} in {module_name}: {e}"
                        )

        # 2. 查找实现 Tool Protocol 的类实例
        for attr_name in dir(module):
            if attr_name.startswith("_"):
                continue

            attr = getattr(module, attr_name)
            if self._is_tool(attr):
                return attr

        # 3. 查找使用 @validate_call 的函数
        for attr_name in dir(module):
            if attr_name.startswith("_"):
                continue

            attr = getattr(module, attr_name)
            if callable(attr) and self._has_validate_call(attr):
                # 将函数包装为工具
                return self._wrap_function_as_tool(attr, module_name)

        return None

    def _is_tool(self, obj: Any) -> bool:
        """
        检查对象是否是工具

        Args:
            obj: 待检查对象

        Returns:
            是否为工具
        """
        # 检查是否有必需的属性
        required_attrs = ["name", "description", "get_definition", "execute"]
        return all(hasattr(obj, attr) for attr in required_attrs)

    def _has_validate_call(self, func: Any) -> bool:
        """
        检查函数是否使用 @validate_call 装饰器

        Args:
            func: 待检查函数

        Returns:
            是否使用 @validate_call
        """
        return hasattr(func, "__pydantic_validator__")

    def _wrap_function_as_tool(self, func: Any, module_name: str) -> Any:
        """
        将函数包装为工具

        Args:
            func: 函数对象
            module_name: 模块名称

        Returns:
            工具实例
        """
        from pstock_sdk.agent.tools.base_tool import BaseTool

        func_name = func.__name__
        func_doc = inspect.getdoc(func) or f"Tool generated from function {func_name}"

        # 创建动态工具类
        class DynamicTool(BaseTool):
            name: str = func_name
            description: str = func_doc

            async def execute(self, input: Any, context: Any = None) -> str:
                if asyncio.iscoroutinefunction(func):
                    return await func(**input)
                else:
                    return func(**input)

        return DynamicTool()
