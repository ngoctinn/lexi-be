from typing import Literal

from application.dtos.base_dto import BaseDTO


class AnalyzeSentenceItem(BaseDTO):
    text: str
    type: Literal["word", "phrase"]
    base: str | None = None
    definition_vi: str | None = None


class AnalyzeSentenceResponse(BaseDTO):
    items: list[AnalyzeSentenceItem]
