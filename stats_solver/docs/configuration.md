# Stats Solver Configuration Guide

This guide explains how to configure Stats Solver for your environment and use case.

## Table of Contents

1. [Configuration Files](#configuration-files)
2. [Environment Variables](#environment-variables)
3. [LLM Configuration](#llm-configuration)
4. [Skill Configuration](#skill-configuration)
5. [Application Settings](#application-settings)
6. [Feature Flags](#feature-flags)
7. [Advanced Configuration](#advanced-configuration)

## Configuration Files

Stats Solver uses multiple configuration sources, loaded in the following priority order:

1. Environment variables (`.env` file)
2. User configuration (`~/.stats_solver/config.yaml`)
3. Project configuration (`config/default.yaml`)
4. Built-in defaults

### Main Configuration File: `config/default.yaml`

This is the primary configuration file included with the project:

```yaml
# Stats Solver Default Configuration

# LLM Configuration
llm:
  provider: ollama  # Options: ollama, lm_studio
  host: localhost
  port: 11434
  model: llama3
  timeout: 30

# Application Settings
app:
  log_level: INFO
  max_recommendations: 5
  output_dir: output
  enable_cache: true

# Feature Flags
features:
  enable_llm_classification: true
  enable_auto_metadata: true
  enable_code_generation: true
  enable_visualization: true

# Skill Configuration
skills:
  base_paths:
    - ../Exploring Mathematics with Python
    - ../Introduction to Probability
  metadata_cache_path: ../data/skills_metadata
  auto_scan: true
  auto_classify: true

# Recommendation Settings
recommendation:
  default_method: balanced
  min_score_threshold: 0.5
  include_alternatives: true
  max_alternatives: 3

# Code Generation Settings
code_generation:
  include_examples: true
  include_docstrings: true
  include_type_hints: true
  include_error_handling: true
  default_template: auto

# Output Settings
output:
  format: markdown
  include_dependencies: true
  include_sample_data: true
  save_intermediate: false

# Validation Settings
validation:
  check_syntax: true
  check_imports: true
  check_style: false
  strict_mode: false
```

## Environment Variables

Stats Solver configuration is primarily managed through YAML configuration files. Environment variables can be set to override specific settings, but the recommended approach is to edit the configuration files directly.

Key environment variables that can be set:

```bash
# LLM Configuration (overrides config/default.yaml)
LLM_PROVIDER=ollama
LLM_HOST=localhost
LLM_PORT=11434
LLM_MODEL=llama3

# Logging
LOG_LEVEL=INFO
```

## LLM Configuration

### Ollama Configuration

Ollama is the default and recommended LLM provider.

```yaml
llm:
  provider: ollama
  host: localhost
  port: 11434
  model: llama3
  timeout: 30
```

**Available Models:**
- `llama3` - General purpose, good balance of speed and quality
- `llama3:70b` - Higher quality, slower inference
- `mistral` - Lightweight, fast
- `gemma` - Good for code generation
- `codellama` - Specialized for code

**Setting up Ollama:**

1. Install Ollama:
   ```bash
   # macOS
   brew install ollama

   # Linux
   curl -fsSL https://ollama.ai/install.sh | sh

   # Windows
   # Download from https://ollama.ai
   ```

2. Pull a model:
   ```bash
   ollama pull llama3
   ```

3. Verify installation:
   ```bash
   ollama list
   ollama run llama3 "Hello, how are you?"
   ```

### LM Studio Configuration

LM Studio provides a GUI for managing models.

```yaml
llm:
  provider: lm_studio
  host: localhost
  port: 1234
  model: your-model-name
  timeout: 30
```

**Setting up LM Studio:**

1. Download LM Studio from https://lmstudio.ai
2. Start LM Studio application
3. Download or load a model
4. Start the server from the server tab
5. Note the API endpoint (default: `http://localhost:1234`)

### Custom LLM Provider

You can add a custom LLM provider by implementing the `LLMProvider` interface:

```python
from stats_solver.llm.base import LLMProvider, LLMMessage, LLMResponse

class CustomProvider(LLMProvider):
    def __init__(self, host: str, port: int, model: str):
        super().__init__(host, port, model)

    def generate(self, messages: List[LLMMessage]) -> LLMResponse:
        # Your implementation
        pass
```

## Skill Configuration

### Base Paths

Configure where Stats Solver looks for skills:

```yaml
skills:
  base_paths:
    - /path/to/skills1
    - /path/to/skills2
    - ../relative/path
```

**Supported path types:**
- Absolute paths: `/home/user/skills`
- Relative paths: `../skills`, `./my_skills`
- Windows paths: `C:\\Users\\skills`

### Metadata Cache

Configure where skill metadata is cached:

```yaml
skills:
  metadata_cache_path: ../data/skills_metadata
```

The default metadata cache path is relative to the `stats_solver/` directory and points to `data/skills_metadata/` at the project root.

### Auto-Scan and Auto-Classify

```yaml
skills:
  auto_scan: true      # Automatically scan base paths on init
  auto_classify: true  # Automatically classify skills using LLM
```

## Application Settings

### Log Level

Control logging verbosity:

```yaml
app:
  log_level: DEBUG  # Options: DEBUG, INFO, WARNING, ERROR
```

- `DEBUG`: Detailed information for debugging
- `INFO`: General informational messages (default)
- `WARNING`: Warning messages
- `ERROR`: Error messages only

### Output Directory

Where generated solutions are saved:

```yaml
app:
  output_dir: output  # Relative or absolute path
```

### Caching

Enable/disable caching for performance:

```yaml
app:
  enable_cache: true
```

## Feature Flags

Control which features are enabled:

```yaml
features:
  enable_llm_classification: true    # Use LLM for skill classification
  enable_auto_metadata: true         # Auto-generate skill metadata
  enable_code_generation: true       # Generate solution code
  enable_visualization: true         # Generate visualization code
```

## Recommendation Settings

### Recommendation Method

Choose the algorithm for ranking recommendations:

```yaml
recommendation:
  default_method: balanced  # Options:
                             #   - weighted_score: Weighted sum of factors
                             #   - confidence_score: Based on LLM confidence
                             #   - balanced: Balanced approach (recommended)
                             #   - popularity: Based on skill popularity
```

### Score Threshold

Minimum score for recommendations:

```yaml
recommendation:
  min_score_threshold: 0.5  # 0.0 to 1.0
```

### Alternatives

Show alternative suggestions:

```yaml
recommendation:
  include_alternatives: true
  max_alternatives: 3
```

## Code Generation Settings

### Code Quality Options

```yaml
code_generation:
  include_examples: true         # Include example usage
  include_docstrings: true       # Include NumPy-style docstrings
  include_type_hints: true       # Include type annotations
  include_error_handling: true   # Include error handling code
```

### Template Selection

```yaml
code_generation:
  default_template: auto  # Options:
                          #   - auto: Automatically choose based on skill type
                          #   - template: Use code templates only
                          #   - llm: Use LLM for code generation
```

## Output Settings

### Output Format

```yaml
output:
  format: markdown  # Options: markdown, json, text, code
```

### Include in Output

```yaml
output:
  include_dependencies: true    # Include required packages
  include_sample_data: true     # Include sample data
  save_intermediate: false      # Save intermediate results
```

## Validation Settings

### Code Validation

```yaml
validation:
  check_syntax: true      # Validate Python syntax
  check_imports: true     # Check if imports are available
  check_style: false      # Check code style (PEP 8)
  strict_mode: false      # Fail on any validation error
```

## Advanced Configuration

### User-Specific Configuration

Create a user-specific config file at `~/.stats_solver/config.yaml`:

```yaml
# Override defaults for your user
llm:
  model: llama3:70b  # Use larger model for better quality

app:
  log_level: DEBUG
```

### Programmatic Configuration

You can also configure programmatically:

```python
from stats_solver import StatsSolver

solver = StatsSolver(
    llm_provider="ollama",
    llm_model="llama3",
    skill_paths=["/custom/skills"],
    max_recommendations=10
)
```

### Configuration Validation

Validate your configuration:

```bash
skills-applier config validate
```

### Viewing Current Configuration

```bash
skills-applier config list
```

### Setting Configuration Values

```bash
skills-applier config set llm.model mistral
skills-applier config set app.log_level DEBUG
```

## Troubleshooting Configuration

### Issue: LLM Connection Fails

**Symptoms**: Connection timeout or refused

**Solutions:**
1. Verify LLM is running: `ollama list` or check LM Studio
2. Check host and port in configuration
3. Increase timeout value
4. Check firewall settings

### Issue: Skills Not Found

**Symptoms**: No skills available after initialization

**Solutions:**
1. Verify skill paths are correct
2. Check file permissions
3. Run `skills-applier init`
4. Enable `DEBUG` logging for more details

### Issue: Poor Recommendations

**Symptoms**: Recommendations don't match problem

**Solutions:**
1. Increase `min_score_threshold`
2. Try different `default_method`
3. Provide more detailed problem description
4. Enable `enable_llm_classification` for better analysis

### Issue: Code Generation Fails

**Symptoms**: Generated code has errors

**Solutions:**
1. Enable `strict_mode` to catch issues early
2. Increase `llm_timeout` for larger models
3. Try different `default_template`
4. Use smaller model for faster generation

## Best Practices

1. **Start Simple**: Begin with default configuration and adjust as needed
2. **Use Caching**: Enable caching for better performance
3. **Monitor Logs**: Set `log_level: DEBUG` when troubleshooting
4. **Validate Configuration**: Run `skills-applier config validate` after changes
5. **Backup Config**: Keep a copy of working configuration
6. **Document Changes**: Comment custom configurations

## Configuration Reference

For a complete list of all configuration options, see:

- `config/default.yaml` - Full configuration with comments
- `stats_solver/config/__init__.py` - Configuration schema and defaults
- Environment variables reference - See `.env.example`

## Support

For configuration help:

- GitHub Issues: https://github.com/boltomli/skills-applier/issues
- Documentation: See `stats_solver/docs/` directory
- Community: https://github.com/boltomli/skills-applier/discussions
