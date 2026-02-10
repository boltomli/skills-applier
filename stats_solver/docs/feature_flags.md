# Feature Flags

Stats Solver uses feature flags to enable/disable specific functionality. This allows you to:

- Control which features are available
- Disable features that require LLM when not available
- Test individual components in isolation
- Gradually roll out new features

## Configuration Location

Feature flags are configured in `config/default.yaml` or can be overridden via environment variables:

```yaml
features:
  enable_llm_classification: true
  enable_auto_metadata: true
  enable_code_generation: true
  enable_visualization: true
```

## Available Feature Flags

### `enable_llm_classification`

**Default:** `true`

**Description:** Controls whether the LLM is used for automatic skill classification.

**When to disable:**
- LLM service is not available
- You want to use only rule-based classification
- Reducing API costs or latency

**Impact when disabled:**
- Skills will be classified using rule-based heuristics only
- Classification accuracy may be reduced
- Auto-generated metadata may be less accurate

**Environment variable:** `ENABLE_LLM_CLASSIFICATION`

**Example:**
```bash
# Disable LLM classification
export ENABLE_LLM_CLASSIFICATION=false
stats-solver init
```

### `enable_auto_metadata`

**Default:** `true`

**Description:** Controls whether metadata is automatically generated for skills.

**When to disable:**
- You want to use manually curated metadata only
- Reducing initialization time
- LLM service is not available

**Impact when disabled:**
- Skills without explicit metadata files will not have metadata
- Search and recommendation accuracy may be reduced
- Manual metadata files will still be used if available

**Environment variable:** `ENABLE_AUTO_METADATA`

**Example:**
```bash
# Disable auto metadata generation
export ENABLE_AUTO_METADATA=false
stats-solver init
```

### `enable_code_generation`

**Default:** `true`

**Description:** Controls whether code generation is available.

**When to disable:**
- You only want recommendations without code
- LLM service is not available
- Reducing resource usage

**Impact when disabled:**
- `stats-solver solve` will only show recommendations
- No Python code will be generated
- Skill descriptions and metadata will still be shown

**Environment variable:** `ENABLE_CODE_GENERATION`

**Example:**
```bash
# Disable code generation
export ENABLE_CODE_GENERATION=false
stats-solver solve "analyze my data"
# Output: Recommendations only, no code
```

### `enable_visualization`

**Default:** `true`

**Description:** Controls whether visualization code is generated.

**When to disable:**
- You don't need visualizations
- Reducing generated code size
- Matplotlib is not installed

**Impact when disabled:**
- Visualization-related skills won't be recommended
- No plot/figure generation code will be created
- Statistical analysis will still work

**Environment variable:** `ENABLE_VISUALIZATION`

**Example:**
```bash
# Disable visualization
export ENABLE_VISUALIZATION=false
stats-solver solve "analyze my data"
# Output: Statistical analysis only, no visualization code
```

## Using Feature Flags

### Via Configuration File

Edit `config/default.yaml`:

```yaml
features:
  enable_llm_classification: false
  enable_auto_metadata: false
  enable_code_generation: true
  enable_visualization: false
```

### Via Environment Variables

Set environment variables before running commands:

```bash
# Linux/macOS
export ENABLE_LLM_CLASSIFICATION=false
export ENABLE_CODE_GENERATION=false

# Windows PowerShell
$env:ENABLE_LLM_CLASSIFICATION="false"
$env:ENABLE_CODE_GENERATION="false"

# Windows CMD
set ENABLE_LLM_CLASSIFICATION=false
set ENABLE_CODE_GENERATION=false
```

### Via Command Line (Future)

Note: Command-line flag support is planned for future versions:

```bash
# Planned feature
stats-solver solve --no-code-generation "analyze my data"
```

## Common Configurations

### Offline Mode (No LLM)

Disable all LLM-dependent features:

```yaml
features:
  enable_llm_classification: false
  enable_auto_metadata: false
  enable_code_generation: false
  enable_visualization: true
```

### Minimal Mode (Recommendations Only)

Disable code generation and visualization:

```yaml
features:
  enable_llm_classification: true
  enable_auto_metadata: true
  enable_code_generation: false
  enable_visualization: false
```

### Full Mode (All Features)

Enable all features (default):

```yaml
features:
  enable_llm_classification: true
  enable_auto_metadata: true
  enable_code_generation: true
  enable_visualization: true
```

### Development Mode

Enable all features with debug logging:

```yaml
app:
  log_level: DEBUG

features:
  enable_llm_classification: true
  enable_auto_metadata: true
  enable_code_generation: true
  enable_visualization: true
```

## Checking Feature Status

You can check which features are enabled by running:

```bash
stats-solver config list
```

This will show all configuration values, including feature flags.

## Feature Dependencies

Some features depend on others:

| Feature | Depends On |
|---------|------------|
| `enable_auto_metadata` | `enable_llm_classification` |
| `enable_code_generation` | `enable_auto_metadata` |
| `enable_visualization` | `enable_code_generation` |

If a dependent feature is disabled, the parent feature may not work as expected.

## Troubleshooting

### Feature Not Working

If a feature doesn't seem to be working:

1. Check the configuration: `stats-solver config list`
2. Verify the feature flag is set correctly
3. Check logs for error messages
4. Ensure dependencies are met

### Unexpected Behavior

If disabling a feature causes unexpected behavior:

1. Check if other features depend on it
2. Review the feature dependencies table above
3. Ensure you have appropriate alternatives configured

### Performance Issues

If performance is slow:

1. Disable `enable_llm_classification` if LLM is slow
2. Disable `enable_auto_metadata` to skip initialization steps
3. Disable `enable_code_generation` if you only need recommendations

## Best Practices

1. **Start Simple**: Begin with defaults and adjust as needed
2. **Test Incrementally**: Change one flag at a time
3. **Document Changes**: Note which flags you change and why
4. **Monitor Logs**: Check logs when debugging feature behavior
5. **Use Offline Mode**: Disable LLM features when not available

## Future Enhancements

Planned features for future versions:

- Per-command feature flags
- Feature-specific timeouts
- Feature health monitoring
- A/B testing support
- Feature usage analytics

## Support

For help with feature flags:

- GitHub Issues: <repository-url>/issues
- Documentation: <repository-url>/docs/feature_flags.md
- Community: <community-url>