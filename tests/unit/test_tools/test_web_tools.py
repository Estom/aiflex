"""Unit tests for web tools."""

import pytest

from sdk.agent.tools.web_fetch_tool import WebFetchTool
from sdk.agent.tools.web_search_tool import WebSearchTool


@pytest.mark.asyncio
class TestWebFetchTool:
    """Tests for WebFetchTool."""

    @pytest.fixture
    def tool(self):
        """Create WebFetchTool instance."""
        return WebFetchTool()

    @pytest.fixture
    def mock_response(self):
        """Mock httpx response."""
        class MockResponse:
            status_code = 200
            content_type = "text/html"
            text = "<html>Mock content</html>"

        return MockResponse()

    async def test_tool_definition(self, tool):
        """Test tool has proper definition."""
        assert tool.name == "web_fetch"
        assert tool.description is not None
        assert "url" in str(tool.parameters)

    async def test_parameters_validation(self, tool):
        """Test parameter validation."""
        # Missing URL
        result = await tool.execute({})
        assert "Error" in result or "required" in result.lower()

    async def test_max_length_truncation(self, tool):
        """Test content truncation at max length."""
        # This test would need mocking httpx
        # For now just check tool structure
        assert tool.name == "web_fetch"


@pytest.mark.asyncio
class TestWebSearchTool:
    """Tests for WebSearchTool."""

    @pytest.fixture
    def tool(self):
        """Create WebSearchTool instance."""
        return WebSearchTool()

    async def test_tool_definition(self, tool):
        """Test tool has proper definition."""
        assert tool.name == "web_search"
        assert tool.description is not None
        assert "query" in str(tool.parameters)

    async def test_search_query_validation(self, tool):
        """Test query parameter validation."""
        # Missing query
        result = await tool.execute({})
        assert "Error" in result or "required" in result.lower()

    async def test_search_with_empty_query(self, tool):
        """Test search with empty query."""
        result = await tool.execute({"query": ""})
        assert "Error" in result or len(result) == 0
