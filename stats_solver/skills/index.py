"""Skill index for storing and querying skills."""

import json
import logging
from pathlib import Path
from typing import Any
from datetime import datetime

from .metadata_schema import (
    SkillMetadata,
    SkillCategory,
    SkillTypeGroup,
    SkillIndexMetadata,
    DataType,
)

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

    def add_skill(self, skill: SkillMetadata, mode: str = "merge") -> None:
        """Add a skill to the index.

        Args:
            skill: Skill metadata to add
            mode: Update mode - 'merge' (update if exists), 'overwrite' (always add new), 'skip' (skip if exists)
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

        if mode == "skip" and existing_idx is not None:
            logger.info(f"Skipped existing skill: {skill.id}")
            return

        if existing_idx is not None:
            # Update existing skill
            self._metadata.skills[existing_idx] = skill
            logger.info(f"Updated skill: {skill.id}")
        else:
            # Add new skill
            self._metadata.add_skill(skill)
            logger.info(f"Added skill: {skill.id}")

    async def batch_add_skills(
        self,
        skills: list[SkillMetadata],
        mode: str = "merge",
        batch_size: int = 50,
        progress_callback=None,
    ) -> dict[str, int]:
        """Add multiple skills in batches, saving progress after each batch.

        Args:
            skills: List of skills to add
            mode: Update mode - 'merge' (update existing, add new), 'overwrite' (replace all), 'skip' (skip existing)
            batch_size: Number of skills to process before saving
            progress_callback: Optional callback function(current, total)

        Returns:
            Dictionary with counts: added, updated, skipped, total
        """
        if not self._metadata:
            self._metadata = SkillIndexMetadata(
                skills=[],
                categories={},
                last_updated=datetime.utcnow().isoformat(),
                total_skills=0,
            )

        stats = {"added": 0, "updated": 0, "skipped": 0, "total": 0}

        # Process in batches
        for i in range(0, len(skills), batch_size):
            batch = skills[i : i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(skills) + batch_size - 1) // batch_size

            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} skills)")

            for j, skill in enumerate(batch):
                global_index = i + j + 1
                if progress_callback:
                    progress_callback(global_index, len(skills))

                # Find existing skill
                existing_idx = next(
                    (k for k, s in enumerate(self._metadata.skills) if s.id == skill.id), None
                )

                # Apply mode logic
                if mode == "skip" and existing_idx is not None:
                    stats["skipped"] += 1
                    logger.debug(f"Skipped existing skill: {skill.id}")
                elif existing_idx is not None:
                    # Update existing skill (merge or overwrite mode)
                    self._metadata.skills[existing_idx] = skill
                    stats["updated"] += 1
                    logger.debug(f"Updated skill: {skill.id}")
                else:
                    # Add new skill
                    self._metadata.add_skill(skill)
                    stats["added"] += 1
                    logger.debug(f"Added skill: {skill.id}")

                stats["total"] += 1

            # Save progress after each batch
            await self.save()
            logger.info(f"Batch {batch_num}/{total_batches} saved")

        return stats

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

    def get_by_type_group(self, type_group: SkillTypeGroup) -> list[SkillMetadata]:
        """Get all skills in a type group.

        Args:
            type_group: Type group (problem_solving or programming)

        Returns:
            List of skills in the type group
        """
        if not self._metadata:
            return []
        return [s for s in self._metadata.skills if s.type_group == type_group]

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
                "type_groups": {},
                "last_updated": None,
            }

        # Count type groups
        type_groups = {}
        for skill in self._metadata.skills:
            group = skill.type_group.value
            type_groups[group] = type_groups.get(group, 0) + 1

        return {
            "total_skills": self._metadata.total_skills,
            "categories": self._metadata.categories,
            "type_groups": type_groups,
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
