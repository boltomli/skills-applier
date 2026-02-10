"""
Unit tests for skill indexing module.
"""

import pytest
import tempfile
from unittest.mock import Mock, patch
from stats_solver.skills.metadata_schema import validate_metadata
from stats_solver.skills.scanner import SkillScanner
from stats_solver.skills.classifier import SkillClassifier
from stats_solver.skills.index import SkillIndex
from stats_solver.skills.editor import SkillEditor


class TestSkillMetadata:
    """Test skill metadata schema."""

    def test_valid_metadata(self):
        """Test validating valid metadata."""
        metadata = {
            "skill_id": "test-skill",
            "name": "Test Skill",
            "description": "A test skill",
            "category": "statistical_method",
            "tags": ["test", "example"],
            "data_types": ["numerical"],
            "problem_types": ["hypothesis_test"],
        }
        result = validate_metadata(metadata)
        assert result.is_valid is True

    def test_missing_required_field(self):
        """Test validating metadata with missing required field."""
        metadata = {"name": "Test Skill", "description": "A test skill"}
        result = validate_metadata(metadata)
        assert result.is_valid is False
        assert "skill_id" in result.errors

    def test_invalid_category(self):
        """Test validating metadata with invalid category."""
        metadata = {
            "skill_id": "test-skill",
            "name": "Test Skill",
            "description": "A test skill",
            "category": "invalid_category",
        }
        result = validate_metadata(metadata)
        assert result.is_valid is False


class TestSkillScanner:
    """Test skill scanner."""

    @pytest.fixture
    def scanner(self):
        """Create a skill scanner instance."""
        return SkillScanner(base_paths=["./test_skills"])

    def test_initialization(self, scanner):
        """Test scanner initialization."""
        assert len(scanner.base_paths) == 1
        assert scanner.base_paths[0] == "./test_skills"

    @patch("pathlib.Path.glob")
    def test_scan_directory(self, mock_glob, scanner):
        """Test scanning a directory."""
        mock_file1 = Mock()
        mock_file1.suffix = ".py"
        mock_file1.is_file.return_value = True

        mock_file2 = Mock()
        mock_file2.suffix = ".md"
        mock_file2.is_file.return_value = True

        mock_glob.return_value = [mock_file1, mock_file2]

        skills = scanner.scan_directory("./test_skills")
        assert len(skills) == 1  # Only .py files


class TestSkillClassifier:
    """Test skill classifier."""

    @pytest.fixture
    def classifier(self):
        """Create a skill classifier instance."""
        return SkillClassifier()

    def test_classify_statistical_method(self, classifier):
        """Test classifying a statistical method."""
        skill_data = {
            "skill_id": "t-test",
            "name": "T-Test",
            "description": "Performs t-test for hypothesis testing",
        }
        result = classifier.classify(skill_data)
        assert result.category == "statistical_method"
        assert "hypothesis_test" in result.tags

    def test_classify_mathematical_implementation(self, classifier):
        """Test classifying a mathematical implementation."""
        skill_data = {
            "skill_id": "fibonacci",
            "name": "Fibonacci",
            "description": "Calculates fibonacci numbers",
        }
        result = classifier.classify(skill_data)
        assert result.category == "mathematical_implementation"
        assert "sequence" in result.tags or "computation" in result.tags


class TestSkillIndex:
    """Test skill index."""

    @pytest.fixture
    def index(self):
        """Create a skill index instance."""
        return SkillIndex(cache_dir=tempfile.mkdtemp())

    def test_initialization(self, index):
        """Test index initialization."""
        assert index is not None
        assert index.cache_dir is not None

    def test_add_skill(self, index):
        """Test adding a skill to the index."""
        metadata = {
            "skill_id": "test-skill",
            "name": "Test Skill",
            "description": "A test skill",
            "category": "statistical_method",
        }
        index.add_skill("test-skill", metadata)
        skill = index.get_skill("test-skill")
        assert skill is not None
        assert skill["skill_id"] == "test-skill"

    def test_search_by_category(self, index):
        """Test searching skills by category."""
        metadata1 = {"skill_id": "skill1", "name": "Skill 1", "category": "statistical_method"}
        metadata2 = {
            "skill_id": "skill2",
            "name": "Skill 2",
            "category": "mathematical_implementation",
        }

        index.add_skill("skill1", metadata1)
        index.add_skill("skill2", metadata2)

        results = index.search(category="statistical_method")
        assert len(results) == 1
        assert results[0]["skill_id"] == "skill1"

    def test_search_by_tag(self, index):
        """Test searching skills by tag."""
        metadata = {
            "skill_id": "skill1",
            "name": "Skill 1",
            "category": "statistical_method",
            "tags": ["hypothesis_test", "parametric"],
        }

        index.add_skill("skill1", metadata)

        results = index.search(tags=["hypothesis_test"])
        assert len(results) == 1

    def test_get_nonexistent_skill(self, index):
        """Test getting a skill that doesn't exist."""
        skill = index.get_skill("nonexistent")
        assert skill is None


class TestSkillEditor:
    """Test skill editor."""

    @pytest.fixture
    def editor(self, tmp_path):
        """Create a skill editor instance."""
        index = SkillIndex(cache_dir=str(tmp_path))
        return SkillEditor(index)

    def test_edit_skill_category(self, editor):
        """Test editing a skill's category."""
        metadata = {
            "skill_id": "test-skill",
            "name": "Test Skill",
            "category": "statistical_method",
        }
        editor.index.add_skill("test-skill", metadata)

        editor.edit_skill("test-skill", category="mathematical_implementation")
        skill = editor.index.get_skill("test-skill")
        assert skill["category"] == "mathematical_implementation"

    def test_edit_skill_tags(self, editor):
        """Test editing a skill's tags."""
        metadata = {
            "skill_id": "test-skill",
            "name": "Test Skill",
            "category": "statistical_method",
            "tags": ["tag1"],
        }
        editor.index.add_skill("test-skill", metadata)

        editor.edit_skill("test-skill", tags=["tag1", "tag2", "tag3"])
        skill = editor.index.get_skill("test-skill")
        assert len(skill["tags"]) == 3
        assert "tag2" in skill["tags"]

    def test_edit_nonexistent_skill(self, editor):
        """Test editing a skill that doesn't exist."""
        with pytest.raises(ValueError):
            editor.edit_skill("nonexistent", category="statistical_method")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
