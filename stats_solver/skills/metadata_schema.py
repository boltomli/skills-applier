"""Skill metadata JSON schema definitions."""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class SkillTypeGroup(str, Enum):
    """技能类型分组：解决问题方法 vs 编程用."""

    PROBLEM_SOLVING = "problem_solving"  # 解决问题的方法
    PROGRAMMING = "programming"  # 编程用


class SkillCategory(str, Enum):
    """Skill category classification."""

    STATISTICAL_METHOD = "statistical_method"
    MATHEMATICAL_IMPLEMENTATION = "mathematical_implementation"
    DATA_ANALYSIS = "data_analysis"
    VISUALIZATION = "visualization"
    ALGORITHM = "algorithm"

    @property
    def type_group(self) -> SkillTypeGroup:
        """获取技能类型分组."""
        # 统计方法、数据分析、可视化属于解决问题的方法
        if self in {
            SkillCategory.STATISTICAL_METHOD,
            SkillCategory.DATA_ANALYSIS,
            SkillCategory.VISUALIZATION,
        }:
            return SkillTypeGroup.PROBLEM_SOLVING
        # 数学实现、算法属于编程用
        else:
            return SkillTypeGroup.PROGRAMMING


class DataType(str, Enum):
    """Data types that skills can work with."""

    NUMERICAL = "numerical"
    CATEGORICAL = "categorical"
    TIME_SERIES = "time_series"
    TEXT = "text"
    BOOLEAN = "boolean"
    MIXED = "mixed"


class SkillMetadata(BaseModel):
    """Metadata schema for a skill."""

    # Basic identification
    name: str = Field(..., description="Name of the skill")
    id: str = Field(..., description="Unique identifier (directory name)")
    path: str = Field(..., description="Relative path to skill directory")

    # Classification
    category: SkillCategory = Field(..., description="Primary skill category")
    type_group: SkillTypeGroup = Field(
        default=SkillTypeGroup.PROBLEM_SOLVING,
        description="Type group: problem_solving (解决问题的方法) or programming (编程用)",
    )
    tags: list[str] = Field(default_factory=list, description="Descriptive tags")

    # Data capabilities
    input_data_types: list[DataType] = Field(
        default_factory=list, description="Data types this skill can accept as input"
    )
    output_format: str | None = Field(
        None, description="Format of output (e.g., 'plot', 'table', 'number')"
    )

    # Description
    description: str = Field(..., description="Brief description of what the skill does")
    long_description: str | None = Field(None, description="Detailed description of the skill")

    # Dependencies
    dependencies: list[str] = Field(
        default_factory=list, description="Python dependencies required"
    )

    # Prerequisites
    prerequisites: list[str] = Field(
        default_factory=list, description="Other skills that should be used before this one"
    )

    # Use cases
    use_cases: list[str] = Field(
        default_factory=list, description="Example use cases or problem scenarios"
    )

    # Statistical context (for statistical methods)
    statistical_concept: str | None = Field(
        None, description="Statistical concept (e.g., 'hypothesis_testing', 'regression')"
    )
    assumptions: list[str] = Field(
        default_factory=list, description="Statistical assumptions the skill relies on"
    )

    # Algorithm context (for mathematical implementations)
    algorithm_name: str | None = Field(None, description="Name of the algorithm implemented")
    complexity: str | None = Field(None, description="Time/space complexity (e.g., 'O(n log n)')")

    # Additional metadata
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Confidence score for auto-generated metadata"
    )
    source: str = Field(
        default="manual", description="Source of metadata ('manual', 'llm', 'hybrid')"
    )
    last_updated: str | None = Field(None, description="ISO timestamp of last update")

    # Custom fields
    custom_fields: dict[str, Any] = Field(
        default_factory=dict, description="Additional custom metadata fields"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "name": "T-Test for Means",
                "id": "t-test-means",
                "path": "Exploring Mathematics with Python/t-test-means",
                "category": "statistical_method",
                "tags": ["hypothesis_testing", "means", "parametric"],
                "input_data_types": ["numerical"],
                "output_format": "table",
                "description": "Performs a t-test to compare means between two groups",
                "dependencies": ["scipy", "numpy", "pandas"],
                "statistical_concept": "hypothesis_testing",
                "assumptions": ["normality", "independent_samples", "equal_variance"],
                "use_cases": [
                    "Comparing average test scores between two classes",
                    "Testing if a new process improves output",
                ],
                "confidence": 0.95,
                "source": "llm",
            }
        }


class SkillIndexMetadata(BaseModel):
    """Metadata for the entire skill index."""

    skills: list[SkillMetadata] = Field(
        default_factory=list, description="List of all indexed skills"
    )
    categories: dict[str, int] = Field(
        default_factory=dict, description="Count of skills per category"
    )
    last_updated: str = Field(..., description="ISO timestamp of last index update")
    total_skills: int = Field(default=0, description="Total number of skills")

    def add_skill(self, skill: SkillMetadata) -> None:
        """Add a skill to the index."""
        self.skills.append(skill)
        self.total_skills = len(self.skills)
        self._update_categories()

    def _update_categories(self) -> None:
        """Update category counts."""
        self.categories = {}
        for skill in self.skills:
            cat = skill.category.value
            self.categories[cat] = self.categories.get(cat, 0) + 1

    def get_by_category(self, category: SkillCategory) -> list[SkillMetadata]:
        """Get all skills in a category."""
        return [s for s in self.skills if s.category == category]

    def get_by_tag(self, tag: str) -> list[SkillMetadata]:
        """Get all skills with a specific tag."""
        return [s for s in self.skills if tag in s.tags]

    def search(self, query: str) -> list[SkillMetadata]:
        """Search skills by name, description, or tags."""
        query = query.lower()
        results = []
        for skill in self.skills:
            if (
                query in skill.name.lower()
                or query in skill.description.lower()
                or any(query in tag.lower() for tag in skill.tags)
            ):
                results.append(skill)
        return results
