"""Problem type classifier for categorizing user problems."""

import logging
from typing import List, Dict, Optional
from enum import Enum

from ..llm.base import LLMProvider
from .data_types import DataTypeDetectionResult

logger = logging.getLogger(__name__)


class ProblemType(str, Enum):
    """Types of statistical/mathematical problems."""

    # Hypothesis testing
    HYPOTHESIS_TEST = "hypothesis_test"
    ONE_SAMPLE_TEST = "one_sample_test"
    TWO_SAMPLE_TEST = "two_sample_test"
    ANOVA = "anova"
    CHI_SQUARE = "chi_square"

    # Regression and correlation
    REGRESSION = "regression"
    LINEAR_REGRESSION = "linear_regression"
    LOGISTIC_REGRESSION = "logistic_regression"
    CORRELATION = "correlation"

    # Classification and clustering
    CLASSIFICATION = "classification"
    CLUSTERING = "clustering"

    # Descriptive statistics
    DESCRIPTIVE = "descriptive"
    DISTRIBUTION_ANALYSIS = "distribution_analysis"

    # Optimization
    OPTIMIZATION = "optimization"
    MINIMIZATION = "minimization"
    MAXIMIZATION = "maximization"

    # Simulation and sampling
    SIMULATION = "simulation"
    MONTE_CARLO = "monte_carlo"
    BOOTSTRAP = "bootstrap"

    # Time series
    TIME_SERIES = "time_series"
    FORECASTING = "forecasting"

    # General
    UNKNOWN = "unknown"
    MULTI_STEP = "multi_step"


class ProblemClassificationResult(BaseModel):
    """Result of problem classification."""

    primary_type: ProblemType
    subtypes: List[ProblemType]
    confidence: float
    reasoning: str
    related_types: List[ProblemType]
    complexity_level: str  # simple, moderate, complex


class ProblemClassifier:
    """Classifier for problem types."""

    # Keyword patterns for each problem type
    TYPE_KEYWORDS = {
        ProblemType.HYPOTHESIS_TEST: [
            "test",
            "hypothesis",
            "significant",
            "p-value",
            "reject",
            "null",
        ],
        ProblemType.ONE_SAMPLE_TEST: [
            "one sample",
            "compare to",
            "known value",
            "population mean",
        ],
        ProblemType.TWO_SAMPLE_TEST: [
            "two sample",
            "compare two",
            "difference between",
            "groups",
        ],
        ProblemType.ANOVA: [
            "anova",
            "analysis of variance",
            "multiple groups",
            "more than two",
        ],
        ProblemType.CHI_SQUARE: [
            "chi-square",
            "chi square",
            "independence",
            "contingency",
        ],
        ProblemType.REGRESSION: [
            "regression",
            "predict",
            "model",
            "relationship",
        ],
        ProblemType.LINEAR_REGRESSION: [
            "linear regression",
            "fit line",
            "slope",
            "intercept",
        ],
        ProblemType.LOGISTIC_REGRESSION: [
            "logistic regression",
            "binary outcome",
            "probability",
        ],
        ProblemType.CORRELATION: [
            "correlation",
            "relationship",
            "association",
            "related",
        ],
        ProblemType.CLASSIFICATION: [
            "classify",
            "predict class",
            "category prediction",
            "label",
        ],
        ProblemType.CLUSTERING: [
            "cluster",
            "group",
            "segment",
            "unsupervised",
        ],
        ProblemType.DESCRIPTIVE: [
            "describe",
            "summarize",
            "statistics",
            "mean",
            "median",
            "mode",
        ],
        ProblemType.DISTRIBUTION_ANALYSIS: [
            "distribution",
            "normality",
            "histogram",
            "shape",
        ],
        ProblemType.OPTIMIZATION: [
            "optimize",
            "optimal",
            "best",
            "minimize",
            "maximize",
        ],
        ProblemType.MINIMIZATION: [
            "minimize",
            "minimum",
            "reduce",
            "lowest",
        ],
        ProblemType.MAXIMIZATION: [
            "maximize",
            "maximum",
            "increase",
            "highest",
        ],
        ProblemType.SIMULATION: [
            "simulate",
            "simulation",
            "generate",
            "random",
        ],
        ProblemType.MONTE_CARLO: [
            "monte carlo",
            "random sampling",
            "estimate",
            "probability",
        ],
        ProblemType.BOOTSTRAP: [
            "bootstrap",
            "resample",
            "confidence interval",
        ],
        ProblemType.TIME_SERIES: [
            "time series",
            "over time",
            "temporal",
            "sequence",
        ],
        ProblemType.FORECASTING: [
            "forecast",
            "predict future",
            "projection",
            "trend",
        ],
    }

    # Type hierarchy for subtype relationships
    TYPE_HIERARCHY = {
        ProblemType.HYPOTHESIS_TEST: [
            ProblemType.ONE_SAMPLE_TEST,
            ProblemType.TWO_SAMPLE_TEST,
            ProblemType.ANOVA,
            ProblemType.CHI_SQUARE,
        ],
        ProblemType.REGRESSION: [
            ProblemType.LINEAR_REGRESSION,
            ProblemType.LOGISTIC_REGRESSION,
        ],
        ProblemType.OPTIMIZATION: [
            ProblemType.MINIMIZATION,
            ProblemType.MAXIMIZATION,
        ],
        ProblemType.SIMULATION: [
            ProblemType.MONTE_CARLO,
            ProblemType.BOOTSTRAP,
        ],
        ProblemType.TIME_SERIES: [
            ProblemType.FORECASTING,
        ],
    }

    def __init__(self, use_llm: bool = False, llm_provider: Optional[LLMProvider] = None) -> None:
        """Initialize problem classifier.

        Args:
            use_llm: Whether to use LLM for classification
            llm_provider: LLM provider instance (required if use_llm=True)
        """
        self.use_llm = use_llm
        self.llm_provider = llm_provider

    async def classify(
        self, text: str, data_type_result: Optional[DataTypeDetectionResult] = None
    ) -> ProblemClassificationResult:
        """Classify the problem type.

        Args:
            text: Problem description text
            data_type_result: Optional data type detection result

        Returns:
            Problem classification result
        """
        if self.use_llm and self.llm_provider:
            return await self._classify_with_llm(text, data_type_result)
        else:
            return self._classify_with_rules(text, data_type_result)

    def _classify_with_rules(
        self, text: str, data_type_result: Optional[DataTypeDetectionResult] = None
    ) -> ProblemClassificationResult:
        """Classify using rule-based approach.

        Args:
            text: Problem description text
            data_type_result: Optional data type detection result

        Returns:
            Problem classification result
        """
        text_lower = text.lower()

        # Score each problem type
        scores = {}
        for problem_type, keywords in self.TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[problem_type] = score

        # Determine primary type
        if not scores:
            primary_type = ProblemType.UNKNOWN
        else:
            primary_type = max(scores, key=scores.get)

        # Find subtypes
        subtypes = self._find_subtypes(primary_type, scores)

        # Find related types
        related_types = self._find_related_types(primary_type, scores)

        # Determine complexity
        complexity_level = self._assess_complexity(text_lower, len(subtypes))

        # Generate reasoning
        reasoning = self._generate_reasoning(primary_type, subtypes, scores)

        # Calculate confidence
        confidence = self._calculate_confidence(scores)

        return ProblemClassificationResult(
            primary_type=primary_type,
            subtypes=subtypes,
            confidence=confidence,
            reasoning=reasoning,
            related_types=related_types,
            complexity_level=complexity_level,
        )

    async def _classify_with_llm(
        self, text: str, data_type_result: Optional[DataTypeDetectionResult] = None
    ) -> ProblemClassificationResult:
        """Classify using LLM.

        Args:
            text: Problem description text
            data_type_result: Optional data type detection result

        Returns:
            Problem classification result
        """
        if not self.llm_provider:
            raise RuntimeError("LLM provider not configured")

        # Add data type context if available
        context = ""
        if data_type_result:
            context = f"\nData type: {data_type_result.primary_type.value}"

        prompt = f"""Classify the following statistical/mathematical problem:

Problem: {text}{context}

Return a JSON object with:
- primary_type: Main problem type (use values: hypothesis_test, one_sample_test, two_sample_test, anova, chi_square, regression, linear_regression, logistic_regression, correlation, classification, clustering, descriptive, distribution_analysis, optimization, minimization, maximization, simulation, monte_carlo, bootstrap, time_series, forecasting, unknown)
- subtypes: Array of specific subtypes
- confidence: Confidence score (0.0 to 1.0)
- reasoning: Brief explanation of why this classification was chosen
- related_types: Array of potentially related problem types
- complexity_level: Complexity level (simple, moderate, complex)"""

        try:
            result = await self.llm_provider.generate_json(
                prompt,
                system_prompt="You are an expert in statistics and mathematics. Classify problems into appropriate types.",
            )

            return ProblemClassificationResult(
                primary_type=ProblemType(result.get("primary_type", "unknown")),
                subtypes=[ProblemType(st) for st in result.get("subtypes", [])],
                confidence=result.get("confidence", 0.8),
                reasoning=result.get("reasoning", ""),
                related_types=[ProblemType(rt) for rt in result.get("related_types", [])],
                complexity_level=result.get("complexity_level", "moderate"),
            )
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return self._classify_with_rules(text, data_type_result)

    def _find_subtypes(
        self, primary_type: ProblemType, scores: Dict[ProblemType, float]
    ) -> List[ProblemType]:
        """Find subtypes of the primary type.

        Args:
            primary_type: Primary problem type
            scores: Type scores

        Returns:
            List of subtypes
        """
        subtypes = []

        # Check hierarchy for subtypes
        for parent_type, child_types in self.TYPE_HIERARCHY.items():
            if parent_type == primary_type:
                for child_type in child_types:
                    if child_type in scores and scores[child_type] > 0:
                        subtypes.append(child_type)

        return subtypes

    def _find_related_types(
        self, primary_type: ProblemType, scores: Dict[ProblemType, float]
    ) -> List[ProblemType]:
        """Find related problem types.

        Args:
            primary_type: Primary problem type
            scores: Type scores

        Returns:
            List of related types
        """
        related = []

        for problem_type, score in scores.items():
            if problem_type != primary_type and score > 0:
                related.append(problem_type)

        return sorted(related, key=lambda t: scores[t], reverse=True)[:3]

    def _assess_complexity(self, text: str, num_subtypes: int) -> str:
        """Assess problem complexity.

        Args:
            text: Lowercase text
            num_subtypes: Number of subtypes found

        Returns:
            Complexity level
        """
        complexity_indicators = [
            "multiple",
            "several",
            "various",
            "complex",
            "advanced",
            "multivariate",
            "interaction",
            "nested",
        ]

        indicator_count = sum(1 for kw in complexity_indicators if kw in text)

        if num_subtypes >= 2 or indicator_count >= 2:
            return "complex"
        elif num_subtypes == 1 or indicator_count == 1:
            return "moderate"
        else:
            return "simple"

    def _generate_reasoning(
        self,
        primary_type: ProblemType,
        subtypes: List[ProblemType],
        scores: Dict[ProblemType, float],
    ) -> str:
        """Generate reasoning for the classification.

        Args:
            primary_type: Primary problem type
            subtypes: List of subtypes
            scores: Type scores

        Returns:
            Reasoning string
        """
        reasoning_parts = []

        reasoning_parts.append(f"Classified as {primary_type.value}")

        if subtypes:
            subtype_names = [st.value for st in subtypes]
            reasoning_parts.append(f"with subtypes: {', '.join(subtype_names)}")

        # Mention the main keywords found
        if primary_type in scores:
            keywords = self.TYPE_KEYWORDS.get(primary_type, [])
            found_keywords = [kw for kw in keywords if kw in " ".join(keywords)]
            if found_keywords:
                reasoning_parts.append(f"based on keywords: {', '.join(found_keywords[:3])}")

        return ". ".join(reasoning_parts)

    def _calculate_confidence(self, scores: Dict[ProblemType, float]) -> float:
        """Calculate confidence in the classification.

        Args:
            scores: Type scores

        Returns:
            Confidence score (0.0 to 1.0)
        """
        if not scores:
            return 0.0

        values = list(scores.values())
        max_score = max(values)
        sum_scores = sum(values)

        if sum_scores == 0:
            return 0.0

        # Confidence based on dominance of top score
        confidence = max_score / sum_scores

        # Boost confidence if there's a clear winner
        if len([v for v in values if v == max_score]) == 1 and max_score > sum_scores * 0.5:
            confidence = min(confidence + 0.1, 1.0)

        return confidence


# Import at end to avoid circular dependency
