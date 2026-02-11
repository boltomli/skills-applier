"""Output format recognition for problem analysis."""

import logging
from typing import List, Dict, Optional, Any
from enum import Enum
import re

from pydantic import BaseModel

from ..llm.base import LLMProvider

logger = logging.getLogger(__name__)


class OutputFormat(str, Enum):
    """Types of output formats."""

    # Visual outputs
    PLOT = "plot"
    GRAPH = "graph"
    CHART = "chart"
    HISTOGRAM = "histogram"
    SCATTER_PLOT = "scatter_plot"
    LINE_PLOT = "line_plot"
    BAR_CHART = "bar_chart"
    HEATMAP = "heatmap"

    # Tabular outputs
    TABLE = "table"
    DATAFRAME = "dataframe"
    SPREADSHEET = "spreadsheet"
    CSV = "csv"

    # Numerical outputs
    NUMBER = "number"
    FLOAT = "float"
    INTEGER = "integer"
    PERCENTAGE = "percentage"

    # Text outputs
    TEXT = "text"
    REPORT = "report"
    SUMMARY = "summary"
    EXPLANATION = "explanation"

    # Boolean outputs
    BOOLEAN = "boolean"
    YES_NO = "yes_no"
    TRUE_FALSE = "true_false"

    # Statistical outputs
    P_VALUE = "p_value"
    CONFIDENCE_INTERVAL = "confidence_interval"
    STATISTIC = "statistic"

    # File outputs
    FILE = "file"
    IMAGE = "image"
    PDF = "pdf"

    # Console outputs
    PRINT = "print"
    DISPLAY = "display"

    # Unknown
    UNKNOWN = "unknown"


class OutputFormatDetectionResult(BaseModel):
    """Result of output format detection."""

    primary_format: OutputFormat
    secondary_formats: List[OutputFormat]
    confidence: float
    reasoning: str
    required_elements: List[str]
    optional_elements: List[str]


class OutputFormatRecognizer:
    """Recognizer for output formats."""

    # Format keywords and patterns
    FORMAT_PATTERNS = {
        OutputFormat.PLOT: [
            r"plot",
            r"graph",
            r"visualize",
            r"visualization",
            r"figure",
            r"matplotlib",
            r"seaborn",
            r"plotly",
        ],
        OutputFormat.HISTOGRAM: [
            r"histogram",
            r"distribution",
            r"freq(uency)?\s+hist",
        ],
        OutputFormat.SCATTER_PLOT: [
            r"scatter",
            r"scatter\s+plot",
            r"point\s+plot",
        ],
        OutputFormat.LINE_PLOT: [
            r"line\s+plot",
            r"line\s+graph",
            r"trend\s+line",
        ],
        OutputFormat.BAR_CHART: [
            r"bar\s+chart",
            r"bar\s+graph",
            r"column\s+chart",
        ],
        OutputFormat.HEATMAP: [
            r"heatmap",
            r"heat\s+map",
            r"correlation\s+matrix",
        ],
        OutputFormat.TABLE: [
            r"table",
            r"tabular",
            r"data\s+table",
        ],
        OutputFormat.DATAFRAME: [
            r"dataframe",
            r"pandas\s+df",
            r"df\s*=|df\.",
        ],
        OutputFormat.CSV: [
            r"csv",
            r"\.csv",
            r"comma\s+separated",
        ],
        OutputFormat.NUMBER: [
            r"number",
            r"value",
            r"result",
            r"single\s+value",
        ],
        OutputFormat.PERCENTAGE: [
            r"percent",
            r"%",
            r"percentage",
            r"proportion",
        ],
        OutputFormat.TEXT: [
            r"text",
            r"string",
            r"message",
            r"output\s+text",
        ],
        OutputFormat.REPORT: [
            r"report",
            r"document",
            r"summary\s+report",
        ],
        OutputFormat.SUMMARY: [
            r"summary",
            r"summarize",
            r"brief",
        ],
        OutputFormat.EXPLANATION: [
            r"explain",
            r"explanation",
            r"describe",
            r"interpret",
        ],
        OutputFormat.BOOLEAN: [
            r"boolean",
            r"bool",
            r"binary",
        ],
        OutputFormat.YES_NO: [
            r"yes\s*/\s*no",
            r"yes\s+or\s+no",
            r"answer\s+yes\s+or\s+no",
        ],
        OutputFormat.TRUE_FALSE: [
            r"true\s*/\s*false",
            r"true\s+or\s+false",
        ],
        OutputFormat.P_VALUE: [
            r"p\s*[-_]?\s*value",
            r"p-value",
            r"p\s*=\s*",
        ],
        OutputFormat.CONFIDENCE_INTERVAL: [
            r"confidence\s+interval",
            r"ci\s*[0-9]?",
            r"95%\s+ci",
        ],
        OutputFormat.STATISTIC: [
            r"statistic",
            r"test\s+statistic",
            r"t-stat",
            r"f-stat",
        ],
        OutputFormat.IMAGE: [
            r"image",
            r"png",
            r"jpg",
            r"jpeg",
            r"save\s+figure",
        ],
        OutputFormat.PDF: [
            r"pdf",
            r"\.pdf",
            r"pdf\s+report",
        ],
        OutputFormat.FILE: [
            r"file",
            r"save\s+to\s+file",
            r"write\s+to\s+file",
        ],
        OutputFormat.PRINT: [
            r"print",
            r"output",
            r"display",
            r"show",
        ],
    }

    # Format hierarchy (parent -> children)
    FORMAT_HIERARCHY = {
        OutputFormat.PLOT: [
            OutputFormat.HISTOGRAM,
            OutputFormat.SCATTER_PLOT,
            OutputFormat.LINE_PLOT,
            OutputFormat.BAR_CHART,
            OutputFormat.HEATMAP,
        ],
        OutputFormat.BOOLEAN: [
            OutputFormat.YES_NO,
            OutputFormat.TRUE_FALSE,
        ],
    }

    def __init__(self, use_llm: bool = False, llm_provider: Optional[LLMProvider] = None) -> None:
        """Initialize output format recognizer.

        Args:
            use_llm: Whether to use LLM for recognition
            llm_provider: LLM provider instance (required if use_llm=True)
        """
        self.use_llm = use_llm
        self.llm_provider = llm_provider

    async def recognize(self, text: str) -> OutputFormatDetectionResult:
        """Recognize output format from text.

        Args:
            text: Problem description text

        Returns:
            Output format detection result
        """
        if self.use_llm and self.llm_provider:
            return await self._recognize_with_llm(text)
        else:
            return self._recognize_with_rules(text)

    def _recognize_with_rules(self, text: str) -> OutputFormatDetectionResult:
        """Recognize using rule-based approach.

        Args:
            text: Problem description text

        Returns:
            Output format detection result
        """
        text_lower = text.lower()

        # Score each format
        scores = {}
        for output_format, patterns in self.FORMAT_PATTERNS.items():
            score = sum(1 for pattern in patterns if re.search(pattern, text_lower))
            if score > 0:
                scores[output_format] = score

        # Determine primary format
        if not scores:
            primary_format = OutputFormat.UNKNOWN
        else:
            primary_format = max(scores, key=scores.get)

        # Find secondary formats
        secondary_formats = self._find_secondary_formats(primary_format, scores)

        # Generate reasoning
        reasoning = self._generate_reasoning(primary_format, secondary_formats, scores)

        # Extract required and optional elements
        required, optional = self._extract_elements(text_lower, primary_format)

        # Calculate confidence
        confidence = self._calculate_confidence(scores)

        return OutputFormatDetectionResult(
            primary_format=primary_format,
            secondary_formats=secondary_formats,
            confidence=confidence,
            reasoning=reasoning,
            required_elements=required,
            optional_elements=optional,
        )

    async def _recognize_with_llm(self, text: str) -> OutputFormatDetectionResult:
        """Recognize using LLM.

        Args:
            text: Problem description text

        Returns:
            Output format detection result
        """
        if not self.llm_provider:
            raise RuntimeError("LLM provider not configured")

        prompt = f"""Identify the output format requested in the following problem description:

{text}

Return a JSON object with:
- primary_format: Main output format (use values: plot, graph, chart, histogram, scatter_plot, line_plot, bar_chart, heatmap, table, dataframe, spreadsheet, csv, number, float, integer, percentage, text, report, summary, explanation, boolean, yes_no, true_false, p_value, confidence_interval, statistic, file, image, pdf, print, display, unknown)
- secondary_formats: Array of secondary output formats
- confidence: Confidence score (0.0 to 1.0)
- reasoning: Brief explanation of why this format was chosen
- required_elements: Array of elements that must be included in the output
- optional_elements: Array of elements that could optionally be included"""

        try:
            result = await self.llm_provider.generate_json(
                prompt,
                system_prompt="You are an expert in identifying output formats from problem descriptions.",
            )

            return OutputFormatDetectionResult(
                primary_format=OutputFormat(result.get("primary_format", "unknown")),
                secondary_formats=[OutputFormat(sf) for sf in result.get("secondary_formats", [])],
                confidence=result.get("confidence", 0.8),
                reasoning=result.get("reasoning", ""),
                required_elements=result.get("required_elements", []),
                optional_elements=result.get("optional_elements", []),
            )
        except Exception as e:
            logger.error(f"LLM recognition failed: {e}")
            return self._recognize_with_rules(text)

    def _find_secondary_formats(
        self, primary_format: OutputFormat, scores: Dict[OutputFormat, float]
    ) -> List[OutputFormat]:
        """Find secondary formats related to the primary format.

        Args:
            primary_format: Primary output format
            scores: Format scores

        Returns:
            List of secondary formats
        """
        secondary = []

        # Check hierarchy for related formats
        for parent, children in self.FORMAT_HIERARCHY.items():
            if parent == primary_format:
                for child in children:
                    if child in scores and scores[child] > 0:
                        secondary.append(child)

        # Also include other high-scoring formats
        for output_format, score in scores.items():
            if output_format != primary_format and score >= scores.get(primary_format, 0) * 0.5:
                if output_format not in secondary:
                    secondary.append(output_format)

        return secondary[:3]

    def _generate_reasoning(
        self,
        primary_format: OutputFormat,
        secondary_formats: List[OutputFormat],
        scores: Dict[OutputFormat, float],
    ) -> str:
        """Generate reasoning for the recognition.

        Args:
            primary_format: Primary output format
            secondary_formats: List of secondary formats
            scores: Format scores

        Returns:
            Reasoning string
        """
        reasoning_parts = []

        reasoning_parts.append(f"Detected {primary_format.value} as primary output format")

        if secondary_formats:
            secondary_names = [sf.value for sf in secondary_formats]
            reasoning_parts.append(f"with secondary formats: {', '.join(secondary_names)}")

        # Mention keywords found
        if primary_format in scores:
            patterns = self.FORMAT_PATTERNS.get(primary_format, [])
            found = [p for p in patterns[:3] if re.search(p, " ".join(patterns).lower())]
            if found:
                reasoning_parts.append(f"based on patterns: {', '.join(found)}")

        return ". ".join(reasoning_parts)

    def _extract_elements(
        self, text: str, primary_format: OutputFormat
    ) -> tuple[List[str], List[str]]:
        """Extract required and optional elements.

        Args:
            text: Lowercase text
            primary_format: Primary output format

        Returns:
            Tuple of (required_elements, optional_elements)
        """
        required = []
        optional = []

        # Format-specific element extraction
        if primary_format == OutputFormat.PLOT:
            if re.search(r"legend", text):
                required.append("legend")
            if re.search(r"title|label", text):
                required.append("axis labels")
            if re.search(r"grid", text):
                optional.append("grid lines")

        elif primary_format == OutputFormat.TABLE:
            if re.search(r"header|column", text):
                required.append("column headers")
            if re.search(r"index", text):
                optional.append("row index")

        elif primary_format == OutputFormat.REPORT:
            required.append("introduction")
            required.append("results")
            optional.append("conclusions")
            optional.append("references")

        return required, optional

    def _calculate_confidence(self, scores: Dict[OutputFormat, float]) -> float:
        """Calculate confidence in the recognition.

        Args:
            scores: Format scores

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
        return max_score / sum_scores

    def get_format_requirements(self, output_format: OutputFormat) -> Dict[str, Any]:
        """Get typical requirements for an output format.

        Args:
            output_format: Output format type

        Returns:
            Dictionary of format requirements
        """
        requirements = {
            OutputFormat.PLOT: {
                "libraries": ["matplotlib", "seaborn"],
                "typical_elements": ["title", "labels", "legend"],
                "file_extensions": [".png", ".jpg", ".svg", ".pdf"],
            },
            OutputFormat.TABLE: {
                "libraries": ["pandas"],
                "typical_elements": ["headers", "index"],
                "file_extensions": [".csv", ".xlsx", ".html"],
            },
            OutputFormat.REPORT: {
                "libraries": ["reportlab", "matplotlib"],
                "typical_elements": ["title", "sections", "figures"],
                "file_extensions": [".pdf", ".docx", ".html"],
            },
            OutputFormat.NUMBER: {
                "libraries": [],
                "typical_elements": ["precision", "units"],
                "file_extensions": [".txt", ".csv"],
            },
        }

        return requirements.get(
            output_format,
            {
                "libraries": [],
                "typical_elements": [],
                "file_extensions": [],
            },
        )


# Import at end to avoid circular dependency
