"""Prerequisite checker for skill dependencies."""

import logging
from typing import List, Dict, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum

from ..skills.metadata_schema import SkillMetadata, SkillCategory
from ..skills.index import SkillIndex

logger = logging.getLogger(__name__)


class PrerequisiteStatus(str, Enum):
    """Status of prerequisite check."""
    
    SATISFIED = "satisfied"
    MISSING = "missing"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


@dataclass
class Prerequisite:
    """A prerequisite requirement."""
    
    skill_id: str
    skill_name: str
    description: str
    status: PrerequisiteStatus
    confidence: float


@dataclass
class PrerequisiteCheckResult:
    """Result of prerequisite check for a skill."""
    
    skill: SkillMetadata
    all_satisfied: bool
    prerequisites: List[Prerequisite]
    missing_count: int
    satisfied_count: int
    warning_message: Optional[str] = None


class PrerequisiteChecker:
    """Checker for skill prerequisites and dependencies."""
    
    def __init__(self, skill_index: SkillIndex) -> None:
        """Initialize prerequisite checker.
        
        Args:
            skill_index: Skill index to check against
        """
        self.skill_index = skill_index
    
    async def check_prerequisites(
        self,
        skill: SkillMetadata,
        available_skills: Optional[List[SkillMetadata]] = None
    ) -> PrerequisiteCheckResult:
        """Check if a skill's prerequisites are satisfied.
        
        Args:
            skill: Skill to check
            available_skills: List of available skills (defaults to all in index)
            
        Returns:
            Prerequisite check result
        """
        if available_skills is None:
            available_skills = self.skill_index.get_all_skills()
        
        # Create lookup of available skills by ID
        available_map = {s.id: s for s in available_skills}
        
        prerequisites = []
        missing_count = 0
        satisfied_count = 0
        
        # Check explicit prerequisites
        for prereq_id in skill.prerequisites:
            prereq = self._check_single_prerequisite(prereq_id, available_map)
            prerequisites.append(prereq)
            
            if prereq.status == PrerequisiteStatus.SATISFIED:
                satisfied_count += 1
            elif prereq.status == PrerequisiteStatus.MISSING:
                missing_count += 1
        
        # Check implicit prerequisites based on category
        implicit_prereqs = self._infer_implicit_prerequisites(skill, available_skills)
        for prereq_id in implicit_prereqs:
            if prereq_id not in skill.prerequisites:  # Don't duplicate
                prereq = self._check_single_prerequisite(prereq_id, available_map)
                prerequisites.append(prereq)
                
                if prereq.status == PrerequisiteStatus.SATISFIED:
                    satisfied_count += 1
                elif prereq.status == PrerequisiteStatus.MISSING:
                    missing_count += 1
        
        # Determine overall status
        all_satisfied = missing_count == 0
        
        # Generate warning if needed
        warning = None
        if missing_count > 0:
            warning = f"Missing {missing_count} prerequisite(s)"
        
        return PrerequisiteCheckResult(
            skill=skill,
            all_satisfied=all_satisfied,
            prerequisites=prerequisites,
            missing_count=missing_count,
            satisfied_count=satisfied_count,
            warning_message=warning,
        )
    
    def _check_single_prerequisite(
        self,
        prereq_id: str,
        available_map: Dict[str, SkillMetadata]
    ) -> Prerequisite:
        """Check a single prerequisite.
        
        Args:
            prereq_id: Prerequisite skill ID
            available_map: Available skills lookup
            
        Returns:
            Prerequisite object
        """
        if prereq_id in available_map:
            prereq_skill = available_map[prereq_id]
            return Prerequisite(
                skill_id=prereq_id,
                skill_name=prereq_skill.name,
                description=prereq_skill.description,
                status=PrerequisiteStatus.SATISFIED,
                confidence=1.0,
            )
        else:
            # Try to find similar skills
            similar = self._find_similar_skills(prereq_id, available_map)
            if similar:
                return Prerequisite(
                    skill_id=prereq_id,
                    skill_name=prereq_id.replace("-", " ").title(),
                    description=f"Similar to: {', '.join(similar)}",
                    status=PrerequisiteStatus.PARTIAL,
                    confidence=0.5,
                )
            else:
                return Prerequisite(
                    skill_id=prereq_id,
                    skill_name=prereq_id.replace("-", " ").title(),
                    description="Prerequisite not found",
                    status=PrerequisiteStatus.MISSING,
                    confidence=0.0,
                )
    
    def _infer_implicit_prerequisites(
        self,
        skill: SkillMetadata,
        available_skills: List[SkillMetadata]
    ) -> List[str]:
        """Infer implicit prerequisites based on skill characteristics.
        
        Args:
            skill: Skill to analyze
            available_skills: Available skills
            
        Returns:
            List of inferred prerequisite IDs
        """
        implicit = []
        
        # Statistical methods often need basic descriptive statistics
        if skill.category == SkillCategory.STATISTICAL_METHOD:
            if not any("descriptive" in s.id.lower() for s in available_skills if s.id in skill.prerequisites):
                descriptive_skills = [
                    s.id for s in available_skills
                    if "descriptive" in s.id.lower() or "summary" in s.id.lower()
                ]
                if descriptive_skills:
                    implicit.extend(descriptive_skills[:1])
        
        # Regression often needs correlation analysis
        if "regression" in skill.id.lower():
            if not any("correlation" in s.id.lower() for s in available_skills if s.id in skill.prerequisites):
                correlation_skills = [
                    s.id for s in available_skills
                    if "correlation" in s.id.lower()
                ]
                if correlation_skills:
                    implicit.extend(correlation_skills[:1])
        
        # Check dependencies
        if "scipy" in skill.dependencies:
            scipy_skills = [
                s.id for s in available_skills
                if "scipy" in s.dependencies and s.id != skill.id
            ]
            # Add skills that commonly use scipy
            implicit.extend(scipy_skills[:2])
        
        return implicit
    
    def _find_similar_skills(
        self,
        prereq_id: str,
        available_map: Dict[str, SkillMetadata]
    ) -> List[str]:
        """Find skills similar to the prerequisite.
        
        Args:
            prereq_id: Prerequisite skill ID
            available_map: Available skills lookup
            
        Returns:
            List of similar skill names
        """
        prereq_lower = prereq_id.lower()
        similar = []
        
        for skill_id, skill in available_map.items():
            # Check for partial matches
            if prereq_lower in skill_id.lower() or skill_id.lower() in prereq_lower:
                similar.append(skill.name)
        
        return similar[:3]
    
    async def check_batch(
        self,
        skills: List[SkillMetadata],
        available_skills: Optional[List[SkillMetadata]] = None
    ) -> List[PrerequisiteCheckResult]:
        """Check prerequisites for multiple skills.
        
        Args:
            skills: Skills to check
            available_skills: Available skills
            
        Returns:
            List of check results
        """
        results = []
        
        for skill in skills:
            result = await self.check_prerequisites(skill, available_skills)
            results.append(result)
        
        return results
    
    def get_missing_prerequisites(
        self,
        results: List[PrerequisiteCheckResult]
    ) -> Dict[str, List[Prerequisite]]:
        """Get all missing prerequisites across results.
        
        Args:
            results: Prerequisite check results
            
        Returns:
            Dictionary mapping skill ID to list of missing prerequisites
        """
        missing = {}
        
        for result in results:
            missing_for_skill = [
                p for p in result.prerequisites
                if p.status == PrerequisiteStatus.MISSING
            ]
            if missing_for_skill:
                missing[result.skill.id] = missing_for_skill
        
        return missing
    
    def filter_by_prerequisites(
        self,
        skills: List[SkillMetadata],
        available_skills: Optional[List[SkillMetadata]] = None,
        require_all: bool = False
    ) -> List[SkillMetadata]:
        """Filter skills by prerequisite satisfaction.
        
        Args:
            skills: Skills to filter
            available_skills: Available skills
            require_all: If True, require all prerequisites; if False, allow some missing
            
        Returns:
            Filtered list of skills
        """
        filtered = []
        
        for skill in skills:
            result = self.check_prerequisites_sync(skill, available_skills)
            
            if require_all:
                if result.all_satisfied:
                    filtered.append(skill)
            else:
                # Allow if at least half of prerequisites are satisfied
                total = len(result.prerequisites)
                if total == 0 or result.satisfied_count >= total / 2:
                    filtered.append(skill)
        
        return filtered
    
    def check_prerequisites_sync(
        self,
        skill: SkillMetadata,
        available_skills: Optional[List[SkillMetadata]] = None
    ) -> PrerequisiteCheckResult:
        """Synchronous version of check_prerequisites.
        
        Args:
            skill: Skill to check
            available_skills: Available skills
            
        Returns:
            Prerequisite check result
        """
        # Simple synchronous implementation
        if available_skills is None:
            available_skills = self.skill_index.get_all_skills()
        
        available_map = {s.id: s for s in available_skills}
        
        prerequisites = []
        missing_count = 0
        satisfied_count = 0
        
        for prereq_id in skill.prerequisites:
            prereq = self._check_single_prerequisite(prereq_id, available_map)
            prerequisites.append(prereq)
            
            if prereq.status == PrerequisiteStatus.SATISFIED:
                satisfied_count += 1
            elif prereq.status == PrerequisiteStatus.MISSING:
                missing_count += 1
        
        all_satisfied = missing_count == 0
        warning = f"Missing {missing_count} prerequisite(s)" if missing_count > 0 else None
        
        return PrerequisiteCheckResult(
            skill=skill,
            all_satisfied=all_satisfied,
            prerequisites=prerequisites,
            missing_count=missing_count,
            satisfied_count=satisfied_count,
            warning_message=warning,
        )
    
    def generate_prerequisite_report(
        self,
        results: List[PrerequisiteCheckResult]
    ) -> Dict[str, Any]:
        """Generate a summary report of prerequisite checks.
        
        Args:
            results: Prerequisite check results
            
        Returns:
            Summary report dictionary
        """
        total = len(results)
        satisfied = sum(1 for r in results if r.all_satisfied)
        missing_total = sum(r.missing_count for r in results)
        satisfied_total = sum(r.satisfied_count for r in results)
        
        return {
            "total_skills": total,
            "fully_satisfied": satisfied,
            "partially_satisfied": total - satisfied,
            "total_prerequisites": missing_total + satisfied_total,
            "missing_prerequisites": missing_total,
            "satisfied_prerequisites": satisfied_total,
            "satisfaction_rate": satisfied / total if total > 0 else 0,
            "skills_with_missing": [
                r.skill.id for r in results if r.missing_count > 0
            ],
        }