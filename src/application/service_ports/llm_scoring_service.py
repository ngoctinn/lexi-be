from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ScoringResult:
    fluency: int
    grammar: int
    vocabulary: int
    overall: int
    feedback: str


class LlmScoringService(ABC):
    """Port (abstraction) cho LLM-based scoring sau session."""

    @abstractmethod
    def score_session(
        self,
        scenario_title: str,
        level: str,
        goals: str,
        learner_transcript: str,
    ) -> ScoringResult:
        """Chấm điểm transcript của learner. Trả về ScoringResult."""
        ...
