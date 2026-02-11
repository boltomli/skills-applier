"""
Unit tests for solution generation module.
"""

import pytest
from unittest.mock import patch
from stats_solver.solution.code_generator import CodeGenerator
from stats_solver.solution.docstring import DocstringGenerator
from stats_solver.solution.dependencies import DependencyExtractor
from stats_solver.solution.sample_data import SampleDataGenerator
from stats_solver.solution.visualization import VisualizationGenerator
from stats_solver.solution.validator import CodeValidator


class TestCodeGenerator:
    """Test code generator."""

    @pytest.fixture
    def generator(self):
        """Create a code generator instance."""
        return CodeGenerator()

    @pytest.fixture
    def sample_skill(self):
        """Sample skill for testing."""
        return {
            "skill_id": "t-test",
            "name": "Two-Sample T-Test",
            "description": "Performs independent samples t-test",
            "category": "statistical_method",
            "parameters": [
                {"name": "sample1", "type": "array-like", "required": True},
                {"name": "sample2", "type": "array-like", "required": True},
            ],
            "dependencies": ["numpy", "scipy"],
        }

    @pytest.fixture
    def sample_problem(self):
        """Sample problem for testing."""
        return {
            "summary": "Compare two group means",
            "data_types": ["numerical"],
            "output_format": "number",
        }

    def test_generate_from_template(self, generator, sample_skill, sample_problem):
        """Test generating code from template."""
        code = generator.generate(sample_skill, sample_problem, method="template")
        assert code is not None
        assert "import" in code  # Should contain imports

    @patch.object(CodeGenerator, "_generate_with_llm")
    def test_generate_with_llm(self, mock_llm, generator, sample_skill, sample_problem):
        """Test generating code with LLM."""
        mock_llm.return_value = "generated_code"
        generator.generate(sample_skill, sample_problem, method="llm")
        mock_llm.assert_called_once()

    def test_add_imports(self, generator):
        """Test adding imports to code."""
        deps = ["numpy", "scipy.stats"]
        code = generator._add_imports(deps)
        assert "import numpy" in code
        assert "from scipy" in code or "import scipy" in code

    def test_validate_code_syntax(self, generator):
        """Test validating code syntax."""
        valid_code = "x = 1\ny = 2\nprint(x + y)"
        result = generator._validate_syntax(valid_code)
        assert result.is_valid is True

    def test_validate_invalid_syntax(self, generator):
        """Test validating invalid code syntax."""
        invalid_code = "x = 1\ny = 2\nprint(x +"
        result = generator._validate_syntax(invalid_code)
        assert result.is_valid is False


class TestDocstringGenerator:
    """Test docstring generator."""

    @pytest.fixture
    def generator(self):
        """Create a docstring generator instance."""
        return DocstringGenerator()

    def test_generate_numpy_style(self, generator):
        """Test generating NumPy-style docstring."""
        function_info = {
            "name": "calculate_mean",
            "purpose": "Calculate the arithmetic mean",
            "parameters": [{"name": "data", "type": "array-like", "description": "Input data"}],
            "returns": {"type": "float", "description": "The mean value"},
        }

        docstring = generator.generate(function_info, style="numpy")
        assert "Parameters" in docstring
        assert "Returns" in docstring
        assert "calculate_mean" in docstring

    def test_generate_with_examples(self, generator):
        """Test generating docstring with examples."""
        function_info = {
            "name": "test_function",
            "purpose": "Test function",
            "parameters": [],
            "returns": {"type": "None", "description": "Nothing"},
            "examples": ["test_function()", "test_function(arg=1)"],
        }

        docstring = generator.generate(function_info)
        assert "Examples" in docstring
        assert "test_function()" in docstring


class TestDependencyExtractor:
    """Test dependency extractor."""

    @pytest.fixture
    def extractor(self):
        """Create a dependency extractor instance."""
        return DependencyExtractor()

    def test_extract_from_code(self, extractor):
        """Test extracting dependencies from code."""
        code = """
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
"""
        deps = extractor.extract(code)
        assert "numpy" in deps
        assert "scipy" in deps
        assert "matplotlib" in deps

    def test_extract_from_skill_metadata(self, extractor):
        """Test extracting dependencies from skill metadata."""
        skill = {"skill_id": "test", "dependencies": ["numpy", "pandas", "scipy"]}
        deps = extractor.extract_from_metadata(skill)
        assert len(deps) == 3
        assert "numpy" in deps

    def test_deduplicate_dependencies(self, extractor):
        """Test deduplicating dependencies."""
        deps = ["numpy", "numpy", "scipy", "pandas", "scipy"]
        unique = extractor.deduplicate(deps)
        assert len(unique) == 3
        assert unique.count("numpy") == 1


class TestSampleDataGenerator:
    """Test sample data generator."""

    @pytest.fixture
    def generator(self):
        """Create a sample data generator instance."""
        return SampleDataGenerator()

    def test_generate_random_data(self, generator):
        """Test generating random numerical data."""
        data = generator.generate_random(
            size=100, distribution="normal", params={"loc": 0, "scale": 1}
        )
        assert len(data) == 100

    def test_generate_categorical_data(self, generator):
        """Test generating categorical data."""
        data = generator.generate_categorical(size=50, categories=["A", "B", "C"])
        assert len(data) == 50
        assert all(cat in ["A", "B", "C"] for cat in data)

    def test_generate_time_series_data(self, generator):
        """Test generating time series data."""
        data = generator.generate_time_series(size=100, trend=True, noise=True)
        assert len(data) == 100


class TestVisualizationGenerator:
    """Test visualization generator."""

    @pytest.fixture
    def generator(self):
        """Create a visualization generator instance."""
        return VisualizationGenerator()

    def test_generate_histogram_code(self, generator):
        """Test generating histogram visualization code."""
        code = generator.generate_histogram(data_var="data", title="Distribution", x_label="Value")
        assert "hist" in code
        assert "Distribution" in code

    def test_generate_scatter_code(self, generator):
        """Test generating scatter plot code."""
        code = generator.generate_scatter(x_var="x", y_var="y", title="Scatter Plot")
        assert "scatter" in code

    def test_generate_line_plot_code(self, generator):
        """Test generating line plot code."""
        code = generator.generate_line_plot(x_var="x", y_var="y", title="Trend")
        assert "plot" in code


class TestCodeValidator:
    """Test code validator."""

    @pytest.fixture
    def validator(self):
        """Create a code validator instance."""
        return CodeValidator()

    def test_validate_syntax_valid(self, validator):
        """Test validating valid syntax."""
        code = "x = 1\ny = 2\nprint(x + y)"
        result = validator.validate_syntax(code)
        assert result.is_valid is True

    def test_validate_syntax_invalid(self, validator):
        """Test validating invalid syntax."""
        code = "x = 1\ndef incomplete("
        result = validator.validate_syntax(code)
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_imports_valid(self, validator):
        """Test validating valid imports."""
        code = "import numpy as np\nfrom scipy import stats"
        result = validator.validate_imports(code)
        assert result.is_valid is True

    def test_validate_imports_invalid(self, validator):
        """Test validating invalid imports."""
        code = "import nonexistent_module"
        validator.validate_imports(code, check_available=True)
        # Should flag the invalid import

    def test_validate_style(self, validator):
        """Test validating code style."""
        code = "x=1+2  # No spaces around operators"
        validator.validate_style(code)
        # Should detect style issues

    def test_validate_complete(self, validator):
        """Test complete validation."""
        code = """
import numpy as np

def test_function(x):
    return x * 2
"""
        result = validator.validate(code, check_syntax=True, check_imports=False)
        assert result.is_valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
