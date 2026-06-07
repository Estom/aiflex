"""Unit tests for skill registry."""

import pytest

from sdk.agent.skills.skill_registry import SkillRegistry


class TestSkillRegistry:
    """Tests for SkillRegistry."""

    @pytest.fixture
    def registry(self):
        """Create SkillRegistry instance."""
        return SkillRegistry()

    @pytest.fixture
    def sample_skill(self):
        """Create a sample skill."""
        return {
            "name": "test_skill",
            "description": "A test skill",
            "version": "1.0.0",
            "content": "This is a test skill content."
        }

    def test_register_skill(self, registry, sample_skill):
        """Test registering a skill."""
        registry.register(sample_skill)
        retrieved = registry.get("test_skill")
        assert retrieved is not None
        assert retrieved["name"] == "test_skill"
        assert retrieved["description"] == "A test skill"

    def test_register_duplicate_skill(self, registry, sample_skill):
        """Test registering duplicate skill."""
        registry.register(sample_skill)
        registry.register(sample_skill)
        # Should not duplicate
        skills = registry.list()
        test_skills = [s for s in skills if s["name"] == "test_skill"]
        assert len(test_skills) == 1

    def test_get_nonexistent_skill(self, registry):
        """Test getting non-existent skill."""
        result = registry.get("nonexistent")
        assert result is None

    def test_list_empty(self, registry):
        """Test listing empty registry."""
        skills = registry.list()
        assert skills == []

    def test_list_multiple_skills(self, registry):
        """Test listing multiple skills."""
        skills = [
            {"name": "skill1", "description": "Skill 1"},
            {"name": "skill2", "description": "Skill 2"},
            {"name": "skill3", "description": "Skill 3"},
        ]
        for skill in skills:
            registry.register(skill)

        result = registry.list()
        assert len(result) == 3

    def test_find_by_tag(self, registry):
        """Test finding skills by tag."""
        skill1 = {"name": "skill1", "description": "Skill 1", "tags": ["analysis", "market"]}
        skill2 = {"name": "skill2", "description": "Skill 2", "tags": ["report"]}
        skill3 = {"name": "skill3", "description": "Skill 3", "tags": ["analysis"]}

        registry.register(skill1)
        registry.register(skill2)
        registry.register(skill3)

        results = registry.find_by_tag("analysis")
        assert len(results) == 2

    def test_clear(self, registry, sample_skill):
        """Test clearing registry."""
        registry.register(sample_skill)
        assert len(registry.list()) == 1

        registry.clear()
        assert len(registry.list()) == 0
