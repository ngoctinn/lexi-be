import re
from typing import Optional

from pydantic import Field, field_validator

from application.dtos.base_dto import BaseDTO


class TranslateVocabularyCommand(BaseDTO):
    word: str = Field(strict=True, min_length=1, max_length=100)
    # Câu chứa từ cần dịch — dùng để AWS Translate hiểu đúng ngữ cảnh
    sentence: str | None = Field(default=None, max_length=5000)
    # Context for phrasal verb detection (e.g., "I got off the bus")
    context: Optional[str] = Field(default=None, max_length=500)

    @field_validator("word")
    @classmethod
    def normalize_word(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.match(r"^[a-zA-Z\s\-']+$", normalized):
            raise ValueError("Word should only contain letters, spaces, hyphens, or apostrophes")
        return normalized


class SynonymDTO(BaseDTO):
    """Synonym with English and Vietnamese translation."""
    en: str
    vi: str = ""


class MeaningDTO(BaseDTO):
    """
    Meaning for a specific part of speech with translations.
    Represents one definition and one example per meaning (FIRST from Dictionary API).
    """
    part_of_speech: str = Field(min_length=1, max_length=50)
    definition: str = Field(min_length=1)
    definition_vi: str = ""
    example: str = ""
    example_vi: str = ""


class DefinitionDTO(BaseDTO):
    """Definition for a specific part of speech."""
    part_of_speech: str
    definition_en: str
    definition_vi: str = ""
    example_en: str = ""
    example_vi: str = ""


class TranslateVocabularyResponse(BaseDTO):
    # Backward compatibility fields
    word: str
    translate_vi: str  # Nghĩa tiếng Việt (từ AWS Translate với context) - MUST match spec
    
    # New enriched fields from Dictionary API
    phonetic: str = ""  # IPA notation
    audio_url: Optional[str] = None  # Audio pronunciation URL
    meanings: list[MeaningDTO] = Field(default_factory=list)  # All meanings with translations
    
    # Legacy fields (kept for backward compatibility with existing code)
    definitions: list[DefinitionDTO] = Field(default_factory=list)
    synonyms: list[SynonymDTO] = Field(default_factory=list)
    
    # Metadata
    response_time_ms: int = 0
    cached: bool = False


class TranslateSentenceCommand(BaseDTO):
    # AWS Translate giới hạn 10,000 bytes per request
    # Tăng lên 5000 chars để cover lượt hội thoại dài
    sentence: str = Field(strict=True, min_length=1, max_length=5000)


class TranslateSentenceResponse(BaseDTO):
    sentence_en: str
    sentence_vi: str  # Bản dịch toàn câu bằng AWS Translate
