"""
Shell Tool - Shell 命令执行工具

在指定目录中执行 Shell 命令
"""

import asyncio
import os
import platform
from typing import Any

from ..core.interfaces import AgentContext, ToolDefinition
from ..tools.base_tool import BaseTool


MAX_CAPTURED_OUTPUT = 120000
DEFAULT_TIMEOUT_MS = 60000


class ShellTool(BaseTool):
    """
    Shell 命令执行工具

    在工作区中执行 bash 命令
    """

    name = "shell"
    display_name = "Shell"
    description = "Executes a POSIX shell command via `bash -lc` inside the workspace. Returns command output, exit code, and execution metadata."
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Literal command string executed as `bash -lc <command>`.",
            },
            "dir_path": {
                "type": "string",
                "description": "Optional working directory. May be absolute or workspace-relative. Defaults to the workspace root.",
            },
            "timeout_seconds": {
                "type": "number",
                "description": "Optional timeout in seconds (default 60, min 5).",
                "minimum": 5,
            },
        },
        "required": ["command"],
    }

    async def execute(self, input: Any, context: AgentContext | None = None) -> str:
        """执行 Shell 命令"""
        params = self._parse_input(input)
        if not params or not params.get("command"):
            return 'Error: `command` is required.'

        if platform.system() == "Windows":
            return "Error: ShellTool only supports POSIX environments."

        workspace_root = self._get_workspace_root(context)
        working_dir = params.get("dir_path")
        if working_dir:
            resolved = self._resolve_within_workspace(workspace_root, working_dir)
            if not resolved:
                return f"Error: dir_path must be inside the workspace. Received: {working_dir}"
            working_dir = resolved
        else:
            working_dir = workspace_root

        if not os.path.isdir(working_dir):
            return f"Error: dir_path is not a directory: {working_dir}"

        timeout_ms = max(5000, int(params.get("timeout_seconds", 60) * 1000))

        try:
            result = await self._run_shell_command(
                params["command"],
                working_dir,
                timeout_ms,
            )
            return self._format_result(result, workspace_root)
        except Exception as e:
            return f"Error executing shell command: {e!s}"

    def _parse_input(self, input: Any) -> dict | None:
        """解析输入"""
        if isinstance(input, str):
            command = input.strip()
            return {"command": command} if command else None

        if isinstance(input, dict):
            command = input.get("command", "").strip() if isinstance(input.get("command"), str) else ""
            if not command:
                return None

            return {
                "command": command,
                "dir_path": input.get("dir_path", "").strip() if isinstance(input.get("dir_path"), str) else None,
                "timeout_seconds": input.get("timeout_seconds") if isinstance(input.get("timeout_seconds"), (int, float)) else None,
            }

        return None

    def _resolve_within_workspace(self, workspace_root: str, user_path: str) -> str | None:
        """解析路径"""
        resolved = os.path.abspath(user_path) if os.path.isabs(user_path) else os.path.abspath(os.path.join(workspace_root, user_path))
        rel = os.path.relpath(resolved, workspace_root)
        if rel == "." or (not rel.startswith("..") and not os.path.isabs(rel)):
            return resolved
        return None

    async def _run_shell_command(self, command: str, cwd: str, timeout_ms: int) -> dict:
        """运行 Shell 命令"""
        proc = await asyncio.create_subprocess_exec(
            "bash",
            ["-lc", command],
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_ms / 1000)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return {
                "command": command,
                "cwd": cwd,
                "stdout": "",
                "stderr": f"Command timed out after {timeout_ms / 1000} seconds",
                "exit_code": -1,
                "timed_out": True,
            }

        stdout_text = stdout.decode("utf-8", errors="replace")
        stderr_text = stderr.decode("utf-8", errors="replace")

        # 截断输出
        if len(stdout_text) > MAX_CAPTURED_OUTPUT:
            stdout_text = stdout_text[:MAX_CAPTURED_OUTPUT] + "\n...[output truncated]"
        if len(stderr_text) > MAX_CAPTURED_OUTPUT:
            stderr_text = stderr_text[:MAX_CAPTURED_OUTPUT] + "\n...[output truncated]"

        return {
            "command": command,
            "cwd": cwd,
            "stdout": stdout_text,
            "stderr": stderr_text,
            "exit_code": proc.returncode or 0,
            "timed_out": False,
        }

    def _format_result(self, result: dict, workspace_root: str) -> str:
        """格式化结果"""
        rel_dir = os.path.relpath(result["cwd"], workspace_root) or "."

        lines = [
            f"Command: {result['command']}",
            f"Directory: {rel_dir}",
            f"Exit Code: {result['exit_code']}",
            f"Timed Out: {result['timed_out']}",
            "",
            "STDOUT:",
            result["stdout"] or "(empty)",
            "",
            "STDERR:",
            result["stderr"] or "(empty)",
        ]

        return "\n".join(lines)
