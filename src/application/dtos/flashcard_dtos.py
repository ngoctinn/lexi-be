import re
from typing import Optional

from pydantic import Field, field_validator

from application.dtos.base_dto import BaseDTO


class CreateFlashCardCommand(BaseDTO):
    user_id: str = Field(strict=True, min_length=1)
    vocab: str = Field(strict=True, min_length=1, max_length=100)

    # Required fields
    vocab_type: str = Field(...)

    # Translation fields
    translation_vi: Optional[str] = Field(default="")
    definition_vi: str = Field(...)

    # Optional fields
    phonetic: Optional[str] = Field(default="")
    audio_url: Optional[str] = Field(default="")
    example_sentence: str = Field(default="", max_length=500)
    source_api: Optional[str] = Field(default="internal")

    # Source tracking (từ session)
    source_session_id: Optional[str] = Field(default=None)
    source_turn_index: Optional[int] = Field(default=None)

    @field_validator("vocab")
    @classmethod
    def validate_no_special_chars(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z\s\-]+$", v):
            raise ValueError("Vocabulary should only contain letters, spaces, or hyphens")
        return v.lower()

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
    definition_vi: str = ""
    phonetic: str = ""
    audio_url: str = ""
    example_sentence: str = ""
    created_at: str = ""
