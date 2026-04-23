from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List

from domain.entities.session import Session
from domain.entities.turn import Turn


@dataclass(frozen=True)
class SpeakingAnalysis:
    key_phrases: List[str] = field(default_factory=list)
    word_count: int = 0
    unique_word_count: int = 0
    sentence_count: int = 0
    syntax_notes: List[str] = field(default_factory=list)
    dominant_language: str = "en"  # ISO 639-1 code, dùng để detect tiếng Việt


class TranscriptAnalysisService(ABC):
    @abstractmethod
    def analyze(self, text: str) -> SpeakingAnalysis:
        ...


class ConversationGenerationService(ABC):
    @abstractmethod
    def generate_reply(
        self,
        session: Session,
        user_turn: Turn,
        analysis: SpeakingAnalysis,
        turn_history: List[Turn],
    ) -> str:
        ...


class SpeechSynthesisService(ABC):
    @abstractmethod
    def synthesize(self, text: str, ai_gender: str, object_key: str | None = None) -> str:
        ...
