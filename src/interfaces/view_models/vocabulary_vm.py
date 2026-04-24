"""
Vocabulary-related view models.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class VocabularyTranslationViewModel:
    """Vocabulary translation view model for API responses."""
    word: str
    translation_vi: str


@dataclass(frozen=True)
class SentenceTranslationViewModel:
    """Sentence translation view model for API responses."""
    sentence_en: str
    sentence_vi: str
