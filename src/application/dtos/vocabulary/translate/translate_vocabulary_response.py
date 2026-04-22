from application.dtos.base_dto import BaseDTO


class TranslateVocabularyResponse(BaseDTO):
    word: str
    translation_vi: str       # Nghĩa tiếng Việt (từ AWS Translate với context)
    part_of_speech: str = ""  # Loại từ (từ dictionary API, nếu có)
    definition_vi: str = ""   # Định nghĩa tiếng Việt (từ dictionary API, nếu có)
    phonetic: str = ""
    audio_url: str = ""
    example_sentence: str = ""
