# Changelog

All notable changes to Stats Solver will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of Stats Solver
- LLM integration with Ollama and LM Studio support
- Skill indexing and classification system
- Problem analysis and feature extraction
- Method recommendation engine
- Code generation with templates
- Interactive CLI interface
- Comprehensive documentation

## [0.1.0] - 2026-02-10

### Added
- Core project structure and modules
- LLM abstraction layer and providers
- Skill scanner, classifier, and indexer
- Problem analyzer with feature extraction
- Recommendation matcher and scorer
- Code generator with template system
- CLI with main commands (init, solve, skills, config)
- Configuration management system
- Testing framework with unit and integration tests
- Documentation (README, configuration guide, skill guide)

### Security
- All LLM calls use local providers only (no cloud dependencies)
- Input validation for all user inputs
- Safe code generation with validation

## [0.0.1] - 2026-01-XX

### Added
- Project initialization
- Basic infrastructure

---

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md with changes
3. Run tests: `pytest`
4. Build package: `python -m build`
5. Check package: `twine check dist/*`
6. Upload to PyPI: `twine upload dist/*`
7. Create git tag: `git tag -a v0.1.0 -m "Release v0.1.0"`
8. Push tag: `git push origin v0.1.0`
