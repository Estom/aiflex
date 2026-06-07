"""Unit tests for shell tool."""


import pytest

from sdk.agent.tools.shell_tool import ShellTool


@pytest.mark.asyncio
class TestShellTool:
    """Tests for ShellTool."""

    @pytest.fixture
    def tool(self):
        """Create ShellTool instance."""
        return ShellTool()

    async def test_shell_echo(self, tool):
        """Test simple echo command."""
        result = await tool.execute({"command": "echo 'Hello, World!'"})
        assert "Hello, World!" in result

    async def test_shell_ls(self, tool):
        """Test ls command."""
        result = await tool.execute({"command": "ls /tmp"})
        assert result is not None

    async def test_shell_exit_code(self, tool):
        """Test command with exit code."""
        result = await tool.execute({"command": "exit 1"})
        # Shell tool should return output even on non-zero exit
        assert result is not None

    async def test_shell_missing_command(self, tool):
        """Test missing command parameter."""
        result = await tool.execute({})
        assert "Error" in result

    async def test_shell_command_with_output(self, tool, tmp_path):
        """Test command that creates output."""
        result = await tool.execute({
            "command": f"echo 'test' > {tmp_path / 'output.txt'} && cat {tmp_path / 'output.txt'}"
        })
        assert "test" in result
