"""Skill chain builder for multi-step analysis workflows."""

import logging
from typing import Any
from dataclasses import dataclass
from enum import Enum

from ..skills.metadata_schema import SkillMetadata
from ..skills.index import SkillIndex
from ..problem.classifier import ProblemType
from ..problem.extractor import ProblemFeatures
from .prerequisites import PrerequisiteChecker, PrerequisiteCheckResult

logger = logging.getLogger(__name__)


class ChainStepType(str, Enum):
    """Types of chain steps."""

    PREPARATION = "preparation"
    CORE_ANALYSIS = "core_analysis"
    POST_PROCESSING = "post_processing"
    VALIDATION = "validation"
    VISUALIZATION = "visualization"


@dataclass
class ChainStep:
    """A single step in a skill chain."""

    skill: SkillMetadata
    step_type: ChainStepType
    order: int
    description: str
    depends_on: list[str]  # IDs of skills this step depends on
    estimated_time: str | None = None


@dataclass
class SkillChain:
    """A chain of skills for multi-step analysis."""

    name: str
    description: str
    steps: list[ChainStep]
    total_steps: int
    estimated_duration: str
    prerequisites_satisfied: bool
    confidence: float
    metadata: dict[str, Any] = None


class SkillChainBuilder:
    """Builder for creating skill chains from recommendations."""

    # Common workflow patterns
    WORKFLOW_PATTERNS = {
        ProblemType.HYPOTHESIS_TEST: [
            ChainStepType.PREPARATION,  # Data loading/validation
            ChainStepType.CORE_ANALYSIS,  # Statistical test
            ChainStepType.VALIDATION,  # Assumption checking
            ChainStepType.VISUALIZATION,  # Results visualization
        ],
        ProblemType.REGRESSION: [
            ChainStepType.PREPARATION,
            ChainStepType.CORE_ANALYSIS,
            ChainStepType.VALIDATION,
            ChainStepType.VISUALIZATION,
        ],
        ProblemType.CLASSIFICATION: [
            ChainStepType.PREPARATION,
            ChainStepType.CORE_ANALYSIS,
            ChainStepType.POST_PROCESSING,
            ChainStepType.VISUALIZATION,
        ],
        ProblemType.DESCRIPTIVE: [
            ChainStepType.PREPARATION,
            ChainStepType.CORE_ANALYSIS,
            ChainStepType.VISUALIZATION,
        ],
        ProblemType.OPTIMIZATION: [
            ChainStepType.PREPARATION,
            ChainStepType.CORE_ANALYSIS,
            ChainStepType.VALIDATION,
        ],
        ProblemType.SIMULATION: [
            ChainStepType.PREPARATION,
            ChainStepType.CORE_ANALYSIS,
            ChainStepType.POST_PROCESSING,
            ChainStepType.VISUALIZATION,
        ],
    }

    def __init__(
        self, skill_index: SkillIndex, prereq_checker: PrerequisiteChecker | None = None
    ) -> None:
        """Initialize skill chain builder.

        Args:
            skill_index: Skill index to use
            prereq_checker: Prerequisite checker instance
        """
        self.skill_index = skill_index
        self.prereq_checker = prereq_checker or PrerequisiteChecker(skill_index)

    async def build_chain(
        self,
        core_skill: SkillMetadata,
        problem_type: ProblemType,
        problem_features: ProblemFeatures,
        available_skills: list[SkillMetadata] | None = None,
    ) -> SkillChain:
        """Build a skill chain starting from a core skill.

        Args:
            core_skill: The primary skill for the analysis
            problem_type: Type of problem being solved
            problem_features: Extracted problem features
            available_skills: Available skills to build chain from

        Returns:
            Constructed skill chain
        """
        if available_skills is None:
            available_skills = self.skill_index.get_all_skills()

        # Get workflow pattern for problem type
        pattern = self.WORKFLOW_PATTERNS.get(
            problem_type,
            [ChainStepType.PREPARATION, ChainStepType.CORE_ANALYSIS, ChainStepType.VISUALIZATION],
        )

        steps = []
        step_order = 0

        # Build chain following the pattern
        for step_type in pattern:
            step_skills = self._find_skills_for_step(
                step_type, core_skill, available_skills, problem_features
            )

            for skill in step_skills:
                depends_on = self._determine_dependencies(skill, steps, step_order)

                step = ChainStep(
                    skill=skill,
                    step_type=step_type,
                    order=step_order,
                    description=self._generate_step_description(skill, step_type),
                    depends_on=depends_on,
                    estimated_time=self._estimate_step_time(skill),
                )
                steps.append(step)
                step_order += 1

        # Check prerequisites
        prereq_results = await self._check_chain_prerequisites(steps, available_skills)
        all_satisfied = all(r.all_satisfied for r in prereq_results)

        # Calculate confidence
        confidence = self._calculate_chain_confidence(steps, prereq_results)

        return SkillChain(
            name=self._generate_chain_name(core_skill, problem_type),
            description=self._generate_chain_description(core_skill, problem_type),
            steps=steps,
            total_steps=len(steps),
            estimated_duration=self._estimate_chain_duration(steps),
            prerequisites_satisfied=all_satisfied,
            confidence=confidence,
            metadata={
                "problem_type": problem_type.value,
                "core_skill": core_skill.id,
                "prerequisite_results": [r.__dict__ for r in prereq_results],
            },
        )

    def _find_skills_for_step(
        self,
        step_type: ChainStepType,
        core_skill: SkillMetadata,
        available_skills: list[SkillMetadata],
        problem_features: ProblemFeatures,
    ) -> list[SkillMetadata]:
        """Find skills for a specific step type.

        Args:
            step_type: Type of step
            core_skill: Core skill
            available_skills: Available skills
            problem_features: Problem features

        Returns:
            List of skills for this step
        """
        skills = []

        if step_type == ChainStepType.CORE_ANALYSIS:
            # Core analysis step uses the main skill
            skills.append(core_skill)

        elif step_type == ChainStepType.PREPARATION:
            # Find data preparation skills
            preparation_keywords = ["load", "clean", "prepare", "validate", "preprocess"]
            for skill in available_skills:
                if skill.id != core_skill.id:
                    if any(
                        kw in skill.id.lower() or kw in skill.description.lower()
                        for kw in preparation_keywords
                    ):
                        skills.append(skill)

        elif step_type == ChainStepType.VALIDATION:
            # Find validation/assumption checking skills
            validation_keywords = ["validate", "check", "test", "assumption", "diagnostic"]
            for skill in available_skills:
                if skill.id != core_skill.id:
                    if any(
                        kw in skill.id.lower() or kw in skill.description.lower()
                        for kw in validation_keywords
                    ):
                        skills.append(skill)

        elif step_type == ChainStepType.POST_PROCESSING:
            # Find post-processing skills
            post_keywords = ["post", "process", "transform", "format", "export"]
            for skill in available_skills:
                if skill.id != core_skill.id:
                    if any(
                        kw in skill.id.lower() or kw in skill.description.lower()
                        for kw in post_keywords
                    ):
                        skills.append(skill)

        elif step_type == ChainStepType.VISUALIZATION:
            # Find visualization skills
            if problem_features.requires_visualization or skill in core_skill.tags:
                viz_keywords = ["plot", "graph", "chart", "visualize", "display"]
                for skill in available_skills:
                    if skill.id != core_skill.id:
                        if any(
                            kw in skill.id.lower()
                            or kw in skill.description.lower()
                            or kw in " ".join(skill.tags).lower()
                            for kw in viz_keywords
                        ):
                            skills.append(skill)

        return skills[:3]  # Limit to 3 skills per step

    def _determine_dependencies(
        self, skill: SkillMetadata, existing_steps: list[ChainStep], current_order: int
    ) -> list[str]:
        """Determine which existing steps this step depends on.

        Args:
            skill: Current skill
            existing_steps: Already added steps
            current_order: Current step order

        Returns:
            List of step IDs this depends on
        """
        dependencies = []

        # Check explicit prerequisites
        for prereq_id in skill.prerequisites:
            for step in existing_steps:
                if prereq_id == step.skill.id:
                    dependencies.append(f"step_{step.order}")

        # Core analysis depends on preparation
        if any(
            s.id == skill.id and s.step_type == ChainStepType.CORE_ANALYSIS for s in existing_steps
        ):
            prep_steps = [s for s in existing_steps if s.step_type == ChainStepType.PREPARATION]
            dependencies.extend([f"step_{s.order}" for s in prep_steps])

        return list(set(dependencies))

    def _generate_step_description(self, skill: SkillMetadata, step_type: ChainStepType) -> str:
        """Generate description for a chain step.

        Args:
            skill: Skill for this step
            step_type: Type of step

        Returns:
            Step description
        """
        type_descriptions = {
            ChainStepType.PREPARATION: "Prepare data",
            ChainStepType.CORE_ANALYSIS: "Perform analysis",
            ChainStepType.POST_PROCESSING: "Process results",
            ChainStepType.VALIDATION: "Validate assumptions",
            ChainStepType.VISUALIZATION: "Visualize results",
        }

        prefix = type_descriptions.get(step_type, "Execute")
        return f"{prefix}: {skill.description}"

    def _estimate_step_time(self, skill: SkillMetadata) -> str:
        """Estimate time required for a step.

        Args:
            skill: Skill to estimate time for

        Returns:
            Time estimate string
        """
        # Simple heuristic based on complexity
        if skill.complexity and "O(n)" in skill.complexity:
            if "log" in skill.complexity:
                return "< 1 minute"
            elif skill.complexity.startswith("O(n^2)"):
                return "1-5 minutes"

        return "< 1 minute"

    async def _check_chain_prerequisites(
        self, steps: list[ChainStep], available_skills: list[SkillMetadata]
    ) -> list[PrerequisiteCheckResult]:
        """Check prerequisites for all steps in the chain.

        Args:
            steps: Chain steps
            available_skills: Available skills

        Returns:
            List of prerequisite check results
        """
        results = []

        for step in steps:
            result = await self.prereq_checker.check_prerequisites(step.skill, available_skills)
            results.append(result)

        return results

    def _calculate_chain_confidence(
        self, steps: list[ChainStep], prereq_results: list[PrerequisiteCheckResult]
    ) -> float:
        """Calculate overall confidence in the chain.

        Args:
            steps: Chain steps
            prereq_results: Prerequisite check results

        Returns:
            Confidence score (0.0 to 1.0)
        """
        if not steps:
            return 0.0

        # Start with base confidence
        confidence = 0.8

        # Penalize for missing prerequisites
        missing_count = sum(r.missing_count for r in prereq_results)
        if missing_count > 0:
            confidence -= min(missing_count * 0.05, 0.3)

        # Boost for well-structured chains
        core_steps = sum(1 for s in steps if s.step_type == ChainStepType.CORE_ANALYSIS)
        if core_steps == 1:
            confidence += 0.1

        # Ensure confidence is in valid range
        return max(0.0, min(1.0, confidence))

    def _generate_chain_name(self, core_skill: SkillMetadata, problem_type: ProblemType) -> str:
        """Generate name for the chain.

        Args:
            core_skill: Core skill
            problem_type: Problem type

        Returns:
            Chain name
        """
        return f"{core_skill.name} Workflow"

    def _generate_chain_description(
        self, core_skill: SkillMetadata, problem_type: ProblemType
    ) -> str:
        """Generate description for the chain.

        Args:
            core_skill: Core skill
            problem_type: Problem type

        Returns:
            Chain description
        """
        return f"Multi-step workflow for {problem_type.value.replace('_', ' ')} using {core_skill.name}"

    def _estimate_chain_duration(self, steps: list[ChainStep]) -> str:
        """Estimate total duration for the chain.

        Args:
            steps: Chain steps

        Returns:
            Duration estimate string
        """
        # Sum up step times (simplified)
        total_minutes = len(steps) * 1  # Assume 1 minute per step

        if total_minutes < 5:
            return "< 5 minutes"
        elif total_minutes < 15:
            return "5-15 minutes"
        else:
            return f"~{total_minutes} minutes"

    async def build_alternative_chains(
        self,
        core_skills: list[SkillMetadata],
        problem_type: ProblemType,
        problem_features: ProblemFeatures,
        max_chains: int = 3,
    ) -> list[SkillChain]:
        """Build alternative chains using different core skills.

        Args:
            core_skills: Alternative core skills
            problem_type: Problem type
            problem_features: Problem features
            max_chains: Maximum number of chains to build

        Returns:
            List of alternative chains
        """
        chains = []

        for core_skill in core_skills[:max_chains]:
            chain = await self.build_chain(core_skill, problem_type, problem_features)
            chains.append(chain)

        # Sort by confidence
        chains.sort(key=lambda c: c.confidence, reverse=True)

        return chains

    def visualize_chain(self, chain: SkillChain) -> str:
        """Generate a text-based visualization of the chain.

        Args:
            chain: Chain to visualize

        Returns:
            Text visualization
        """
        lines = [f"Chain: {chain.name}", f"Description: {chain.description}", ""]

        for step in chain.steps:
            dep_str = f" (depends on: {', '.join(step.depends_on)})" if step.depends_on else ""
            time_str = f" [{step.estimated_time}]" if step.estimated_time else ""

            lines.append(
                f"  [{step.order}] {step.skill.name} ({step.step_type.value}){time_str}{dep_str}"
            )
            lines.append(f"      {step.description}")
            lines.append("")

        lines.append(f"Total steps: {chain.total_steps}")
        lines.append(f"Estimated duration: {chain.estimated_duration}")
        lines.append(f"Prerequisites satisfied: {chain.prerequisites_satisfied}")
        lines.append(f"Confidence: {chain.confidence:.2f}")

        return "\n".join(lines)
