import re
from typing import Optional

from pydantic import Field, field_validator

from application.dtos.base_dto import BaseDTO


class CreateFlashCardCommand(BaseDTO):
    user_id: str = Field(strict=True, min_length=1)
    word: str = Field(strict=True, min_length=1, max_length=100)

    # Required fields
    vocab_type: str = Field(...)

    # Translation fields
    translation_vi: Optional[str] = Field(default="")

    # Optional fields
    phonetic: Optional[str] = Field(default="")
    audio_url: Optional[str] = Field(default="")
    example_sentence: str = Field(default="", max_length=500)

    # Source tracking (từ session)
    source_session_id: Optional[str] = Field(default=None)
    source_turn_index: Optional[int] = Field(default=None)

    @field_validator("word")
    @classmethod
    def validate_word_format(cls, v: str) -> str:
        """Validate word format.
        
        Allows:
        - Letters (a-z, A-Z)
        - Spaces (for phrases like "phrasal verb")
        - Hyphens (-) for compound words (e.g., "well-known")
        - Apostrophes (') for contractions (e.g., "don't", "I'm")
        - Dots (.) for abbreviations (e.g., "Mr.", "etc.")
        
        Rejects:
        - Long sentences (> 50 characters)
        - Multiple sentences (multiple . or !)
        - Sentence punctuation (!?;:,)
        
        Examples:
            Valid: "run", "phrasal verb", "don't", "Mr. Smith", "well-known"
            Invalid: "Hello! I'm Sarah.", "This is a long sentence."
        """
        # Trim whitespace
        v = v.strip()
        
        # Check length (prevent full sentences)
        if len(v) > 50:
            raise ValueError(
                "Word too long (max 50 characters). "
                "Please enter a single word or short phrase, not a full sentence."
            )
        
        # Check for sentence punctuation (indicators of full sentences)
        sentence_indicators = ['!', '?', ';', ':', ',']
        if any(char in v for char in sentence_indicators):
            raise ValueError(
                f"Word should not contain sentence punctuation ({', '.join(sentence_indicators)}). "
                "Please enter a word or phrase only."
            )
        
        # Check for multiple sentences (multiple dots not at end)
        # Allow single dot at end (e.g., "Mr.") but not multiple dots
        if v.count('.') > 1:
            raise ValueError(
                "Word should be a single word or phrase, not multiple sentences."
            )
        
        # Allow letters, spaces, hyphens, apostrophes, single dot
        if not re.match(r"^[a-zA-Z\s\-'.]+$", v):
            raise ValueError(
                "Word should only contain letters, spaces, hyphens (-), apostrophes ('), or dots (.)."
            )
        
        # Additional check: If it looks like a full sentence (starts with capital + ends with .)
        if v[0].isupper() and v.endswith('.') and len(v) > 20:
            raise ValueError(
                "This looks like a full sentence. Please enter only the word or phrase you want to learn."
            )
        
        return v.strip().lower()

    @field_validator("vocab_type")
    @classmethod
    def validate_vocab_type(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("vocab_type must be a string")
        normalized = v.strip().lower()
        valid_types = {
            "noun", "verb", "adjective", "adverb", "pronoun", "preposition",
            "conjunction", "interjection", "phrase", "idiom",
            "n", "v", "adj", "adv", "prep", "conj", "int", "pron",
        }
        if normalized not in valid_types:
            raise ValueError(f"Invalid vocab_type. Must be one of {sorted(valid_types)}")
        return normalized


class CreateFlashCardResponse(BaseDTO):
    """DTO đầu ra cho CreateFlashCardUC."""
    flashcard_id: str
    word: str
    translation_vi: str = ""
    phonetic: str = ""
    audio_url: str = ""
    example_sentence: str = ""
    created_at: str = ""
