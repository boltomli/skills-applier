"""Skill classifier for categorizing skills."""

import logging

from .metadata_schema import SkillMetadata, SkillCategory, SkillTypeGroup, DataType
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

    def __init__(self, use_llm: bool = False, llm_provider: LLMProvider | None = None) -> None:
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

        # Set type_group based on category
        skill.type_group = skill.category.type_group

        # Extract data types
        data_types = self._extract_data_types(text_to_analyze)
        if not skill.input_data_types:
            skill.input_data_types = data_types

        skill.source = "rules"
        return skill

    # Normalization mappings for common invalid LLM responses
    CATEGORY_NORMALIZATION = {
        "programming": SkillCategory.ALGORITHM,
        "code": SkillCategory.ALGORITHM,
        "implementation": SkillCategory.MATHEMATICAL_IMPLEMENTATION,
        "math": SkillCategory.MATHEMATICAL_IMPLEMENTATION,
        "stats": SkillCategory.STATISTICAL_METHOD,
        "statistical": SkillCategory.STATISTICAL_METHOD,
        "visual": SkillCategory.VISUALIZATION,
        "chart": SkillCategory.VISUALIZATION,
    }

    DATA_TYPE_NORMALIZATION = {
        "nominal": DataType.CATEGORICAL,
        "list": DataType.ARRAY,
        "vector": DataType.ARRAY,
        "matrix": DataType.ARRAY,
        "sequence": DataType.TIME_SERIES,
        "string": DataType.TEXT,
        "str": DataType.TEXT,
        "bool": DataType.BOOLEAN,
    }

    def _normalize_category(self, category_value: str) -> SkillCategory | None:
        """Normalize category value to valid enum.

        Args:
            category_value: Raw category value from LLM

        Returns:
            Normalized SkillCategory or None if unresolvable
        """
        category_value = category_value.lower().strip()

        # Direct enum match
        for category in SkillCategory:
            if category.value == category_value:
                return category

        # Normalization mapping
        if category_value in self.CATEGORY_NORMALIZATION:
            normalized = self.CATEGORY_NORMALIZATION[category_value]
            logger.info(f"Normalized category '{category_value}' -> '{normalized.value}'")
            return normalized

        return None

    def _normalize_data_type(self, data_type_value: str) -> DataType | None:
        """Normalize data type value to valid enum.

        Args:
            data_type_value: Raw data type value from LLM

        Returns:
            Normalized DataType or None if unresolvable
        """
        data_type_value = data_type_value.lower().strip()

        # Direct enum match
        for data_type in DataType:
            if data_type.value == data_type_value:
                return data_type

        # Normalization mapping
        if data_type_value in self.DATA_TYPE_NORMALIZATION:
            normalized = self.DATA_TYPE_NORMALIZATION[data_type_value]
            logger.info(f"Normalized data type '{data_type_value}' -> '{normalized.value}'")
            return normalized

        return None

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
                normalized_category = self._normalize_category(result["category"])
                if normalized_category:
                    skill.category = normalized_category
                else:
                    logger.warning(
                        f"Invalid category from LLM: {result['category']}, using existing value"
                    )

            if "type_group" in result:
                try:
                    skill.type_group = SkillTypeGroup(result["type_group"])
                except ValueError:
                    logger.warning(
                        f"Invalid type_group from LLM: {result['type_group']}, using category's type_group"
                    )
                    skill.type_group = skill.category.type_group
            else:
                # Fallback to category's type_group
                skill.type_group = skill.category.type_group

            if "data_types" in result:
                skill.input_data_types = []
                valid_types = []
                for dt in result["data_types"]:
                    normalized_type = self._normalize_data_type(dt)
                    if normalized_type:
                        valid_types.append(normalized_type)
                    else:
                        logger.warning(f"Invalid data type from LLM: {dt}")
                skill.input_data_types = valid_types if valid_types else [DataType.NUMERICAL]

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

Return a JSON object with EXACT values from the following lists:

- category: MUST be one of these EXACT values:
  * "statistical_method" - Statistical tests and analysis methods
  * "mathematical_implementation" - Pure math algorithms and computations
  * "data_analysis" - Data processing and manipulation
  * "visualization" - Charts, plots, and visual representations
  * "algorithm" - General algorithms and programming utilities
  DO NOT use "programming" - that is a type_group, not a category

- type_group: MUST be either:
  * "problem_solving" (解决问题的方法) - for: statistical_method, data_analysis, visualization
  * "programming" (编程用) - for: mathematical_implementation, algorithm

- data_types: Array of applicable data types, MUST use ONLY these EXACT values:
  * "numerical" - Numbers, measurements, counts
  * "categorical" - Labels, groups, classes (nominal data without order)
  * "ordinal" - Ordered categories (e.g., low/medium/high, 1-5 ratings)
  * "time_series" - Temporal data, sequences, timestamps
  * "text" - Strings, natural language
  * "boolean" - True/false, yes/no
  * "array" - Multi-dimensional arrays, lists, vectors, matrices
  * "mixed" - Multiple data types combined
  DO NOT use "nominal", "list", "vector", "matrix", etc.

- tags: Array of relevant descriptive tags (3-5 tags)

- statistical_concept: The main statistical concept if applicable (e.g., "hypothesis_testing", "regression"), or null

- confidence: Your confidence in this classification (0.0 to 1.0)

CRITICAL: Use ONLY the exact values listed above. Do not invent or abbreviate any values."""

    def _extract_data_types(self, text: str) -> list[DataType]:
        """Extract data types from text.

        Args:
            text: Text to analyze

        Returns:
            List of detected data types
        """
        detected_types: set[DataType] = set()

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

    async def batch_classify(self, skills: list[SkillMetadata]) -> list[SkillMetadata]:
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

    async def batch_classify_with_progress(
        self, skills: list[SkillMetadata], batch_size: int = 50, progress_callback=None
    ) -> list[SkillMetadata]:
        """Classify multiple skills in batches with progress callback.

        Args:
            skills: List of skills to classify
            batch_size: Number of skills to classify before saving progress (for future use)
            progress_callback: Optional callback function(current, total)

        Returns:
            List of classified skills
        """
        classified = []
        total = len(skills)

        for i, skill in enumerate(skills):
            classified_skill = await self.classify(skill)
            classified.append(classified_skill)

            if progress_callback:
                progress_callback(i + 1, total)

            # Optional: log progress periodically
            if (i + 1) % batch_size == 0 or i + 1 == total:
                logger.info(f"Classified {i + 1}/{total} skills")

        logger.info(f"Classified {len(classified)} skills total")
        return classified
