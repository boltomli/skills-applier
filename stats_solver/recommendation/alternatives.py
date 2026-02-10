"""Alternative finder for suggesting alternative solutions."""

import logging
from typing import List, Dict, Optional, Set, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from ..skills.metadata_schema import SkillMetadata, SkillCategory, DataType
from ..skills.index import SkillIndex
from ..problem.classifier import ProblemType
from ..problem.data_types import DataTypeDetectionResult
from .matcher import MatchResult

logger = logging.getLogger(__name__)


class AlternativeType(str, Enum):
    """Types of alternatives."""
    
    SIMILAR_METHOD = "similar_method"
    SIMPLER_ALTERNATIVE = "simpler_alternative"
    MORE_ADVANCED = "more_advanced"
    DIFFERENT_APPROACH = "different_approach"
    COMPLEMENTARY = "complementary"


@dataclass
class Alternative:
    """An alternative solution."""
    
    skill: SkillMetadata
    alternative_type: AlternativeType
    similarity_score: float
    advantages: List[str]
    disadvantages: List[str]
    use_when: List[str]
    confidence: float


@dataclass
class AlternativeSet:
    """A set of alternative solutions."""
    
    primary_recommendation: SkillMetadata
    alternatives: List[Alternative]
    total_alternatives: int
    reasoning: str
    metadata: Dict[str, Any] = None


class AlternativeFinder:
    """Finder for alternative solutions and approaches."""
    
    # Method alternatives mapping
    METHOD_ALTERNATIVES = {
        "t-test": ["mann-whitney", "wilcoxon", "bootstrap"],
        "anova": ["kruskal-wallis", "bootstrap"],
        "linear_regression": ["polynomial_regression", "generalized_linear_model", "decision_tree"],
        "correlation": ["spearman", "kendall", "mutual_information"],
        "chi-square": ["fisher_exact", "bootstrap"],
    }
    
    # Complexity levels
    COMPLEXITY_ORDER = [
        "simple",
        "moderate",
        "complex",
        "advanced",
    ]
    
    def __init__(self, skill_index: SkillIndex) -> None:
        """Initialize alternative finder.
        
        Args:
            skill_index: Skill index to search
        """
        self.skill_index = skill_index
    
    async def find_alternatives(
        self,
        primary_skill: SkillMetadata,
        problem_type: ProblemType,
        data_type_result: Optional[DataTypeDetectionResult] = None,
        max_alternatives: int = 5
    ) -> AlternativeSet:
        """Find alternative solutions to the primary recommendation.
        
        Args:
            primary_skill: Primary recommended skill
            problem_type: Problem type
            data_type_result: Data type detection result
            max_alternatives: Maximum alternatives to find
            
        Returns:
            Set of alternative solutions
        """
        all_skills = self.skill_index.get_all_skills()
        
        # Find different types of alternatives
        alternatives = []
        
        # 1. Similar methods
        similar = await self._find_similar_methods(
            primary_skill, all_skills, problem_type
        )
        alternatives.extend(similar)
        
        # 2. Simpler alternatives
        simpler = await self._find_simpler_alternatives(
            primary_skill, all_skills, problem_type
        )
        alternatives.extend(simpler)
        
        # 3. More advanced methods
        advanced = await self._find_more_advanced(
            primary_skill, all_skills, problem_type
        )
        alternatives.extend(advanced)
        
        # 4. Different approaches
        different = await self._find_different_approaches(
            primary_skill, all_skills, problem_type, data_type_result
        )
        alternatives.extend(different)
        
        # 5. Complementary methods
        complementary = await self._find_complementary(
            primary_skill, all_skills, problem_type
        )
        alternatives.extend(complementary)
        
        # Remove duplicates and sort by similarity
        alternatives = self._deduplicate_alternatives(alternatives)
        alternatives.sort(key=lambda a: a.similarity_score, reverse=True)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(primary_skill, alternatives)
        
        return AlternativeSet(
            primary_recommendation=primary_skill,
            alternatives=alternatives[:max_alternatives],
            total_alternatives=len(alternatives),
            reasoning=reasoning,
            metadata={
                "problem_type": problem_type.value,
                "searched_types": [
                    AlternativeType.SIMILAR_METHOD.value,
                    AlternativeType.SIMPLER_ALTERNATIVE.value,
                    AlternativeType.MORE_ADVANCED.value,
                    AlternativeType.DIFFERENT_APPROACH.value,
                    AlternativeType.COMPLEMENTARY.value,
                ],
            },
        )
    
    async def _find_similar_methods(
        self,
        primary_skill: SkillMetadata,
        all_skills: List[SkillMetadata],
        problem_type: ProblemType
    ) -> List[Alternative]:
        """Find methods similar to the primary skill.
        
        Args:
            primary_skill: Primary skill
            all_skills: All available skills
            problem_type: Problem type
            
        Returns:
            List of similar method alternatives
        """
        alternatives = []
        
        # Check for direct alternatives in mapping
        skill_id_lower = primary_skill.id.lower()
        
        for method_id, alt_method_ids in self.METHOD_ALTERNATIVES.items():
            if method_id in skill_id_lower:
                for alt_id in alt_method_ids:
                    for skill in all_skills:
                        if alt_id in skill.id.lower() and skill.id != primary_skill.id:
                            alt = Alternative(
                                skill=skill,
                                alternative_type=AlternativeType.SIMILAR_METHOD,
                                similarity_score=self._calculate_similarity(primary_skill, skill),
                                advantages=self._get_advantages(skill, primary_skill),
                                disadvantages=self._get_disadvantages(skill, primary_skill),
                                use_when=self._get_use_when(skill, "similar"),
                                confidence=0.8,
                            )
                            alternatives.append(alt)
        
        # Also find by category and tags
        for skill in all_skills:
            if skill.id == primary_skill.id:
                continue
            
            # Same category
            if skill.category == primary_skill.category:
                # Check tag overlap
                tag_overlap = set(skill.tags) & set(primary_skill.tags)
                if len(tag_overlap) >= 2:
                    alt = Alternative(
                        skill=skill,
                        alternative_type=AlternativeType.SIMILAR_METHOD,
                        similarity_score=self._calculate_similarity(primary_skill, skill),
                        advantages=self._get_advantages(skill, primary_skill),
                        disadvantages=self._get_disadvantages(skill, primary_skill),
                        use_when=self._get_use_when(skill, "similar"),
                        confidence=0.7,
                    )
                    alternatives.append(alt)
        
        return alternatives[:3]
    
    async def _find_simpler_alternatives(
        self,
        primary_skill: SkillMetadata,
        all_skills: List[SkillMetadata],
        problem_type: ProblemType
    ) -> List[Alternative]:
        """Find simpler alternatives to the primary skill.
        
        Args:
            primary_skill: Primary skill
            all_skills: All available skills
            problem_type: Problem type
            
        Returns:
            List of simpler alternatives
        """
        alternatives = []
        
        # Look for skills with "simple", "basic", or "easy" keywords
        simple_keywords = ["simple", "basic", "easy", "quick", "introductory"]
        
        for skill in all_skills:
            if skill.id == primary_skill.id:
                continue
            
            skill_text = f"{skill.id} {skill.description}".lower()
            
            if any(kw in skill_text for kw in simple_keywords):
                # Check if it's actually for the same problem type
                if self._is_compatible_problem_type(skill, problem_type):
                    alt = Alternative(
                        skill=skill,
                        alternative_type=AlternativeType.SIMPLER_ALTERNATIVE,
                        similarity_score=self._calculate_similarity(primary_skill, skill) * 0.8,
                        advantages=["Easier to understand", "Faster computation", "Fewer assumptions"],
                        disadvantages=["Less powerful", "May miss nuanced patterns"],
                        use_when=["Simplicity is prioritized", "Quick results needed", "Learning stage"],
                        confidence=0.75,
                    )
                    alternatives.append(alt)
        
        return alternatives[:2]
    
    async def _find_more_advanced(
        self,
        primary_skill: SkillMetadata,
        all_skills: List[SkillMetadata],
        problem_type: ProblemType
    ) -> List[Alternative]:
        """Find more advanced alternatives to the primary skill.
        
        Args:
            primary_skill: Primary skill
            all_skills: All available skills
            problem_type: Problem type
            
        Returns:
            List of more advanced alternatives
        """
        alternatives = []
        
        # Look for skills with "advanced", "sophisticated", or "complex" keywords
        advanced_keywords = ["advanced", "sophisticated", "complex", "robust", "enhanced"]
        
        for skill in all_skills:
            if skill.id == primary_skill.id:
                continue
            
            skill_text = f"{skill.id} {skill.description}".lower()
            
            if any(kw in skill_text for kw in advanced_keywords):
                # Check if it's actually for the same problem type
                if self._is_compatible_problem_type(skill, problem_type):
                    alt = Alternative(
                        skill=skill,
                        alternative_type=AlternativeType.MORE_ADVANCED,
                        similarity_score=self._calculate_similarity(primary_skill, skill) * 0.9,
                        advantages=["More powerful", "Handles edge cases", "Better accuracy"],
                        disadvantages=["More complex", "Slower computation", "Requires more data"],
                        use_when=["High accuracy needed", "Complex data patterns", "Expert users"],
                        confidence=0.7,
                    )
                    alternatives.append(alt)
        
        return alternatives[:2]
    
    async def _find_different_approaches(
        self,
        primary_skill: SkillMetadata,
        all_skills: List[SkillMetadata],
        problem_type: ProblemType,
        data_type_result: Optional[DataTypeDetectionResult] = None
    ) -> List[Alternative]:
        """Find different approaches to solving the same problem.
        
        Args:
            primary_skill: Primary skill
            all_skills: All available skills
            problem_type: Problem type
            data_type_result: Data type detection result
            
        Returns:
            List of different approach alternatives
        """
        alternatives = []
        
        for skill in all_skills:
            if skill.id == primary_skill.id:
                continue
            
            # Check if it solves the same problem type but differently
            if self._is_compatible_problem_type(skill, problem_type):
                # Check if it's truly different (low similarity)
                similarity = self._calculate_similarity(primary_skill, skill)
                
                if 0.3 <= similarity <= 0.6:  # Moderately similar, not too different
                    alt = Alternative(
                        skill=skill,
                        alternative_type=AlternativeType.DIFFERENT_APPROACH,
                        similarity_score=similarity,
                        advantages=self._get_advantages(skill, primary_skill),
                        disadvantages=self._get_disadvantages(skill, primary_skill),
                        use_when=self._get_use_when(skill, "different"),
                        confidence=0.65,
                    )
                    alternatives.append(alt)
        
        return alternatives[:2]
    
    async def _find_complementary(
        self,
        primary_skill: SkillMetadata,
        all_skills: List[SkillMetadata],
        problem_type: ProblemType
    ) -> List[Alternative]:
        """Find methods that complement the primary skill.
        
        Args:
            primary_skill: Primary skill
            all_skills: All available skills
            problem_type: Problem type
            
        Returns:
            List of complementary alternatives
        """
        alternatives = []
        
        # Look for visualization skills for statistical methods
        if primary_skill.category == SkillCategory.STATISTICAL_METHOD:
            viz_keywords = ["plot", "graph", "chart", "visualize"]
            
            for skill in all_skills:
                if skill.id == primary_skill.id:
                    continue
                
                if any(kw in skill.id.lower() or kw in skill.description.lower() for kw in viz_keywords):
                    alt = Alternative(
                        skill=skill,
                        alternative_type=AlternativeType.COMPLEMENTARY,
                        similarity_score=0.5,
                        advantages=["Visual representation", "Better communication", "Pattern detection"],
                        disadvantages=["Additional step", "Requires visualization libraries"],
                        use_when=["Need to present results", "Explore data visually", "Create reports"],
                        confidence=0.8,
                    )
                    alternatives.append(alt)
        
        return alternatives[:2]
    
    def _calculate_similarity(
        self,
        skill1: SkillMetadata,
        skill2: SkillMetadata
    ) -> float:
        """Calculate similarity between two skills.
        
        Args:
            skill1: First skill
            skill2: Second skill
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        score = 0.0
        
        # Category match
        if skill1.category == skill2.category:
            score += 0.3
        
        # Tag overlap
        tags1 = set(skill1.tags)
        tags2 = set(skill2.tags)
        if tags1 and tags2:
            overlap = len(tags1 & tags2)
            score += min(overlap * 0.15, 0.3)
        
        # Statistical concept match
        if skill1.statistical_concept and skill2.statistical_concept:
            if skill1.statistical_concept == skill2.statistical_concept:
                score += 0.2
            elif skill1.statistical_concept in skill2.statistical_concept or skill2.statistical_concept in skill1.statistical_concept:
                score += 0.1
        
        # Data type compatibility
        types1 = set(skill1.input_data_types) or {DataType.NUMERICAL}
        types2 = set(skill2.input_data_types) or {DataType.NUMERICAL}
        if types1 & types2:
            score += 0.2
        
        return min(score, 1.0)
    
    def _is_compatible_problem_type(
        self,
        skill: SkillMetadata,
        problem_type: ProblemType
    ) -> bool:
        """Check if skill is compatible with problem type.
        
        Args:
            skill: Skill to check
            problem_type: Problem type
            
        Returns:
            True if compatible
        """
        # Check tags
        type_keywords = problem_type.value.split("_")
        skill_text = f"{skill.id} {skill.description} {' '.join(skill.tags)}".lower()
        
        return any(kw in skill_text for kw in type_keywords)
    
    def _get_advantages(
        self,
        alternative_skill: SkillMetadata,
        primary_skill: SkillMetadata
    ) -> List[str]:
        """Get advantages of the alternative over primary.
        
        Args:
            alternative_skill: Alternative skill
            primary_skill: Primary skill
            
        Returns:
            List of advantages
        """
        advantages = []
        
        # Check for fewer dependencies
        if len(alternative_skill.dependencies) < len(primary_skill.dependencies):
            advantages.append("Fewer dependencies")
        
        # Check for simpler complexity
        if alternative_skill.complexity and primary_skill.complexity:
            if "O(n)" in alternative_skill.complexity and "O(n^2)" in primary_skill.complexity:
                advantages.append("Better time complexity")
        
        # Check for more use cases
        if len(alternative_skill.use_cases) > len(primary_skill.use_cases):
            advantages.append("More use cases")
        
        if not advantages:
            advantages.append("Different approach")
        
        return advantages
    
    def _get_disadvantages(
        self,
        alternative_skill: SkillMetadata,
        primary_skill: SkillMetadata
    ) -> List[str]:
        """Get disadvantages of the alternative compared to primary.
        
        Args:
            alternative_skill: Alternative skill
            primary_skill: Primary skill
            
        Returns:
            List of disadvantages
        """
        disadvantages = []
        
        # Check for more dependencies
        if len(alternative_skill.dependencies) > len(primary_skill.dependencies):
            disadvantages.append("More dependencies")
        
        # Check for higher complexity
        if alternative_skill.complexity and primary_skill.complexity:
            if "O(n^2)" in alternative_skill.complexity and "O(n)" in primary_skill.complexity:
                disadvantages.append("Worse time complexity")
        
        # Check for lower confidence
        if alternative_skill.confidence < primary_skill.confidence:
            disadvantages.append("Lower confidence in classification")
        
        if not disadvantages:
            disadvantages.append("Different approach")
        
        return disadvantages
    
    def _get_use_when(
        self,
        skill: SkillMetadata,
        alt_type: str
    ) -> List[str]:
        """Get use cases for the alternative.
        
        Args:
            skill: Alternative skill
            alt_type: Type of alternative
            
        Returns:
            List of use cases
        """
        if alt_type == "similar":
            return ["Similar requirements", "Alternative approach needed"]
        elif alt_type == "different":
            return ["Different perspective", "Verify results"]
        else:
            return skill.use_cases[:2] if skill.use_cases else ["General use"]
    
    def _deduplicate_alternatives(
        self,
        alternatives: List[Alternative]
    ) -> List[Alternative]:
        """Remove duplicate alternatives.
        
        Args:
            alternatives: Alternatives to deduplicate
            
        Returns:
            Deduplicated alternatives
        """
        seen = set()
        unique = []
        
        for alt in alternatives:
            key = (alt.skill.id, alt.alternative_type)
            if key not in seen:
                seen.add(key)
                unique.append(alt)
        
        return unique
    
    def _generate_reasoning(
        self,
        primary_skill: SkillMetadata,
        alternatives: List[Alternative]
    ) -> str:
        """Generate reasoning for the alternative set.
        
        Args:
            primary_skill: Primary skill
            alternatives: Alternative skills
            
        Returns:
            Reasoning string
        """
        if not alternatives:
            return f"No alternatives found for {primary_skill.name}"
        
        type_counts = {}
        for alt in alternatives:
            type_counts[alt.alternative_type] = type_counts.get(alt.alternative_type, 0) + 1
        
        type_str = ", ".join([f"{t.value} ({c})" for t, c in type_counts.items()])
        
        return f"Found {len(alternatives)} alternatives for {primary_skill.name}: {type_str}"