"""Skill classifier for categorizing skills."""

import logging
from typing import List, Optional, Set

from .metadata_schema import SkillMetadata, SkillCategory, DataType
from ..llm.base import LLMProvider

logger = logging.getLogger(__name__)


class SkillClassifier:
    """Classifier for categorizing skills into types."""

    # Keywords indicating statistical methods
    STATISTICAL_KEYWORDS = {
        "test",
        "hypothesis",
        "regression",
        "correlation",
        "analysis",
        "distribution",
        "probability",
        "confidence",
        "significance",
        "variance",
        "standard deviation",
        "mean",
        "median",
        "mode",
        "p-value",
        "anova",
        "chi-square",
        "t-test",
        "z-test",
        "bayes",
        "bayesian",
        "monte carlo",
        "bootstrap",
        "sampling",
        "estimate",
        "estimation",
        "fit",
        "fitting",
        "model",
        "modeling",
        "predict",
        "prediction",
        "forecast",
        "forecasting",
        "trend",
        "outlier",
        "anomaly",
        "cluster",
        "clustering",
        "classify",
        "classification",
        "dimensionality",
        "pca",
        "factor",
        "latent",
    }

    # Keywords indicating mathematical implementations
    MATH_KEYWORDS = {
        "algorithm",
        "sort",
        "search",
        "graph",
        "tree",
        "heap",
        "stack",
        "queue",
        "hash",
        "dynamic programming",
        "recursion",
        "iteration",
        "matrix",
        "vector",
        "transform",
        "rotation",
        "geometry",
        "calculus",
        "integration",
        "differentiation",
        "derivative",
        "equation",
        "solve",
        "root",
        "polynomial",
        "factorial",
        "fibonacci",
        "prime",
        "combinatorial",
        "permutation",
        "sequence",
        "series",
        "limit",
        "convergence",
        "fractal",
        "bezier",
        "spline",
        "interpolation",
        "optimization",
        "minimize",
        "maximize",
        "coordinate",
        "affine",
        "projection",
        "reflection",
    }

    # Keywords indicating data types
    DATA_TYPE_KEYWORDS = {
        DataType.NUMERICAL: {
            "number",
            "numeric",
            "integer",
            "float",
            "decimal",
            "continuous",
            "discrete",
            "count",
            "value",
            "magnitude",
            "measurement",
        },
        DataType.CATEGORICAL: {
            "category",
            "class",
            "label",
            "group",
            "factor",
            "nominal",
            "ordinal",
            "binary",
            "boolean",
            "yes/no",
            "true/false",
        },
        DataType.TIME_SERIES: {
            "time",
            "date",
            "temporal",
            "sequence",
            "trend",
            "seasonal",
            "forecast",
            "historical",
            "period",
            "interval",
            "timestamp",
        },
        DataType.TEXT: {
            "text",
            "string",
            "word",
            "sentence",
            "document",
            "corpus",
            "natural language",
            "token",
            "vocabulary",
            "semantic",
        },
    }

    def __init__(self, use_llm: bool = False, llm_provider: Optional[LLMProvider] = None) -> None:
        """Initialize skill classifier.

        Args:
            use_llm: Whether to use LLM for classification
            llm_provider: LLM provider instance (required if use_llm=True)
        """
        self.use_llm = use_llm
        self.llm_provider = llm_provider

    async def classify(self, skill: SkillMetadata) -> SkillMetadata:
        """Classify a skill's category and data types.

        Args:
            skill: Skill metadata to classify

        Returns:
            Updated skill metadata with classification
        """
        if self.use_llm and self.llm_provider:
            return await self._classify_with_llm(skill)
        else:
            return self._classify_with_rules(skill)

    def _classify_with_rules(self, skill: SkillMetadata) -> SkillMetadata:
        """Classify skill using rule-based approach.

        Args:
            skill: Skill metadata to classify

        Returns:
            Updated skill metadata
        """
        # Extract text to analyze
        text_to_analyze = " ".join(
            [
                skill.name,
                skill.description,
                skill.long_description or "",
                " ".join(skill.tags),
            ]
        ).lower()

        # Count keyword matches
        stat_score = sum(1 for kw in self.STATISTICAL_KEYWORDS if kw in text_to_analyze)
        math_score = sum(1 for kw in self.MATH_KEYWORDS if kw in text_to_analyze)

        # Determine category based on scores
        if stat_score > math_score:
            skill.category = SkillCategory.STATISTICAL_METHOD
        elif math_score > stat_score:
            skill.category = SkillCategory.MATHEMATICAL_IMPLEMENTATION
        else:
            # Use existing category as default
            pass

        # Extract data types
        data_types = self._extract_data_types(text_to_analyze)
        if not skill.input_data_types:
            skill.input_data_types = data_types

        skill.source = "rules"
        return skill

    async def _classify_with_llm(self, skill: SkillMetadata) -> SkillMetadata:
        """Classify skill using LLM.

        Args:
            skill: Skill metadata to classify

        Returns:
            Updated skill metadata
        """
        if not self.llm_provider:
            raise RuntimeError("LLM provider not configured")

        prompt = self._build_classification_prompt(skill)

        try:
            result = await self.llm_provider.generate_json(
                prompt,
                system_prompt="You are a helpful assistant that classifies mathematical and statistical skills.",
            )

            # Update skill with LLM results
            if "category" in result:
                try:
                    skill.category = SkillCategory(result["category"])
                except ValueError:
                    logger.warning(f"Invalid category from LLM: {result['category']}")

            if "data_types" in result:
                skill.input_data_types = []
                for dt in result["data_types"]:
                    try:
                        skill.input_data_types.append(DataType(dt))
                    except ValueError:
                        logger.warning(f"Invalid data type from LLM: {dt}")

            if "tags" in result:
                skill.tags.extend(result["tags"])

            if "statistical_concept" in result:
                skill.statistical_concept = result["statistical_concept"]

            skill.confidence = result.get("confidence", 0.8)
            skill.source = "llm"

        except Exception as e:
            logger.error(f"LLM classification failed for {skill.name}: {e}")
            # Fallback to rule-based
            return self._classify_with_rules(skill)

        return skill

    def _build_classification_prompt(self, skill: SkillMetadata) -> str:
        """Build classification prompt for LLM.

        Args:
            skill: Skill metadata

        Returns:
            Classification prompt string
        """
        return f"""Classify the following mathematical/statistical skill:

Name: {skill.name}
Description: {skill.description}
Current Tags: {", ".join(skill.tags)}
Dependencies: {", ".join(skill.dependencies)}

Return a JSON object with:
- category: One of "statistical_method", "mathematical_implementation", "data_analysis", "visualization", or "algorithm"
- data_types: Array of applicable data types (numerical, categorical, time_series, text, boolean, mixed)
- tags: Array of relevant descriptive tags (3-5 tags)
- statistical_concept: The main statistical concept if applicable (e.g., "hypothesis_testing", "regression"), or null
- confidence: Your confidence in this classification (0.0 to 1.0)"""

    def _extract_data_types(self, text: str) -> List[DataType]:
        """Extract data types from text.

        Args:
            text: Text to analyze

        Returns:
            List of detected data types
        """
        detected_types: Set[DataType] = set()

        for data_type, keywords in self.DATA_TYPE_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                detected_types.add(data_type)

        # If multiple types detected, use mixed
        if len(detected_types) > 1:
            return [DataType.MIXED]
        elif len(detected_types) == 1:
            return list(detected_types)
        else:
            # Default to numerical if no specific type detected
            return [DataType.NUMERICAL]

    async def batch_classify(self, skills: List[SkillMetadata]) -> List[SkillMetadata]:
        """Classify multiple skills.

        Args:
            skills: List of skills to classify

        Returns:
            List of classified skills
        """
        classified = []
        for skill in skills:
            classified_skill = await self.classify(skill)
            classified.append(classified_skill)

        logger.info(f"Classified {len(classified)} skills")
        return classified
