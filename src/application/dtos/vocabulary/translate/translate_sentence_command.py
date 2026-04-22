from pydantic import Field

from application.dtos.base_dto import BaseDTO


class TranslateSentenceCommand(BaseDTO):
    # AWS Translate giới hạn 10,000 bytes per request
    # Tăng lên 5000 chars để cover lượt hội thoại dài
    sentence: str = Field(strict=True, min_length=1, max_length=5000)
