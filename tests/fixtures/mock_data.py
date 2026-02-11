"""
Mock data for testing the stats solver system.
"""

import numpy as np
from typing import Any


class MockLLMResponses:
    """Mock LLM responses for testing."""

    @staticmethod
    def problem_analysis_response() -> dict[str, Any]:
        """Mock response for problem analysis."""
        return {
            "summary": "Compare test scores between two classes to test for significant difference",
            "primary_goal": "Determine if there is a statistically significant difference between two groups",
            "data_types": ["numerical"],
            "sample_size_hint": "medium (30 per group)",
            "data_source_hints": ["experiment", "observation"],
            "problem_type": "hypothesis_test",
            "subtypes": ["two_sample_test"],
            "complexity_level": "simple",
            "constraints": [],
            "output_format": "number",
            "statistical_concepts": ["hypothesis_testing", "mean_comparison"],
            "assumptions": [
                "Samples are independent",
                "Data is approximately normally distributed",
                "Equal variances between groups",
            ],
            "domain": "education",
            "confidence": 0.9,
        }

    @staticmethod
    def recommendation_response() -> dict[str, Any]:
        """Mock response for recommendation."""
        return {
            "primary_recommendation": {
                "skill_id": "t-test-two-sample",
                "skill_name": "Two-Sample T-Test",
                "match_score": 0.95,
                "confidence": 0.9,
                "reasoning": "Directly addresses the goal of comparing two group means with numerical data",
            },
            "alternative_recommendations": [
                {
                    "skill_id": "mann-whitney",
                    "skill_name": "Mann-Whitney U Test",
                    "match_score": 0.8,
                    "reasoning": "Non-parametric alternative if normality assumptions are violated",
                },
                {
                    "skill_id": "bootstrap-difference",
                    "skill_name": "Bootstrap Difference Test",
                    "match_score": 0.75,
                    "reasoning": "Distribution-free approach that doesn't require normality",
                },
            ],
            "recommendation_chain": [
                {
                    "step": 1,
                    "skill_id": "descriptive-statistics",
                    "skill_name": "Descriptive Statistics",
                    "purpose": "Understand the data distribution before testing",
                },
                {
                    "step": 2,
                    "skill_id": "normality-test",
                    "skill_name": "Normality Test",
                    "purpose": "Verify t-test assumptions",
                },
                {
                    "step": 3,
                    "skill_id": "t-test-two-sample",
                    "skill_name": "Two-Sample T-Test",
                    "purpose": "Perform the hypothesis test",
                },
            ],
            "assumptions": [
                "Samples are independent",
                "Data is approximately normally distributed",
                "Equal variances between groups (or use Welch's t-test)",
            ],
            "warnings": [
                "Check normality assumptions before using t-test",
                "Consider sample size - small samples may reduce power",
            ],
            "confidence": 0.9,
        }

    @staticmethod
    def code_generation_response() -> dict[str, Any]:
        """Mock response for code generation."""
        return {
            "code": '''import numpy as np
from scipy import stats

def two_sample_ttest(sample1, sample2):
    """
    Perform an independent two-sample t-test.

    Parameters
    ----------
    sample1 : array-like
        First sample data
    sample2 : array-like
        Second sample data

    Returns
    -------
    result : dict
        Dictionary containing t-statistic and p-value
    """
    sample1 = np.asarray(sample1)
    sample2 = np.asarray(sample2)

    # Perform t-test
    statistic, pvalue = stats.ttest_ind(sample1, sample2)

    return {
        'statistic': statistic,
        'pvalue': pvalue
    }

if __name__ == "__main__":
    # Example usage
    data1 = np.random.normal(50, 10, 30)
    data2 = np.random.normal(52, 10, 30)
    result = two_sample_ttest(data1, data2)
    print(f"T-statistic: {result['statistic']:.4f}")
    print(f"P-value: {result['pvalue']:.4f}")''',
            "imports": ["import numpy as np", "from scipy import stats"],
            "docstring": "Perform an independent two-sample t-test.",
            "confidence": 0.95,
        }


class MockSkillData:
    """Mock skill data for testing."""

    @staticmethod
    def statistical_methods() -> list[dict[str, Any]]:
        """Mock statistical methods."""
        return [
            {
                "skill_id": "t-test-two-sample",
                "name": "Two-Sample T-Test",
                "description": "Performs an independent two-sample t-test",
                "category": "statistical_method",
                "subcategory": "hypothesis_test",
                "tags": ["hypothesis_testing", "mean_comparison", "parametric"],
                "data_types": ["numerical"],
                "problem_types": ["hypothesis_test"],
                "output_types": ["number", "statistic", "pvalue"],
                "complexity": "simple",
                "dependencies": ["numpy", "scipy"],
                "popularity": 0.9,
            },
            {
                "skill_id": "mann-whitney",
                "name": "Mann-Whitney U Test",
                "description": "Non-parametric alternative to t-test",
                "category": "statistical_method",
                "subcategory": "hypothesis_test",
                "tags": ["non-parametric", "hypothesis_testing"],
                "data_types": ["numerical"],
                "problem_types": ["hypothesis_test"],
                "output_types": ["number", "statistic", "pvalue"],
                "complexity": "simple",
                "dependencies": ["numpy", "scipy"],
                "popularity": 0.85,
            },
            {
                "skill_id": "linear-regression",
                "name": "Linear Regression",
                "description": "Performs linear regression analysis",
                "category": "statistical_method",
                "subcategory": "regression",
                "tags": ["modeling", "prediction", "linear"],
                "data_types": ["numerical"],
                "problem_types": ["regression", "modeling"],
                "output_types": ["model", "parameters", "predictions"],
                "complexity": "moderate",
                "dependencies": ["numpy", "scipy", "sklearn"],
                "popularity": 0.95,
            },
        ]

    @staticmethod
    def mathematical_implementations() -> list[dict[str, Any]]:
        """Mock mathematical implementations."""
        return [
            {
                "skill_id": "fibonacci-sequence",
                "name": "Fibonacci Sequence Generator",
                "description": "Generates Fibonacci numbers",
                "category": "mathematical_implementation",
                "subcategory": "sequence",
                "tags": ["sequence", "recursion", "iteration"],
                "data_types": ["numerical"],
                "problem_types": ["computation", "generation"],
                "output_types": ["array", "number"],
                "complexity": "moderate",
                "dependencies": ["numpy"],
                "popularity": 0.85,
            },
            {
                "skill_id": "matrix-operations",
                "name": "Matrix Operations",
                "description": "Performs basic matrix operations",
                "category": "mathematical_implementation",
                "subcategory": "linear_algebra",
                "tags": ["matrix", "linear_algebra"],
                "data_types": ["numerical"],
                "problem_types": ["computation"],
                "output_types": ["array"],
                "complexity": "simple",
                "dependencies": ["numpy"],
                "popularity": 0.9,
            },
        ]

    @staticmethod
    def visualization_skills() -> list[dict[str, Any]]:
        """Mock visualization skills."""
        return [
            {
                "skill_id": "histogram-visualization",
                "name": "Histogram Visualization",
                "description": "Creates histogram plots",
                "category": "mathematical_implementation",
                "subcategory": "visualization",
                "tags": ["visualization", "plotting", "distribution"],
                "data_types": ["numerical"],
                "problem_types": ["visualization"],
                "output_types": ["plot", "figure"],
                "complexity": "simple",
                "dependencies": ["matplotlib", "numpy"],
                "popularity": 0.9,
            },
            {
                "skill_id": "scatter-plot",
                "name": "Scatter Plot",
                "description": "Creates scatter plots",
                "category": "mathematical_implementation",
                "subcategory": "visualization",
                "tags": ["visualization", "plotting", "correlation"],
                "data_types": ["numerical"],
                "problem_types": ["visualization"],
                "output_types": ["plot", "figure"],
                "complexity": "simple",
                "dependencies": ["matplotlib", "numpy"],
                "popularity": 0.85,
            },
        ]


class MockProblemData:
    """Mock problem data for testing."""

    @staticmethod
    def hypothesis_test_problem() -> dict[str, Any]:
        """Mock hypothesis test problem."""
        return {
            "description": "I have test scores from two different classes and want to know if there's a significant difference between them.",
            "expected_type": "hypothesis_test",
            "expected_data_types": ["numerical"],
            "expected_complexity": "simple",
        }

    @staticmethod
    def regression_problem() -> dict[str, Any]:
        """Mock regression problem."""
        return {
            "description": "I want to predict house prices based on square footage and number of bedrooms.",
            "expected_type": "regression",
            "expected_data_types": ["numerical"],
            "expected_complexity": "moderate",
        }

    @staticmethod
    def classification_problem() -> dict[str, Any]:
        """Mock classification problem."""
        return {
            "description": "I want to classify customers into different segments based on their purchasing behavior.",
            "expected_type": "classification",
            "expected_data_types": ["numerical", "categorical"],
            "expected_complexity": "moderate",
        }

    @staticmethod
    def visualization_problem() -> dict[str, Any]:
        """Mock visualization problem."""
        return {
            "description": "I want to visualize the distribution of my data using a histogram.",
            "expected_type": "visualization",
            "expected_data_types": ["numerical"],
            "expected_complexity": "simple",
        }


class MockSampleData:
    """Mock sample data for testing."""

    @staticmethod
    def generate_test_scores(size: int = 30) -> np.ndarray:
        """Generate mock test scores."""
        return np.random.normal(75, 10, size)

    @staticmethod
    def generate_two_groups(size: int = 30) -> tuple:
        """Generate mock data for two groups."""
        group1 = np.random.normal(50, 10, size)
        group2 = np.random.normal(52, 10, size)
        return group1, group2

    @staticmethod
    def generate_regression_data(size: int = 100) -> tuple:
        """Generate mock regression data."""
        x = np.random.uniform(0, 100, size)
        y = 2 * x + 50 + np.random.normal(0, 10, size)
        return x, y

    @staticmethod
    def generate_categorical_data(size: int = 50, categories: int = 3) -> np.ndarray:
        """Generate mock categorical data."""
        return np.random.choice([f"cat_{i}" for i in range(categories)], size)

    @staticmethod
    def generate_time_series_data(size: int = 100) -> np.ndarray:
        """Generate mock time series data."""
        trend = np.linspace(0, 10, size)
        noise = np.random.normal(0, 0.5, size)
        return trend + noise

    @staticmethod
    def generate_mixed_data(size: int = 50) -> dict[str, np.ndarray]:
        """Generate mock mixed data types."""
        return {
            "numerical": np.random.normal(50, 10, size),
            "categorical": np.random.choice(["A", "B", "C"], size),
            "boolean": np.random.choice([True, False], size),
        }


# Initialize mock skill database
mock_skill_database = (
    MockSkillData.statistical_methods()
    + MockSkillData.mathematical_implementations()
    + MockSkillData.visualization_skills()
)
