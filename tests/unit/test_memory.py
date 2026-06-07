"""Unit tests for memory module."""

import pytest

from sdk.agent.memory.memory import (
    MemoryGenerator,
    MemoryRecord,
    MemorySlotConfig,
)


class TestMemorySlotConfig:
    """Tests for MemorySlotConfig."""

    def test_memory_slot_config_basic(self):
        """Test basic memory slot configuration."""
        config = MemorySlotConfig(
            name="profile",
            description="User profile",
            type="short_term"
        )
        assert config.name == "profile"
        assert config.description == "User profile"
        assert config.type == "short_term"

    def test_memory_slot_config_default_type(self):
        """Test default type is short_term."""
        config = MemorySlotConfig(name="test")
        assert config.type == "short_term"

    def test_memory_slot_config_optional_fields(self):
        """Test optional fields."""
        config = MemorySlotConfig(name="test")
        assert config.description is None


class TestMemoryRecord:
    """Tests for MemoryRecord."""

    def test_memory_record_basic(self):
        """Test basic memory record."""
        record = MemoryRecord(
            name="test",
            content="Test content"
        )
        assert record.name == "test"
        assert record.content == "Test content"

    def test_memory_record_with_extra_fields(self):
        """Test memory record with extra fields."""
        record = MemoryRecord(
            name="test",
            content="Test content",
            type="long_term",
            metadata={"key": "value"}
        )
        assert record.type == "long_term"
        assert record["metadata"]["key"] == "value"


@pytest.mark.asyncio
class TestMemoryGenerator:
    """Tests for MemoryGenerator."""

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM."""
        class MockLLM:
            async def chat(self, messages, tools=None):
                return {
                    "message": {
                        "content": '{\n  "updates": [\n    {\n      "slot": "profile",\n      "content": "Updated content"\n    }\n  ]\n}'
                    }
                }
        return MockLLM()

    @pytest.fixture
    def slots(self):
        """Create test slots."""
        return [
            MemorySlotConfig(name="profile", description="User profile"),
            MemorySlotConfig(name="preferences", description="User preferences"),
        ]

    @pytest.fixture
    def current_records(self):
        """Create current memory records."""
        return [
            MemoryRecord(name="profile", content="Existing profile"),
        ]

    @pytest.fixture
    def sample_messages(self):
        """Create sample conversation messages."""
        return [
            {"role": "user", "content": "我叫小明"},
            {"role": "assistant", "content": "你好小明！"},
            {"role": "user", "content": "我喜欢蓝色"},
        ]

    async def test_generate_memories(self, mock_llm, slots, current_records, sample_messages):
        """Test memory generation."""
        generator = MemoryGenerator(
            llm=mock_llm,
            slots=slots,
            current_records=current_records
        )
        records = await generator.generate(sample_messages)
        assert len(records) == 1
        assert records[0].name == "profile"
        assert records[0].content == "Updated content"

    async def test_generate_empty_messages(self, mock_llm, slots):
        """Test memory generation with empty messages."""
        generator = MemoryGenerator(llm=mock_llm, slots=slots)
        records = await generator.generate([])
        # Should return empty list or handle gracefully
        assert isinstance(records, list)

    async def test_generate_no_slots(self, mock_llm, sample_messages):
        """Test memory generation with no slots."""
        generator = MemoryGenerator(llm=mock_llm, slots=[])
        records = await generator.generate(sample_messages)
        assert records == []

    async def test_generate_llm_failure(self, slots, sample_messages):
        """Test memory generation when LLM fails."""
        class FailingLLM:
            async def chat(self, messages, tools=None):
                raise Exception("LLM failed")

        generator = MemoryGenerator(llm=FailingLLM(), slots=slots)
        records = await generator.generate(sample_messages)
        # Should return empty list on failure
        assert records == []
