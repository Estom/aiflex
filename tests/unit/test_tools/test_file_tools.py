"""Unit tests for file tools."""


import pytest

from sdk.agent.tools.read_file_tool import ReadFileTool
from sdk.agent.tools.write_file_tool import WriteFileTool


@pytest.mark.asyncio
class TestReadFileTool:
    """Tests for ReadFileTool."""

    @pytest.fixture
    def tool(self):
        """Create ReadFileTool instance."""
        return ReadFileTool()

    @pytest.fixture
    def workspace(self, tmp_path):
        """Create temporary workspace with test files."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5")
        return tmp_path

    async def test_read_file_basic(self, tool, workspace):
        """Test basic file reading."""
        result = await tool.execute({"file_path": str(workspace / "test.txt")})
        assert "Line 1" in result
        assert "Line 5" in result
        assert "Showing lines 1-5" in result

    async def test_read_file_with_offset(self, tool, workspace):
        """Test file reading with offset."""
        result = await tool.execute({"file_path": str(workspace / "test.txt"), "offset": 2})
        assert "Line 1" not in result
        assert "Line 3" in result

    async def test_read_file_with_limit(self, tool, workspace):
        """Test file reading with limit."""
        result = await tool.execute({"file_path": str(workspace / "test.txt"), "limit": 2})
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" not in result

    async def test_read_file_not_found(self, tool):
        """Test reading non-existent file."""
        result = await tool.execute({"file_path": "/nonexistent/file.txt"})
        assert "Error" in result

    async def test_read_file_missing_path(self, tool):
        """Test reading file with missing path."""
        result = await tool.execute({})
        assert "Error" in result


@pytest.mark.asyncio
class TestWriteFileTool:
    """Tests for WriteFileTool."""

    @pytest.fixture
    def tool(self):
        """Create WriteFileTool instance."""
        return WriteFileTool()

    @pytest.fixture
    def workspace(self, tmp_path):
        """Create temporary workspace."""
        return tmp_path

    async def test_write_file_basic(self, tool, workspace):
        """Test basic file writing."""
        file_path = workspace / "output.txt"
        result = await tool.execute({
            "file_path": str(file_path),
            "content": "Hello, World!"
        })
        assert "Successfully wrote" in result or "OK" in result.upper()
        assert file_path.exists()
        assert file_path.read_text() == "Hello, World!"

    async def test_write_file_overwrite(self, tool, workspace):
        """Test overwriting existing file."""
        file_path = workspace / "output.txt"
        file_path.write_text("Old content")

        result = await tool.execute({
            "file_path": str(file_path),
            "content": "New content"
        })
        assert file_path.read_text() == "New content"

    async def test_write_file_missing_content(self, tool, workspace):
        """Test writing file with missing content."""
        file_path = workspace / "output.txt"
        result = await tool.execute({"file_path": str(file_path)})
        assert "Error" in result or "required" in result.lower()
