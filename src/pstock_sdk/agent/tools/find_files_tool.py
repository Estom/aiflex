"""
Find Files Tool - 文件查找工具

使用 glob 模式查找文件
"""

import fnmatch
import os
from pathlib import Path
from typing import Any

from ..core.interfaces import AgentContext, ToolDefinition
from ..tools.base_tool import BaseTool
from ...utils.path_utils import gather_allowed_roots, resolve_within_allowed_roots


class FindFilesTool(BaseTool):
    """
    文件查找工具

    使用 glob 模式在指定目录中查找文件
    """

    name = "find_files"
    display_name = "FindFiles"
    description = "Find files by glob pattern (e.g. **/*.ts, src/**/*.js). Supports optional directory, case sensitivity, and ignore rules."
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Glob pattern to match (e.g. **/*.ts, src/**/*.js).",
            },
            "dir_path": {
                "type": "string",
                "description": "Optional directory to search in (default: current working directory).",
            },
            "case_sensitive": {
                "type": "boolean",
                "description": "Whether the match should be case-sensitive (default: false).",
            },
        },
        "required": ["pattern"],
    }

    async def execute(self, input: Any, context: AgentContext | None = None) -> str:
        """执行文件查找"""
        params = self._parse_input(input)
        if not params.get("pattern"):
            return 'Error: `pattern` is required and must be a non-empty string.'

        workspace_root = self._get_workspace_root(context)
        allowed_roots = gather_allowed_roots(workspace_root, context)

        dir_path = params.get("dir_path", ".")
        search_dir = resolve_within_allowed_roots(allowed_roots, dir_path)
        if not search_dir:
            return f"Error: dir_path must be within allowed roots. Received: {dir_path}"

        if not os.path.isdir(search_dir):
            return f"Error: dir_path is not a directory: {search_dir}"

        # 执行文件查找
        pattern = params["pattern"]
        case_sensitive = params.get("case_sensitive", False)

        matches = []
        search_path = Path(search_dir)

        # 使用 glob 查找
        from glob import glob

        abs_pattern = str(search_path / pattern)
        glob_files = glob(abs_pattern, recursive=True)

        for file_path in glob_files:
            if os.path.isfile(file_path):
                matches.append(file_path)

        if not matches:
            return f'No files found matching pattern "{pattern}" in {search_dir}.'

        # 按修改时间排序
        with_stats = []
        for p in matches:
            try:
                stat = os.stat(p)
                with_stats.append({"path": p, "mtime": stat.st_mtime})
            except OSError:
                with_stats.append({"path": p, "mtime": 0})

        with_stats.sort(key=lambda x: (-x["mtime"], x["path"]))

        lines = [item["path"] for item in with_stats]
        return f'Found {len(lines)} file(s) matching "{pattern}" in {search_dir}, sorted by modification time (newest first):\n' + "\n".join(lines)

    def _parse_input(self, input: Any) -> dict:
        """解析输入"""
        if isinstance(input, str):
            return {"pattern": input.strip()}

        if isinstance(input, dict):
            return {
                "pattern": input.get("pattern", "").strip() if isinstance(input.get("pattern"), str) else "",
                "dir_path": input.get("dir_path") if isinstance(input.get("dir_path"), str) else None,
                "case_sensitive": input.get("case_sensitive") if isinstance(input.get("case_sensitive"), bool) else None,
            }

        return {"pattern": ""}
