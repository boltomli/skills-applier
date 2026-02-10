"""
Unit tests for method recommendation module.
"""

import pytest
from unittest.mock import Mock
from stats_solver.recommendation.matcher import SkillMatcher
from stats_solver.recommendation.scorer import RecommendationScorer
from stats_solver.recommendation.prerequisites import PrerequisiteChecker
from stats_solver.recommendation.chain_builder import ChainBuilder
from stats_solver.recommendation.alternatives import AlternativeSuggester


class TestSkillMatcher:
    """Test skill matcher."""

    @pytest.fixture
    def matcher(self):
        """Create a skill matcher instance."""
        return SkillMatcher()

    @pytest.fixture
    def sample_skills(self):
        """Sample skills for testing."""
        return [
            {
                "skill_id": "t-test",
                "name": "T-Test",
                "category": "statistical_method",
                "data_types": ["numerical"],
                "problem_types": ["hypothesis_test"],
            },
            {
                "skill_id": "regression",
                "name": "Linear Regression",
                "category": "statistical_method",
                "data_types": ["numerical"],
                "problem_types": ["regression"],
            },
        ]

    def test_match_by_problem_type(self, matcher, sample_skills):
        """Test matching skills by problem type."""
        problem_features = Mock()
        problem_features.problem_type = "hypothesis_test"
        problem_features.data_types = ["numerical"]

        matches = matcher.match(sample_skills, problem_features)
        assert len(matches) > 0
        assert matches[0]["skill_id"] == "t-test"

    def test_match_by_data_type(self, matcher, sample_skills):
        """Test matching skills by data type."""
        problem_features = Mock()
        problem_features.data_types = ["numerical"]

        matches = matcher.match(sample_skills, problem_features)
        assert len(matches) == 2  # Both skills work with numerical data

    def test_no_matches(self, matcher):
        """Test when no skills match."""
        skills = [{"skill_id": "text-analysis", "data_types": ["text"]}]
        problem_features = Mock()
        problem_features.data_types = ["numerical"]

        matches = matcher.match(skills, problem_features)
        assert len(matches) == 0


class TestRecommendationScorer:
    """Test recommendation scorer."""

    @pytest.fixture
    def scorer(self):
        """Create a recommendation scorer instance."""
        return RecommendationScorer()

    def test_score_perfect_match(self, scorer):
        """Test scoring a perfect match."""
        skill = {
            "skill_id": "t-test",
            "category": "statistical_method",
            "data_types": ["numerical"],
            "problem_types": ["hypothesis_test"],
            "popularity": 0.9,
        }
        problem_features = Mock()
        problem_features.problem_type = "hypothesis_test"
        problem_features.data_types = ["numerical"]
        problem_features.constraints = []

        score = scorer.score(skill, problem_features)
        assert score > 0.8  # High score for good match

    def test_score_partial_match(self, scorer):
        """Test scoring a partial match."""
        skill = {
            "skill_id": "regression",
            "category": "statistical_method",
            "data_types": ["numerical"],
            "problem_types": ["regression"],
            "popularity": 0.7,
        }
        problem_features = Mock()
        problem_features.problem_type = "hypothesis_test"  # Different type
        problem_features.data_types = ["numerical"]

        score = scorer.score(skill, problem_features)
        assert score < 0.8  # Lower score for partial match

    def test_score_data_type_mismatch(self, scorer):
        """Test scoring with data type mismatch."""
        skill = {"skill_id": "text-analysis", "data_types": ["text"]}
        problem_features = Mock()
        problem_features.data_types = ["numerical"]

        score = scorer.score(skill, problem_features)
        assert score == 0.0  # No score for mismatch


class TestPrerequisiteChecker:
    """Test prerequisite checker."""

    @pytest.fixture
    def checker(self):
        """Create a prerequisite checker instance."""
        return PrerequisiteChecker()

    def test_no_prerequisites(self, checker):
        """Test skill with no prerequisites."""
        skill = {"skill_id": "simple-test", "prerequisites": []}
        problem_context = {"available_skills": []}

        result = checker.check(skill, problem_context)
        assert result.satisfied is True

    def test_satisfied_prerequisites(self, checker):
        """Test skill with satisfied prerequisites."""
        skill = {"skill_id": "advanced-test", "prerequisites": ["simple-test"]}
        problem_context = {"available_skills": ["simple-test"]}

        result = checker.check(skill, problem_context)
        assert result.satisfied is True

    def test_unsatisfied_prerequisites(self, checker):
        """Test skill with unsatisfied prerequisites."""
        skill = {"skill_id": "advanced-test", "prerequisites": ["simple-test", "data-prep"]}
        problem_context = {"available_skills": ["simple-test"]}

        result = checker.check(skill, problem_context)
        assert result.satisfied is False
        assert "data-prep" in result.missing


class TestChainBuilder:
    """Test chain builder."""

    @pytest.fixture
    def builder(self):
        """Create a chain builder instance."""
        return ChainBuilder()

    @pytest.fixture
    def sample_skills(self):
        """Sample skills for testing."""
        return [
            {
                "skill_id": "descriptive",
                "name": "Descriptive Statistics",
                "category": "statistical_method",
                "prerequisites": [],
            },
            {
                "skill_id": "normality-test",
                "name": "Normality Test",
                "category": "statistical_method",
                "prerequisites": ["descriptive"],
            },
            {
                "skill_id": "t-test",
                "name": "T-Test",
                "category": "statistical_method",
                "prerequisites": ["normality-test"],
            },
        ]

    def test_build_chain(self, builder, sample_skills):
        """Test building a skill chain."""
        target_skill = "t-test"
        chain = builder.build(sample_skills, target_skill)

        assert len(chain) == 3
        assert chain[0]["skill_id"] == "descriptive"
        assert chain[1]["skill_id"] == "normality-test"
        assert chain[2]["skill_id"] == "t-test"

    def test_build_chain_with_prerequisites_satisfied(self, builder, sample_skills):
        """Test building chain when prerequisites are already satisfied."""
        target_skill = "t-test"
        context = {"available_skills": ["descriptive"]}
        chain = builder.build(sample_skills, target_skill, context)

        assert len(chain) == 2  # descriptive already available
        assert chain[0]["skill_id"] == "normality-test"


class TestAlternativeSuggester:
    """Test alternative suggester."""

    @pytest.fixture
    def suggester(self):
        """Create an alternative suggester instance."""
        return AlternativeSuggester()

    @pytest.fixture
    def sample_skills(self):
        """Sample skills for testing."""
        return [
            {
                "skill_id": "t-test",
                "name": "T-Test",
                "category": "statistical_method",
                "tags": ["parametric", "hypothesis_test"],
            },
            {
                "skill_id": "mann-whitney",
                "name": "Mann-Whitney U Test",
                "category": "statistical_method",
                "tags": ["non-parametric", "hypothesis_test"],
            },
            {
                "skill_id": "bootstrap",
                "name": "Bootstrap Test",
                "category": "statistical_method",
                "tags": ["distribution-free", "hypothesis_test"],
            },
        ]

    def test_suggest_alternatives(self, suggester, sample_skills):
        """Test suggesting alternatives for a skill."""
        primary_skill = sample_skills[0]
        alternatives = suggester.suggest(sample_skills, primary_skill)

        assert len(alternatives) > 0
        assert all(alt["skill_id"] != primary_skill["skill_id"] for alt in alternatives)

    def test_alternatives_by_tag_similarity(self, suggester, sample_skills):
        """Test alternatives with similar tags."""
        primary_skill = sample_skills[0]  # t-test with hypothesis_test tag
        alternatives = suggester.suggest(sample_skills, primary_skill)

        # Should suggest other hypothesis_test skills
        hypothesis_test_alts = [
            alt for alt in alternatives if "hypothesis_test" in alt.get("tags", [])
        ]
        assert len(hypothesis_test_alts) > 0

    def test_no_alternatives(self, suggester):
        """Test when no alternatives exist."""
        skills = [{"skill_id": "unique-skill", "tags": ["unique"]}]
        primary_skill = skills[0]

        alternatives = suggester.suggest(skills, primary_skill)
        assert len(alternatives) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
