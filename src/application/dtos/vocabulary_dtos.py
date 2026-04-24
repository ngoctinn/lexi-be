import re

from pydantic import Field, field_validator

from application.dtos.base_dto import BaseDTO


class TranslateVocabularyCommand(BaseDTO):
    word: str = Field(strict=True, min_length=1, max_length=100)
    # Câu chứa từ cần dịch — dùng để AWS Translate hiểu đúng ngữ cảnh
    sentence: str | None = Field(default=None, max_length=5000)

    @field_validator("word")
    @classmethod
    def normalize_word(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.match(r"^[a-zA-Z\s\-']+$", normalized):
            raise ValueError("Word should only contain letters, spaces, hyphens, or apostrophes")
        return normalized


class TranslateVocabularyResponse(BaseDTO):
    word: str
    translation_vi: str       # Nghĩa tiếng Việt (từ AWS Translate với context)
    part_of_speech: str = ""  # Loại từ (từ dictionary API, nếu có)
    definition_vi: str = ""   # Định nghĩa tiếng Việt (từ dictionary API, nếu có)
    phonetic: str = ""
    audio_url: str = ""
    example_sentence: str = ""


class TranslateSentenceCommand(BaseDTO):
    # AWS Translate giới hạn 10,000 bytes per request
    # Tăng lên 5000 chars để cover lượt hội thoại dài
    sentence: str = Field(strict=True, min_length=1, max_length=5000)


class TranslateSentenceResponse(BaseDTO):
    sentence_en: str
    sentence_vi: str  # Bản dịch toàn câu bằng AWS Translate
