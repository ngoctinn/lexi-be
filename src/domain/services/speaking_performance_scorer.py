"""Domain service for scoring learner's speaking performance.

This service orchestrates the scoring process using LLM-based external scorer.
"""

import logging
from typing import List

from domain.entities.turn import Turn

logger = logging.getLogger(__name__)


class SpeakingPerformanceScorer:
    """Score learner's speaking performance using LLM (Bedrock)."""

    def __init__(self, external_scorer):
        """
        Args:
            external_scorer: External scorer implementation (e.g., BedrockScorerAdapter).
                           Required - no fallback to heuristic.
        """
        if not external_scorer:
            raise ValueError("external_scorer is required")
        self.external_scorer = external_scorer

    def score_session(
        self, user_turns: List[Turn], level: str, scenario_title: str
    ) -> dict:
        """
        Score learner's speaking performance using LLM.

        Args:
            user_turns: List of user Turn entities
            level: Proficiency level (A1-C2)
            scenario_title: Scenario name

        Returns:
            {
                "fluency_score": 76,
                "pronunciation_score": 72,
                "grammar_score": 71,
                "vocabulary_score": 67,
                "overall_score": 72,
                "feedback": "..."
            }

        Raises:
            ValueError: If no turns provided
            Exception: If LLM scoring fails
        """
        if not user_turns:
            raise ValueError("Cannot score session with no user turns")

        result = self.external_scorer.score(user_turns, level, scenario_title)
        if not result:
            raise Exception("LLM scoring returned empty result")

        return result
