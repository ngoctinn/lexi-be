import re
from typing import Optional

from pydantic import Field
from application.dtos.base_dto import BaseDTO
from domain.value_objects.enums import VocabType

class CreateFlashCardCommand(BaseDTO):
    # Not allowed to casting dynamically
    user_id: str = Field(strict=True, min_length=1)
    vocab_id: str
    
    # Required fields
    vocab_type: VocabType
    
    definition_vi: str

    # Optional fields
    phonetic: Optional[str] = Field(default="")
    audio_url: Optional[str] = Field(default="") # use Http annotation specialized for URL type hint
    example_sentence: str = Field(default="", max_length=500)
    source_api: Optional[str] = Field(default="internal")


    
