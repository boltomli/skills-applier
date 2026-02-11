"""Skill index for storing and querying skills."""

import json
import logging
from pathlib import Path
from typing import Any
from datetime import datetime

from .metadata_schema import SkillMetadata, SkillCategory, SkillIndexMetadata, DataType

logger = logging.getLogger(__name__)


class SkillIndex:
    """Index for storing and querying skill metadata."""

    def __init__(self, storage_path: Path | None = None) -> None:
        """Initialize skill index.

        Args:
            storage_path: Path to store index JSON file
        """
        self.storage_path = storage_path or Path("data/skills_metadata/index.json")
        self._metadata: SkillIndexMetadata | None = None
        self._ensure_storage_dir()

    def _ensure_storage_dir(self) -> None:
        """Ensure storage directory exists."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    async def load(self) -> SkillIndexMetadata:
        """Load skill index from storage.

        Returns:
            Skill index metadata
        """
        if not self.storage_path.exists():
            logger.info("No existing index found, creating new one")
            self._metadata = SkillIndexMetadata(
                skills=[],
                categories={},
                last_updated=datetime.utcnow().isoformat(),
                total_skills=0,
            )
            return self._metadata

        try:
            with open(self.storage_path, encoding="utf-8") as f:
                data = json.load(f)

            self._metadata = SkillIndexMetadata(**data)
            logger.info(f"Loaded index with {self._metadata.total_skills} skills")
            return self._metadata

        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            # Return empty index
            self._metadata = SkillIndexMetadata(
                skills=[],
                categories={},
                last_updated=datetime.utcnow().isoformat(),
                total_skills=0,
            )
            return self._metadata

    async def save(self) -> None:
        """Save skill index to storage."""
        if not self._metadata:
            logger.warning("No metadata to save")
            return

        try:
            self._metadata.last_updated = datetime.utcnow().isoformat()

            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self._metadata.model_dump(), f, indent=2, ensure_ascii=False)

            logger.info(f"Saved index with {self._metadata.total_skills} skills")

        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            raise

    def add_skill(self, skill: SkillMetadata) -> None:
        """Add a skill to the index.

        Args:
            skill: Skill metadata to add
        """
        if not self._metadata:
            self._metadata = SkillIndexMetadata(
                skills=[],
                categories={},
                last_updated=datetime.utcnow().isoformat(),
                total_skills=0,
            )

        # Check if skill already exists
        existing_idx = next(
            (i for i, s in enumerate(self._metadata.skills) if s.id == skill.id), None
        )

        if existing_idx is not None:
            # Update existing skill
            self._metadata.skills[existing_idx] = skill
            logger.info(f"Updated skill: {skill.id}")
        else:
            # Add new skill
            self._metadata.add_skill(skill)
            logger.info(f"Added skill: {skill.id}")

    def get_skill(self, skill_id: str) -> SkillMetadata | None:
        """Get a skill by ID.

        Args:
            skill_id: Skill identifier

        Returns:
            Skill metadata or None if not found
        """
        if not self._metadata:
            return None

        for skill in self._metadata.skills:
            if skill.id == skill_id:
                return skill
        return None

    def get_all_skills(self) -> list[SkillMetadata]:
        """Get all skills in the index.

        Returns:
            List of all skills
        """
        if not self._metadata:
            return []
        return self._metadata.skills.copy()

    def get_by_category(self, category: SkillCategory) -> list[SkillMetadata]:
        """Get all skills in a category.

        Args:
            category: Skill category

        Returns:
            List of skills in the category
        """
        if not self._metadata:
            return []
        return self._metadata.get_by_category(category)

    def get_by_tag(self, tag: str) -> list[SkillMetadata]:
        """Get all skills with a specific tag.

        Args:
            tag: Tag to search for

        Returns:
            List of skills with the tag
        """
        if not self._metadata:
            return []
        return self._metadata.get_by_tag(tag)

    def search(self, query: str) -> list[SkillMetadata]:
        """Search skills by name, description, or tags.

        Args:
            query: Search query

        Returns:
            List of matching skills
        """
        if not self._metadata:
            return []
        return self._metadata.search(query)

    def filter_by_data_type(self, data_type: DataType) -> list[SkillMetadata]:
        """Filter skills by input data type.

        Args:
            data_type: Data type to filter by

        Returns:
            List of skills that accept this data type
        """
        if not self._metadata:
            return []

        return [
            skill
            for skill in self._metadata.skills
            if data_type in skill.input_data_types or DataType.MIXED in skill.input_data_types
        ]

    def get_statistics(self) -> dict[str, Any]:
        """Get index statistics.

        Returns:
            Dictionary with index statistics
        """
        if not self._metadata:
            return {
                "total_skills": 0,
                "categories": {},
                "last_updated": None,
            }

        return {
            "total_skills": self._metadata.total_skills,
            "categories": self._metadata.categories,
            "last_updated": self._metadata.last_updated,
        }

    def get_top_tags(self, limit: int = 20) -> list[tuple[str, int]]:
        """Get most common tags across all skills.

        Args:
            limit: Maximum number of tags to return

        Returns:
            List of (tag, count) tuples sorted by count
        """
        if not self._metadata:
            return []

        tag_counts: dict[str, int] = {}

        for skill in self._metadata.skills:
            for tag in skill.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

    def get_dependencies_summary(self) -> dict[str, int]:
        """Get summary of dependencies across all skills.

        Returns:
            Dictionary mapping dependency name to count of skills using it
        """
        if not self._metadata:
            return {}

        dep_counts: dict[str, int] = {}

        for skill in self._metadata.skills:
            for dep in skill.dependencies:
                dep_counts[dep] = dep_counts.get(dep, 0) + 1

        return dict(sorted(dep_counts.items(), key=lambda x: x[1], reverse=True))

    def remove_skill(self, skill_id: str) -> bool:
        """Remove a skill from the index.

        Args:
            skill_id: Skill identifier

        Returns:
            True if skill was removed, False if not found
        """
        if not self._metadata:
            return False

        initial_count = len(self._metadata.skills)
        self._metadata.skills = [s for s in self._metadata.skills if s.id != skill_id]

        if len(self._metadata.skills) < initial_count:
            self._metadata.total_skills = len(self._metadata.skills)
            self._metadata._update_categories()
            logger.info(f"Removed skill: {skill_id}")
            return True

        return False

    def clear(self) -> None:
        """Clear all skills from the index."""
        if self._metadata:
            self._metadata.skills = []
            self._metadata.categories = {}
            self._metadata.total_skills = 0
            logger.info("Cleared skill index")
