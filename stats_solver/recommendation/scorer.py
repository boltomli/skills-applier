"""Recommendation scoring system for ranking skill matches."""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

from .matcher import MatchResult
from ..skills.metadata_schema import SkillMetadata

logger = logging.getLogger(__name__)


class RankingMethod(str, Enum):
    """Methods for ranking recommendations."""

    WEIGHTED_SCORE = "weighted_score"
    CONFIDENCE_SCORE = "confidence_score"
    BALANCED = "balanced"
    POPULARITY = "popularity"
    RECENTLY_USED = "recently_used"


@dataclass
class Recommendation:
    """A single recommendation with scoring details."""

    skill: SkillMetadata
    match_score: float
    confidence: float
    final_score: float
    match_reasons: List[str]
    mismatches: List[str]
    ranking_position: Optional[int] = None
    metadata: Dict[str, Any] = None


class RecommendationScorer:
    """Scorer for ranking and evaluating skill recommendations."""

    # Scoring weights for different factors
    SCORING_WEIGHTS = {
        "match_quality": 0.6,
        "confidence": 0.2,
        "skill_popularity": 0.1,
        "recency": 0.1,
    }

    def __init__(
        self,
        ranking_method: RankingMethod = RankingMethod.BALANCED,
        skill_usage_history: Optional[Dict[str, int]] = None,
    ) -> None:
        """Initialize recommendation scorer.

        Args:
            ranking_method: Method to use for ranking
            skill_usage_history: Dictionary mapping skill IDs to usage counts
        """
        self.ranking_method = ranking_method
        self.skill_usage_history = skill_usage_history or {}

    def score_recommendations(
        self, match_results: List[MatchResult], max_recommendations: int = 5
    ) -> List[Recommendation]:
        """Score and rank match results into recommendations.

        Args:
            match_results: Match results from the matcher
            max_recommendations: Maximum number of recommendations to return

        Returns:
            List of scored and ranked recommendations
        """
        recommendations = []

        for match_result in match_results:
            final_score = self._calculate_final_score(match_result)

            recommendation = Recommendation(
                skill=match_result.skill,
                match_score=match_result.score,
                confidence=match_result.confidence,
                final_score=final_score,
                match_reasons=match_result.match_reasons,
                mismatches=match_result.mismatches,
                metadata={
                    "ranking_method": self.ranking_method.value,
                },
            )
            recommendations.append(recommendation)

        # Sort by ranking method
        recommendations = self._rank_recommendations(recommendations)

        # Assign ranking positions
        for i, rec in enumerate(recommendations):
            rec.ranking_position = i + 1

        return recommendations[:max_recommendations]

    def _calculate_final_score(self, match_result: MatchResult) -> float:
        """Calculate final score based on ranking method.

        Args:
            match_result: Match result to score

        Returns:
            Final score
        """
        if self.ranking_method == RankingMethod.WEIGHTED_SCORE:
            return match_result.score

        elif self.ranking_method == RankingMethod.CONFIDENCE_SCORE:
            return match_result.confidence

        elif self.ranking_method == RankingMethod.BALANCED:
            # Balanced approach combining match score and confidence
            return (match_result.score * 0.7) + (match_result.confidence * 0.3)

        elif self.ranking_method == RankingMethod.POPULARITY:
            # Consider usage history
            usage_count = self.skill_usage_history.get(match_result.skill.id, 0)
            max_usage = max(self.skill_usage_history.values()) if self.skill_usage_history else 1
            popularity_score = usage_count / max_usage if max_usage > 0 else 0

            return (match_result.score * 0.7) + (popularity_score * 0.3)

        elif self.ranking_method == RankingMethod.RECENTLY_USED:
            # Similar to popularity, could be enhanced with timestamps
            usage_count = self.skill_usage_history.get(match_result.skill.id, 0)
            max_usage = max(self.skill_usage_history.values()) if self.skill_usage_history else 1
            recency_score = usage_count / max_usage if max_usage > 0 else 0

            return (match_result.score * 0.8) + (recency_score * 0.2)

        return match_result.score

    def _rank_recommendations(self, recommendations: List[Recommendation]) -> List[Recommendation]:
        """Rank recommendations by final score.

        Args:
            recommendations: Recommendations to rank

        Returns:
            Ranked recommendations
        """
        return sorted(recommendations, key=lambda r: r.final_score, reverse=True)

    def compare_recommendations(self, recommendations: List[Recommendation]) -> Dict[str, Any]:
        """Generate comparison summary of recommendations.

        Args:
            recommendations: Recommendations to compare

        Returns:
            Comparison summary dictionary
        """
        if not recommendations:
            return {
                "count": 0,
                "summary": "No recommendations available",
            }

        top = recommendations[0]

        # Calculate statistics
        scores = [r.final_score for r in recommendations]
        match_scores = [r.match_score for r in recommendations]
        confidences = [r.confidence for r in recommendations]

        return {
            "count": len(recommendations),
            "top_recommendation": {
                "name": top.skill.name,
                "score": top.final_score,
                "match_score": top.match_score,
                "confidence": top.confidence,
            },
            "score_statistics": {
                "mean": sum(scores) / len(scores),
                "min": min(scores),
                "max": max(scores),
            },
            "match_score_statistics": {
                "mean": sum(match_scores) / len(match_scores),
                "min": min(match_scores),
                "max": max(match_scores),
            },
            "confidence_statistics": {
                "mean": sum(confidences) / len(confidences),
                "min": min(confidences),
                "max": max(confidences),
            },
            "categories": self._get_category_distribution(recommendations),
        }

    def _get_category_distribution(self, recommendations: List[Recommendation]) -> Dict[str, int]:
        """Get distribution of skill categories.

        Args:
            recommendations: Recommendations to analyze

        Returns:
            Dictionary mapping category to count
        """
        distribution = {}

        for rec in recommendations:
            category = rec.skill.category.value
            distribution[category] = distribution.get(category, 0) + 1

        return distribution

    def filter_by_threshold(
        self, recommendations: List[Recommendation], threshold: float = 0.5
    ) -> List[Recommendation]:
        """Filter recommendations by score threshold.

        Args:
            recommendations: Recommendations to filter
            threshold: Minimum score threshold

        Returns:
            Filtered recommendations
        """
        return [r for r in recommendations if r.final_score >= threshold]

    def get_diverse_recommendations(
        self, recommendations: List[Recommendation], max_per_category: int = 2
    ) -> List[Recommendation]:
        """Get diverse recommendations across categories.

        Args:
            recommendations: Recommendations to diversify
            max_per_category: Maximum recommendations per category

        Returns:
            Diversified recommendations
        """
        # Group by category
        by_category: Dict[str, List[Recommendation]] = {}

        for rec in recommendations:
            category = rec.skill.category.value
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(rec)

        # Take top N from each category
        diverse = []
        for category, recs in by_category.items():
            diverse.extend(recs[:max_per_category])

        # Re-sort by final score
        diverse.sort(key=lambda r: r.final_score, reverse=True)

        return diverse

    def explain_score(self, recommendation: Recommendation) -> Dict[str, Any]:
        """Generate explanation for a recommendation's score.

        Args:
            recommendation: Recommendation to explain

        Returns:
            Explanation dictionary
        """
        explanation = {
            "skill_name": recommendation.skill.name,
            "final_score": recommendation.final_score,
            "components": {
                "match_quality": recommendation.match_score,
                "confidence": recommendation.confidence,
            },
            "match_reasons": recommendation.match_reasons,
            "mismatches": recommendation.mismatches,
            "ranking_method": self.ranking_method.value,
        }

        if self.ranking_method == RankingMethod.POPULARITY:
            usage = self.skill_usage_history.get(recommendation.skill.id, 0)
            explanation["components"]["popularity"] = usage

        # Add interpretive text
        if recommendation.final_score >= 0.8:
            explanation["interpretation"] = "Excellent match - highly recommended"
        elif recommendation.final_score >= 0.6:
            explanation["interpretation"] = "Good match - suitable choice"
        elif recommendation.final_score >= 0.4:
            explanation["interpretation"] = "Moderate match - may work with some adjustments"
        else:
            explanation["interpretation"] = "Weak match - consider alternatives"

        return explanation

    def aggregate_scores(self, recommendations: List[Recommendation]) -> float:
        """Calculate aggregate score for a set of recommendations.

        Args:
            recommendations: Recommendations to aggregate

        Returns:
            Aggregate score
        """
        if not recommendations:
            return 0.0

        return sum(r.final_score for r in recommendations) / len(recommendations)
