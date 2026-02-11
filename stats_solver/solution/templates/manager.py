"""Template manager for code generation templates."""

import logging
from pathlib import Path

from ..skills.metadata_schema import SkillCategory
from .base import BaseTemplate

logger = logging.getLogger(__name__)


class TemplateManager:
    """Manager for code generation templates."""

    def __init__(self, templates_dir: Path | None = None) -> None:
        """Initialize template manager.

        Args:
            templates_dir: Directory containing template files
        """
        self.templates_dir = templates_dir or Path(__file__).parent
        self._templates: dict[str, BaseTemplate] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load templates from files."""
        # Import template classes
        from .statistical_method import StatisticalMethodTemplate
        from .mathematical_implementation import MathematicalImplementationTemplate
        from .data_analysis import DataAnalysisTemplate
        from .visualization import VisualizationTemplate

        # Register templates
        self.register_template(SkillCategory.STATISTICAL_METHOD, StatisticalMethodTemplate())
        self.register_template(
            SkillCategory.MATHEMATICAL_IMPLEMENTATION, MathematicalImplementationTemplate()
        )
        self.register_template(SkillCategory.DATA_ANALYSIS, DataAnalysisTemplate())
        self.register_template(SkillCategory.VISUALIZATION, VisualizationTemplate())

        logger.info(f"Loaded {len(self._templates)} templates")

    def register_template(self, category: str, template: BaseTemplate) -> None:
        """Register a template for a category.

        Args:
            category: Skill category
            template: Template instance
        """
        self._templates[category] = template
        logger.debug(f"Registered template for category: {category}")

    def get_template(self, category: SkillCategory) -> BaseTemplate:
        """Get template for a skill category.

        Args:
            category: Skill category

        Returns:
            Template instance
        """
        template = self._templates.get(category.value)

        if template is None:
            logger.warning(f"No template found for category: {category.value}, using default")
            return self._get_default_template()

        return template

    def _get_default_template(self) -> BaseTemplate:
        """Get default template for unknown categories.

        Returns:
            Default template
        """
        from .mathematical_implementation import MathematicalImplementationTemplate

        return MathematicalImplementationTemplate()

    def list_templates(self) -> dict[str, str]:
        """List all registered templates.

        Returns:
            Dictionary mapping category to template name
        """
        return {category: template.get_name() for category, template in self._templates.items()}
