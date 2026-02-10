"""
Search Text Tool - 文本搜索工具

在文件内容中搜索正则表达式模式
"""

import asyncio
import re
from pathlib import Path
from typing import Any

from ..core.interfaces import AgentContext
from ..tools.base_tool import BaseTool


DEFAULT_MAX_MATCHES = 200
MAX_FILE_BYTES = 1024 * 1024  # 1MB


class SearchTextTool(BaseTool):
    """
    文本搜索工具

    在文件内容中搜索正则表达式模式
    """

    name = "search_text"
    display_name = "SearchText"
    description = "Searches for a regular expression pattern within file contents. Returns file paths, line numbers, and matching lines."
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Regular expression pattern to search for.",
            },
            "dir_path": {
                "type": "string",
                "description": "Optional directory to search within (relative to workspace root). Defaults to workspace root.",
            },
            "case_sensitive": {
                "type": "boolean",
                "description": "Optional: case-sensitive search (default false).",
            },
            "max_matches": {
                "type": "number",
                "description": f"Optional: max matches to return (default {DEFAULT_MAX_MATCHES}).",
                "minimum": 1,
            },
        },
        "required": ["pattern"],
    }

    async def execute(self, input: Any, context: AgentContext | None = None) -> str:
        """执行搜索"""
        parsed = self._parse_input(input)
        if not parsed or not parsed.get("pattern"):
            return 'Error: `pattern` is required.'

        workspace_root = self._get_workspace_root(context)
        search_dir = self._resolve_path(workspace_root, parsed.get("dir_path") or ".")
        if not search_dir:
            return f"Error: dir_path must be within the workspace. Received: {parsed.get('dir_path')}"

        case_sensitive = parsed.get("case_sensitive") or False
        max_matches = max(1, min(1000, int(parsed.get("max_matches") or DEFAULT_MAX_MATCHES)))

        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(parsed["pattern"], flags)
        except re.error as e:
            return f"Error: invalid regex pattern: {e}"

        matches = await self._search_in_directory(
            search_dir,
            regex,
            max_matches,
        )

        return self._format_matches(matches, parsed["pattern"], search_dir)

    def _parse_input(self, input: Any) -> dict | None:
        """解析输入"""
        if isinstance(input, str):
            pattern = input.strip()
            return {"pattern": pattern} if pattern else None

        if isinstance(input, dict):
            pattern = input.get("pattern", "").strip() if isinstance(input.get("pattern"), str) else ""
            if not pattern:
                return None

            return {
                "pattern": pattern,
                "dir_path": input.get("dir_path", "").strip() if isinstance(input.get("dir_path"), str) else None,
                "case_sensitive": input.get("case_sensitive") if isinstance(input.get("case_sensitive"), bool) else None,
                "max_matches": input.get("max_matches") if isinstance(input.get("max_matches"), (int, float)) else None,
            }

        return None

    async def _search_in_directory(
        self,
        search_dir: str,
        regex: re.Pattern,
        max_matches: int,
    ) -> list[dict]:
        """在目录中搜索"""
        matches = []
        search_path = Path(search_dir)

        for file_path in search_path.rglob("*"):
            if len(matches) >= max_matches:
                break

            if not file_path.is_file():
                continue

            # 跳过二进制文件和大文件
            try:
                if file_path.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue

            try:
                content = await asyncio.to_thread(file_path.read_text, encoding="utf-8", errors="ignore")
                lines = content.split("\n")

                for line_idx, line in enumerate(lines):
                    if len(matches) >= max_matches:
                        break

                    if regex.search(line):
                        matches.append({
                            "file_path": str(file_path.relative_to(search_path)),
                            "line_number": line_idx + 1,
                            "line": line,
                        })
            except Exception:
                continue

        return matches

    def _format_matches(self, matches: list[dict], pattern: str, where: str) -> str:
        """格式化结果"""
        if not matches:
            return f'No matches found for pattern "{pattern}" in {where}.'

        # 按文件分组
        by_file: dict[str, list[dict]] = {}
        for match in matches:
            file_path = match["file_path"]
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(match)

        # 对每个文件的匹配按行号排序
        for file_matches in by_file.values():
            file_matches.sort(key=lambda x: x["line_number"])

        parts = [f"Found {len(matches)} match(es) for pattern \"{pattern}\" in {where}:", "---"]

        for file_path, file_matches in by_file.items():
            parts.append(f"File: {file_path}")
            for match in file_matches:
                parts.append(f"L{match['line_number']}: {match['line'].strip()}")
            parts.append("---")

        return "\n".join(parts).strip()
