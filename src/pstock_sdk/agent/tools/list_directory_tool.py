"""
List Directory Tool - 目录列表工具

列出目录中的文件和子目录
"""

import fnmatch
import os
from pathlib import Path
from typing import Any

from ..core.interfaces import AgentContext
from ..tools.base_tool import BaseTool


class ListDirectoryTool(BaseTool):
    """
    目录列表工具

    列出指定目录中的文件和子目录
    """

    name = "list_directory"
    display_name = "ListDirectory"
    description = "List files and subdirectories in a directory, with basic metadata. Supports glob ignore patterns."
    parameters = {
        "type": "object",
        "properties": {
            "dir_path": {
                "type": "string",
                "description": "Directory path to list (relative to current working directory or absolute).",
            },
            "ignore": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional glob patterns to ignore (matched against entry name).",
            },
        },
        "required": ["dir_path"],
    }

    async def execute(self, input: Any, context: AgentContext | None = None) -> str:
        """执行目录列表"""
        params = self._parse_input(input)
        if not params.get("dir_path"):
            return 'Error: `dir_path` is required and must be a non-empty string.'

        workspace_root = self._get_workspace_root(context)
        dir_path = self._resolve_path(workspace_root, params["dir_path"])
        if not dir_path:
            return f"Error: invalid dir_path: {params['dir_path']}"

        if not os.path.isdir(dir_path):
            return f"Error: Path is not a directory: {dir_path}"

        ignore_patterns = params.get("ignore") or []
        if not isinstance(ignore_patterns, list):
            ignore_patterns = []

        entries = []
        for entry in Path(dir_path).iterdir():
            name = entry.name

            # 检查 ignore patterns
            if any(fnmatch.fnmatch(name.lower(), pat.lower()) for pat in ignore_patterns):
                continue

            try:
                stat = entry.stat()
                entries.append({
                    "name": name,
                    "path": str(entry),
                    "is_directory": entry.is_dir(),
                    "size": 0 if entry.is_dir() else stat.st_size,
                    "modified_time": stat.st_mtime,
                })
            except OSError:
                continue

        if not entries:
            return f"Directory {dir_path} is empty (or all entries were ignored)."

        # 排序：目录优先，然后按名称
        entries.sort(key=lambda x: (not x["is_directory"], x["name"].lower()))

        lines = []
        for entry in entries:
            kind = "[DIR]" if entry["is_directory"] else "[FILE]"
            mtime = entry["modified_time"]
            lines.append(f"{kind} {entry['name']} | size={entry['size']} | mtime={mtime} | path={entry['path']}")

        return f"Directory listing for {dir_path}:\n" + "\n".join(lines)

    def _parse_input(self, input: Any) -> dict:
        """解析输入"""
        if isinstance(input, str):
            return {"dir_path": input.strip()}

        if isinstance(input, dict):
            return {
                "dir_path": input.get("dir_path", "").strip() if isinstance(input.get("dir_path"), str) else "",
                "ignore": input.get("ignore") if isinstance(input.get("ignore"), list) else [],
            }

        return {"dir_path": ""}
