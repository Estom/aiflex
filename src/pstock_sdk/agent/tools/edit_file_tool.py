"""
Edit File Tool - 文件编辑工具

精确的文本替换工具
"""

import asyncio
import hashlib
import os
from pathlib import Path
from typing import Any

from ..core.interfaces import AgentContext, ToolDefinition
from ..tools.base_tool import BaseTool
from ...utils.path_utils import gather_allowed_roots, resolve_within_allowed_roots


def _normalize_line_endings(value: str) -> str:
    """规范化行尾符"""
    return value.replace("\r\n", "\n")


def _detect_line_ending(value: str) -> str:
    """检测行尾符"""
    return "\r\n" if "\r\n" in value else "\n"


def _hash_content(content: str) -> str:
    """计算内容哈希"""
    return hashlib.sha256(content.encode()).hexdigest()


def _count_occurrences(haystack: str, needle: str) -> int:
    """计算出现次数"""
    if not needle:
        return 0
    return haystack.split(needle).__len__() - 1


class EditFileTool(BaseTool):
    """
    文件编辑工具

    精确的文本替换工具，支持多种替换策略
    """

    name = "edit_file"
    display_name = "EditFile"
    description = "Precise text replacement utility. Always inspect the latest file contents before calling, then provide the literal snippet to replace and the literal replacement."
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Location of the file to modify. Use a workspace-relative path (preferred) or an absolute path that still resides inside the workspace.",
            },
            "old_string": {
                "type": "string",
                "description": "Exact literal snippet to replace, including indentation, whitespace, and at least ~3 lines of surrounding context to uniquely identify the target. Leave empty ONLY when creating a brand-new file.",
            },
            "new_string": {
                "type": "string",
                "description": "Exact literal text that should replace old_string. Ensure it already contains the final formatting/indentation.",
            },
            "expected_replacements": {
                "type": "number",
                "description": "Optional safety rail specifying how many occurrences must be replaced. Defaults to 1.",
                "minimum": 1,
            },
        },
        "required": ["file_path", "old_string", "new_string"],
    }

    async def execute(self, input: Any, context: AgentContext | None = None) -> str:
        """执行文件编辑"""
        parsed = self._parse_input(input)
        if not parsed:
            return 'Error: `file_path`, `old_string`, and `new_string` are required.'

        workspace_root = self._get_workspace_root(context)
        allowed_roots = gather_allowed_roots(workspace_root, context)
        resolved_path = resolve_within_allowed_roots(allowed_roots, parsed["file_path"])
        if not resolved_path:
            return f"Error: file_path must be within the workspace. Received: {parsed['file_path']}"

        expected = max(1, int(parsed.get("expected_replacements", 1)))

        # 处理文件创建
        if not parsed["old_string"]:
            if os.path.exists(resolved_path):
                return f"Error: cannot create file because it already exists: {os.path.relpath(resolved_path, workspace_root)}"

            Path(resolved_path).parent.mkdir(parents=True, exist_ok=True)
            await asyncio.to_thread(Path(resolved_path).write_text, parsed["new_string"], encoding="utf-8")
            return f"OK: created file {os.path.relpath(resolved_path, workspace_root)} ({len(parsed['new_string'])} characters)"

        # 读取文件
        try:
            raw_content = await asyncio.to_thread(Path(resolved_path).read_text, encoding="utf-8")
        except FileNotFoundError:
            return f"Error: file not found. Use an empty old_string to create {os.path.relpath(resolved_path, workspace_root)}."
        except Exception as e:
            return f"Error reading file: {e!s}"

        original_line_ending = _detect_line_ending(raw_content)
        normalized_current = _normalize_line_endings(raw_content)
        normalized_search = _normalize_line_endings(parsed["old_string"])
        normalized_replace = _normalize_line_endings(parsed["new_string"])
        baseline_hash = _hash_content(normalized_current)

        # 执行替换
        occurrences = _count_occurrences(normalized_current, normalized_search)
        if occurrences == 0:
            return f"Error: failed to edit; unable to locate target snippet in {os.path.relpath(resolved_path, workspace_root)}."

        if occurrences != expected:
            return f"Error: expected {expected} occurrence(s) but found {occurrences} in {os.path.relpath(resolved_path, workspace_root)}."

        if normalized_search == normalized_replace:
            return "Error: no changes to apply; old_string and new_string are identical."

        new_content = normalized_current.replace(normalized_search, normalized_replace)

        # 确保文件未被修改
        latest = await asyncio.to_thread(Path(resolved_path).read_text, encoding="utf-8")
        latest_normalized = _normalize_line_endings(latest)
        if _hash_content(latest_normalized) != baseline_hash:
            return "Error: file changed externally before writing; please retry with the latest content."

        # 恢复原始行尾符
        if original_line_ending == "\r\n":
            new_content = new_content.replace("\n", "\r\n")

        await asyncio.to_thread(Path(resolved_path).write_text, new_content, encoding="utf-8")
        return f"OK: edited {os.path.relpath(resolved_path, workspace_root)} ({occurrences} replacement(s))"

    def _parse_input(self, input: Any) -> dict | None:
        """解析输入"""
        if not input or not isinstance(input, dict):
            return None

        file_path = input.get("file_path", "").strip() if isinstance(input.get("file_path"), str) else ""
        old_string = input.get("old_string", "") if isinstance(input.get("old_string"), str) else None
        new_string = input.get("new_string", "") if isinstance(input.get("new_string"), str) else None

        if not file_path or old_string is None or new_string is None:
            return None

        return {
            "file_path": file_path,
            "old_string": old_string,
            "new_string": new_string,
            "expected_replacements": input.get("expected_replacements") if isinstance(input.get("expected_replacements"), (int, float)) else None,
        }
