"""Skill matching algorithm for problem-skill compatibility."""

import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass

from ..skills.metadata_schema import SkillMetadata, SkillCategory, DataType
from ..problem.extractor import ProblemFeatures
from ..problem.classifier import ProblemType
from ..problem.data_types import DataTypeDetectionResult
from ..problem.output_format import OutputFormat

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """Result of matching a skill to a problem."""
    
    skill: SkillMetadata
    score: float
    match_reasons: List[str]
    mismatches: List[str]
    confidence: float


class SkillMatcher:
    """Matcher for finding skills compatible with a problem."""
    
    # Weight factors for different matching criteria
    WEIGHTS = {
        "category_match": 0.3,
        "data_type_match": 0.25,
        "problem_type_match": 0.2,
        "output_format_match": 0.1,
        "tag_relevance": 0.1,
        "statistical_concept_match": 0.05,
    }
    
    def __init__(
        self,
        use_llm: bool = False,
        llm_provider: Optional[Any] = None
    ) -> None:
        """Initialize skill matcher.
        
        Args:
            use_llm: Whether to use LLM for enhanced matching
            llm_provider: LLM provider instance (required if use_llm=True)
        """
        self.use_llm = use_llm
        self.llm_provider = llm_provider
    
    async def match(
        self,
        skills: List[SkillMetadata],
        problem_features: ProblemFeatures,
        problem_type: ProblemType,
        data_type_result: Optional[DataTypeDetectionResult] = None,
        output_format: Optional[OutputFormat] = None,
        top_k: int = 10
    ) -> List[MatchResult]:
        """Match skills to a problem.
        
        Args:
            skills: List of skills to match
            problem_features: Extracted problem features
            problem_type: Classified problem type
            data_type_result: Optional data type detection result
            output_format: Optional output format
            top_k: Maximum number of results to return
            
        Returns:
            List of match results sorted by score
        """
        results = []
        
        for skill in skills:
            match_result = await self._match_single_skill(
                skill,
                problem_features,
                problem_type,
                data_type_result,
                output_format
            )
            results.append(match_result)
        
        # Sort by score and return top k
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]
    
    async def _match_single_skill(
        self,
        skill: SkillMetadata,
        problem_features: ProblemFeatures,
        problem_type: ProblemType,
        data_type_result: Optional[DataTypeDetectionResult] = None,
        output_format: Optional[OutputFormat] = None
    ) -> MatchResult:
        """Match a single skill to the problem.
        
        Args:
            skill: Skill to match
            problem_features: Problem features
            problem_type: Problem type
            data_type_result: Data type result
            output_format: Output format
            
        Returns:
            Match result
        """
        match_reasons = []
        mismatches = []
        scores = {}
        
        # Category match
        category_score, category_reason = self._match_category(skill, problem_features)
        scores["category_match"] = category_score
        if category_reason:
            match_reasons.append(category_reason)
        
        # Data type match
        data_type_score, data_type_reason = self._match_data_types(
            skill, problem_features, data_type_result
        )
        scores["data_type_match"] = data_type_score
        if data_type_reason:
            match_reasons.append(data_type_reason)
        
        # Problem type match
        problem_type_score, problem_type_reason = self._match_problem_type(
            skill, problem_type
        )
        scores["problem_type_match"] = problem_type_score
        if problem_type_reason:
            match_reasons.append(problem_type_reason)
        
        # Output format match
        output_score, output_reason = self._match_output_format(skill, output_format)
        scores["output_format_match"] = output_score
        if output_reason:
            match_reasons.append(output_reason)
        else:
            mismatches.append("Output format mismatch")
        
        # Tag relevance
        tag_score, tag_reason = self._match_tags(skill, problem_features)
        scores["tag_relevance"] = tag_score
        if tag_reason:
            match_reasons.append(tag_reason)
        
        # Statistical concept match
        concept_score, concept_reason = self._match_statistical_concept(skill, problem_features)
        scores["statistical_concept_match"] = concept_score
        if concept_reason:
            match_reasons.append(concept_reason)
        
        # Calculate weighted score
        total_score = sum(
            score * self.WEIGHTS.get(key, 0)
            for key, score in scores.items()
        )
        
        # Calculate confidence based on number of positive matches
        confidence = min(len(match_reasons) / 4.0, 1.0)
        
        return MatchResult(
            skill=skill,
            score=total_score,
            match_reasons=match_reasons,
            mismatches=mismatches,
            confidence=confidence,
        )
    
    def _match_category(
        self,
        skill: SkillMetadata,
        problem_features: ProblemFeatures
    ) -> Tuple[float, Optional[str]]:
        """Match skill category to problem type.
        
        Args:
            skill: Skill metadata
            problem_features: Problem features
            
        Returns:
            Tuple of (score, reason)
        """
        # Map problem types to expected skill categories
        category_map = {
            "hypothesis_test": SkillCategory.STATISTICAL_METHOD,
            "one_sample_test": SkillCategory.STATISTICAL_METHOD,
            "two_sample_test": SkillCategory.STATISTICAL_METHOD,
            "anova": SkillCategory.STATISTICAL_METHOD,
            "chi_square": SkillCategory.STATISTICAL_METHOD,
            "regression": SkillCategory.STATISTICAL_METHOD,
            "correlation": SkillCategory.STATISTICAL_METHOD,
            "classification": SkillCategory.STATISTICAL_METHOD,
            "clustering": SkillCategory.STATISTICAL_METHOD,
            "descriptive": SkillCategory.STATISTICAL_METHOD,
            "distribution_analysis": SkillCategory.STATISTICAL_METHOD,
            "optimization": SkillCategory.MATHEMATICAL_IMPLEMENTATION,
            "simulation": SkillCategory.MATHEMATICAL_IMPLEMENTATION,
            "time_series": SkillCategory.STATISTICAL_METHOD,
            "forecasting": SkillCategory.STATISTICAL_METHOD,
        }
        
        expected_category = category_map.get(problem_features.problem_type)
        
        if expected_category and skill.category == expected_category:
            return 1.0, f"Category matches: {skill.category.value}"
        elif skill.category == SkillCategory.STATISTICAL_METHOD:
            # Statistical methods are often flexible
            return 0.7, f"Statistical method applicable to {problem_features.problem_type}"
        else:
            return 0.3, "Category may not be optimal for this problem type"
    
    def _match_data_types(
        self,
        skill: SkillMetadata,
        problem_features: ProblemFeatures,
        data_type_result: Optional[DataTypeDetectionResult] = None
    ) -> Tuple[float, Optional[str]]:
        """Match skill's data types to problem's data types.
        
        Args:
            skill: Skill metadata
            problem_features: Problem features
            data_type_result: Data type detection result
            
        Returns:
            Tuple of (score, reason)
        """
        if not skill.input_data_types or not problem_features.data_types:
            return 0.5, "Data type compatibility unclear"
        
        # Check for overlap
        skill_types = set(skill.input_data_types)
        problem_types = set(problem_features.data_types)
        
        # Mixed type is compatible with anything
        if DataType.MIXED in skill_types:
            return 1.0, "Skill supports mixed data types"
        
        if DataType.MIXED in problem_types:
            # Problem has mixed data, check if skill handles at least one type
            if skill_types & problem_types:
                overlap = skill_types & problem_types
                return 0.7, f"Supports {', '.join(dt.value for dt in overlap)}"
        
        # Direct overlap
        overlap = skill_types & problem_types
        if overlap:
            if len(overlap) == len(problem_types):
                return 1.0, f"Fully compatible data types: {', '.join(dt.value for dt in overlap)}"
            else:
                return 0.6, f"Partially compatible: {', '.join(dt.value for dt in overlap)}"
        
        return 0.2, "Data type mismatch"
    
    def _match_problem_type(
        self,
        skill: SkillMetadata,
        problem_type: ProblemType
    ) -> Tuple[float, Optional[str]]:
        """Match skill to problem type.
        
        Args:
            skill: Skill metadata
            problem_type: Problem type
            
        Returns:
            Tuple of (score, reason)
        """
        # Check if skill's tags or description contain problem type keywords
        problem_type_keywords = problem_type.value.split("_")
        
        skill_text = " ".join([
            skill.name.lower(),
            skill.description.lower(),
            " ".join(tag.lower() for tag in skill.tags),
        ])
        
        matches = sum(1 for kw in problem_type_keywords if kw in skill_text)
        
        if matches >= 2:
            return 1.0, f"Directly addresses {problem_type.value}"
        elif matches == 1:
            return 0.7, f"Related to {problem_type.value}"
        
        # Check statistical concept
        if skill.statistical_concept:
            concept_lower = skill.statistical_concept.lower()
            if any(kw in concept_lower for kw in problem_type_keywords):
                return 0.6, f"Statistical concept matches: {skill.statistical_concept}"
        
        return 0.4, f"May be applicable to {problem_type.value}"
    
    def _match_output_format(
        self,
        skill: SkillMetadata,
        output_format: Optional[OutputFormat]
    ) -> Tuple[float, Optional[str]]:
        """Match skill's output format to required format.
        
        Args:
            skill: Skill metadata
            output_format: Required output format
            
        Returns:
            Tuple of (score, reason)
        """
        if not output_format or output_format == OutputFormat.UNKNOWN:
            return 1.0, "No specific output format required"
        
        skill_format = skill.output_format.lower() if skill.output_format else ""
        required_format = output_format.value.lower()
        
        # Direct match
        if required_format in skill_format or skill_format in required_format:
            return 1.0, f"Output format matches: {skill.output_format}"
        
        # Check tags for format hints
        format_keywords = {
            OutputFormat.PLOT: ["plot", "graph", "chart", "visual", "figure"],
            OutputFormat.TABLE: ["table", "dataframe", "tabular"],
            OutputFormat.NUMBER: ["number", "value", "result", "scalar"],
            OutputFormat.TEXT: ["text", "report", "summary", "explain"],
        }
        
        keywords = format_keywords.get(output_format, [])
        if any(kw in skill.description.lower() or kw in " ".join(skill.tags).lower() for kw in keywords):
            return 0.8, f"Can produce {output_format.value} output"
        
        return 0.5, "Output format compatibility uncertain"
    
    def _match_tags(
        self,
        skill: SkillMetadata,
        problem_features: ProblemFeatures
    ) -> Tuple[float, Optional[str]]:
        """Match skill tags to problem context.
        
        Args:
            skill: Skill metadata
            problem_features: Problem features
            
        Returns:
            Tuple of (score, reason)
        """
        if not skill.tags or not problem_features.context_keywords:
            return 0.5, "Tag relevance unclear"
        
        skill_tags = set(tag.lower() for tag in skill.tags)
        problem_keywords = set(kw.lower() for kw in problem_features.context_keywords)
        
        # Check for tag matches
        matches = skill_tags & problem_keywords
        
        if len(matches) >= 2:
            return 1.0, f"Tags match: {', '.join(matches)}"
        elif len(matches) == 1:
            return 0.7, f"Tag match: {', '.join(matches)}"
        
        # Check use cases
        if skill.use_cases:
            for use_case in skill.use_cases:
                use_case_lower = use_case.lower()
                if any(kw in use_case_lower for kw in problem_keywords):
                    return 0.6, f"Use case relevant: {use_case[:50]}"
        
        return 0.4, "No direct tag matches"
    
    def _match_statistical_concept(
        self,
        skill: SkillMetadata,
        problem_features: ProblemFeatures
    ) -> Tuple[float, Optional[str]]:
        """Match skill's statistical concept to problem.
        
        Args:
            skill: Skill metadata
            problem_features: Problem features
            
        Returns:
            Tuple of (score, reason)
        """
        if not skill.statistical_concept:
            return 0.5, "No statistical concept specified"
        
        concept_lower = skill.statistical_concept.lower()
        problem_text = " ".join([
            problem_features.description.lower(),
            problem_features.primary_goal.lower(),
            " ".join(problem_features.context_keywords),
        ])
        
        # Check for concept in problem
        if concept_lower in problem_text:
            return 1.0, f"Statistical concept directly matches: {skill.statistical_concept}"
        
        # Check for related terms
        related_terms = {
            "hypothesis_testing": ["test", "hypothesis", "significant", "p-value"],
            "regression": ["predict", "model", "relationship", "fit"],
            "correlation": ["correlate", "relationship", "association"],
            "clustering": ["cluster", "group", "segment"],
            "distribution_analysis": ["distribution", "normality", "shape"],
        }
        
        if skill.statistical_concept in related_terms:
            terms = related_terms[skill.statistical_concept]
            if any(term in problem_text for term in terms):
                return 0.7, f"Related to {skill.statistical_concept}"
        
        return 0.5, f"Statistical concept: {skill.statistical_concept}"
    
    def filter_by_min_score(
        self,
        results: List[MatchResult],
        min_score: float = 0.5
    ) -> List[MatchResult]:
        """Filter results by minimum score.
        
        Args:
            results: Match results to filter
            min_score: Minimum score threshold
            
        Returns:
            Filtered results
        """
        return [r for r in results if r.score >= min_score]