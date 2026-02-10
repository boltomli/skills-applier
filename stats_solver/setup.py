"""
Setup script for Stats Solver.
This script provides additional functionality beyond pyproject.toml.
"""

from setuptools import setup
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    long_description=long_description,
    long_description_content_type="text/markdown",
)