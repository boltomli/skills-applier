"""
Unit tests for problem analysis module.
"""

import pytest
from unittest.mock import patch
from stats_solver.problem.extractor import ProblemExtractor
from stats_solver.problem.data_types import DataTypeDetector
from stats_solver.problem.classifier import ProblemClassifier
from stats_solver.problem.constraints import ConstraintExtractor
from stats_solver.problem.output_format import OutputFormatRecognizer


class TestDataTypeDetector:
    """Test data type detector."""

    @pytest.fixture
    def detector(self):
        """Create a data type detector instance."""
        return DataTypeDetector()

    def test_detect_numerical_data(self, detector):
        """Test detecting numerical data."""
        description = "I have numerical test scores from students"
        result = detector.detect(description)
        assert "numerical" in result

    def test_detect_categorical_data(self, detector):
        """Test detecting categorical data."""
        description = "I have survey responses with categories"
        result = detector.detect(description)
        assert "categorical" in result

    def test_detect_time_series_data(self, detector):
        """Test detecting time series data."""
        description = "I have stock prices over time"
        result = detector.detect(description)
        assert "time_series" in result

    def test_detect_mixed_data(self, detector):
        """Test detecting mixed data types."""
        description = "I have both numerical scores and categorical responses"
        result = detector.detect(description)
        assert "numerical" in result
        assert "categorical" in result


class TestProblemClassifier:
    """Test problem classifier."""

    @pytest.fixture
    def classifier(self):
        """Create a problem classifier instance."""
        return ProblemClassifier()

    def test_classify_hypothesis_test(self, classifier):
        """Test classifying hypothesis test problems."""
        description = "I want to test if there's a significant difference between two groups"
        result = classifier.classify(description)
        assert result.problem_type == "hypothesis_test"
        assert "two_sample_test" in result.subtypes

    def test_classify_regression(self, classifier):
        """Test classifying regression problems."""
        description = "I want to predict sales based on advertising spend"
        result = classifier.classify(description)
        assert result.problem_type == "regression"

    def test_classify_classification(self, classifier):
        """Test classifying classification problems."""
        description = "I want to classify customers into segments"
        result = classifier.classify(description)
        assert result.problem_type == "classification"

    def test_classify_descriptive(self, classifier):
        """Test classifying descriptive statistics problems."""
        description = "I want to analyze the distribution of my data"
        result = classifier.classify(description)
        assert result.problem_type == "descriptive"

    def test_determine_complexity_simple(self, classifier):
        """Test determining complexity for simple problems."""
        description = "Calculate the mean of this dataset"
        result = classifier.classify(description)
        assert result.complexity_level == "simple"

    def test_determine_complexity_complex(self, classifier):
        """Test determining complexity for complex problems."""
        description = "I want to perform multivariate analysis with interaction effects and non-linear transformations"
        result = classifier.classify(description)
        assert result.complexity_level == "complex"


class TestConstraintExtractor:
    """Test constraint extractor."""

    @pytest.fixture
    def extractor(self):
        """Create a constraint extractor instance."""
        return ConstraintExtractor()

    def test_extract_sample_size_constraint(self, extractor):
        """Test extracting sample size constraint."""
        description = "I have 30 samples"
        result = extractor.extract(description)
        assert "sample_size" in result.constraints
        assert result.constraints["sample_size"] == 30

    def test_extract_output_format_constraint(self, extractor):
        """Test extracting output format constraint."""
        description = "I need a plot showing the results"
        result = extractor.extract(description)
        assert "output_format" in result.constraints
        assert "plot" in result.constraints["output_format"]

    def test_extract_accuracy_constraint(self, extractor):
        """Test extracting accuracy constraint."""
        description = "I need high accuracy results"
        result = extractor.extract(description)
        assert "accuracy" in result.constraints


class TestOutputFormatRecognizer:
    """Test output format recognizer."""

    @pytest.fixture
    def recognizer(self):
        """Create an output format recognizer instance."""
        return OutputFormatRecognizer()

    def test_recognize_plot_output(self, recognizer):
        """Test recognizing plot output format."""
        description = "Show me a visualization"
        result = recognizer.recognize(description)
        assert "plot" in result.formats

    def test_recognize_table_output(self, recognizer):
        """Test recognizing table output format."""
        description = "Display results in a table"
        result = recognizer.recognize(description)
        assert "table" in result.formats

    def test_recognize_number_output(self, recognizer):
        """Test recognizing number output format."""
        description = "Calculate the p-value"
        result = recognizer.recognize(description)
        assert "number" in result.formats

    def test_recognize_text_output(self, recognizer):
        """Test recognizing text output format."""
        description = "Explain the results"
        result = recognizer.recognize(description)
        assert "text" in result.formats


class TestProblemExtractor:
    """Test problem extractor."""

    @pytest.fixture
    def extractor(self):
        """Create a problem extractor instance."""
        return ProblemExtractor()

    def test_extract_summary(self, extractor):
        """Test extracting problem summary."""
        description = "I have test scores from two classes and want to know if there's a difference"
        result = extractor.extract(description)
        assert result.summary is not None
        assert len(result.summary) > 0

    def test_extract_features(self, extractor):
        """Test extracting problem features."""
        description = "I have numerical test scores and want to perform a hypothesis test"
        result = extractor.extract(description)
        assert len(result.data_types) > 0
        assert result.problem_type is not None

    def test_extract_assumptions(self, extractor):
        """Test extracting problem assumptions."""
        description = "I have test scores and assume they are normally distributed"
        result = extractor.extract(description)
        assert "normality" in str(result.assumptions).lower()

    @patch.object(ProblemExtractor, "_use_llm_extraction")
    def test_llm_fallback(self, mock_llm, extractor):
        """Test using LLM extraction as fallback."""
        mock_llm.return_value = {
            "summary": "LLM extracted summary",
            "problem_type": "hypothesis_test",
            "confidence": 0.9,
        }

        description = "Complex problem requiring deeper analysis"
        result = extractor.extract(description)

        mock_llm.assert_called_once()
        assert result.summary is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
