# Stats Solver

An intelligent statistics method recommendation system that uses local LLMs to analyze your data problems and recommend the most appropriate statistical methods and mathematical implementations from the available skill library.

## Features

- **Smart Problem Analysis**: Understands your data problems using natural language processing
- **Skill Classification**: Automatically categorizes skills into "Statistical Methods" and "Mathematical Implementations"
- **Intelligent Matching**: Recommends the best skills based on problem type, data characteristics, and constraints
- **Code Generation**: Automatically generates complete, well-documented Python solutions
- **Local LLM Support**: Works with Ollama and LM Studio for privacy-friendly, offline operation
- **Interactive CLI**: Easy-to-use command-line interface for seamless workflow

## Installation

### Prerequisites

- Python 3.9 or higher
- Local LLM (Ollama or LM Studio)
- pip package manager

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd stats_solver
```

### Step 2: Install Dependencies

```bash
pip install -e .
```

Or install manually:

```bash
pip install httpx pydantic typer rich pyyaml jinja2 numpy scipy matplotlib
```

### Step 3: Configure Local LLM

#### Option A: Using Ollama

1. Install Ollama from https://ollama.ai
2. Pull a model (e.g., Llama 3):
   ```bash
   ollama pull llama3
   ```
3. Verify Ollama is running:
   ```bash
   ollama list
   ```

#### Option B: Using LM Studio

1. Download LM Studio from https://lmstudio.ai
2. Start LM Studio and load a model
3. Configure the API endpoint (default: http://localhost:1234)

### Step 4: Configure Stats Solver

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your LLM configuration:
   ```env
   LLM_PROVIDER=ollama
   LLM_HOST=localhost
   LLM_PORT=11434
   LLM_MODEL=llama3
   ```

3. Configure skill paths in `config/default.yaml`:
   ```yaml
   skills:
     base_paths:
       - ../Exploring Mathematics with Python
       - ../Introduction to Probability
   ```

## Quick Start

### 1. Initialize the System

```bash
stats-solver init
```

This will scan your skill directories and build the index.

### 2. Check LLM Connection

```bash
stats-solver check
```

### 3. Get Recommendations

Interactive mode:
```bash
stats-solver solve
```

Direct mode:
```bash
stats-solver solve "I have test scores from two classes and want to know if there's a significant difference"
```

### 4. Browse Available Skills

```bash
stats-solver skills list
stats-solver skills search --tag hypothesis_test
```

## Usage

### Interactive Mode

The interactive mode guides you through your problem:

```bash
$ stats-solver solve
Describe your data problem: I have customer ratings and want to analyze their distribution

Analyzing your problem...
Problem Type: Descriptive Analysis
Data Types: numerical
Recommended Skills:
  1. Histogram Visualization (score: 0.95)
  2. Descriptive Statistics (score: 0.90)

Generate solution? [y/n]: y
```

### Command Reference

#### `stats-solver init`
Initialize the system and scan skills.

```bash
stats-solver init [--force]
```

#### `stats-solver check`
Check LLM connection and system status.

```bash
stats-solver check
```

#### `stats-solver solve`
Get recommendations and generate solutions.

```bash
stats-solver solve [PROBLEM] [--method METHOD] [--output OUTPUT]
```

Options:
- `PROBLEM`: Your problem description (optional, prompts if not provided)
- `--method`: Method to use (auto, template, llm)
- `--output`: Output format (markdown, json, code)

#### `stats-solver skills`
Manage and browse skills.

```bash
stats-solver skills list [--category CATEGORY]
stats-solver skills search --tag TAG [--data-type TYPE]
stats-solver skills show SKILL_ID
```

#### `stats-solver config`
Manage configuration.

```bash
stats-solver config set KEY VALUE
stats-solver config get KEY
stats-solver config list
```

## Project Structure

```
stats_solver/
├── cli/                 # Command-line interface
├── llm/                 # LLM integration
├── problem/             # Problem analysis
├── recommendation/      # Method recommendation
├── skills/              # Skill indexing
├── solution/            # Code generation
├── prompts/             # LLM prompts
├── config/              # Configuration files
└── templates/           # Code templates
```

## Skill Categories

### Statistical Methods
- Hypothesis testing (t-test, ANOVA, chi-square)
- Regression analysis (linear, logistic, polynomial)
- Classification (clustering, decision trees)
- Time series analysis
- Descriptive statistics

### Mathematical Implementations
- Algorithms (sorting, optimization)
- Numerical methods (integration, differentiation)
- Linear algebra operations
- Sequence generation
- Geometric calculations

## Configuration

### LLM Settings

Edit `config/default.yaml`:

```yaml
llm:
  provider: ollama  # or lm_studio
  host: localhost
  port: 11434
  model: llama3
  timeout: 30
```

### Application Settings

```yaml
app:
  log_level: INFO
  max_recommendations: 5
  output_dir: output
  enable_cache: true
```

### Skill Settings

```yaml
skills:
  base_paths:
    - path/to/skills1
    - path/to/skills2
  auto_scan: true
  auto_classify: true
```

## Examples

### Example 1: Hypothesis Testing

```bash
$ stats-solver solve "Compare test scores between two classes"

Problem: Hypothesis Test
Recommended: Two-Sample T-Test
Confidence: 0.92

[Generated Code]
import numpy as np
from scipy import stats

def two_sample_ttest(sample1, sample2):
    # ... implementation ...
```

### Example 2: Regression Analysis

```bash
$ stats-solver solve "Predict sales based on advertising spend"

Problem: Regression
Recommended: Linear Regression
Confidence: 0.88

[Generated Code]
import numpy as np
from sklearn.linear_model import LinearRegression

def linear_regression(X, y):
    # ... implementation ...
```

### Example 3: Data Visualization

```bash
$ stats-solver solve "Visualize the distribution of my data"

Problem: Visualization
Recommended: Histogram Visualization
Confidence: 0.95

[Generated Code]
import matplotlib.pyplot as plt
import numpy as np

def create_histogram(data):
    # ... implementation ...
```

## Troubleshooting

### LLM Connection Issues

**Problem**: Cannot connect to LLM service

**Solution**:
1. Verify LLM is running: `ollama list` or check LM Studio
2. Check configuration in `.env` file
3. Verify host and port settings

### No Skills Found

**Problem**: No skills available after initialization

**Solution**:
1. Check skill paths in `config/default.yaml`
2. Verify paths are correct and accessible
3. Run `stats-solver init --force` to rescan

### Poor Recommendations

**Problem**: Recommendations don't match your needs

**Solution**:
1. Provide more detailed problem description
2. Ensure skills have proper metadata
3. Use manual skill browsing: `stats-solver skills list`

## Contributing

To add new skills:

1. Create skill file in appropriate directory
2. Add metadata following the schema
3. Run `stats-solver init` to re-index
4. Test with `stats-solver skills show SKILL_ID`

## License

MIT License

## Support

For issues and questions:
- GitHub Issues: <repository-url>/issues
- Documentation: <repository-url>/docs

## Acknowledgments

Built using:
- Ollama for local LLM inference
- Typer for CLI interface
- Rich for terminal formatting
- NumPy, SciPy for numerical computing
- Matplotlib for visualization
