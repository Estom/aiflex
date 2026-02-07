"""
Write File Tool - 文件写入工具

将文本内容写入文件
"""

import os
from pathlib import Path
from typing import Any

from ..core.interfaces import AgentContext, ToolDefinition
from ..tools.base_tool import BaseTool
from ...utils.path_utils import gather_allowed_roots, resolve_within_allowed_roots


class WriteFileTool(BaseTool):
    """
    文件写入工具

    将文本内容写入文件，创建父目录（如需要）
    """

    name = "write_file"
    display_name = "WriteFile"
    description = "Writes text content to a file within the workspace. Creates parent directories if needed."
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to write (relative to workspace root or absolute within workspace).",
            },
            "content": {
                "type": "string",
                "description": "The text content to write to the file.",
            },
        },
        "required": ["file_path", "content"],
    }

    async def execute(self, input: Any, context: AgentContext | None = None) -> str:
        """执行文件写入"""
        parsed = self._parse_input(input)
        if not parsed or not parsed.get("file_path") or parsed.get("content") is None:
            return 'Error: `file_path` and `content` are required.'

        workspace_root = self._get_workspace_root(context)
        allowed_roots = gather_allowed_roots(workspace_root, context)
        resolved_path = resolve_within_allowed_roots(allowed_roots, parsed["file_path"])
        if not resolved_path:
            return f"Error: file_path must be within the workspace. Received: {parsed['file_path']}"

        # 检查是否是目录
        if os.path.isdir(resolved_path):
            return f"Error: path is a directory, not a file: {os.path.relpath(resolved_path, workspace_root)}"

        try:
            # 创建父目录
            Path(resolved_path).parent.mkdir(parents=True, exist_ok=True)

            # 写入文件
            await asyncio.to_thread(Path(resolved_path).write_text, parsed["content"], encoding="utf-8")

            rel_path = os.path.relpath(resolved_path, workspace_root) or os.path.basename(resolved_path)
            return f"OK: wrote {len(parsed['content'])} characters to {rel_path}"
        except Exception as e:
            return f"Error writing file: {e!s}"

    def _parse_input(self, input: Any) -> dict | None:
        """解析输入"""
        if not input or not isinstance(input, dict):
            return None

        file_path = input.get("file_path", "").strip() if isinstance(input.get("file_path"), str) else ""
        content = input.get("content", "") if isinstance(input.get("content"), str) else None

        if not file_path:
            return None

        return {"file_path": file_path, "content": content}


import asyncio
