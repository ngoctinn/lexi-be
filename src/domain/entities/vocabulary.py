"""Domain entities for vocabulary definitions."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Phonetic:
    """Phonetic representation with optional audio."""
    text: str  # IPA notation
    audio: Optional[str] = None  # Audio URL


@dataclass
class Meaning:
    """
    Meaning for a specific part of speech with translations.
    
    Contains ONE definition and ONE example per meaning (FIRST from Dictionary API).
    Includes Vietnamese translations for both.
    """
    part_of_speech: str  # "noun", "verb", "adjective", etc.
    definition: str  # English definition (FIRST from API)
    definition_vi: str = ""  # Vietnamese translation of definition
    example: str = ""  # English example sentence (FIRST from API, if exists)
    example_vi: str = ""  # Vietnamese translation of example


@dataclass
class Vocabulary:
    """
    Complete vocabulary information from Dictionary API + AWS Translate.
    
    Represents a word with its pronunciation, meanings, and translations.
    Maintains backward compatibility with word and translate_vi at top level.
    """
    word: str  # English word (original or detected phrasal verb)
    translate_vi: str  # Vietnamese translation of the word
    phonetic: str  # Primary phonetic (IPA notation)
    audio_url: Optional[str] = None  # Audio URL (from first phonetic)
    meanings: List[Meaning] = field(default_factory=list)  # All meanings with translations
    origin: Optional[str] = None  # Word origin (if available from API)
