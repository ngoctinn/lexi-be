import re
from typing import Optional

from pydantic import Field, field_validator, model_validator

from application.dtos.base_dto import BaseDTO
from domain.value_objects.enums import VocabType

class CreateFlashCardCommand(BaseDTO):
    # Not allowed to casting dynamically
    user_id: str = Field(strict=True, min_length=1)
    vocab: str = Field(
        strict=True, 
        min_length=1, 
        max_length=100,
        pattern=r'^[a-zA-Z\s\-]+$')
    
    # Required fields
    vocab_type: VocabType = Field(...)
    
    definition_vi: str = Field(...)

    # Optional fields
    phonetic: Optional[str] = Field(default="")
    audio_url: Optional[str] = Field(default="") # use Http annotation specialized for URL type hint
    example_sentence: str = Field(default="", max_length=500)
    source_api: Optional[str] = Field(default="internal")


    
