"""Dependency generator for managing code dependencies."""

import logging

logger = logging.getLogger(__name__)


class DependencyGenerator:
    """Generator for managing Python code dependencies."""

    # Standard library imports (don't need to be listed in requirements)
    STANDARD_LIBRARY = {
        "os",
        "sys",
        "math",
        "random",
        "statistics",
        "itertools",
        "collections",
        "functools",
        "datetime",
        "json",
        "csv",
        "re",
        "string",
        "pathlib",
        "typing",
        "dataclasses",
    }

    # Package to pip install name mapping
    PACKAGE_ALIASES = {
        "numpy": "numpy",
        "np": "numpy",
        "pandas": "pandas",
        "pd": "pandas",
        "scipy": "scipy",
        "stats": "scipy",
        "matplotlib": "matplotlib",
        "plt": "matplotlib",
        "pyplot": "matplotlib",
        "seaborn": "seaborn",
        "sns": "seaborn",
        "sklearn": "scikit-learn",
        "plotly": "plotly",
        "statsmodels": "statsmodels",
    }

    # Import statement templates
    IMPORT_TEMPLATES = {
        "standard": "import {module}",
        "from": "from {module} import {name}",
        "as": "import {module} as {alias}",
    }

    def __init__(self) -> None:
        """Initialize dependency generator."""
        pass

    def generate_imports(self, dependencies: list[str]) -> list[str]:
        """Generate import statements from dependencies.

        Args:
            dependencies: List of dependency names

        Returns:
            List of import statements
        """
        imports = []
        seen = set()

        for dep in dependencies:
            import_stmt = self._generate_import_statement(dep)
            if import_stmt and import_stmt not in seen:
                imports.append(import_stmt)
                seen.add(import_stmt)

        return imports

    def _generate_import_statement(self, dependency: str) -> str | None:
        """Generate a single import statement.

        Args:
            dependency: Dependency name

        Returns:
            Import statement or None if standard library
        """
        # Check if it's a standard library
        if dependency.lower() in self.STANDARD_LIBRARY:
            return None

        # Generate appropriate import statement
        if "." in dependency:
            # From import (e.g., "scipy.stats")
            parts = dependency.split(".")
            return f"from {'.'.join(parts[:-1])} import {parts[-1]}"
        else:
            # Simple import
            alias = self._get_alias(dependency)
            if alias:
                return f"import {dependency} as {alias}"
            else:
                return f"import {dependency}"

    def _get_alias(self, dependency: str) -> str | None:
        """Get common alias for a package.

        Args:
            dependency: Package name

        Returns:
            Common alias or None
        """
        aliases = {
            "numpy": "np",
            "pandas": "pd",
            "matplotlib.pyplot": "plt",
            "seaborn": "sns",
        }

        for pkg, alias in aliases.items():
            if dependency.lower().startswith(pkg):
                return alias

        return None

    def generate_requirements_txt(self, dependencies: list[str]) -> str:
        """Generate requirements.txt content.

        Args:
            dependencies: List of dependency names

        Returns:
            requirements.txt content
        """
        packages = self._extract_packages(dependencies)

        # Group by package and deduplicate
        unique_packages: set[tuple[str, str | None]] = set()
        for pkg, version in packages:
            unique_packages.add((pkg, version))

        # Generate requirements lines
        lines = []
        for pkg, version in sorted(unique_packages):
            if version:
                lines.append(f"{pkg}{version}")
            else:
                lines.append(pkg)

        return "\n".join(lines)

    def _extract_packages(self, dependencies: list[str]) -> list[tuple[str, str | None]]:
        """Extract package names from dependencies.

        Args:
            dependencies: List of dependency names

        Returns:
            List of (package, version) tuples
        """
        packages = []

        for dep in dependencies:
            # Skip standard library
            if dep.lower() in self.STANDARD_LIBRARY:
                continue

            # Parse version if specified
            version = None
            if ">=" in dep or "==" in dep or "~=" in dep:
                parts = dep.split(">=" if ">=" in dep else "==" if "==" in dep else "~=")
                pkg_name = parts[0]
                version = parts[1] if len(parts) > 1 else None
            else:
                pkg_name = dep

            # Get actual package name
            actual_pkg = self.PACKAGE_ALIASES.get(pkg_name.lower(), pkg_name)

            packages.append((actual_pkg, version))

        return packages

    def generate_setup_py(self, dependencies: list[str], project_name: str) -> str:
        """Generate setup.py content.

        Args:
            dependencies: List of dependency names
            project_name: Name of the project

        Returns:
            setup.py content
        """
        packages = self._extract_packages(dependencies)
        install_requires = [f"{pkg}{version or ''}" for pkg, version in packages]

        return f"""from setuptools import setup, find_packages

setup(
    name="{project_name}",
    version="0.1.0",
    packages=find_packages(),
    install_requires={install_requires},
    python_requires=">=3.8",
)"""

    def generate_pyproject_toml_dependencies(self, dependencies: list[str]) -> str:
        """Generate pyproject.toml dependencies section.

        Args:
            dependencies: List of dependency names

        Returns:
            pyproject.toml dependencies string
        """
        packages = self._extract_packages(dependencies)
        deps_lines = [f'"{pkg}{version or ""}"' for pkg, version in packages]

        return f"dependencies = [\n    {',\\n    '.join(deps_lines)}\n]"

    def check_conflicts(self, dependencies: list[str]) -> list[str]:
        """Check for potential dependency conflicts.

        Args:
            dependencies: List of dependency names

        Returns:
            List of conflict warnings
        """
        conflicts = []

        # Known conflicting packages
        known_conflicts = [
            ("tensorflow", "torch"),
            ("theano", "tensorflow"),
        ]

        packages = [
            self.PACKAGE_ALIASES.get(d.lower(), d).split(">=")[0].split("==")[0].split("~=")[0]
            for d in dependencies
        ]

        for pkg1, pkg2 in known_conflicts:
            if pkg1 in packages and pkg2 in packages:
                conflicts.append(
                    f"Potential conflict: {pkg1} and {pkg2} may not work well together"
                )

        return conflicts

    def suggest_alternatives(self, dependency: str) -> list[str]:
        """Suggest alternative packages for a dependency.

        Args:
            dependency: Dependency name

        Returns:
            List of alternative package names
        """
        alternatives = {
            "matplotlib": ["plotly", "bokeh"],
            "pandas": ["polars"],
            "scikit-learn": ["xgboost", "lightgbm"],
            "scipy": ["statsmodels"],
        }

        pkg = dependency.split(">=")[0].split("==")[0].split("~=")[0].lower()
        return alternatives.get(pkg, [])

    def get_dependency_info(self, dependency: str) -> dict[str, str]:
        """Get information about a dependency.

        Args:
            dependency: Dependency name

        Returns:
            Dictionary with dependency information
        """
        pkg = dependency.split(">=")[0].split("==")[0].split("~=")[0]

        return {
            "name": pkg,
            "alias": self._get_alias(pkg),
            "package": self.PACKAGE_ALIASES.get(pkg.lower(), pkg),
            "is_standard": pkg.lower() in self.STANDARD_LIBRARY,
            "import_statement": self._generate_import_statement(pkg),
        }

    def merge_dependencies(self, dependency_lists: list[list[str]]) -> list[str]:
        """Merge multiple dependency lists, removing duplicates.

        Args:
            dependency_lists: List of dependency lists

        Returns:
            Merged and deduplicated list
        """
        all_deps = set()

        for deps in dependency_lists:
            all_deps.update(deps)

        # Remove standard library
        filtered = [d for d in all_deps if d.lower() not in self.STANDARD_LIBRARY]

        return sorted(filtered)

    def generate_install_command(self, dependencies: list[str]) -> str:
        """Generate pip install command.

        Args:
            dependencies: List of dependency names

        Returns:
            Install command string
        """
        packages = self._extract_packages(dependencies)
        pkg_list = " ".join([pkg for pkg, _ in packages])

        return f"pip install {pkg_list}"
