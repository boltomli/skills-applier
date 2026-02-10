"""Problem feature extractor for analyzing user queries."""

import logging
from typing import Dict, List, Optional, Any
import re

from ..llm.base import LLMProvider
from ..skills.metadata_schema import DataType

logger = logging.getLogger(__name__)


class ProblemFeatures(BaseModel):
    """Extracted features from a user problem."""
    
    # Core problem statement
    description: str
    summary: str
    
    # Data characteristics
    data_types: List[DataType]
    data_source_hints: List[str]
    sample_size_hint: Optional[str] = None
    
    # Problem type
    problem_type: str
    subtypes: List[str]
    
    # Goals and objectives
    primary_goal: str
    secondary_goals: List[str]
    
    # Constraints
    constraints: List[str]
    assumptions: List[str]
    
    # Expected output
    output_format: Optional[str] = None
    output_requirements: List[str] = []
    
    # Domain and context
    domain: Optional[str] = None
    context_keywords: List[str] = []
    
    # Complexity indicators
    complexity_score: float = 0.5
    requires_multi_step: bool = False
    requires_visualization: bool = False


class ProblemExtractor:
    """Extract features from user problem descriptions."""
    
    # Keywords indicating different problem types
    PROBLEM_TYPE_KEYWORDS = {
        "hypothesis_test": [
            "test", "hypothesis", "compare", "difference", "significant",
            "p-value", "confidence", "reject", "fail to reject",
        ],
        "regression": [
            "predict", "relationship", "correlation", "trend", "model",
            "fit", "forecast", "linear", "regression",
        ],
        "classification": [
            "classify", "category", "group", "label", "predict class",
            "decision", "separate", "cluster",
        ],
        "descriptive": [
            "describe", "summarize", "analyze", "explore", "understand",
            "distribution", "statistics", "mean", "median",
        ],
        "optimization": [
            "optimize", "minimize", "maximize", "best", "optimal",
            "find", "solve", "min", "max",
        ],
        "simulation": [
            "simulate", "monte carlo", "random", "generate", "sample",
            "bootstrap", "resample",
        ],
    }
    
    # Keywords indicating data sources
    DATA_SOURCE_KEYWORDS = {
        "survey": ["survey", "questionnaire", "poll", "response"],
        "experiment": ["experiment", "trial", "treatment", "control"],
        "observation": ["observe", "measure", "record", "collect"],
        "sensor": ["sensor", "device", "instrument", "monitor"],
        "database": ["database", "records", "log", "data"],
    }
    
    def __init__(self, use_llm: bool = False, llm_provider: Optional[LLMProvider] = None) -> None:
        """Initialize problem extractor.
        
        Args:
            use_llm: Whether to use LLM for extraction
            llm_provider: LLM provider instance (required if use_llm=True)
        """
        self.use_llm = use_llm
        self.llm_provider = llm_provider
    
    async def extract(self, problem_description: str) -> ProblemFeatures:
        """Extract features from a problem description.
        
        Args:
            problem_description: User's problem description
            
        Returns:
            Extracted problem features
        """
        if self.use_llm and self.llm_provider:
            return await self._extract_with_llm(problem_description)
        else:
            return self._extract_with_rules(problem_description)
    
    def _extract_with_rules(self, problem_description: str) -> ProblemFeatures:
        """Extract features using rule-based approach.
        
        Args:
            problem_description: User's problem description
            
        Returns:
            Extracted problem features
        """
        text = problem_description.lower()
        
        # Detect problem type
        problem_type, subtypes = self._detect_problem_type(text)
        
        # Detect data types
        data_types = self._detect_data_types(text)
        
        # Detect data source hints
        data_source_hints = self._detect_data_sources(text)
        
        # Extract goals
        primary_goal, secondary_goals = self._extract_goals(problem_description)
        
        # Extract constraints
        constraints = self._extract_constraints(problem_description)
        
        # Detect output format hints
        output_format = self._detect_output_format(text)
        
        # Extract context keywords
        context_keywords = self._extract_context_keywords(problem_description)
        
        # Assess complexity
        complexity_score, requires_multi_step, requires_visualization = (
            self._assess_complexity(text)
        )
        
        return ProblemFeatures(
            description=problem_description,
            summary=self._generate_summary(problem_description),
            data_types=data_types,
            data_source_hints=data_source_hints,
            problem_type=problem_type,
            subtypes=subtypes,
            primary_goal=primary_goal,
            secondary_goals=secondary_goals,
            constraints=constraints,
            assumptions=[],
            output_format=output_format,
            context_keywords=context_keywords,
            complexity_score=complexity_score,
            requires_multi_step=requires_multi_step,
            requires_visualization=requires_visualization,
        )
    
    async def _extract_with_llm(self, problem_description: str) -> ProblemFeatures:
        """Extract features using LLM.
        
        Args:
            problem_description: User's problem description
            
        Returns:
            Extracted problem features
        """
        if not self.llm_provider:
            raise RuntimeError("LLM provider not configured")
        
        prompt = self._build_extraction_prompt(problem_description)
        
        try:
            result = await self.llm_provider.generate_json(
                prompt,
                system_prompt="You are an expert in analyzing mathematical and statistical problems. Extract structured features from problem descriptions.",
            )
            
            # Parse data types
            data_types = []
            for dt in result.get("data_types", []):
                try:
                    data_types.append(DataType(dt))
                except ValueError:
                    pass
            
            return ProblemFeatures(
                description=problem_description,
                summary=result.get("summary", ""),
                data_types=data_types,
                data_source_hints=result.get("data_source_hints", []),
                sample_size_hint=result.get("sample_size_hint"),
                problem_type=result.get("problem_type", "unknown"),
                subtypes=result.get("subtypes", []),
                primary_goal=result.get("primary_goal", ""),
                secondary_goals=result.get("secondary_goals", []),
                constraints=result.get("constraints", []),
                assumptions=result.get("assumptions", []),
                output_format=result.get("output_format"),
                output_requirements=result.get("output_requirements", []),
                domain=result.get("domain"),
                context_keywords=result.get("context_keywords", []),
                complexity_score=result.get("complexity_score", 0.5),
                requires_multi_step=result.get("requires_multi_step", False),
                requires_visualization=result.get("requires_visualization", False),
            )
            
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            # Fallback to rule-based
            return self._extract_with_rules(problem_description)
    
    def _build_extraction_prompt(self, problem_description: str) -> str:
        """Build extraction prompt for LLM.
        
        Args:
            problem_description: User's problem description
            
        Returns:
            Prompt string
        """
        return f"""Analyze the following problem description and extract structured features:

Problem: {problem_description}

Return a JSON object with:
- summary: A one-sentence summary of the problem
- data_types: Array of data types involved (numerical, categorical, time_series, text, boolean, mixed)
- data_source_hints: Array of potential data sources (survey, experiment, observation, sensor, database)
- sample_size_hint: Hint about sample size if mentioned (e.g., "small", "large", "100 samples") or null
- problem_type: Main problem type (hypothesis_test, regression, classification, descriptive, optimization, simulation)
- subtypes: Array of specific problem subtypes (e.g., ["t_test", "two_sample"])
- primary_goal: The primary goal of the analysis
- secondary_goals: Array of secondary goals
- constraints: Array of constraints or limitations mentioned
- assumptions: Array of assumptions that can be made
- output_format: Expected output format (plot, table, number, boolean, text) or null
- output_requirements: Array of specific output requirements
- domain: Domain of the problem (e.g., "biology", "finance", "engineering") or null
- context_keywords: Array of relevant context keywords
- complexity_score: Complexity score (0.0 to 1.0)
- requires_multi_step: Boolean indicating if multi-step analysis is needed
- requires_visualization: Boolean indicating if visualization is needed"""
    
    def _detect_problem_type(self, text: str) -> tuple[str, list[str]]:
        """Detect problem type from text.
        
        Args:
            text: Lowercase text to analyze
            
        Returns:
            Tuple of (problem_type, subtypes)
        """
        scores = {}
        for problem_type, keywords in self.PROBLEM_TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[problem_type] = score
        
        if not scores:
            return "unknown", []
        
        # Get highest scoring type
        problem_type = max(scores, key=scores.get)
        
        # Generate subtypes based on specific keywords found
        subtypes = []
        for kw in self.PROBLEM_TYPE_KEYWORDS[problem_type]:
            if kw in text:
                subtypes.append(kw)
        
        return problem_type, subtypes[:5]
    
    def _detect_data_types(self, text: str) -> List[DataType]:
        """Detect data types from text.
        
        Args:
            text: Lowercase text to analyze
            
        Returns:
            List of detected data types
        """
        detected_types = set()
        
        if any(kw in text for kw in ["number", "numeric", "count", "value", "amount"]):
            detected_types.add(DataType.NUMERICAL)
        
        if any(kw in text for kw in ["category", "class", "group", "type", "label"]):
            detected_types.add(DataType.CATEGORICAL)
        
        if any(kw in text for kw in ["time", "date", "trend", "over time", "period"]):
            detected_types.add(DataType.TIME_SERIES)
        
        if any(kw in text for kw in ["text", "word", "string", "document"]):
            detected_types.add(DataType.TEXT)
        
        if any(kw in text for kw in ["yes/no", "true/false", "binary", "boolean"]):
            detected_types.add(DataType.BOOLEAN)
        
        if len(detected_types) > 1:
            return [DataType.MIXED]
        elif detected_types:
            return list(detected_types)
        else:
            return [DataType.NUMERICAL]
    
    def _detect_data_sources(self, text: str) -> List[str]:
        """Detect data source hints from text.
        
        Args:
            text: Lowercase text to analyze
            
        Returns:
            List of detected data sources
        """
        sources = []
        for source, keywords in self.DATA_SOURCE_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                sources.append(source)
        return sources
    
    def _extract_goals(self, text: str) -> tuple[str, list[str]]:
        """Extract goals from problem description.
        
        Args:
            text: Problem description text
            
        Returns:
            Tuple of (primary_goal, secondary_goals)
        """
        # Look for goal indicators
        goal_indicators = ["i want", "need to", "want to", "should", "goal is", "objective"]
        
        sentences = text.split(". ")
        goals = []
        
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in goal_indicators):
                goals.append(sentence.strip())
        
        if not goals:
            return "Analyze the problem", []
        
        return goals[0], goals[1:]
    
    def _extract_constraints(self, text: str) -> List[str]:
        """Extract constraints from problem description.
        
        Args:
            text: Problem description text
            
        Returns:
            List of constraints
        """
        constraints = []
        
        constraint_patterns = [
            r"only\s+(\w+)",
            r"must\s+(\w+)",
            r"cannot\s+(\w+)",
            r"limited\s+to\s+(\w+)",
            r"maximum\s+(\w+)",
            r"minimum\s+(\w+)",
        ]
        
        for pattern in constraint_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            constraints.extend(matches)
        
        return list(set(constraints))
    
    def _detect_output_format(self, text: str) -> Optional[str]:
        """Detect expected output format from text.
        
        Args:
            text: Lowercase text to analyze
            
        Returns:
            Output format or None
        """
        if any(kw in text for kw in ["plot", "graph", "chart", "visualize", "figure"]):
            return "plot"
        elif any(kw in text for kw in ["table", "spreadsheet", "data frame"]):
            return "table"
        elif any(kw in text for kw in ["number", "value", "result", "score"]):
            return "number"
        elif any(kw in text for kw in ["yes/no", "true/false", "decision"]):
            return "boolean"
        elif any(kw in text for kw in ["explain", "describe", "report", "summary"]):
            return "text"
        
        return None
    
    def _extract_context_keywords(self, text: str) -> List[str]:
        """Extract relevant context keywords.
        
        Args:
            text: Problem description text
            
        Returns:
            List of context keywords
        """
        # Simple keyword extraction (could be enhanced)
        keywords = re.findall(r"\b[a-z]{4,}\b", text.lower())
        
        # Filter out common words
        stop_words = {"this", "that", "with", "from", "have", "will", "what", "when", "where", "which", "their", "about"}
        keywords = [kw for kw in keywords if kw not in stop_words]
        
        return list(set(keywords))[:10]
    
    def _assess_complexity(self, text: str) -> tuple[float, bool, bool]:
        """Assess problem complexity.
        
        Args:
            text: Lowercase text to analyze
            
        Returns:
            Tuple of (complexity_score, requires_multi_step, requires_visualization)
        """
        complexity_indicators = [
            "multiple", "several", "various", "compare", "relationship",
            "interaction", "multivariate", "complex", "sophisticated",
        ]
        
        visualization_indicators = [
            "plot", "graph", "chart", "visualize", "display", "show",
        ]
        
        multi_step_indicators = [
            "then", "after", "followed by", "next", "finally", "first",
        ]
        
        complexity_score = min(len([kw for kw in complexity_indicators if kw in text]) * 0.2, 1.0)
        requires_multi_step = any(kw in text for kw in multi_step_indicators)
        requires_visualization = any(kw in text for kw in visualization_indicators)
        
        return complexity_score, requires_multi_step, requires_visualization
    
    def _generate_summary(self, text: str) -> str:
        """Generate a brief summary of the problem.
        
        Args:
            text: Problem description text
            
        Returns:
            Summary string
        """
        # Simple extractive summary (first sentence)
        sentences = text.split(". ")
        if sentences:
            return sentences[0].strip()
        return text[:100] + "..."


# Import at end to avoid circular dependency
from pydantic import BaseModel