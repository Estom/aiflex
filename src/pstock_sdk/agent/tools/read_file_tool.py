"""
Read File Tool - 文件读取工具

读取文本文件内容
"""

import os
from pathlib import Path
from typing import Any

from ..core.interfaces import AgentContext, ToolDefinition
from ..tools.base_tool import BaseTool
from ...utils.path_utils import gather_allowed_roots, resolve_within_allowed_roots


DEFAULT_LIMIT = 200
MAX_LIMIT = 2000


class ReadFileTool(BaseTool):
    """
    文件读取工具

    读取文本文件内容，支持分页
    """

    name = "read_file"
    display_name = "ReadFile"
    description = "Reads a text file from the workspace. Supports pagination with 'offset' (0-based line) and 'limit' (max lines). Returns a clear truncation message when not all lines are shown."
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to read (relative to workspace root or absolute within workspace).",
            },
            "offset": {
                "type": "number",
                "description": "Optional: 0-based line offset for text files. Use with 'limit' to paginate.",
                "minimum": 0,
            },
            "limit": {
                "type": "number",
                "description": f"Optional: max number of lines to read (default {DEFAULT_LIMIT}, max {MAX_LIMIT}). Use with 'offset' to paginate.",
                "minimum": 1,
            },
        },
        "required": ["file_path"],
    }

    async def execute(self, input: Any, context: AgentContext | None = None) -> str:
        """执行文件读取"""
        parsed = self._parse_input(input)
        if not parsed or not parsed.get("file_path"):
            return 'Error: `file_path` is required.'

        workspace_root = self._get_workspace_root(context)
        allowed_roots = gather_allowed_roots(workspace_root, context)
        resolved_path = resolve_within_allowed_roots(allowed_roots, parsed["file_path"])
        if not resolved_path:
            return f"Error: file_path must be within allowed roots. Received: {parsed['file_path']}"

        if not os.path.isfile(resolved_path):
            return f"Error: path is not a file: {os.path.relpath(resolved_path, workspace_root)}"

        offset = max(0, int(parsed.get("offset", 0)))
        limit = min(MAX_LIMIT, max(1, int(parsed.get("limit", DEFAULT_LIMIT))))

        try:
            content = await asyncio.to_thread(Path(resolved_path).read_text, encoding="utf-8")
            lines = content.split("\n")
            total = len(lines)

            start_index = min(offset, total)
            end_index = min(start_index + limit, total)
            shown = lines[start_index:end_index]

            is_truncated = end_index < total
            start_line_1 = start_index + 1
            end_line_1 = end_index

            if is_truncated:
                header = "\n".join([
                    "IMPORTANT: The file content has been truncated.",
                    f"Status: Showing lines {start_line_1}-{end_line_1} of {total} total lines.",
                    f"Action: To read more, call read_file with offset={end_index} and limit={limit}.",
                    "--- FILE CONTENT (truncated) ---",
                ])
            else:
                header = f"Status: Showing lines {start_line_1}-{end_line_1} of {total} total lines.\n--- FILE CONTENT ---"

            return f"{header}\n" + "\n".join(shown)
        except Exception as e:
            return f"Error reading file: {e!s}"

    def _parse_input(self, input: Any) -> dict | None:
        """解析输入"""
        if isinstance(input, str):
            file_path = input.strip()
            return {"file_path": file_path} if file_path else None

        if isinstance(input, dict):
            file_path = input.get("file_path", "").strip() if isinstance(input.get("file_path"), str) else ""
            if not file_path:
                return None

            return {
                "file_path": file_path,
                "offset": input.get("offset") if isinstance(input.get("offset"), (int, float)) else None,
                "limit": input.get("limit") if isinstance(input.get("limit"), (int, float)) else None,
            }

        return None


import asyncio
