"""Skill scanner for discovering and indexing skills."""

import logging
from pathlib import Path
from typing import List, Dict, Optional, Set
import re

from .metadata_schema import SkillMetadata, SkillCategory, DataType

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
    
    # File patterns to ignore
    IGNORE_PATTERNS = {
        r"__pycache__",
        r"\.pyc$",
        r"\.git",
        r"test_",
        r"_test\.py$",
    }
    
    def __init__(self, base_paths: List[str]) -> None:
        """Initialize skill scanner.
        
        Args:
            base_paths: List of base directory paths to scan for skills
        """
        self.base_paths = [Path(p).resolve() for p in base_paths]
        self._scanned_skills: List[SkillMetadata] = []
    
    def scan_all(self) -> List[SkillMetadata]:
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
    
    def _scan_directory(self, directory: Path) -> List[SkillMetadata]:
        """Scan a directory for skills.
        
        Args:
            directory: Directory path to scan
            
        Returns:
            List of skills found in this directory
        """
        skills = []
        
        # Check if this directory itself is a skill (contains Python files)
        python_files = self._find_python_files(directory)
        if python_files:
            skill = self._create_basic_metadata(directory, python_files)
            skills.append(skill)
        else:
            # Otherwise, scan subdirectories
            for item in directory.iterdir():
                if item.is_dir() and not self._should_ignore(item.name):
                    sub_skills = self._scan_directory(item)
                    skills.extend(sub_skills)
        
        return skills
    
    def _find_python_files(self, directory: Path) -> List[Path]:
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
    
    def _create_basic_metadata(self, directory: Path, python_files: List[Path]) -> SkillMetadata:
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
    
    def _extract_dependencies(self, python_files: List[Path]) -> List[str]:
        """Extract Python dependencies from files.
        
        Args:
            python_files: List of Python file paths
            
        Returns:
            List of dependency names
        """
        dependencies: Set[str] = set()
        
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
    
    def get_scanned_skills(self) -> List[SkillMetadata]:
        """Get list of scanned skills.
        
        Returns:
            List of skills that have been scanned
        """
        return self._scanned_skills.copy()
    
    def clear_cache(self) -> None:
        """Clear the scanned skills cache."""
        self._scanned_skills = []