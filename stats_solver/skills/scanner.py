"""Skill scanner for discovering and indexing skills."""

import json
import logging
from pathlib import Path
import re

from .metadata_schema import SkillMetadata, SkillCategory

logger = logging.getLogger(__name__)


class SkillScanner:
    """Scanner for discovering skills in the codebase."""

    # Common Python dependencies patterns
    DEPENDENCY_PATTERNS = {
        r"import\s+(numpy|np)": "numpy",
        r"import\s+(pandas|pd)": "pandas",
        r"import\s+(scipy)": "scipy",
        r"import\s+(matplotlib|plt)": "matplotlib",
        r"import\s+(seaborn|sns)": "seaborn",
        r"import\s+(sklearn)": "scikit-learn",
        r"from\s+(numpy|pandas|scipy|matplotlib|seaborn|sklearn)": None,  # Will match above
    }

    # Python file extensions to scan
    PYTHON_EXTENSIONS = {".py"}
    # JSON metadata extensions to scan
    JSON_EXTENSIONS = {".json"}
    # Markdown skill files
    MARKDOWN_EXTENSIONS = {".md"}

    # File patterns to ignore
    IGNORE_PATTERNS = {
        r"__pycache__",
        r"\.pyc$",
        r"\.git",
        r"test_",
        r"_test\.py$",
    }

    def __init__(self, base_paths: list[str], ignore_example: bool = False) -> None:
        """Initialize skill scanner.

        Args:
            base_paths: List of base directory paths to scan for skills
            ignore_example: Whether to ignore example JSON metadata in data/skills_metadata
        """
        self.base_paths = [Path(p).resolve() for p in base_paths]
        self.ignore_example = ignore_example
        self._scanned_skills: list[SkillMetadata] = []

    def scan_all(self) -> list[SkillMetadata]:
        """Scan all base paths for skills.

        Returns:
            List of discovered skills with basic metadata
        """
        self._scanned_skills = []

        for base_path in self.base_paths:
            if not base_path.exists():
                logger.warning(f"Base path does not exist: {base_path}")
                continue

            logger.info(f"Scanning base path: {base_path}")
            skills = self._scan_directory(base_path)
            self._scanned_skills.extend(skills)

        logger.info(f"Scanned {len(self._scanned_skills)} skills total")
        return self._scanned_skills

    def _scan_directory(self, directory: Path) -> list[SkillMetadata]:
        """Scan a directory for skills.

        Args:
            directory: Directory path to scan

        Returns:
            List of skills found in this directory
        """
        skills = []

        # Check if this directory is the example metadata directory and should be ignored
        if self.ignore_example:
            if "skills_metadata" in str(directory) and "data" in str(directory):
                logger.info(f"Ignoring example metadata directory: {directory}")
                return skills

        # Check if this directory contains SKILL.md file
        skill_md = directory / "SKILL.md"
        if skill_md.exists():
            skill = self._load_from_markdown(skill_md, directory)
            if skill:
                skills.append(skill)
            return skills

        # Check if this directory contains JSON skill metadata files
        json_files = self._find_json_files(directory)
        if json_files:
            for json_file in json_files:
                skill = self._load_from_json(json_file)
                if skill:
                    skills.append(skill)
            return skills

        # Otherwise, check if this directory itself is a skill (contains Python files)
        python_files = self._find_python_files(directory)
        if python_files:
            skill = self._create_basic_metadata(directory, python_files)
            skills.append(skill)
        else:
            # Scan subdirectories
            for item in directory.iterdir():
                if item.is_dir() and not self._should_ignore(item.name):
                    sub_skills = self._scan_directory(item)
                    skills.extend(sub_skills)

        return skills

    def _find_python_files(self, directory: Path) -> list[Path]:
        """Find Python files in a directory.

        Args:
            directory: Directory to search

        Returns:
            List of Python file paths
        """
        python_files = []

        try:
            for item in directory.iterdir():
                if item.is_file() and item.suffix in self.PYTHON_EXTENSIONS:
                    if not self._should_ignore(item.name):
                        python_files.append(item)
        except PermissionError:
            logger.warning(f"Permission denied: {directory}")

        return python_files

    def _find_json_files(self, directory: Path) -> list[Path]:
        """Find JSON metadata files in a directory.

        Args:
            directory: Directory to search

        Returns:
            List of JSON file paths
        """
        json_files = []

        try:
            for item in directory.iterdir():
                if item.is_file() and item.suffix in self.JSON_EXTENSIONS:
                    if not self._should_ignore(item.name):
                        json_files.append(item)
        except PermissionError:
            logger.warning(f"Permission denied: {directory}")

        return json_files

    def _load_from_markdown(self, md_path: Path, directory: Path) -> SkillMetadata | None:
        """Load skill metadata from SKILL.md file.

        Args:
            md_path: Path to SKILL.md file
            directory: Directory containing the skill

        Returns:
            SkillMetadata or None if loading fails
        """
        try:
            with open(md_path, encoding="utf-8") as f:
                content = f.read()

            # Parse metadata from YAML frontmatter or markdown content
            metadata = self._parse_markdown_metadata(content, directory)

            return metadata
        except Exception as e:
            logger.warning(f"Failed to load skill from {md_path}: {e}")
            return None

    def _parse_markdown_metadata(self, content: str, directory: Path) -> SkillMetadata:
        """Parse metadata from SKILL.md content.

        Args:
            content: SKILL.md file content
            directory: Directory containing the skill

        Returns:
            SkillMetadata object
        """
        import yaml

        # Try to extract YAML frontmatter
        frontmatter_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)

        if frontmatter_match:
            try:
                yaml_content = frontmatter_match.group(1)
                data = yaml.safe_load(yaml_content)

                if data and isinstance(data, dict):
                    return self._convert_dict_to_metadata(data, directory)
            except Exception as e:
                logger.debug(f"Failed to parse YAML frontmatter in {directory.name}: {e}")
                # Fall through to basic parsing

        # If no valid frontmatter, try to parse the entire file as markdown content
        # Look for structured content that might contain metadata
        skill_id = directory.name
        name = self._format_name(skill_id)

        # Extract title (first heading)
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if title_match:
            name = title_match.group(1).strip()

        # Extract description from first paragraph after title
        desc_match = re.search(r"^(?!#)(.+?)(?:\n\n|$)", content, re.MULTILINE)
        description = desc_match.group(1).strip() if desc_match else f"Skill: {name}"

        # Extract tags from content - look for various patterns
        tags = []
        tag_patterns = [
            r"tags:\s*\[(.*?)\]",
            r"Tags:\s*\[(.*?)\]",
            r"Tags:\s*(.+?)(?:\n|$)",
        ]
        for pattern in tag_patterns:
            tag_match = re.search(pattern, content, re.DOTALL)
            if tag_match:
                tags_str = tag_match.group(1)
                tags = [t.strip().strip("\"'") for t in tags_str.split(",")]
                break

        # Try to extract category from content
        category = SkillCategory.ALGORITHM
        category_match = re.search(r"category:\s*(\w+)", content, re.IGNORECASE)
        if category_match:
            category = self._map_category(category_match.group(1))

        # Calculate path safely
        try:
            path = str(directory.relative_to(Path.cwd()))
        except ValueError:
            path = str(directory)

        return SkillMetadata(
            name=name,
            id=skill_id,
            path=path,
            category=category,
            tags=tags,
            description=description,
            dependencies=[],
            source="markdown",
            confidence=0.3,  # Lower confidence for basic parsing
        )

    def _convert_dict_to_metadata(self, data: dict, directory: Path) -> SkillMetadata:
        """Convert YAML dict to SkillMetadata.

        Args:
            data: Dictionary from YAML frontmatter
            directory: Directory containing the skill

        Returns:
            SkillMetadata object
        """
        skill_id = data.get("id", directory.name)
        name = data.get("name", self._format_name(skill_id))

        # Calculate path safely
        try:
            path = str(directory.relative_to(Path.cwd()))
        except ValueError:
            path = str(directory)

        skill_data = {
            "name": name,
            "id": skill_id,
            "path": path,
            "category": self._map_category(data.get("category", "algorithm")),
            "tags": data.get("tags", []),
            "input_data_types": self._map_data_types(data.get("data_types", [])),
            "output_format": data.get("output_format"),
            "description": data.get("description", f"Skill: {name}"),
            "dependencies": data.get("dependencies", []),
            "prerequisites": data.get("prerequisites", []),
            "assumptions": data.get("assumptions", []),
            "use_cases": data.get("use_cases", []),
            "statistical_concept": data.get("statistical_concept"),
            "algorithm_name": data.get("algorithm_name"),
            "complexity": data.get("complexity"),
            "source": "markdown",
            "confidence": data.get("confidence", 1.0),
        }

        return SkillMetadata(**skill_data)

    def _load_from_json(self, json_path: Path) -> SkillMetadata | None:
        """Load skill metadata from JSON file.

        Args:
            json_path: Path to JSON metadata file

        Returns:
            SkillMetadata or None if loading fails
        """
        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)

            # Map JSON fields to SkillMetadata schema
            # Handle different field names between JSON schema and SkillMetadata
            skill_data = {
                "name": data.get("name", data.get("skill_id", json_path.stem)),
                "id": data.get("skill_id", json_path.stem),
                "path": str(json_path.parent.relative_to(Path.cwd())),
                "category": self._map_category(data.get("category", "algorithm")),
                "tags": data.get("tags", []),
                "input_data_types": self._map_data_types(data.get("data_types", [])),
                "output_format": self._get_output_format(data),
                "description": data.get("description", "No description"),
                "dependencies": data.get("dependencies", []),
                "prerequisites": data.get("prerequisites", []),
                "assumptions": data.get("assumptions", []),
                "use_cases": data.get("use_cases", []),
                "statistical_concept": data.get("statistical_concept"),
                "source": "json",
                "confidence": data.get("confidence_score", 1.0),
            }

            return SkillMetadata(**skill_data)
        except Exception as e:
            logger.warning(f"Failed to load skill from {json_path}: {e}")
            return None

    def _map_category(self, category: str) -> SkillCategory:
        """Map category string to SkillCategory enum.

        Args:
            category: Category string

        Returns:
            SkillCategory enum value
        """
        category_lower = category.lower().replace("-", "_")

        category_mapping = {
            "statistical_method": SkillCategory.STATISTICAL_METHOD,
            "statistical-method": SkillCategory.STATISTICAL_METHOD,
            "mathematical_implementation": SkillCategory.MATHEMATICAL_IMPLEMENTATION,
            "mathematical-implementation": SkillCategory.MATHEMATICAL_IMPLEMENTATION,
            "data_analysis": SkillCategory.DATA_ANALYSIS,
            "data-analysis": SkillCategory.DATA_ANALYSIS,
            "visualization": SkillCategory.VISUALIZATION,
            "algorithm": SkillCategory.ALGORITHM,
        }

        return category_mapping.get(category_lower, SkillCategory.ALGORITHM)

    def _map_data_types(self, data_types: list[str]) -> list:
        """Map data type strings to DataType enum.

        Args:
            data_types: List of data type strings

        Returns:
            List of DataType enum values
        """
        from .metadata_schema import DataType

        type_mapping = {
            "numerical": DataType.NUMERICAL,
            "categorical": DataType.CATEGORICAL,
            "time_series": DataType.TIME_SERIES,
            "time-series": DataType.TIME_SERIES,
            "text": DataType.TEXT,
            "boolean": DataType.BOOLEAN,
            "mixed": DataType.MIXED,
        }

        result = []
        for dt in data_types:
            dt_lower = dt.lower().replace("-", "_")
            if dt_lower in type_mapping:
                result.append(type_mapping[dt_lower])

        return result if result else [DataType.NUMERICAL]

    def _get_output_format(self, data: dict) -> str | None:
        """Get output format from JSON data.

        Args:
            data: JSON data dictionary

        Returns:
            Output format string or None
        """
        if "output_format" in data:
            if isinstance(data["output_format"], dict):
                return data["output_format"].get("type")
            return data["output_format"]
        elif "output_types" in data:
            return ", ".join(data["output_types"])
        return None

    def _should_ignore(self, name: str) -> bool:
        """Check if a file/directory should be ignored.

        Args:
            name: File or directory name

        Returns:
            True if should be ignored
        """
        for pattern in self.IGNORE_PATTERNS:
            if re.search(pattern, name, re.IGNORECASE):
                return True
        return False

    def _create_basic_metadata(self, directory: Path, python_files: list[Path]) -> SkillMetadata:
        """Create basic metadata for a skill from its files.

        Args:
            directory: Skill directory path
            python_files: List of Python files in the skill

        Returns:
            Basic skill metadata
        """
        # Use directory name as skill ID
        skill_id = directory.name

        # Extract dependencies from Python files
        dependencies = self._extract_dependencies(python_files)

        # Create basic metadata
        return SkillMetadata(
            name=self._format_name(skill_id),
            id=skill_id,
            path=str(directory.relative_to(Path.cwd())),
            category=SkillCategory.MATHEMATICAL_IMPLEMENTATION,  # Default
            description=f"Skill: {skill_id}",
            dependencies=dependencies,
            source="scanner",
        )

    def _extract_dependencies(self, python_files: list[Path]) -> list[str]:
        """Extract Python dependencies from files.

        Args:
            python_files: List of Python file paths

        Returns:
            List of dependency names
        """
        dependencies: set[str] = set()

        for file_path in python_files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")

                for pattern, dep in self.DEPENDENCY_PATTERNS.items():
                    if re.search(pattern, content):
                        if dep:  # Some patterns have None as value
                            dependencies.add(dep)
            except Exception as e:
                logger.warning(f"Failed to read {file_path}: {e}")

        return sorted(dependencies)

    def _format_name(self, skill_id: str) -> str:
        """Format skill ID into a readable name.

        Args:
            skill_id: Skill identifier (directory name)

        Returns:
            Formatted name
        """
        # Convert kebab-case to Title Case
        name = skill_id.replace("-", " ").replace("_", " ")
        return " ".join(word.capitalize() for word in name.split())

    def get_scanned_skills(self) -> list[SkillMetadata]:
        """Get list of scanned skills.

        Returns:
            List of skills that have been scanned
        """
        return self._scanned_skills.copy()

    def clear_cache(self) -> None:
        """Clear the scanned skills cache."""
        self._scanned_skills = []
