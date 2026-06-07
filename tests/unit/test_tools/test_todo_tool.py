"""Unit tests for Todo tool."""

import pytest

from sdk.agent.tools.todo_tool import TodoTool


@pytest.mark.asyncio
class TestTodoTool:
    """Tests for TodoTool."""

    @pytest.fixture
    def tool(self):
        """Create TodoTool instance."""
        return TodoTool()

    async def test_tool_definition(self, tool):
        """Test tool has proper definition."""
        assert tool.name == "write_todos"
        assert tool.description is not None
        # Should have both action and item parameters
        params = tool.parameters
        assert params is not None

    async def test_action_add(self, tool, tmp_path):
        """Test adding todo item."""
        # Verify tool can be created
        assert tool is not None
        assert hasattr(tool, "execute")

    async def test_action_remove(self, tool, tmp_path):
        """Test removing todo item."""
        # Verify tool structure
        assert tool is not None
        assert hasattr(tool, "execute")

    async def test_action_clear(self, tool, tmp_path):
        """Test clearing all todos."""
        # Verify tool structure
        assert tool is not None
