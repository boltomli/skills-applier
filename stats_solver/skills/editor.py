"""Manual skill classification editor for correcting metadata."""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

from .metadata_schema import SkillMetadata, SkillCategory, DataType
from .index import SkillIndex

logger = logging.getLogger(__name__)


class SkillEditor:
    """Editor for manually correcting skill metadata."""

    def __init__(self, index: SkillIndex) -> None:
        """Initialize skill editor.

        Args:
            index: Skill index to edit
        """
        self.index = index

    def update_category(
        self, skill_id: str, new_category: SkillCategory
    ) -> Optional[SkillMetadata]:
        """Update the category of a skill.

        Args:
            skill_id: Skill identifier
            new_category: New category

        Returns:
            Updated skill metadata or None if not found
        """
        skill = self.index.get_skill(skill_id)
        if not skill:
            logger.warning(f"Skill not found: {skill_id}")
            return None

        old_category = skill.category
        skill.category = new_category
        skill.source = "manual"
        skill.confidence = 1.0

        logger.info(f"Updated category for {skill_id}: {old_category} -> {new_category}")
        return skill

    def update_tags(
        self, skill_id: str, tags: list[str], mode: str = "replace"
    ) -> Optional[SkillMetadata]:
        """Update the tags of a skill.

        Args:
            skill_id: Skill identifier
            tags: New tags
            mode: Operation mode - "replace", "append", or "remove"

        Returns:
            Updated skill metadata or None if not found
        """
        skill = self.index.get_skill(skill_id)
        if not skill:
            logger.warning(f"Skill not found: {skill_id}")
            return None

        if mode == "replace":
            skill.tags = tags
        elif mode == "append":
            for tag in tags:
                if tag not in skill.tags:
                    skill.tags.append(tag)
        elif mode == "remove":
            skill.tags = [t for t in skill.tags if t not in tags]
        else:
            logger.warning(f"Invalid mode: {mode}")
            return None

        skill.source = "manual"
        skill.confidence = 1.0

        logger.info(f"Updated tags for {skill_id} ({mode})")
        return skill

    def update_description(
        self, skill_id: str, description: str, long_description: Optional[str] = None
    ) -> Optional[SkillMetadata]:
        """Update the description of a skill.

        Args:
            skill_id: Skill identifier
            description: New brief description
            long_description: New detailed description (optional)

        Returns:
            Updated skill metadata or None if not found
        """
        skill = self.index.get_skill(skill_id)
        if not skill:
            logger.warning(f"Skill not found: {skill_id}")
            return None

        skill.description = description
        if long_description is not None:
            skill.long_description = long_description

        skill.source = "manual"
        skill.confidence = 1.0

        logger.info(f"Updated description for {skill_id}")
        return skill

    def update_data_types(
        self, skill_id: str, data_types: list[DataType]
    ) -> Optional[SkillMetadata]:
        """Update the input data types of a skill.

        Args:
            skill_id: Skill identifier
            data_types: New data types

        Returns:
            Updated skill metadata or None if not found
        """
        skill = self.index.get_skill(skill_id)
        if not skill:
            logger.warning(f"Skill not found: {skill_id}")
            return None

        skill.input_data_types = data_types
        skill.source = "manual"
        skill.confidence = 1.0

        logger.info(f"Updated data types for {skill_id}")
        return skill

    def update_statistical_concept(
        self, skill_id: str, concept: Optional[str]
    ) -> Optional[SkillMetadata]:
        """Update the statistical concept of a skill.

        Args:
            skill_id: Skill identifier
            concept: New statistical concept or None to remove

        Returns:
            Updated skill metadata or None if not found
        """
        skill = self.index.get_skill(skill_id)
        if not skill:
            logger.warning(f"Skill not found: {skill_id}")
            return None

        skill.statistical_concept = concept
        skill.source = "manual"
        skill.confidence = 1.0

        logger.info(f"Updated statistical concept for {skill_id}")
        return skill

    def update_dependencies(
        self, skill_id: str, dependencies: list[str], mode: str = "replace"
    ) -> Optional[SkillMetadata]:
        """Update the dependencies of a skill.

        Args:
            skill_id: Skill identifier
            dependencies: New dependencies
            mode: Operation mode - "replace", "append", or "remove"

        Returns:
            Updated skill metadata or None if not found
        """
        skill = self.index.get_skill(skill_id)
        if not skill:
            logger.warning(f"Skill not found: {skill_id}")
            return None

        if mode == "replace":
            skill.dependencies = dependencies
        elif mode == "append":
            for dep in dependencies:
                if dep not in skill.dependencies:
                    skill.dependencies.append(dep)
        elif mode == "remove":
            skill.dependencies = [d for d in skill.dependencies if d not in dependencies]
        else:
            logger.warning(f"Invalid mode: {mode}")
            return None

        skill.source = "manual"
        skill.confidence = 1.0

        logger.info(f"Updated dependencies for {skill_id} ({mode})")
        return skill

    def add_use_case(self, skill_id: str, use_case: str) -> Optional[SkillMetadata]:
        """Add a use case to a skill.

        Args:
            skill_id: Skill identifier
            use_case: New use case description

        Returns:
            Updated skill metadata or None if not found
        """
        skill = self.index.get_skill(skill_id)
        if not skill:
            logger.warning(f"Skill not found: {skill_id}")
            return None

        if use_case not in skill.use_cases:
            skill.use_cases.append(use_case)
            skill.source = "manual"
            skill.confidence = 1.0
            logger.info(f"Added use case for {skill_id}")

        return skill

    def update_custom_field(
        self, skill_id: str, field_name: str, field_value: Any
    ) -> Optional[SkillMetadata]:
        """Update a custom field for a skill.

        Args:
            skill_id: Skill identifier
            field_name: Custom field name
            field_value: Custom field value

        Returns:
            Updated skill metadata or None if not found
        """
        skill = self.index.get_skill(skill_id)
        if not skill:
            logger.warning(f"Skill not found: {skill_id}")
            return None

        skill.custom_fields[field_name] = field_value
        skill.source = "manual"
        skill.confidence = 1.0

        logger.info(f"Updated custom field '{field_name}' for {skill_id}")
        return skill

    def bulk_update(self, updates: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        """Update multiple skills at once.

        Args:
            updates: Dictionary mapping skill_id to update parameters

        Returns:
            Dictionary mapping skill_id to success status
        """
        results = {}

        for skill_id, params in updates.items():
            skill = self.index.get_skill(skill_id)
            if not skill:
                results[skill_id] = False
                continue

            try:
                # Apply each update parameter
                for key, value in params.items():
                    if hasattr(skill, key):
                        setattr(skill, key, value)

                skill.source = "manual"
                skill.confidence = 1.0
                results[skill_id] = True
                logger.info(f"Bulk updated {skill_id}")

            except Exception as e:
                logger.error(f"Failed to update {skill_id}: {e}")
                results[skill_id] = False

        return results

    def review_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Generate a review summary for a skill.

        Args:
            skill_id: Skill identifier

        Returns:
            Review summary dictionary or None if not found
        """
        skill = self.index.get_skill(skill_id)
        if not skill:
            return None

        return {
            "id": skill.id,
            "name": skill.name,
            "category": skill.category.value,
            "description": skill.description,
            "tags": skill.tags,
            "data_types": [dt.value for dt in skill.input_data_types],
            "statistical_concept": skill.statistical_concept,
            "dependencies": skill.dependencies,
            "use_cases": skill.use_cases,
            "source": skill.source,
            "confidence": skill.confidence,
            "suggestions": self._generate_suggestions(skill),
        }

    def _generate_suggestions(self, skill: SkillMetadata) -> list[str]:
        """Generate improvement suggestions for a skill.

        Args:
            skill: Skill to analyze

        Returns:
            List of suggestions
        """
        suggestions = []

        if skill.confidence < 0.8:
            suggestions.append("Consider manually reviewing this skill (low confidence)")

        if not skill.long_description:
            suggestions.append("Add a long description for better understanding")

        if not skill.use_cases:
            suggestions.append("Add example use cases")

        if skill.category == SkillCategory.STATISTICAL_METHOD and not skill.statistical_concept:
            suggestions.append("Specify the statistical concept")

        if not skill.tags:
            suggestions.append("Add descriptive tags for better searchability")

        return suggestions

    def export_skill_metadata(self, skill_id: str, output_path: Path) -> bool:
        """Export skill metadata to a JSON file.

        Args:
            skill_id: Skill identifier
            output_path: Path to output file

        Returns:
            True if successful
        """
        skill = self.index.get_skill(skill_id)
        if not skill:
            logger.warning(f"Skill not found: {skill_id}")
            return False

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(skill.model_dump_json(indent=2))

            logger.info(f"Exported metadata for {skill_id} to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export metadata: {e}")
            return False
