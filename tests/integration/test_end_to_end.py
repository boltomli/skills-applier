"""
End-to-end integration tests for the stats solver system.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from stats_solver.llm.manager import LLMManager
from stats_solver.skills.index import SkillIndex
from stats_solver.skills.scanner import SkillScanner
from stats_solver.problem.extractor import ProblemExtractor
from stats_solver.recommendation.matcher import SkillMatcher
from stats_solver.recommendation.scorer import RecommendationScorer
from stats_solver.solution.code_generator import CodeGenerator


class TestEndToEndWorkflow:
    """Test complete end-to-end workflow."""

    @pytest.fixture
    def skill_index(self, tmp_path):
        """Create a skill index with sample skills."""
        index = SkillIndex(cache_dir=str(tmp_path))

        # Add sample skills
        sample_skills = [
            {
                "skill_id": "t-test",
                "name": "Two-Sample T-Test",
                "description": "Performs independent samples t-test",
                "category": "statistical_method",
                "data_types": ["numerical"],
                "problem_types": ["hypothesis_test"],
                "tags": ["parametric", "hypothesis_test"],
                "dependencies": ["numpy", "scipy"],
                "popularity": 0.9
            },
            {
                "skill_id": "linear-regression",
                "name": "Linear Regression",
                "description": "Performs linear regression analysis",
                "category": "statistical_method",
                "data_types": ["numerical"],
                "problem_types": ["regression"],
                "tags": ["modeling", "prediction"],
                "dependencies": ["numpy", "scipy", "sklearn"],
                "popularity": 0.95
            },
            {
                "skill_id": "fibonacci",
                "name": "Fibonacci Sequence",
                "description": "Generates Fibonacci numbers",
                "category": "mathematical_implementation",
                "data_types": ["numerical"],
                "problem_types": ["computation"],
                "tags": ["sequence", "algorithm"],
                "dependencies": ["numpy"],
                "popularity": 0.85
            }
        ]

        for skill in sample_skills:
            index.add_skill(skill["skill_id"], skill)

        return index

    def test_complete_workflow_hypothesis_test(self, skill_index):
        """Test complete workflow for hypothesis test problem."""
        # Step 1: User describes problem
        user_problem = "I have test scores from two different classes and want to know if there's a significant difference between them. Each class has about 30 students."

        # Step 2: Extract problem features
        extractor = ProblemExtractor()
        problem_features = extractor.extract(user_problem)

        assert problem_features.problem_type == "hypothesis_test"
        assert "numerical" in problem_features.data_types

        # Step 3: Match skills to problem
        skills = skill_index.get_all_skills()
        matcher = SkillMatcher()
        matches = matcher.match(skills, problem_features)

        assert len(matches) > 0
        assert matches[0]["skill_id"] == "t-test"

        # Step 4: Score and rank recommendations
        scorer = RecommendationScorer()
        scored_matches = scorer.score_matches(matches, problem_features)

        assert len(scored_matches) > 0
        assert scored_matches[0]["score"] > 0.5

        # Step 5: Generate solution code
        generator = CodeGenerator()
        solution = generator.generate(
            skill=scored_matches[0]["skill"],
            problem=problem_features,
            method="template"
        )

        assert solution is not None
        assert "import" in solution
        assert "def" in solution

    def test_complete_workflow_regression(self, skill_index):
        """Test complete workflow for regression problem."""
        user_problem = "I want to predict house prices based on square footage and number of bedrooms."

        extractor = ProblemExtractor()
        problem_features = extractor.extract(user_problem)

        assert problem_features.problem_type == "regression"

        skills = skill_index.get_all_skills()
        matcher = SkillMatcher()
        matches = matcher.match(skills, problem_features)

        assert len(matches) > 0
        assert matches[0]["skill_id"] == "linear-regression"

    def test_complete_workflow_math_computation(self, skill_index):
        """Test complete workflow for mathematical computation."""
        user_problem = "I need to generate the first 100 Fibonacci numbers."

        extractor = ProblemExtractor()
        problem_features = extractor.extract(user_problem)

        assert problem_features.problem_type == "computation"

        skills = skill_index.get_all_skills()
        matcher = SkillMatcher()
        matches = matcher.match(skills, problem_features)

        assert len(matches) > 0
        assert matches[0]["skill_id"] == "fibonacci"

    @patch.object(LLMManager, 'check_connection')
    def test_workflow_with_llm_integration(self, mock_check, skill_index):
        """Test workflow with LLM integration."""
        mock_check.return_value = (True, ["llama3"])

        user_problem = "Analyze the relationship between advertising spend and sales revenue."

        # This would use LLM for enhanced analysis
        extractor = ProblemExtractor(use_llm=True)
        problem_features = extractor.extract(user_problem)

        # Verify LLM was called (or fallback was used)
        assert problem_features is not None


class TestSkillScanningIntegration:
    """Test skill scanning integration."""

    @pytest.fixture
    def temp_skill_dir(self, tmp_path):
        """Create temporary skill directory with sample files."""
        skill_dir = tmp_path / "skills"
        skill_dir.mkdir()

        # Create sample skill files
        (skill_dir / "t_test.py").write_text("""
def two_sample_ttest(sample1, sample2):
    # T-test implementation
    pass
""")

        (skill_dir / "fibonacci.py").write_text("""
def fibonacci(n):
    # Fibonacci implementation
    pass
""")

        return skill_dir

    def test_scan_and_index_skills(self, temp_skill_dir, tmp_path):
        """Test scanning skills and indexing them."""
        scanner = SkillScanner(base_paths=[str(temp_skill_dir)])
        skills = scanner.scan_directory(str(temp_skill_dir))

        assert len(skills) >= 2

        # Index the skills
        index = SkillIndex(cache_dir=str(tmp_path))
        for skill in skills:
            index.add_skill(skill["skill_id"], skill)

        # Verify skills are indexed
        all_skills = index.get_all_skills()
        assert len(all_skills) >= 2


class TestErrorHandlingIntegration:
    """Test error handling in integration scenarios."""

    def test_handle_no_matching_skills(self, tmp_path):
        """Test handling when no skills match."""
        index = SkillIndex(cache_dir=str(tmp_path))

        user_problem = "I need to perform quantum computing calculations on my data."

        extractor = ProblemExtractor()
        problem_features = extractor.extract(user_problem)

        skills = index.get_all_skills()
        matcher = SkillMatcher()
        matches = matcher.match(skills, problem_features)

        # Should handle empty matches gracefully
        assert len(matches) == 0

    def test_handle_invalid_user_input(self):
        """Test handling invalid user input."""
        invalid_input = ""
        extractor = ProblemExtractor()

        with pytest.raises(ValueError):
            extractor.extract(invalid_input)

    def test_handle_skill_with_missing_metadata(self, tmp_path):
        """Test handling skills with incomplete metadata."""
        index = SkillIndex(cache_dir=str(tmp_path))

        # Add skill with incomplete metadata
        incomplete_skill = {
            "skill_id": "incomplete",
            "name": "Incomplete Skill"
            # Missing required fields
        }

        index.add_skill("incomplete", incomplete_skill)

        # Should handle gracefully
        skill = index.get_skill("incomplete")
        assert skill is not None


class TestPerformanceIntegration:
    """Test performance in integration scenarios."""

    def test_large_skill_index_performance(self, tmp_path):
        """Test performance with large skill index."""
        index = SkillIndex(cache_dir=str(tmp_path))

        # Add many skills
        for i in range(100):
            skill = {
                "skill_id": f"skill-{i}",
                "name": f"Skill {i}",
                "description": f"Description for skill {i}",
                "category": "statistical_method",
                "data_types": ["numerical"],
                "problem_types": ["hypothesis_test"]
            }
            index.add_skill(f"skill-{i}", skill)

        # Test search performance
        import time
        start = time.time()
        results = index.search(category="statistical_method")
        elapsed = time.time() - start

        assert len(results) == 100
        assert elapsed < 1.0  # Should be fast

    def test_multiple_recommendations_performance(self, tmp_path):
        """Test performance of multiple recommendations."""
        index = SkillIndex(cache_dir=str(tmp_path))

        # Add sample skills
        for i in range(10):
            skill = {
                "skill_id": f"skill-{i}",
                "name": f"Skill {i}",
                "description": f"Description {i}",
                "category": "statistical_method",
                "data_types": ["numerical"],
                "problem_types": ["hypothesis_test"]
            }
            index.add_skill(f"skill-{i}", skill)

        # Test multiple recommendations
        problem_features = Mock()
        problem_features.problem_type = "hypothesis_test"
        problem_features.data_types = ["numerical"]

        skills = index.get_all_skills()
        matcher = SkillMatcher()
        scorer = RecommendationScorer()

        matches = matcher.match(skills, problem_features)
        scored = scorer.score_matches(matches, problem_features)

        assert len(scored) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])