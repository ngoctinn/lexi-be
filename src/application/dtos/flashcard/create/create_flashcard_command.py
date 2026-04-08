import re
from typing import Optional

from pydantic import Field, field_validator, model_validator

from application.dtos.base_dto import BaseDTO

class CreateFlashCardCommand(BaseDTO):
    # Not allowed to casting dynamically
    user_id: str = Field(strict=True, min_length=1)
    vocab: str = Field(strict=True, min_length=1, max_length=100)
    
    # Required fields
    vocab_type: str = Field(...)
    definition_vi: str = Field(...)

    # Optional fields
    phonetic: Optional[str] = Field(default="")
    audio_url: Optional[str] = Field(default="") # use Http annotation specialized for URL type hint
    example_sentence: str = Field(default="", max_length=500)
    source_api: Optional[str] = Field(default="internal")

    # 1. Field Validator: Kiểm tra định dạng từ vựng
    @field_validator('vocab')
    @classmethod
    def validate_no_special_chars(cls, v: str):
        # Đảm bảo từ vựng không chứa ký tự lạ, chỉ cho phép chữ cái và khoảng trắng/gạch nối
        if not re.match(r'^[a-zA-Z\s\-]+$', v):
            raise ValueError('Vocabulary should only contain letters, spaces, or hyphens')
        return v.lower() 

    # 2. Field Validator: Kiểm tra loại từ (Part of Speech)
    @field_validator('vocab_type')
    @classmethod
    def validate_vocab_type(cls, v: str) -> str:
        valid_types = {'n', 'v', 'adj', 'adv', 'prep', 'conj', 'int', 'pron', ''}
        if v.lower() not in valid_types:
            raise ValueError(f'Invalid vocab_type. Must be one of {valid_types}')
        return v.lower()

    # 3. Model Validator: Kiểm tra tính logic giữa các trường
    @model_validator(mode='after')
    def check_audio_if_external_source(self) -> 'CreateFlashCardCommand':
        # Ví dụ: Nếu nguồn từ API ngoài thì bắt buộc phải có audio_url
        if self.source_api != "internal" and not self.audio_url:
            raise ValueError('External API sources must provide an audio_url')
        
        # Kiểm tra nếu có ví dụ thì ví dụ phải chứa từ vựng (vocab)
        if self.example_sentence and self.vocab not in self.example_sentence.lower():
            # Đây là một cảnh báo nhẹ hoặc lỗi tùy bạn quyết định logic nghiệp vụ
            pass 
            
        return self