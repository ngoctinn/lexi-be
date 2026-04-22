from typing import List

from application.dtos.base_dto import BaseDTO


class VocabMeaning(BaseDTO):
    part_of_speech: str
    definition_vi: str
    example_sentence: str = ""


class TranslateVocabularyResponse(BaseDTO):
    word: str
    translation_vi: str
    part_of_speech: str       # Loại từ của meaning đầu tiên (backward compat)
    definition_vi: str        # Định nghĩa của meaning đầu tiên (backward compat)
    phonetic: str = ""
    audio_url: str = ""
    example_sentence: str = ""
    source_api: str = ""
    detected_phrase: str | None = None
    phrase_type: str | None = None
    meanings: List[VocabMeaning] = []  # Tất cả meanings từ dictionary API
