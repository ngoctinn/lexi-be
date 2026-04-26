"""
Vocabulary-related view models.
"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass(frozen=True)
class SynonymVM:
    """Synonym view model."""
    en: str
    vi: str = ""


@dataclass(frozen=True)
class DefinitionVM:
    """Definition view model."""
    part_of_speech: str
    definition_en: str
    definition_vi: str = ""
    example_en: str = ""
    example_vi: str = ""


@dataclass(frozen=True)
class VocabularyTranslationViewModel:
    """Vocabulary translation view model for API responses."""
    word: str
    translation_vi: str
    phonetic: str = ""
    definitions: List[DefinitionVM] = field(default_factory=list)
    synonyms: List[SynonymVM] = field(default_factory=list)
    response_time_ms: int = 0
    cached: bool = False


@dataclass(frozen=True)
class SentenceTranslationViewModel:
    """Sentence translation view model for API responses."""
    sentence_en: str
    sentence_vi: str
