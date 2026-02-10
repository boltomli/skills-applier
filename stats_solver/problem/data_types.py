"""Data type detection for problem analysis."""

import logging
from typing import List, Dict, Optional, Any
import re

from ..skills.metadata_schema import DataType

logger = logging.getLogger(__name__)


class DataTypeDetectionResult(BaseModel):
    """Result of data type detection."""
    
    primary_type: DataType
    secondary_types: List[DataType]
    confidence: float
    evidence: List[str]
    mixed_type: bool = False


class DataTypeDetector:
    """Detector for identifying data types in problems."""
    
    # Patterns indicating different data types
    NUMERICAL_PATTERNS = {
        "numbers": [r"\d+", r"\d+\.\d+", r"percent", r"%", r"rate", r"ratio"],
        "measurements": [r"kg", r"g", r"m", r"cm", r"mm", r"seconds?", r"minutes?", r"hours?"],
        "values": [r"value", r"amount", r"count", r"total", r"sum", r"average"],
        "math": [r"mean", r"median", r"mode", r"std", r"variance", r"deviation"],
    }
    
    CATEGORICAL_PATTERNS = {
        "groups": [r"group", r"category", r"class", r"type", r"level", r"factor"],
        "labels": [r"label", r"tag", r"identifier", r"id", r"code"],
        "comparisons": [r"compare", r"difference between", r"versus", r"vs"],
        "enumerations": [r"list of", r"types of", r"kinds of"],
    }
    
    TIME_SERIES_PATTERNS = {
        "time": [r"time", r"date", r"year", r"month", r"day", r"hour"],
        "temporal": [r"trend", r"over time", r"time series", r"historical", r"forecast"],
        "periods": [r"daily", r"weekly", r"monthly", r"quarterly", r"annually"],
        "sequence": [r"sequence", r"period", r"interval", r"duration"],
    }
    
    TEXT_PATTERNS = {
        "text": [r"text", r"string", r"word", r"sentence", r"paragraph"],
        "language": [r"natural language", r"nlp", r"text analysis", r"sentiment"],
        "documents": [r"document", r"article", r"report", r"message"],
    }
    
    BOOLEAN_PATTERNS = {
        "binary": [r"yes/no", r"true/false", r"binary", r"on/off"],
        "decisions": [r"decide", r"determine if", r"check if", r"whether"],
        "outcomes": [r"success/failure", r"pass/fail", r"positive/negative"],
    }
    
    def __init__(self, use_llm: bool = False, llm_provider: Optional[Any] = None) -> None:
        """Initialize data type detector.
        
        Args:
            use_llm: Whether to use LLM for detection
            llm_provider: LLM provider instance (required if use_llm=True)
        """
        self.use_llm = use_llm
        self.llm_provider = llm_provider
    
    async def detect(self, text: str) -> DataTypeDetectionResult:
        """Detect data types from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Data type detection result
        """
        if self.use_llm and self.llm_provider:
            return await self._detect_with_llm(text)
        else:
            return self._detect_with_rules(text)
    
    def _detect_with_rules(self, text: str) -> DataTypeDetectionResult:
        """Detect data types using rule-based approach.
        
        Args:
            text: Text to analyze
            
        Returns:
            Data type detection result
        """
        text_lower = text.lower()
        
        # Score each data type
        scores = {
            DataType.NUMERICAL: self._score_numerical(text_lower),
            DataType.CATEGORICAL: self._score_categorical(text_lower),
            DataType.TIME_SERIES: self._score_time_series(text_lower),
            DataType.TEXT: self._score_text(text_lower),
            DataType.BOOLEAN: self._score_boolean(text_lower),
        }
        
        # Get top scoring types
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary_type, primary_score = sorted_scores[0]
        
        # Get secondary types (any with score > 0)
        secondary_types = [dt for dt, score in sorted_scores[1:] if score > 0]
        
        # Collect evidence
        evidence = self._collect_evidence(text_lower)
        
        # Check if mixed type
        mixed_type = len([s for s in scores.values() if s > 0]) >= 2
        
        # Calculate confidence
        confidence = self._calculate_confidence(scores)
        
        return DataTypeDetectionResult(
            primary_type=primary_type,
            secondary_types=secondary_types,
            confidence=confidence,
            evidence=evidence,
            mixed_type=mixed_type,
        )
    
    async def _detect_with_llm(self, text: str) -> DataTypeDetectionResult:
        """Detect data types using LLM.
        
        Args:
            text: Text to analyze
            
        Returns:
            Data type detection result
        """
        if not self.llm_provider:
            raise RuntimeError("LLM provider not configured")
        
        prompt = f"""Analyze the following text and identify the data types involved:

{text}

Return a JSON object with:
- primary_type: Main data type (numerical, categorical, time_series, text, boolean, mixed)
- secondary_types: Array of secondary data types
- confidence: Confidence score (0.0 to 1.0)
- evidence: Array of phrases that indicate the data types
- mixed_type: Boolean indicating if multiple data types are present"""
        
        try:
            result = await self.llm_provider.generate_json(
                prompt,
                system_prompt="You are an expert in identifying data types from text descriptions.",
            )
            
            primary_type = DataType(result.get("primary_type", "numerical"))
            secondary_types = [DataType(dt) for dt in result.get("secondary_types", [])]
            
            return DataTypeDetectionResult(
                primary_type=primary_type,
                secondary_types=secondary_types,
                confidence=result.get("confidence", 0.8),
                evidence=result.get("evidence", []),
                mixed_type=result.get("mixed_type", False),
            )
        except Exception as e:
            logger.error(f"LLM detection failed: {e}")
            return self._detect_with_rules(text)
    
    def _score_numerical(self, text: str) -> float:
        """Score numerical data type indicators.
        
        Args:
            text: Lowercase text
            
        Returns:
            Numerical score
        """
        score = 0.0
        for category, patterns in self.NUMERICAL_PATTERNS.items():
            matches = sum(1 for pattern in patterns if re.search(pattern, text))
            score += matches * 0.3
        return min(score, 1.0)
    
    def _score_categorical(self, text: str) -> float:
        """Score categorical data type indicators.
        
        Args:
            text: Lowercase text
            
        Returns:
            Categorical score
        """
        score = 0.0
        for category, patterns in self.CATEGORICAL_PATTERNS.items():
            matches = sum(1 for pattern in patterns if re.search(pattern, text))
            score += matches * 0.3
        return min(score, 1.0)
    
    def _score_time_series(self, text: str) -> float:
        """Score time series data type indicators.
        
        Args:
            text: Lowercase text
            
        Returns:
            Time series score
        """
        score = 0.0
        for category, patterns in self.TIME_SERIES_PATTERNS.items():
            matches = sum(1 for pattern in patterns if re.search(pattern, text))
            score += matches * 0.4
        return min(score, 1.0)
    
    def _score_text(self, text: str) -> float:
        """Score text data type indicators.
        
        Args:
            text: Lowercase text
            
        Returns:
            Text score
        """
        score = 0.0
        for category, patterns in self.TEXT_PATTERNS.items():
            matches = sum(1 for pattern in patterns if re.search(pattern, text))
            score += matches * 0.5
        return min(score, 1.0)
    
    def _score_boolean(self, text: str) -> float:
        """Score boolean data type indicators.
        
        Args:
            text: Lowercase text
            
        Returns:
            Boolean score
        """
        score = 0.0
        for category, patterns in self.BOOLEAN_PATTERNS.items():
            matches = sum(1 for pattern in patterns if re.search(pattern, text))
            score += matches * 0.5
        return min(score, 1.0)
    
    def _collect_evidence(self, text: str) -> List[str]:
        """Collect evidence phrases from text.
        
        Args:
            text: Lowercase text
            
        Returns:
            List of evidence phrases
        """
        evidence = []
        
        # Look for specific patterns
        all_patterns = [
            *self.NUMERICAL_PATTERNS["values"],
            *self.CATEGORICAL_PATTERNS["groups"],
            *self.TIME_SERIES_PATTERNS["temporal"],
            *self.TEXT_PATTERNS["text"],
            *self.BOOLEAN_PATTERNS["binary"],
        ]
        
        for pattern in all_patterns:
            if re.search(pattern, text):
                # Extract context around the match
                match = re.search(pattern, text)
                if match:
                    start = max(0, match.start() - 20)
                    end = min(len(text), match.end() + 20)
                    evidence.append(text[start:end].strip())
        
        return list(set(evidence))[:5]
    
    def _calculate_confidence(self, scores: Dict[DataType, float]) -> float:
        """Calculate confidence in the detection.
        
        Args:
            scores: Dictionary of data type scores
            
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
        
        # Confidence based on how dominant the top score is
        return max_score / sum_scores
    
    def detect_batch(self, texts: List[str]) -> List[DataTypeDetectionResult]:
        """Detect data types for multiple texts.
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of detection results
        """
        # For batch processing, use rule-based approach for efficiency
        return [self._detect_with_rules(text) for text in texts]


# Import at end to avoid circular dependency
from pydantic import BaseModel