# Rollback Procedures

This document describes how to roll back Stats Solver to a previous version or state.

## Table of Contents

1. [Quick Rollback](#quick-rollback)
2. [Git-Based Rollback](#git-based-rollback)
3. [Configuration Rollback](#configuration-rollback)
4. [Feature Rollback](#feature-rollback)
5. [Complete System Rollback](#complete-system-rollback)
6. [Testing Rollback](#testing-rollback)

## Quick Rollback

### Rollback to Previous Git Tag

```bash
# List available tags
git tag

# Rollback to specific tag
git checkout v0.1.0

# Reinstall with previous version
pip install -e .
```

### Rollback to Previous Commit

```bash
# View commit history
git log --oneline

# Rollback to specific commit
git checkout <commit-hash>

# Reinstall
pip install -e .
```

## Git-Based Rollback

### Scenario 1: Rollback After a Bad Commit

**Situation:** A recent commit introduced bugs or issues.

**Steps:**

1. Identify the problematic commit:
   ```bash
   git log --oneline -10
   ```

2. Rollback to the commit before the bad one:
   ```bash
   git checkout <previous-commit-hash>
   ```

3. Verify the state:
   ```bash
   git status
   stats-solver --version
   ```

4. Reinstall:
   ```bash
   pip install -e .
   ```

5. Test functionality:
   ```bash
   stats-solver check
   stats-solver skills list
   ```

### Scenario 2: Create a Rollback Branch

**Situation:** You want to preserve the current state while rolling back.

**Steps:**

1. Create a branch for current state:
   ```bash
   git branch broken-state
   ```

2. Rollback to previous tag:
   ```bash
   git checkout v0.1.0
   ```

3. Create a rollback branch:
   ```bash
   git branch rollback-<date>
   ```

4. Test the rollback:
   ```bash
   pip install -e .
   stats-solver check
   ```

### Scenario 3: Revert Specific Changes

**Situation:** You want to undo specific commits without losing other changes.

**Steps:**

1. Identify commits to revert:
   ```bash
   git log --oneline
   ```

2. Revert specific commits:
   ```bash
   git revert <commit-hash>
   ```

3. Resolve any conflicts if they arise

4. Commit the revert:
   ```bash
   git commit -m "Revert problematic changes"
   ```

## Configuration Rollback

### Scenario 1: Restore Default Configuration

**Situation:** Configuration changes caused issues.

**Steps:**

1. Backup current configuration:
   ```bash
   cp config/default.yaml config/default.yaml.backup
   ```

2. Restore default configuration:
   ```bash
   git checkout HEAD -- config/default.yaml
   ```

3. Or copy from example:
   ```bash
   cp config/default.yaml.example config/default.yaml
   ```

4. Restart the application:
   ```bash
   stats-solver check
   ```

### Scenario 2: Rollback Environment Variables

**Situation:** Environment variables are causing problems.

**Steps:**

1. Check current environment variables:
   ```bash
   env | grep STATS_SOLVER
   env | grep LLM_
   ```

2. Unset problematic variables:
   ```bash
   # Linux/macOS
   unset ENABLE_LLM_CLASSIFICATION
   unset ENABLE_CODE_GENERATION

   # Windows PowerShell
   Remove-Item Env:ENABLE_LLM_CLASSIFICATION
   Remove-Item Env:ENABLE_CODE_GENERATION

   # Windows CMD
   set ENABLE_LLM_CLASSIFICATION=
   set ENABLE_CODE_GENERATION=
   ```

3. Restart terminal/application

### Scenario 3: Restore Skill Metadata

**Situation:** Skill metadata was corrupted or incorrectly generated.

**Steps:**

1. Backup current metadata:
   ```bash
   cp -r data/skills_metadata data/skills_metadata.backup
   ```

2. Remove corrupted metadata:
   ```bash
   rm -rf data/skills_metadata/*
   ```

3. Regenerate metadata:
   ```bash
   stats-solver init --force
   ```

## Feature Rollback

### Scenario 1: Disable a Feature Flag

**Situation:** A new feature is causing issues.

**Steps:**

1. Edit configuration file:
   ```bash
   nano config/default.yaml
   ```

2. Disable the problematic feature:
   ```yaml
   features:
     enable_llm_classification: false  # Disable this
     enable_auto_metadata: true
     enable_code_generation: true
     enable_visualization: true
   ```

3. Restart the application:
   ```bash
   stats-solver check
   ```

### Scenario 2: Rollback Feature Changes

**Situation:** Feature implementation changes need to be reverted.

**Steps:**

1. Identify commits for the feature:
   ```bash
   git log --oneline --grep="feature-name"
   ```

2. Revert feature commits:
   ```bash
   git revert <feature-commit-hash>
   ```

3. Disable feature flag:
   ```yaml
   features:
     enable_problematic_feature: false
   ```

4. Test rollback:
   ```bash
   stats-solver check
   ```

## Complete System Rollback

### Scenario 1: Full System Reinstall

**Situation:** Complete system failure or corruption.

**Steps:**

1. Uninstall current version:
   ```bash
   pip uninstall stats-solver
   ```

2. Clone fresh repository:
   ```bash
   git clone <repository-url> stats-solver-fresh
   cd stats-solver-fresh
   ```

3. Checkout stable version:
   ```bash
   git checkout v0.1.0
   ```

4. Install dependencies:
   ```bash
   pip install -e .
   ```

5. Configure:
   ```bash
   cp .env.example .env
   # Edit .env as needed
   ```

6. Initialize:
   ```bash
   stats-solver init
   ```

7. Test:
   ```bash
   stats-solver check
   ```

### Scenario 2: Restore from Backup

**Situation:** You have a backup of a working state.

**Steps:**

1. Restore configuration:
   ```bash
   cp backup/config/default.yaml config/default.yaml
   cp backup/.env .env
   ```

2. Restore skill metadata:
   ```bash
   cp -r backup/data/skills_metadata/* data/skills_metadata/
   ```

3. Restore cache (if needed):
   ```bash
   cp -r backup/.cache/stats_solver ~/.cache/stats_solver
   ```

4. Test:
   ```bash
   stats-solver check
   ```

## Testing Rollback

### Rollback Testing Checklist

After performing any rollback, verify the following:

- [ ] Application starts without errors
- [ ] `stats-solver check` passes
- [ ] Skills are properly indexed
- [ ] LLM connection works (if applicable)
- [ ] Basic commands work (`solve`, `skills list`, etc.)
- [ ] Configuration is correct
- [ ] No error messages in logs

### Automated Rollback Test

Create a test script to verify rollback:

```bash
#!/bin/bash
# test_rollback.sh

echo "Testing rollback..."

# Test 1: Check application
if stats-solver check; then
    echo "✓ Application check passed"
else
    echo "✗ Application check failed"
    exit 1
fi

# Test 2: List skills
if stats-solver skills list > /dev/null 2>&1; then
    echo "✓ Skills list passed"
else
    echo "✗ Skills list failed"
    exit 1
fi

# Test 3: Test recommendation
echo "test" | stats-solver solve > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Recommendation test passed"
else
    echo "✗ Recommendation test failed"
    exit 1
fi

echo "All tests passed!"
```

Run the test:
```bash
chmod +x test_rollback.sh
./test_rollback.sh
```

## Rollback Best Practices

1. **Always Backup**: Before any rollback, backup current state
2. **Test Incrementally**: Test after each rollback step
3. **Document Changes**: Keep track of what was rolled back and why
4. **Use Git Tags**: Tag stable versions for easy rollback
5. **Keep History**: Maintain git history for all changes
6. **Verify Thoroughly**: Test all functionality after rollback
7. **Plan Ahead**: Have rollback procedures documented before issues occur

## Prevention

To minimize the need for rollbacks:

1. **Use Feature Flags**: Test new features with flags before enabling
2. **Run Tests**: Always run tests before committing
3. **Review Changes**: Carefully review code before merging
4. **Use Branches**: Work on feature branches, not main
5. **Gradual Rollout**: Roll out changes gradually
6. **Monitor Logs**: Watch for errors and warnings

## Emergency Rollback

If the system is completely unresponsive:

1. Stop any running processes:
   ```bash
   pkill -f stats-solver
   ```

2. Rollback to known good state:
   ```bash
   git checkout v0.1.0
   ```

3. Reinstall:
   ```bash
   pip install -e .
   ```

4. Test:
   ```bash
   stats-solver check
   ```

5. If still broken, perform complete system reinstall (see above)

## Support

If rollback procedures don't work:

1. Check GitHub Issues: <repository-url>/issues
2. Review documentation: <repository-url>/docs
3. Contact support: <support-email>
4. Consider opening a new issue with rollback details

## Additional Resources

- Git Documentation: https://git-scm.com/docs
- Configuration Guide: `docs/configuration.md`
- Feature Flags: `docs/feature_flags.md`
- Troubleshooting: README.md#troubleshooting
