"""Code generator for creating Python solutions."""

import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass

from ..skills.metadata_schema import SkillMetadata
from ..llm.base import LLMProvider
from .templates import TemplateManager
from .docstring import DocstringGenerator
from .dependencies import DependencyGenerator

logger = logging.getLogger(__name__)


@dataclass
class GeneratedCode:
    """Generated Python code."""

    code: str
    imports: List[str]
    docstring: str
    metadata: Dict[str, Any]


@dataclass
class GenerationContext:
    """Context for code generation."""

    skill: SkillMetadata
    problem_description: str
    data_description: Optional[str] = None
    output_requirements: Optional[str] = None
    additional_context: Dict[str, Any] = None


class CodeGenerator:
    """Generator for creating Python code solutions."""

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        template_manager: Optional[TemplateManager] = None,
    ) -> None:
        """Initialize code generator.

        Args:
            llm_provider: LLM provider for enhanced generation
            template_manager: Template manager for code templates
        """
        self.llm_provider = llm_provider
        self.template_manager = template_manager or TemplateManager()
        self.docstring_generator = DocstringGenerator(llm_provider)
        self.dependency_generator = DependencyGenerator()

    async def generate(self, context: GenerationContext, use_llm: bool = False) -> GeneratedCode:
        """Generate Python code for a skill.

        Args:
            context: Generation context
            use_llm: Whether to use LLM for generation

        Returns:
            Generated code
        """
        if use_llm and self.llm_provider:
            return await self._generate_with_llm(context)
        else:
            return self._generate_with_template(context)

    def _generate_with_template(self, context: GenerationContext) -> GeneratedCode:
        """Generate code using templates.

        Args:
            context: Generation context

        Returns:
            Generated code
        """
        # Get template for skill category
        template = self.template_manager.get_template(context.skill.category)

        # Prepare template variables
        variables = {
            "skill_name": context.skill.name,
            "skill_id": context.skill.id,
            "description": context.skill.description,
            "problem_description": context.problem_description,
            "data_description": context.data_description or "data",
            "output_requirements": context.output_requirements or "result",
            "dependencies": context.skill.dependencies,
        }

        # Generate code from template
        code = template.render(**variables)

        # Extract imports
        imports = self.dependency_generator.generate_imports(context.skill.dependencies)

        # Generate docstring
        docstring = self.docstring_generator.generate(context)

        return GeneratedCode(
            code=code,
            imports=imports,
            docstring=docstring,
            metadata={
                "method": "template",
                "skill_id": context.skill.id,
            },
        )

    async def _generate_with_llm(self, context: GenerationContext) -> GeneratedCode:
        """Generate code using LLM.

        Args:
            context: Generation context

        Returns:
            Generated code
        """
        if not self.llm_provider:
            raise RuntimeError("LLM provider not configured")

        prompt = self._build_generation_prompt(context)

        try:
            result = await self.llm_provider.generate_json(
                prompt,
                system_prompt="You are an expert Python programmer specializing in statistics and data analysis. Generate clean, well-documented code.",
            )

            code = result.get("code", "")
            imports = result.get("imports", context.skill.dependencies)
            docstring = result.get("docstring", "")

            return GeneratedCode(
                code=code,
                imports=imports,
                docstring=docstring,
                metadata={
                    "method": "llm",
                    "skill_id": context.skill.id,
                    "confidence": result.get("confidence", 0.8),
                },
            )
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            # Fallback to template
            return self._generate_with_template(context)

    def _build_generation_prompt(self, context: GenerationContext) -> str:
        """Build code generation prompt.

        Args:
            context: Generation context

        Returns:
            Prompt string
        """
        return f"""Generate Python code for the following statistical/mathematical skill:

**Skill**: {context.skill.name}
**Description**: {context.skill.description}
**Category**: {context.skill.category.value}

**Problem to Solve**: {context.problem_description}

**Data Description**: {context.data_description or "Numerical data"}

**Output Requirements**: {context.output_requirements or "Return the result"}

**Dependencies Available**: {', '.join(context.skill.dependencies) if context.skill.dependencies else 'None'}

**Additional Context**:
- Statistical Concept: {context.skill.statistical_concept or 'None'}
- Assumptions: {', '.join(context.skill.assumptions) if context.skill.assumptions else 'None'}

Return a JSON object with:
- code: Complete Python code (including imports, function definition, and example usage)
- imports: List of import statements
- docstring: Docstring for the main function
- confidence: Confidence in generated code (0.0 to 1.0)

Requirements:
1. Write clean, PEP 8 compliant code
2. Include comprehensive docstrings
3. Add error handling where appropriate
4. Include example usage in a if __name__ == "__main__" block
5. Use the specified dependencies
6. Return the result in the specified format"""

    def format_code(self, generated: GeneratedCode) -> str:
        """Format generated code into a complete file.

        Args:
            generated: Generated code

        Returns:
            Formatted complete code
        """
        lines = []

        # Add imports
        if generated.imports:
            lines.append("# Imports")
            lines.extend(generated.imports)
            lines.append("")

        # Add main function with docstring
        lines.append(generated.code)

        return "\n".join(lines)

    async def generate_multiple(
        self, contexts: List[GenerationContext], use_llm: bool = False
    ) -> List[GeneratedCode]:
        """Generate code for multiple contexts.

        Args:
            contexts: List of generation contexts
            use_llm: Whether to use LLM

        Returns:
            List of generated code
        """
        results = []

        for context in contexts:
            result = await self.generate(context, use_llm)
            results.append(result)

        return results

    def generate_script(self, generated: GeneratedCode, script_name: str) -> str:
        """Generate a complete executable script.

        Args:
            generated: Generated code
            script_name: Name of the script

        Returns:
            Complete script content
        """
        script_parts = [
            "#!/usr/bin/env python3",
            "# -*- coding: utf-8 -*-",
            '"""',
            script_name,
            "",
            generated.docstring,
            '"""',
            "",
            self.format_code(generated),
        ]
        return "\n".join(script_parts)

    async def generate_with_chain(
        self, contexts: List[GenerationContext], chain_description: str, use_llm: bool = False
    ) -> str:
        """Generate a complete script from a chain of contexts.

        Args:
            contexts: List of generation contexts in order
            chain_description: Description of the chain
            use_llm: Whether to use LLM

        Returns:
            Complete script with chained functions
        """
        lines = [
            "#!/usr/bin/env python3",
            "# -*- coding: utf-8 -*-",
            '"""',
            f"{chain_description}",
            '"""',
            "",
            "# Imports",
        ]

        # Collect all imports
        all_imports = set()
        for context in contexts:
            all_imports.update(context.skill.dependencies)

        import_lines = self.dependency_generator.generate_imports(list(all_imports))
        lines.extend(import_lines)
        lines.append("")

        # Generate each function
        for i, context in enumerate(contexts, 1):
            generated = await self.generate(context, use_llm)
            lines.append(f"# Step {i}: {context.skill.name}")
            lines.append(generated.code)
            lines.append("")

        # Add main function to orchestrate the chain
        lines.append("# Main workflow")
        lines.append("def main():")
        lines.append('    """Execute the complete analysis workflow."""')
        for i, context in enumerate(contexts, 1):
            func_name = self._infer_function_name(context.skill)
            lines.append(f"    # Step {i}: {context.skill.description}")
            lines.append(f"    result_{i} = {func_name}(...)")
        lines.append("")
        lines.append("    return result_" + str(len(contexts)))
        lines.append("")
        lines.append("")
        lines.append("if __name__ == '__main__':")
        lines.append("    main()")

        return "\n".join(lines)

    def _infer_function_name(self, skill: SkillMetadata) -> str:
        """Infer a suitable function name from skill metadata.

        Args:
            skill: Skill metadata

        Returns:
            Function name
        """
        # Convert skill ID to snake_case function name
        name = skill.id.replace("-", "_")
        return f"perform_{name}"
