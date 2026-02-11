"""Constraint extraction for problem analysis."""

import logging
from enum import Enum
import re

from pydantic import BaseModel

from ..llm.base import LLMProvider

logger = logging.getLogger(__name__)


class ConstraintType(str, Enum):
    """Types of constraints."""

    # Data constraints
    SAMPLE_SIZE = "sample_size"
    DATA_TYPE = "data_type"
    DATA_QUALITY = "data_quality"
    MISSING_VALUES = "missing_values"

    # Statistical constraints
    ASSUMPTIONS = "assumptions"
    DISTRIBUTION = "distribution"
    INDEPENDENCE = "independence"
    NORMALITY = "normality"

    # Practical constraints
    TIME_LIMIT = "time_limit"
    COMPUTATIONAL = "computational"
    RESOURCE = "resource"
    ACCURACY = "accuracy"

    # Output constraints
    OUTPUT_FORMAT = "output_format"
    PRECISION = "precision"
    CONFIDENCE_LEVEL = "confidence_level"

    # Domain constraints
    DOMAIN_RULES = "domain_rules"
    VALIDATION = "validation"

    # General
    UNKNOWN = "unknown"


class Constraint(BaseModel):
    """A single constraint."""

    type: ConstraintType
    description: str
    value: str | None = None
    strict: bool = False
    source: str = "extracted"  # extracted, implied, user_specified


class ConstraintExtractionResult(BaseModel):
    """Result of constraint extraction."""

    constraints: list[Constraint]
    summary: str
    critical_constraints: list[Constraint]
    flexible_constraints: list[Constraint]
    implied_assumptions: list[str]


class ConstraintExtractor:
    """Extractor for constraints from problem descriptions."""

    # Constraint patterns
    CONSTRAINT_PATTERNS = {
        ConstraintType.SAMPLE_SIZE: [
            r"(\d+)\s+(sample|observation|record|data point)",
            r"sample\s+size\s+(?:of\s+)?(\d+)",
            r"n\s*=\s*(\d+)",
            r"small\s+sample",
            r"large\s+sample",
        ],
        ConstraintType.DATA_TYPE: [
            r"(?:must|should|needs to be)\s+(\w+)\s+(?:data|type)",
            r"(?:only|just)\s+(\w+)\s+data",
            r"require\s+(\w+)",
        ],
        ConstraintType.NORMALITY: [
            r"(?:assume|assuming)\s+normal(?:ity)?",
            r"normal\s+distribution",
            r"gaussian",
        ],
        ConstraintType.INDEPENDENCE: [
            r"(?:assume|assuming)\s+independent",
            r"independent\s+(?:samples?|observation)",
        ],
        ConstraintType.TIME_LIMIT: [
            r"(?:within|under|in)\s+(\d+)\s+(second|minute|hour)",
            r"time\s+limit",
            r"(?:quick|fast)\s+(?:result|response)",
        ],
        ConstraintType.OUTPUT_FORMAT: [
            r"(?:output|result)\s+(?:as|in)\s+(?:a\s+)?(\w+)",
            r"(?:generate|create|produce)\s+a\s+(\w+)",
            r"(?:display|show)\s+(?:as|as\s+a)\s+(\w+)",
        ],
        ConstraintType.CONFIDENCE_LEVEL: [
            r"(\d+)%\s+confidence",
            r"confidence\s+level\s+(?:of\s+)?(\d+)",
            r"(\d+)%\s+(?:confidence|certain)",
        ],
        ConstraintType.ACCURACY: [
            r"(?:accuracy|precision)\s+(?:of|within)\s+([.\d]+)",
            r"error\s+rate\s+(?:below|less\s+than)\s+([.\d]+)",
        ],
    }

    # Value extraction patterns
    VALUE_PATTERNS = {
        "number": r"(\d+(?:\.\d+)?)",
        "percentage": r"(\d+)%",
        "time": r"(\d+)\s+(second|minute|hour)",
    }

    def __init__(self, use_llm: bool = False, llm_provider: LLMProvider | None = None) -> None:
        """Initialize constraint extractor.

        Args:
            use_llm: Whether to use LLM for extraction
            llm_provider: LLM provider instance (required if use_llm=True)
        """
        self.use_llm = use_llm
        self.llm_provider = llm_provider

    async def extract(self, text: str) -> ConstraintExtractionResult:
        """Extract constraints from text.

        Args:
            text: Problem description text

        Returns:
            Constraint extraction result
        """
        if self.use_llm and self.llm_provider:
            return await self._extract_with_llm(text)
        else:
            return self._extract_with_rules(text)

    def _extract_with_rules(self, text: str) -> ConstraintExtractionResult:
        """Extract constraints using rule-based approach.

        Args:
            text: Problem description text

        Returns:
            Constraint extraction result
        """
        text_lower = text.lower()
        constraints = []

        # Extract constraints by type
        for constraint_type, patterns in self.CONSTRAINT_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text_lower, re.IGNORECASE)
                for match in matches:
                    constraint = self._create_constraint_from_match(constraint_type, match, text)
                    constraints.append(constraint)

        # Remove duplicates
        constraints = self._deduplicate_constraints(constraints)

        # Categorize constraints
        critical = [c for c in constraints if c.strict]
        flexible = [c for c in constraints if not c.strict]

        # Extract implied assumptions
        implied = self._extract_implied_assumptions(text_lower, constraints)

        # Generate summary
        summary = self._generate_summary(constraints)

        return ConstraintExtractionResult(
            constraints=constraints,
            summary=summary,
            critical_constraints=critical,
            flexible_constraints=flexible,
            implied_assumptions=implied,
        )

    async def _extract_with_llm(self, text: str) -> ConstraintExtractionResult:
        """Extract constraints using LLM.

        Args:
            text: Problem description text

        Returns:
            Constraint extraction result
        """
        if not self.llm_provider:
            raise RuntimeError("LLM provider not configured")

        prompt = f"""Extract constraints and requirements from the following problem description:

{text}

Return a JSON object with:
- constraints: Array of constraint objects, each with:
  - type: Constraint type (sample_size, data_type, data_quality, missing_values, assumptions, distribution, independence, normality, time_limit, computational, resource, accuracy, output_format, precision, confidence_level, domain_rules, validation, unknown)
  - description: Description of the constraint
  - value: Specific value if mentioned (or null)
  - strict: Boolean indicating if this is a strict requirement
- summary: Brief summary of all constraints
- implied_assumptions: Array of assumptions that can be reasonably implied"""

        try:
            result = await self.llm_provider.generate_json(
                prompt,
                system_prompt="You are an expert in identifying constraints and requirements from problem descriptions.",
            )

            constraints = []
            for c in result.get("constraints", []):
                try:
                    constraints.append(Constraint(**c))
                except Exception as e:
                    logger.warning(f"Failed to parse constraint: {e}")

            critical = [c for c in constraints if c.strict]
            flexible = [c for c in constraints if not c.strict]

            return ConstraintExtractionResult(
                constraints=constraints,
                summary=result.get("summary", ""),
                critical_constraints=critical,
                flexible_constraints=flexible,
                implied_assumptions=result.get("implied_assumptions", []),
            )
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return self._extract_with_rules(text)

    def _create_constraint_from_match(
        self, constraint_type: ConstraintType, match: re.Match, text: str
    ) -> Constraint:
        """Create a constraint from a regex match.

        Args:
            constraint_type: Type of constraint
            match: Regex match object
            text: Original text

        Returns:
            Constraint object
        """
        matched_text = match.group(0)

        # Extract value if available
        value = None
        if match.groups():
            value = match.group(1)

        # Determine if strict
        strict_keywords = ["must", "require", "only", "exactly", "strictly"]
        is_strict = any(kw in matched_text.lower() for kw in strict_keywords)

        return Constraint(
            type=constraint_type,
            description=matched_text,
            value=value,
            strict=is_strict,
            source="extracted",
        )

    def _deduplicate_constraints(self, constraints: list[Constraint]) -> list[Constraint]:
        """Remove duplicate constraints.

        Args:
            constraints: List of constraints

        Returns:
            Deduplicated list
        """
        seen = set()
        unique = []

        for constraint in constraints:
            key = (constraint.type, constraint.description.lower())
            if key not in seen:
                seen.add(key)
                unique.append(constraint)

        return unique

    def _extract_implied_assumptions(self, text: str, constraints: list[Constraint]) -> list[str]:
        """Extract implied assumptions from text and constraints.

        Args:
            text: Lowercase text
            constraints: Extracted constraints

        Returns:
            List of implied assumptions
        """
        assumptions = []

        # Common implied assumptions
        implied_map = {
            "hypothesis test": "Data follows appropriate distribution for the test",
            "regression": "Relationship between variables is approximately linear",
            "correlation": "Variables are measured on interval or ratio scale",
            "sample": "Sample is representative of the population",
        }

        for phrase, assumption in implied_map.items():
            if phrase in text:
                assumptions.append(assumption)

        # Add assumptions based on constraints
        for c in constraints:
            if c.type == ConstraintType.SAMPLE_SIZE and c.value:
                try:
                    n = int(c.value)
                    if n < 30:
                        assumptions.append("Small sample size may limit statistical power")
                except ValueError:
                    pass

        return list(set(assumptions))

    def _generate_summary(self, constraints: list[Constraint]) -> str:
        """Generate a summary of constraints.

        Args:
            constraints: List of constraints

        Returns:
            Summary string
        """
        if not constraints:
            return "No explicit constraints identified"

        by_type: dict[ConstraintType, list[Constraint]] = {}
        for c in constraints:
            if c.type not in by_type:
                by_type[c.type] = []
            by_type[c.type].append(c)

        summary_parts = []

        if by_type.get(ConstraintType.SAMPLE_SIZE):
            summary_parts.append(
                f"Sample size constraints: {len(by_type[ConstraintType.SAMPLE_SIZE])}"
            )

        if by_type.get(ConstraintType.OUTPUT_FORMAT):
            summary_parts.append(
                f"Output format requirements: {len(by_type[ConstraintType.OUTPUT_FORMAT])}"
            )

        critical_count = sum(1 for c in constraints if c.strict)
        if critical_count > 0:
            summary_parts.append(f"{critical_count} strict requirement(s)")

        return (
            "; ".join(summary_parts)
            if summary_parts
            else f"{len(constraints)} constraint(s) identified"
        )

    def get_constraint_by_type(
        self, result: ConstraintExtractionResult, constraint_type: ConstraintType
    ) -> list[Constraint]:
        """Get all constraints of a specific type.

        Args:
            result: Extraction result
            constraint_type: Type to filter by

        Returns:
            List of constraints of that type
        """
        return [c for c in result.constraints if c.type == constraint_type]

    def merge_constraints(
        self, results: list[ConstraintExtractionResult]
    ) -> ConstraintExtractionResult:
        """Merge multiple constraint extraction results.

        Args:
            results: List of extraction results

        Returns:
            Merged result
        """
        all_constraints = []
        for result in results:
            all_constraints.extend(result.constraints)

        all_constraints = self._deduplicate_constraints(all_constraints)

        critical = [c for c in all_constraints if c.strict]
        flexible = [c for c in all_constraints if not c.strict]

        all_implied = []
        for result in results:
            all_implied.extend(result.implied_assumptions)

        return ConstraintExtractionResult(
            constraints=all_constraints,
            summary=f"Merged from {len(results)} sources: {len(all_constraints)} total constraints",
            critical_constraints=critical,
            flexible_constraints=flexible,
            implied_assumptions=list(set(all_implied)),
        )


# Import at end to avoid circular dependency
