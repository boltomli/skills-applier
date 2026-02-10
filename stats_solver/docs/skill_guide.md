# Adding Skills to Stats Solver

This guide explains how to add new statistical methods and mathematical implementations to the Stats Solver skill library.

## Table of Contents

1. [Understanding Skills](#understanding-skills)
2. [Skill File Structure](#skill-file-structure)
3. [Skill Metadata](#skill-metadata)
4. [Creating a New Skill](#creating-a-new-skill)
5. [Testing Skills](#testing-skills)
6. [Best Practices](#best-practices)
7. [Examples](#examples)

## Understanding Skills

Skills are reusable Python implementations that perform statistical analysis, mathematical computations, or data visualization. Stats Solver uses skills to:

- Solve specific data analysis problems
- Generate complete Python solutions
- Provide building blocks for complex workflows

### Skill Categories

**Statistical Methods**
- Hypothesis tests (t-test, ANOVA, chi-square)
- Regression analysis (linear, logistic, polynomial)
- Classification algorithms
- Time series analysis
- Descriptive statistics

**Mathematical Implementations**
- Numerical methods (integration, differentiation)
- Optimization algorithms
- Linear algebra operations
- Sequence generation
- Geometric calculations

## Skill File Structure

A skill consists of two parts:

1. **Implementation File** - The actual Python code
2. **Metadata File** - JSON description of the skill

### Example Directory Structure

```
skills/
├── statistical_methods/
│   ├── t_test.py
│   ├── t_test.json
│   ├── anova.py
│   └── anova.json
├── mathematical_implementations/
│   ├── fibonacci.py
│   ├── fibonacci.json
│   └── matrix_operations.py
└── metadata_cache/
    └── all_skills.json
```

## Skill Metadata

Metadata describes what a skill does, how it works, and when to use it. Create a `.json` file alongside your skill implementation.

### Required Fields

```json
{
  "skill_id": "unique-skill-identifier",
  "name": "Human Readable Name",
  "description": "Brief description of what the skill does",
  "category": "statistical_method"
}
```

### Optional Fields

```json
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
  "prerequisites": ["descriptive-statistics"],
  "assumptions": ["Samples are independent", "Normality assumption"],
  "parameters": [
    {
      "name": "sample1",
      "type": "array-like",
      "description": "First sample data",
      "required": true,
      "default": null
    }
  ],
  "input_requirements": {
    "min_samples": 2,
    "min_observations": 5
  },
  "output_format": {
    "type": "dictionary",
    "fields": ["statistic", "pvalue"]
  },
  "usage_examples": [
    "Compare test scores between two classes",
    "Test treatment vs control group"
  ],
  "confidence_score": 0.95,
  "popularity": 0.9,
  "last_updated": "2026-02-10"
}
```

### Metadata Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `skill_id` | string | Yes | Unique identifier (use kebab-case) |
| `name` | string | Yes | Human-readable name |
| `description` | string | Yes | Brief description (1-2 sentences) |
| `category` | string | Yes | `statistical_method` or `mathematical_implementation` |
| `subcategory` | string | No | More specific category (e.g., `hypothesis_test`) |
| `tags` | array | No | List of relevant tags for matching |
| `data_types` | array | No | Data types skill works with (`numerical`, `categorical`, etc.) |
| `problem_types` | array | No | Types of problems skill solves |
| `output_types` | array | No | Types of output skill produces |
| `complexity` | string | No | `simple`, `moderate`, or `complex` |
| `dependencies` | array | No | Required Python packages |
| `prerequisites` | array | No | Skills that should be run first |
| `assumptions` | array | No | Statistical/mathematical assumptions |
| `parameters` | array | No | Function parameters with descriptions |
| `input_requirements` | object | No | Minimum/maximum input requirements |
| `output_format` | object | No | Description of output structure |
| `usage_examples` | array | No | Example use cases |
| `confidence_score` | number | No | LLM confidence in classification (0-1) |
| `popularity` | number | No | How commonly used (0-1) |
| `last_updated` | string | No | Last update date (ISO 8601) |

## Creating a New Skill

### Step 1: Implement the Skill

Create a Python file with your implementation:

```python
# t_test.py
import numpy as np
from scipy import stats
from typing import Dict, Any, Union, List

def two_sample_ttest(sample1: Union[List, np.ndarray],
                     sample2: Union[List, np.ndarray],
                     equal_var: bool = True) -> Dict[str, float]:
    """
    Perform an independent two-sample t-test.

    This function tests the null hypothesis that two independent samples
    have identical average (expected) values.

    Parameters
    ----------
    sample1 : array-like
        First sample data
    sample2 : array-like
        Second sample data
    equal_var : bool, optional
        Assume equal variances (default: True)
        If False, use Welch's t-test

    Returns
    -------
    result : dict
        Dictionary containing:
        - 'statistic' : float
            The calculated t-statistic
        - 'pvalue' : float
            The two-tailed p-value
        - 'degrees_of_freedom' : int
            Degrees of freedom

    Raises
    ------
    ValueError
        If either sample is empty or has insufficient data

    Examples
    --------
    >>> data1 = [85, 90, 78, 92, 88]
    >>> data2 = [82, 88, 75, 90, 85]
    >>> result = two_sample_ttest(data1, data2)
    >>> print(f"T-statistic: {result['statistic']:.4f}")
    >>> print(f"P-value: {result['pvalue']:.4f}")

    Notes
    -----
    The t-test assumes:
    - Samples are independent
    - Data is approximately normally distributed
    - Equal variances between samples (unless using Welch's test)

    References
    ----------
    .. [1] Student, "The probable error of a mean", Biometrika, 1908.
    """
    # Convert to numpy arrays
    sample1 = np.asarray(sample1)
    sample2 = np.asarray(sample2)

    # Input validation
    if len(sample1) < 2 or len(sample2) < 2:
        raise ValueError("Each sample must have at least 2 observations")

    # Perform t-test
    statistic, pvalue = stats.ttest_ind(sample1, sample2, equal_var=equal_var)

    # Calculate degrees of freedom
    n1, n2 = len(sample1), len(sample2)
    degrees_of_freedom = n1 + n2 - 2

    return {
        'statistic': float(statistic),
        'pvalue': float(pvalue),
        'degrees_of_freedom': int(degrees_of_freedom)
    }


if __name__ == "__main__":
    # Example usage
    np.random.seed(42)
    data1 = np.random.normal(75, 10, 30)
    data2 = np.random.normal(80, 10, 30)

    result = two_sample_ttest(data1, data2)

    print("Two-Sample T-Test Results:")
    print(f"T-statistic: {result['statistic']:.4f}")
    print(f"P-value: {result['pvalue']:.4f}")
    print(f"Degrees of Freedom: {result['degrees_of_freedom']}")

    # Interpretation
    alpha = 0.05
    if result['pvalue'] < alpha:
        print("\nResult is statistically significant (reject null hypothesis)")
    else:
        print("\nResult is not statistically significant (fail to reject null hypothesis)")
```

### Step 2: Create Metadata

Create a `.json` file with the same base name:

```json
{
  "skill_id": "t-test-two-sample",
  "name": "Two-Sample T-Test",
  "description": "Performs an independent two-sample t-test to determine if there is a significant difference between the means of two groups.",
  "category": "statistical_method",
  "subcategory": "hypothesis_test",
  "tags": [
    "hypothesis_testing",
    "mean_comparison",
    "two_groups",
    "parametric",
    "independent_samples"
  ],
  "data_types": ["numerical"],
  "problem_types": ["hypothesis_test", "comparison"],
  "output_types": ["number", "statistic", "pvalue"],
  "complexity": "simple",
  "dependencies": ["numpy", "scipy"],
  "prerequisites": ["descriptive-statistics", "normality-test"],
  "assumptions": [
    "Samples are independent",
    "Data is approximately normally distributed",
    "Equal variances between groups (or use Welch's t-test)",
    "Continuous data"
  ],
  "parameters": [
    {
      "name": "sample1",
      "type": "array-like",
      "description": "First sample data",
      "required": true,
      "default": null
    },
    {
      "name": "sample2",
      "type": "array-like",
      "description": "Second sample data",
      "required": true,
      "default": null
    },
    {
      "name": "equal_var",
      "type": "bool",
      "description": "Assume equal variances. If False, use Welch's t-test.",
      "required": false,
      "default": true
    }
  ],
  "input_requirements": {
    "min_samples": 2,
    "min_observations": 2,
    "max_samples": null,
    "max_observations": null
  },
  "output_format": {
    "type": "dictionary",
    "fields": [
      {
        "name": "statistic",
        "type": "float",
        "description": "The calculated t-statistic"
      },
      {
        "name": "pvalue",
        "type": "float",
        "description": "The two-tailed p-value"
      },
      {
        "name": "degrees_of_freedom",
        "type": "int",
        "description": "Degrees of freedom"
      }
    ]
  },
  "usage_examples": [
    "Compare test scores between two classes",
    "Test if treatment group differs from control group",
    "Compare product ratings from two different sources",
    "Analyze A/B test results"
  ],
  "confidence_score": 0.95,
  "popularity": 0.9,
  "last_updated": "2026-02-10"
}
```

### Step 3: Place Files in Correct Location

Put the files in the appropriate skill directory:

```
stats_solver/skills/
├── statistical_methods/
│   ├── t_test.py          ← Your implementation
│   └── t_test.json        ← Your metadata
```

Or add to your custom skill paths configured in `config/default.yaml`.

### Step 4: Re-index Skills

Run the initialization command to update the skill index:

```bash
stats-solver init --force
```

### Step 5: Verify the Skill

Check that the skill is recognized:

```bash
stats-solver skills show t-test-two-sample
```

Or search for it:

```bash
stats-solver skills search --tag hypothesis_testing
```

## Testing Skills

### Manual Testing

Test your skill directly:

```python
from skills.statistical_methods.t_test import two_sample_ttest

# Test with sample data
import numpy as np
data1 = np.array([1, 2, 3, 4, 5])
data2 = np.array([2, 3, 4, 5, 6])
result = two_sample_ttest(data1, data2)
print(result)
```

### Automated Testing

Create a test file:

```python
# tests/test_t_test.py
import pytest
import numpy as np
from skills.statistical_methods.t_test import two_sample_ttest

def test_basic_functionality():
    """Test basic t-test functionality."""
    data1 = [1, 2, 3, 4, 5]
    data2 = [2, 3, 4, 5, 6]
    result = two_sample_ttest(data1, data2)

    assert 'statistic' in result
    assert 'pvalue' in result
    assert isinstance(result['statistic'], float)
    assert isinstance(result['pvalue'], float)

def test_input_validation():
    """Test input validation."""
    with pytest.raises(ValueError):
        two_sample_ttest([1], [2, 3])  # Too few observations

def test_known_result():
    """Test against known result."""
    # Known data with known result
    data1 = [85, 90, 78, 92, 88]
    data2 = [82, 88, 75, 90, 85]
    result = two_sample_ttest(data1, data2)

    # Result should be reasonable
    assert 0.0 <= result['pvalue'] <= 1.0
```

Run tests:

```bash
pytest tests/test_t_test.py -v
```

## Best Practices

### Code Quality

1. **Follow PEP 8**: Use standard Python style guidelines
2. **Type Hints**: Include type annotations for function parameters
3. **Docstrings**: Use NumPy-style docstrings with full sections
4. **Error Handling**: Validate inputs and provide clear error messages
5. **Examples**: Include working examples in docstrings

### Metadata Quality

1. **Be Descriptive**: Provide clear, concise descriptions
2. **Use Standard Tags**: Use commonly understood tags
3. **List Dependencies**: Include all required packages
4. **Document Assumptions**: Be explicit about assumptions
5. **Provide Examples**: Include real-world use cases

### Performance

1. **Use NumPy**: Vectorize operations when possible
2. **Avoid Loops**: Use built-in functions instead
3. **Cache Results**: Consider memoization for expensive operations
4. **Profile Code**: Identify and optimize bottlenecks

### Documentation

1. **Explain Purpose**: Clearly state what the skill does
2. **Describe Parameters**: Document all parameters with types
3. **Show Usage**: Provide examples showing how to use the skill
4. **Cite References**: Include academic references for statistical methods
5. **Note Limitations**: Be honest about limitations and edge cases

## Examples

### Example 1: Simple Mathematical Function

```python
# fibonacci.py
def fibonacci(n: int) -> List[int]:
    """
    Generate the first n Fibonacci numbers.

    Parameters
    ----------
    n : int
        Number of Fibonacci numbers to generate

    Returns
    -------
    List[int]
        List of Fibonacci numbers

    Examples
    --------
    >>> fibonacci(10)
    [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    """
    if n <= 0:
        return []
    elif n == 1:
        return [0]

    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])

    return fib
```

```json
{
  "skill_id": "fibonacci-sequence",
  "name": "Fibonacci Sequence Generator",
  "description": "Generates Fibonacci numbers using an iterative approach.",
  "category": "mathematical_implementation",
  "subcategory": "sequence",
  "tags": ["sequence", "recursion", "iteration", "algorithm"],
  "data_types": ["numerical"],
  "problem_types": ["computation", "generation"],
  "output_types": ["array", "number"],
  "complexity": "simple",
  "dependencies": [],
  "assumptions": ["Input is a positive integer"],
  "parameters": [
    {
      "name": "n",
      "type": "int",
      "description": "Number of Fibonacci numbers to generate",
      "required": true
    }
  ],
  "usage_examples": [
    "Generate first N Fibonacci numbers",
    "Demonstrate sequence algorithms",
    "Calculate nth Fibonacci number"
  ],
  "popularity": 0.85
}
```

### Example 2: Statistical Method with Visualization

```python
# histogram_analysis.py
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

def histogram_analysis(data: np.ndarray,
                       bins: int = 30,
                       show_stats: bool = True) -> plt.Figure:
    """
    Create a histogram with statistical overlays.

    Parameters
    ----------
    data : np.ndarray
        Input data to analyze
    bins : int, optional
        Number of histogram bins (default: 30)
    show_stats : bool, optional
        Show mean and standard deviation (default: True)

    Returns
    -------
    plt.Figure
        The generated figure

    Examples
    --------
    >>> import numpy as np
    >>> data = np.random.normal(0, 1, 1000)
    >>> fig = histogram_analysis(data)
    >>> plt.show()
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # Create histogram
    n, bins_edges, patches = ax.hist(data, bins=bins, edgecolor='black', alpha=0.7)

    # Add statistics
    if show_stats:
        mean = np.mean(data)
        std = np.std(data)

        ax.axvline(mean, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean:.2f}')
        ax.axvline(mean + std, color='green', linestyle='--', linewidth=2, label=f'+1 SD: {mean + std:.2f}')
        ax.axvline(mean - std, color='green', linestyle='--', linewidth=2, label=f'-1 SD: {mean - std:.2f}')

    ax.set_xlabel('Value')
    ax.set_ylabel('Frequency')
    ax.set_title('Distribution Analysis')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig
```

## Troubleshooting

### Skill Not Recognized

**Problem**: Skill doesn't appear after running `stats-solver init`

**Solutions**:
1. Verify metadata file exists and has valid JSON
2. Check file names match (skill.py and skill.json)
3. Ensure files are in a configured skill path
4. Run with `--force` flag to rescan

### Metadata Validation Errors

**Problem**: Metadata validation fails

**Solutions**:
1. Check JSON syntax using online validator
2. Ensure all required fields are present
3. Verify field types match schema
4. Check for trailing commas in JSON

### Code Import Errors

**Problem**: Cannot import skill code

**Solutions**:
1. Verify dependencies are listed in metadata
2. Install missing dependencies
3. Check Python syntax is valid
4. Ensure file is in Python path

## Support

For help with adding skills:

- GitHub Issues: <repository-url>/issues
- Documentation: <repository-url>/docs
- Community: <community-url>
