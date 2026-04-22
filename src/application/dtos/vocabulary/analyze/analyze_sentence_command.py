from pydantic import Field, field_validator

from application.dtos.base_dto import BaseDTO


class AnalyzeSentenceCommand(BaseDTO):
    text: str = Field(strict=True, min_length=1, max_length=500)

    @field_validator("text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = " ".join(value.strip().split())
        if not normalized:
            raise ValueError("Text không được để trống")
        return normalized
