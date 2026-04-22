from pydantic import Field

from application.dtos.base_dto import BaseDTO


class TranslateSentenceCommand(BaseDTO):
    sentence: str = Field(strict=True, min_length=1, max_length=1000)
