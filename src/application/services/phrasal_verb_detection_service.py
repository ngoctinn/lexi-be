from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class AnalyzedVocabularyToken:
    text: str
    token_type: str
    base: str | None = None
    definition_vi: str | None = None


class PhrasalVerbDetectionService(ABC):
    @abstractmethod
    def analyze(self, text: str) -> list[AnalyzedVocabularyToken]:
        ...
