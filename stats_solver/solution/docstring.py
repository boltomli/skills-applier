"""Docstring generator for generated code."""

import logging

from ..skills.metadata_schema import SkillMetadata
from ..llm.base import LLMProvider

logger = logging.getLogger(__name__)


class DocstringGenerator:
    """Generator for Python docstrings."""

    def __init__(self, llm_provider: LLMProvider | None = None) -> None:
        """Initialize docstring generator.

        Args:
            llm_provider: LLM provider for enhanced generation
        """
        self.llm_provider = llm_provider

    def generate(
        self, skill: SkillMetadata, problem_description: str | None = None, use_llm: bool = False
    ) -> str:
        """Generate a docstring for a skill.

        Args:
            skill: Skill metadata
            problem_description: Optional problem description
            use_llm: Whether to use LLM for generation

        Returns:
            Generated docstring
        """
        if use_llm and self.llm_provider:
            return self._generate_with_llm(skill, problem_description)
        else:
            return self._generate_with_template(skill, problem_description)

    def _generate_with_template(
        self, skill: SkillMetadata, problem_description: str | None = None
    ) -> str:
        """Generate docstring using template.

        Args:
            skill: Skill metadata
            problem_description: Optional problem description

        Returns:
            Generated docstring
        """
        lines = []

        # Summary line
        summary = skill.description
        if problem_description:
            summary = f"{summary} - {problem_description}"
        lines.append(summary)
        lines.append("")

        # Extended description
        if skill.long_description:
            lines.append(skill.long_description)
            lines.append("")

        # Parameters section
        lines.append("Parameters")
        lines.append("----------")
        lines.append("data : array-like")
        lines.append(f"    {skill.description}")
        lines.append("")

        # Returns section
        lines.append("Returns")
        lines.append("-------")
        output_type = skill.output_format or "result"
        lines.append(f"{output_type} : {output_type}")
        lines.append(f"    {skill.description}")
        lines.append("")

        # Examples section
        lines.append("Examples")
        lines.append("--------")
        lines.append(">>> import numpy as np")
        lines.append(">>> data = np.array([1, 2, 3, 4, 5])")
        func_name = skill.id.replace("-", "_")
        lines.append(f">>> result = {func_name}(data)")
        lines.append(">>> print(result)")
        lines.append("")

        # Notes section
        if skill.assumptions:
            lines.append("Notes")
            lines.append("-----")
            for assumption in skill.assumptions:
                lines.append(f"- {assumption}")
            lines.append("")

        return "\n".join(lines)

    async def _generate_with_llm(
        self, skill: SkillMetadata, problem_description: str | None = None
    ) -> str:
        """Generate docstring using LLM.

        Args:
            skill: Skill metadata
            problem_description: Optional problem description

        Returns:
            Generated docstring
        """
        if not self.llm_provider:
            raise RuntimeError("LLM provider not configured")

        prompt = self._build_generation_prompt(skill, problem_description)

        try:
            result = await self.llm_provider.generate(
                prompt,
                system_prompt="You are an expert technical writer. Generate clear, comprehensive Python docstrings following NumPy documentation style.",
            )

            return result.content

        except Exception as e:
            logger.error(f"LLM docstring generation failed: {e}")
            return self._generate_with_template(skill, problem_description)

    def _build_generation_prompt(
        self, skill: SkillMetadata, problem_description: str | None = None
    ) -> str:
        """Build docstring generation prompt.

        Args:
            skill: Skill metadata
            problem_description: Optional problem description

        Returns:
            Prompt string
        """
        parts = [
            "Generate a NumPy-style docstring for the following function:",
            "",
            f"**Function Name**: {skill.id.replace('-', '_')}",
            f"**Purpose**: {skill.description}",
            "",
        ]

        if problem_description:
            parts.append(f"**Problem Context**: {problem_description}")
            parts.append("")

        if skill.long_description:
            parts.append(f"**Extended Description**: {skill.long_description}")
            parts.append("")

        if skill.statistical_concept:
            parts.append(f"**Statistical Concept**: {skill.statistical_concept}")
            parts.append("")

        if skill.assumptions:
            parts.append("**Assumptions**:")
            for assumption in skill.assumptions:
                parts.append(f"- {assumption}")
            parts.append("")

        if skill.use_cases:
            parts.append("**Use Cases**:")
            for use_case in skill.use_cases:
                parts.append(f"- {use_case}")
            parts.append("")

        parts.append("Generate a docstring with the following sections:")
        parts.append("- Brief summary (one line)")
        parts.append("- Extended description (if applicable)")
        parts.append("- Parameters section")
        parts.append("- Returns section")
        parts.append("- Examples section with sample code")
        parts.append("- Notes section (if there are assumptions or important notes)")

        return "\n".join(parts)

    def generate_function_docstring(
        self,
        function_name: str,
        parameters: dict[str, str],
        returns: str,
        description: str,
        examples: list[str] | None = None,
    ) -> str:
        """Generate a docstring for a specific function.

        Args:
            function_name: Name of the function
            parameters: Dictionary of parameter names to descriptions
            returns: Return value description
            description: Function description
            examples: Optional list of example code lines

        Returns:
            Generated docstring
        """
        lines = [description, ""]

        # Parameters
        if parameters:
            lines.append("Parameters")
            lines.append("----------")
            for param_name, param_desc in parameters.items():
                lines.append(f"{param_name} : type")
                lines.append(f"    {param_desc}")
            lines.append("")

        # Returns
        lines.append("Returns")
        lines.append("-------")
        lines.append("result : type")
        lines.append(f"    {returns}")
        lines.append("")

        # Examples
        if examples:
            lines.append("Examples")
            lines.append("--------")
            for example in examples:
                lines.append(f">>> {example}")
            lines.append("")

        return "\n".join(lines)

    def generate_module_docstring(
        self,
        module_name: str,
        description: str,
        classes: dict[str, str] | None = None,
        functions: dict[str, str] | None = None,
    ) -> str:
        """Generate a module-level docstring.

        Args:
            module_name: Name of the module
            description: Module description
            classes: Optional dictionary of class names to descriptions
            functions: Optional dictionary of function names to descriptions

        Returns:
            Generated module docstring
        """
        lines = [
            description,
            "",
        ]

        # Classes
        if classes:
            lines.append("Classes")
            lines.append("-------")
            for class_name, class_desc in classes.items():
                lines.append(f"{class_name}")
                lines.append(f"    {class_desc}")
            lines.append("")

        # Functions
        if functions:
            lines.append("Functions")
            lines.append("---------")
            for func_name, func_desc in functions.items():
                lines.append(f"{func_name}")
                lines.append(f"    {func_desc}")
            lines.append("")

        return "\n".join(lines)
