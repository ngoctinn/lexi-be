import re

from pydantic import Field, field_validator

from application.dtos.base_dto import BaseDTO


class TranslateVocabularyCommand(BaseDTO):
    word: str = Field(strict=True, min_length=1, max_length=100)

    @field_validator("word")
    @classmethod
    def normalize_word(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.match(r"^[a-zA-Z\s\-']+$", normalized):
            raise ValueError("Word should only contain letters, spaces, hyphens, or apostrophes")
        return normalized
