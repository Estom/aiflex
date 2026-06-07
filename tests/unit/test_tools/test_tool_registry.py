"""Unit tests for tool registry."""

import pytest

from sdk.agent.tools.tool_registry import ToolRegistry
from sdk.agent.tools.base_tool import BaseTool


class SimpleTool(BaseTool):
    """Simple tool for testing."""

    name = "simple_tool"
    description = "A simple test tool"

    async def execute(self, input, context=None):
        return f"Executed with: {input}"


@pytest.mark.asyncio
class TestToolRegistry:
    """Tests for ToolRegistry."""

    @pytest.fixture
    def registry(self):
        """Create ToolRegistry instance."""
        return ToolRegistry()

    @pytest.fixture
    def sample_tool(self):
        """Create sample tool."""
        return SimpleTool()

    def test_register_tool(self, registry, sample_tool):
        """Test registering a tool."""
        registry.register(sample_tool)

        tools = registry.list()
        assert len(tools) == 1
        assert tools[0].name == "simple_tool"

    def test_register_duplicate_tool(self, registry, sample_tool):
        """Test registering duplicate tool."""
        registry.register(sample_tool)
        registry.register(sample_tool)

        tools = registry.list()
        # Should not duplicate
        tool_names = [t.name for t in tools]
        assert tool_names.count("simple_tool") == 1

    def test_get_tool(self, registry, sample_tool):
        """Test getting a tool."""
        registry.register(sample_tool)

        tool = registry.get("simple_tool")
        assert tool is not None
        assert tool.name == "simple_tool"

    def test_get_nonexistent_tool(self, registry):
        """Test getting non-existent tool."""
        tool = registry.get("nonexistent_tool")
        assert tool is None

    def test_unregister_tool(self, registry, sample_tool):
        """Test unregistering a tool."""
        registry.register(sample_tool)

        # Verify tool exists
        tool_before = registry.get("simple_tool")
        assert tool_before is not None

        # Unregister
        registry.unregister("simple_tool")

        # Verify tool is gone
        tool_after = registry.get("simple_tool")
        assert tool_after is None

    def test_unregister_nonexistent_tool(self, registry):
        """Test unregistering non-existent tool."""
        # Should not raise error (returns None)
        result = registry.unregister("nonexistent_tool")
        assert result is None

    def test_get_definitions(self, registry, sample_tool):
        """Test getting tool definitions."""
        registry.register(sample_tool)

        definitions = registry.definitions()
        assert len(definitions) == 1

    def test_get_empty_definitions(self, registry):
        """Test getting definitions from empty registry."""
        definitions = registry.definitions()
        assert len(definitions) == 0

    def test_unregister_removes_all(self, registry, sample_tool):
        """Test unregistering removes tool."""
        registry.register(sample_tool)

        # Verify tool exists
        assert len(registry.list()) == 1

        # Unregister
        registry.unregister(sample_tool.name)

        # Verify empty
        assert len(registry.list()) == 0
